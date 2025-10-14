import collections 
import itertools
import numpy as np
import os

import mcs
import mode
import util

#
# Functions related to processing expressions for display using dash and plotly
# by computing a dash layout
#

# compute a unique id for use in html
ids = collections.defaultdict(lambda: 0)
def uid(s):
    ids[s] += 1
    return f"{s}-{ids[s]}"


#
# given a Manipulate Expression, compute a layout
#
# note that on every slider move this evaluates target_expr (e.g. Plot3D),
# which then compiles its expr (e.g. Sin etc.) on every slider move
# we could lift that compilation into Manipulate by compiling target_expr,
# but timings show that would be practically meaningless for performance,
# and it would complicate the implementation
# 

def layout_Manipulate(fe, manipulate_expr):

    target_expr = manipulate_expr.elements[0]
    slider_exprs = manipulate_expr.elements[1:]

    # parse slider specs
    S = collections.namedtuple("S", ["name", "lo", "init", "hi", "step"])
    def slider(e):
        spec = e.to_python()
        v, lo, hi = spec[0:3]
        step = spec[3] if len(spec) > 3 else (hi-lo)/10 # TODO: better default step
        v, init = v if isinstance(v, (list,tuple)) else (v, lo)
        v = str(v).split("`")[-1] # strip off namespace pfx
        spec = S(v, lo, init, hi, step)
        return spec
    sliders = [slider(e) for e in slider_exprs]

    # compute a layout for an expr given a set of values
    # this is the callback for this Manipulate to update the target with new values
    def eval_and_layout(values):
        # TODO: always Global?
        # TODO: always Real?
        # TODO: best order for replace_vars and eval?
        values = {s.name: a for s, a in zip(sliders, values)}
        with util.Timer("replace and eval"):
            expr = target_expr.replace_vars({"Global`"+n: mcs.Real(v) for n, v in values.items()})
            expr = expr.evaluate(fe.session.evaluation)
        with util.Timer("layout"):
            layout = mode.layout_expr(fe, expr)
        return layout

    # compute the layout for the plot
    init_values = [s.init for s in sliders]
    init_target_layout = eval_and_layout(init_values)
    layout = mode.panel(init_target_layout, sliders, eval_and_layout)
        
    return layout


#
# collect options from a Graphics or Graphics3D element
# TODO: this is probably just for the demo, and gets replaced
# by machinery already in place in mathics core
#

def process_options(fe, expr, dim):

    # process options
    # TODO: defaults here or in mode_plotly.py?
    options = mode.Options(
        x_range = None,
        y_range = None,
        z_range = None,
        axes = True,
        showscale = False,
        colorscale = "viridis",
        width = 400,
        height = 350,
    )

    for sym, value in util.get_rule_values(expr):

        # TODO: why are we having to evaluate - shouldn't it be done already by this point?
        # or is there a simpler or more standard way to do this?
        if isinstance(value, mcs.Expression):
            value = mcs.Expression(mcs.Symbol("System`N"), value)
            value = value.evaluate(fe.session.evaluation)
            value = value.to_python()

        # TODO: regularize this
        if sym == mcs.SymbolPlotRange:
            if not isinstance(value, (list,tuple)):
                value = [value, value, value]
            ranges = [v if isinstance(v, (tuple,list)) else None for v in value]
            # TODO: just pass through as tuple?
            if dim == 3:
                options.x_range, options.y_range, options.z_range = ranges
            else:
                options.x_range, options.y_range = ranges
        elif sym == mcs.SymbolAxes:
            # TODO: expand to tuple here or just let flow into plot2d/plot3d?
            options.axes = value if isinstance(value,(tuple,list)) else (value,) * dim
        elif sym == mcs.SymbolPlotLegends:
            # TODO: what if differs from ColorFunction->?
            # TODO: what if multiple legends requested?
            options.showscale = True
            # TODO: value sometimes comes through as expr, sometimes as tuple?
            if getattr(value, "head", None) == mcs.SymbolBarLegend:
                # TODO: for some reason value has literal quotes?
                options.colorscale = str(value.elements[0])[1:-1]
            elif isinstance(value, (tuple,list)):
                options.colorscale = value[0]
        elif sym == mcs.SymbolColorFunction:
            # TODO: for some reason value is coming through with literal quotes?
            # TODO: what if differs from PlotLegends?
            options.colorscale = value[1:-1]
        elif sym == mcs.SymbolImageSize:
            # TODO: separate width, height
            if not isinstance(value, str) and not isinstance(value, mcs.Expression):
                options.width = options.height = value
        elif sym == mcs.SymbolAspectRatio:
            if not isinstance(value, str):
                options.height = value * options.width
        else:
            # TODO: Plot is passing through all options even e.g. PlotPoints
            #print(f"option {sym} not recognized")
            pass

    #options = mode.Options(axes=axes, width=width, height=height, showscale=showscale, colorscale=colorscale)
    return options

