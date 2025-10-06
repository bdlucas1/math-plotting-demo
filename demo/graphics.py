import collections 
import itertools
import numpy as np

import ev
import ex
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
        expr = target_expr.replace_vars({"Global`"+n: mcs.Real(v) for n, v in values.items()})
        expr = ev.eval_expr(fe, expr)
        layout = mode.layout_expr(fe, expr)
        return layout

    # compute the layout for the plot
    init_values = [s.init for s in sliders]
    init_target_layout = eval_and_layout(init_values)
    layout = mode.panel(init_target_layout, sliders, eval_and_layout)
        
    # set timer display for slider updates after initial display
    util.Timer.level = 1 # to see top-level timings as sliders move
    #util.Timer.level = 0 # no timings as sliders move


    return layout


#
# compute a layout for a Graphics3D object, such as returned by Plot3D
#
def layout_Graphics3D(fe, expr):

    xyzs = []
    ijks = []

    def handle_g(g):

        if g.head == mcs.SymbolPolygon:
            poly = [p.value for p in g.elements[0].elements]
            i = len(xyzs)
            xyzs.extend(poly)
            ijks.append([i+1,i+2,i+3]) # ugh - 1-based to match GraphicsComplex Polygon

        elif g.head == mcs.SymbolLine:
            line = [p.value for p in g.elements[0].elements]

        elif g.head == mcs.SymbolGraphicsComplex:

            with util.Timer("xyzs"):
                xyzs.extend(g.elements[0].value)

            def handle_c(c):

                if c.head == mcs.SymbolPolygon:

                    polys = c.elements[0]
                    if isinstance(polys, ex.NumpyArrayListExpr):
                        with util.Timer("ijks from NumpyArrayListExpr"):
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

        else:
            raise Exception(f"Unknown head {g.head}")

    for g in expr.elements:
        handle_g(g)

    # process options
    x_range = y_range = z_range = None
    axes = True
    showscale = False
    colorscale = "viridis"
    width = 400
    height = 350
    for sym, value in ex.get_rule_values(expr):
        if sym == mcs.SymbolPlotRange:
            if not isinstance(value, (list,tuple)):
                value = [value, value, value]
            x_range, y_range, z_range = [v if isinstance(v, (tuple,list)) else None for v in value]
        elif sym == mcs.SymbolAxes:
            axes = value
        elif sym == mcs.SymbolPlotLegends:
            # TODO: what if differs from ColorFunction->?
            # TODO: what if multiple legends requested?
            showscale = True
            # TODO: value sometimes comes through as expr, sometimes as tuple?
            if getattr(value, "head", None) == mcs.SymbolBarLegend:
                # TODO: for some reason value has literal quotes?
                colorscale = str(value.elements[0])[1:-1]
            elif isinstance(value, (tuple,list)):
                colorscale = value[0]
        elif sym == mcs.SymbolColorFunction:
            # TODO: for some reason value is coming through with literal quotes?
            # TODO: what if differs from PlotLegends?
            colorscale = value[1:-1]
        elif sym == mcs.SymbolImageSize:
            # TODO: separate width, height
            width = height = value
        else:
            # TODO: Plot is passing through all options even e.g. PlotPoints
            #print(f"option {sym} not recognized")
            pass

    with util.Timer("construct xyz and ijk arrays"):
        xyzs = np.array(xyzs)
        ijks = np.array(ijks) - 1 # ugh - indices in Polygon are 1-based

    with util.Timer("mode.mes3d_plot"):
        figure = mode.mesh3d_plot(xyzs, ijks, showscale, colorscale, axes, width, height, z_range)

    with util.Timer("layout"):
        layout = mode.graph(figure, height)

    return layout

def layout_Row(fe, expr):
    def do(e):
        # TODO: temp demo hack until we integrate Demo` into system and eliminate ev.eval_expr
        # then this will already have been done
        e = ev.eval_expr(fe, e)
        return mode.layout_expr(fe, e)
    # TODO: expr.elements[1] is a separator
    layout = mode.row([do(e) for e in expr.elements[0].elements])
    return layout

# TODO: I think this should be in mode_unbox.py
def layout_Grid(fe, expr):

    def do(e):
        # TODO: temp demo hack until we integrate Demo` into system and eliminate ev.eval_expr
        # then this will already have been done
        e = ev.eval_expr(fe, e)
        layout = mode.layout_expr(fe, e)
        return layout

    # arrange in a ragged array
    grid_content = [[do(cell) for cell in row] for row in expr.elements[0]]
    layout = mode.grid(grid_content)
    return layout

#
# Compute a layout 
#

layout_funs = {
    mcs.SymbolManipulate: layout_Manipulate,
    mcs.SymbolGraphics3D: layout_Graphics3D,
    mcs.SymbolRow: layout_Row,
    mcs.SymbolGrid: layout_Grid,
}

