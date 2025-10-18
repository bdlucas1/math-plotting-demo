"""
Layout functions for GraphicsBox, Graphics3DBox, and ManipulateBox.
These functions are called by expression_to_layout in layout.py; see
comment there for general explanation of layouts.
"""

import collections 
import itertools
import numpy as np
import os

from mathics.core.builtin import Builtin
from mathics.core.load_builtin import add_builtins

import layout as lt
import mcs
import mode
import util

#
# Manipulate builtin
#

class Manipulate(Builtin):

    attributes = mcs.A_HOLD_FIRST

    # TODO: expr is held so it arrives here safely, but for some reason by the time it
    # gets to eval_makeboxes it has some funky HoldForm's interspersed. To see that,
    # comment this eval out and look at the expr in eval_makeboxes. Don't know why or how to avoid.
    # So hack: immediately turn it into a String, then re-parse in eval_makeboxes.
    # There must be a better way.
    def eval(self, evaluation, expr, sliders):
        "Manipulate[expr_, sliders___]"
        if not isinstance(expr, mcs.String):
            return mcs.Expression(mcs.SymbolManipulate, mcs.String(str(expr)), sliders)
        return None

    def eval_makeboxes(self, evaluation, expr, sliders, form, *args, **kwargs):
        "MakeBoxes[Manipulate[expr_, sliders___], form:StandardForm|TraditionalForm|OutputForm|InputForm]"
        expr = evaluation.parse(expr.value) # hack - see note above
        return ManipulateBox(expr, sliders)


    """
    options = {
        "Axes": "{False, True}",
        "AspectRatio": "1 / GoldenRatio",
    }
    """

# TODO: Mathematica does something more complicated, and, I think,
# more general here. Do we need to also? Investigate whether there are
# other functions besides Manipulate that might generate an
# interactive ui.
class ManipulateBox(mcs.BoxExpression):
    def __init__(self, expr, sliders):
        super().__init__(self, expr, sliders)

# regarding expression=False: see mathics/core/builtin.py:221 "can be confusing"
add_builtins([("System`Manipulate", Manipulate(expression=False))])


#
# given a ManipulateBox Expression, compute a layout
#

def layout_ManipulateBox(fe, manipulate_expr):

    target_expr = manipulate_expr.elements[0]
    slider_expr = manipulate_expr.elements[1]

    # TODO: slider_expr came from matching an ___ pattern in Manipulate (see above)
    # According to Mathematica documentation(?), the ___ notation is meant to take
    # the rest of elements and wrap them in a List, even if there is only one.
    # Instead we get just the element if only one, and the elements in a Sequence (not List) if >1
    # Am I doing something wrong or misunderstanding?
    if slider_expr.head == mcs.SymbolSequence:
        slider_specs = [s.to_python() for s in slider_expr.elements]
    else:
        slider_specs = [slider_expr.to_python()]

    # parse slider specs
    S = collections.namedtuple("S", ["name", "lo", "init", "hi", "step"])
    def slider(spec):
        v, lo, hi = spec[0:3]
        step = spec[3] if len(spec) > 3 else (hi-lo)/10 # TODO: better default step
        v, init = v if isinstance(v, (list,tuple)) else (v, lo)
        v = str(v).split("`")[-1] # strip off namespace pfx
        spec = S(v, lo, init, hi, step)
        return spec
    sliders = [slider(spec) for spec in slider_specs]

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
            layout = lt.expression_to_layout(fe, expr)
        return layout

    # compute the layout for the plot
    init_values = [s.init for s in sliders]
    init_target_layout = eval_and_layout(init_values)
    layout = mode.manipulate(init_target_layout, sliders, eval_and_layout)
        
    return layout


#
# collect options from a Graphics or Graphics3D element
# TODO: see Graphics[3D]Box._prepare_elements
#

def process_options(fe, expr, dim):

    # process options
    # TODO: defaults come from get_option_values - eliminate these?
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

    graphics_options = expr.get_option_values(expr.elements[1:])
    if graphics_options:
        graphics_options = ((mcs.Symbol(k), v.to_python()) for k, v in graphics_options.items())
    else:
        # TODO: non-boxed case - remove when we go fully boxed?
        graphics_options = util.get_rule_values(expr)

    # get_option_values supplies default values
    # TODO: see get_option_values impl - there may be some value in passing in an evaluation here
    for sym, value in graphics_options:

        #sym = mcs.Symbol(sym) # TODO or change the below to strings
        #value = value.to_python()

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

        if g.head == mcs.SymbolPolygon or g.head == mcs.SymbolPolygon3DBox:
            poly = [p.value for p in g.elements[0].elements]
            i = len(xyzs)
            xyzs.extend(poly)
            ijks.append([i+1,i+2,i+3]) # ugh - 1-based to match GraphicsComplex Polygon

        elif g.head == mcs.SymbolLine or g.head == mcs.SymbolLineBox or g.head == mcs.SymbolLine3DBox:
            value = g.elements[0].to_python()
            if len(value) and len(value[0]) and isinstance(value[0][0], (tuple,list)):
                for line in value:
                    lines.append(np.array(line))
            elif len(value):
                lines.append(np.array(value))

        elif g.head == mcs.SymbolPoint or g.head == mcs.SymbolPointBox:
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


# dim=2, mode.plot2d
def layout_GraphicsBox(fe, expr):
    xyzs, ijks, lines, points = collect_graphics(expr)
    options = process_options(fe, expr, dim=2)
    # TODO: xyzs, ijks in 2d mode?
    figure = mode.plot2d(lines, points, options)
    layout = mode.graph(figure, options.height)
    return layout

# dim=3, mode.plot3d
def layout_Graphics3DBox(fe, expr):
    options = process_options(fe, expr, dim=3)
    xyzs, ijks, lines, points = collect_graphics(expr)
    figure = mode.plot3d(xyzs, ijks, lines, points, options)
    layout = mode.graph(figure, options.height)
    return layout

layout_funs = {
    mcs.SymbolManipulateBox: layout_ManipulateBox,
    mcs.SymbolGraphicsBox: layout_GraphicsBox,
    mcs.SymbolGraphics3DBox: layout_Graphics3DBox,
}