#
# traverse a Graphics or Graphics3D expression and collect points, lines, and triangles
# as numpy arrays that are efficient to traverse
#
# TODO: can this be plugged into existing machinery for processing Graphics and Graphics3D?
# there seems to be a bunch of stuff related to this in mathics.format that could be reused,
# but it currently seems to assume that a string is being generated to be saved in a file
#

def collect_graphics(expr):

    # xyzs is numpy array representing coordinates of triangular mesh points
    # ijks is numpy array represent triangles as triples of indexes into xyzs
    xyzs = []
    ijks = []

    # list of lines, each line represented by a numpy array containing
    # coordinates of points on the line
    lines = []

    # numpy array of point coordinates
    points = []

    # options we ignore for now because not implemented
    tbd = set(["System`Hue"])

    def handle_g(g):

        if g.head == mcs.SymbolPolygon:
            poly = [p.value for p in g.elements[0].elements]
            i = len(xyzs)
            xyzs.extend(poly)
            ijks.append([i+1,i+2,i+3]) # ugh - 1-based to match GraphicsComplex Polygon

        elif g.head == mcs.SymbolLine:
            value = g.elements[0].to_python()
            if isinstance(value[0][0], (tuple,list)):
                for line in value:
                    lines.append(np.array(line))
            else:
                lines.append(np.array(value))

        elif g.head == mcs.SymbolPoint:
            ps = g.elements[0].value
            points.extend(ps)

        elif g.head == mcs.SymbolGraphicsComplex:

            with util.Timer("xyzs"):
                xyzs.extend(g.elements[0].value)

            def handle_c(c):

                if c.head == mcs.SymbolPolygon:

                    polys = c.elements[0]
                    if isinstance(polys, mcs.NumpyArrayListExpression):
                        with util.Timer("ijks from NumpyArrayListExpression"):
                            # use advanced indexing to break the polygons down into triangles
                            ngon = polys.value.shape[1]
                            for i in range(1, ngon-1):
                                inx = [0, i, i+1]
                                tris = polys.value[:, inx]
                                ijks.extend(tris)

                    else:
                        with util.Timer("ijks from mathics List of polys"):
                            for poly in polys.elements:
                                for j, k in zip(poly.elements[1:-1], poly.elements[2:]):
                                    ijks.append([poly.elements[0].value, j.value, k.value])

                else:
                    raise Exception(f"Unknown head {c.head} in GraphicsComplex")

            for c in g.elements[1:]:
                handle_c(c)

        elif g.head == mcs.SymbolRule:
            pass

        elif g.head == mcs.SymbolList:
            for gg in g.elements:
                handle_g(gg)

        elif str(g.head) in tbd:
            #print("tbd", g.head)
            pass

        else:
            raise Exception(f"Unknown head {g.head}")

    # collect graphic elements
    for g in expr.elements:
        handle_g(g)

    # finalize to np arrays
    # lines is already in final form: python list of np arrays, each representing a line
    if len(xyzs) and len(ijks):
        with util.Timer("construct xyz and ijk arrays"):
            xyzs = np.array(xyzs)
            ijks = np.array(ijks) - 1 # ugh - indices in Polygon are 1-based
    points = np.array(points)

    return xyzs, ijks, lines, points

# dim=3, mode.plot3d
def layout_Graphics3D(fe, expr):
    xyzs, ijks, lines, points = collect_graphics(expr)
    options = process_options(fe, expr, dim=3)
    # TODO: lines and points are currently ignored
    figure = mode.plot3d(xyzs, ijks, lines, points, options)
    layout = mode.graph(figure, options.height)
    return layout

# dim=2, mode.plot2d
def layout_Graphics(fe, expr):
    xyzs, ijks, lines, points = collect_graphics(expr)
    options = process_options(fe, expr, dim=2)
    # TODO: xyzs, ijks in 2d mode?
    figure = mode.plot2d(lines, points, options)
    layout = mode.graph(figure, options.height)
    return layout

#
#
#

def layout_Row(fe, expr):
    # TODO: expr.elements[1] is a separator
    do = lambda e: mode.layout_expr(fe, e)
    row_content = [do(e) for e in expr.elements[0].elements]
    layout = mode.row(row_content)
    return layout

# TODO: I think this should be in mode_unbox.py
def layout_Grid(fe, expr):
    # arrange in a ragged array
    do = lambda e: mode.layout_expr(fe, e)
    grid_content = [[do(cell) for cell in row] for row in expr.elements[0]]
    layout = mode.grid(grid_content)
    return layout

#
# Compute a layout 
#

layout_funs = {
    mcs.SymbolManipulate: layout_Manipulate,
    mcs.SymbolGraphics3D: layout_Graphics3D,
    mcs.SymbolGraphics: layout_Graphics,
    mcs.SymbolRow: layout_Row,
    mcs.SymbolGrid: layout_Grid,
}

