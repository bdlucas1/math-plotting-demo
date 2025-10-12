import collections 
import itertools
import math
import numpy as np

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
    # compile fun
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
    rules = [mcs.Expression(mcs.SymbolRule, mcs.Symbol(n), v) for n, v in options.items()]
    quads_expr = mcs.NumpyArrayListExpression(quads)
    xyzs_expr = mcs.NumpyArrayListExpression(xyzs)
    poly_expr = mcs.Expression(mcs.SymbolPolygon, quads_expr)
    gc_expr = mcs.Expression(mcs.SymbolGraphicsComplex, xyzs_expr, poly_expr)
    result = mcs.Expression(mcs.SymbolGraphics3D, gc_expr, *rules)

    return result

# for demo monkey-patch it in
import mathics.builtin.drawing.plot
mathics.builtin.drawing.plot.eval_plot3d = demo_eval_plot3d


