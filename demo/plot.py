"""
Implementation of eval_plot3d that use numpy to efficiently evaluate Plot3D
(that is, compute a Graphics3D) by using numpy.

Uses compile.demo_compile to compile the function to be plotted into
a Python function that will take numpy arrays for efficient computation of the function.

Generates Graphics3D that contains GraphicsComplex, which is an efficient
representation of graphics objects like meshes. As far as I know this, while standard
Mathematica, is not yet understood by any part of Mathics, although it is understood
by the demo layout functions in graphics.py. 
"""

import collections 
import itertools
import math
import numpy as np
import os

import compile
import mcs
import util

# https://github.com/Mathics3/mathics-core/blob/master/mathics/eval/drawing/plot.py
# https://github.com/Mathics3/mathics-core/blob/master/mathics/eval/drawing/plot3d.py

@util.Timer("demo_eval_plot3d")
def demo_eval_plot3d(
    self,
    functions,
    x, xstart, xstop,
    y, ystart, ystop,
    evaluation: mcs.Evaluation,
    options: dict,
):
    # TODO: handle multiple functions

    # compile the function
    # In the case of Manipulate we are doing this compilation on every slider move.
    # We could lift that compilation into ManipulateBox, but that would require
    # somehow getting it through Plot3D to here. Or we could cache the result.
    # But timings show that would be practically meaningless for performance,
    # so better to spend effort elsewhere.
    x_name, y_name = str(x).split("`")[-1], str(y).split("`")[-1]
    with util.Timer("compile"):
        fun = compile.demo_compile(evaluation, functions, [x_name, y_name]) # XXX

    # compute xs and ys
    nx, ny = options["System`PlotPoints"].to_python() # xxx default values
    xs = np.linspace(xstart.value, xstop.value, nx)
    ys = np.linspace(ystart.value, ystop.value, ny)
    xs, ys = np.meshgrid(xs, ys)

    # compute zs from xs and ys using compiled function
    with util.Timer("compute zs"):
        zs = fun(**{x_name: xs, y_name: ys})

    # sometimes expr gets compiled into something that returns a complex even though the imaginary part is 0
    # TODO: check that imag is all 0?
    # TODO: needed this for Hypergeometric - look into that
    #assert np.all(np.isreal(zs)), "array contains complex values"
    zs = np.real(zs)

    # reshape for GraphicsComplex
    n = math.prod(xs.shape)
    inxs = np.arange(n).reshape(xs.shape)                                                       # shape = (nx,ny)
    quads = np.stack([inxs[:-1,:-1], inxs[:-1,1:], inxs[1:,1:], inxs[1:,:-1]]).T.reshape(-1, 4) # shape = ((nx-1)*(nx-1), 4)
    xyzs = np.stack([xs, ys, zs]).transpose(1,2,0).reshape(-1,3)                                # shape = (nx*ny, 3)

    # ugh - indices in Polygon are 1-based
    quads += 1

    # construct Graphics3D
    # TODO: use class from core
    # TODO: see how the rules get passed on in mathics.builtin.drawing.plot.eval_plot3d and emulate that
    rules = [mcs.Expression(mcs.SymbolRule, mcs.Symbol(n), v) for n, v in options.items()]
    quads_expr = mcs.NumpyArrayListExpression(quads)
    xyzs_expr = mcs.NumpyArrayListExpression(xyzs)
    poly_expr = mcs.Expression(mcs.SymbolPolygon, quads_expr)
    gc_expr = mcs.Expression(mcs.SymbolGraphicsComplex, xyzs_expr, poly_expr)
    result = mcs.Expression(mcs.SymbolGraphics3D, gc_expr, *rules)

    return result

if os.getenv("DEMO_USE_MATHICS_PLOT"):
    print("using mathics plot")
else:
    # for demo monkey-patch it in
    print("using demo plot")
    import mathics.builtin.drawing.plot
    mathics.builtin.drawing.plot.eval_plot3d = demo_eval_plot3d
    mathics.builtin.drawing.plot.Plot3D.attributes = mcs.A_HOLD_FIRST | mcs.A_PROTECTED


