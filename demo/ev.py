import collections 
import itertools
import math
import numpy as np

import compile
import mcs
import util

#
#
#

# https://github.com/Mathics3/mathics-core/blob/master/mathics/eval/drawing/plot.py
# https://github.com/Mathics3/mathics-core/blob/master/mathics/eval/drawing/plot3d.py

# given a Plot3D expr, evaluate it on a grid of xs and ys, generating zs,
# as directed by Plot3D options
def eval_plot3d_xyzs(fe, expr):

    # Plot3D arg exprs
    fun_expr = expr.elements[0]
    xlims_expr = expr.elements[1]
    ylims_expr = expr.elements[2]

    # process rules that we understand
    # rules that we don't consume remain in rules to be passed through to Graphics output
    # TODO: use symbol, not string
    # TODO: hook into existing infrastructure for plotting
    x_points = y_points = 10 # default
    for sym, value in util.get_rule_values(expr):
        if sym == mcs.SymbolPlotPoints:
            if isinstance(value, (tuple,list)):
                x_points, y_points = value
            else:
                x_points = y_points = value

    # compile fun
    fun_args = [str(xlims_expr.elements[0]), str(ylims_expr.elements[0])]
    fun = compile.my_compile(fe.session.evaluation, fun_expr, fun_args)

    # parse xlims, construct namedtuple
    # TODO: namedtuple probably not needed any more
    A = collections.namedtuple("A", ["name", "lo", "hi", "count"])
    def to_python_axis_spec(expr, pts):
        return A(str(expr.elements[0]).split("`")[-1], *[e.to_python() for e in expr.elements[1:]], pts)
    xlims = to_python_axis_spec(xlims_expr, x_points)
    ylims = to_python_axis_spec(ylims_expr, y_points)

    # parse zlims
    #zlims = [zlims_expr.elements[0].value, zlims_expr.elements[1].value] if zlims_expr else None

    # compute xs and ys
    xs = np.linspace(xlims.lo, xlims.hi, xlims.count)
    ys = np.linspace(ylims.lo, ylims.hi, ylims.count)
    xs, ys = np.meshgrid(xs, ys)

    # compute zs from xs and ys using compiled function
    zs = fun(**{xlims.name: xs, ylims.name: ys})

    # sometimes expr gets compiled into something that returns a complex even though the imaginary part is 0
    # TODO: check that imag is all 0?
    # TODO: needed this for Hypergeometric - look into that
    #assert np.all(np.isreal(zs)), "array contains complex values"
    zs = np.real(zs)

    return xs, ys, zs


# given a grid of xs, ys, zs, generate a Graphics object using a GraphicsComplex,
# which consists of a list of points and a list of polys,
# each poly being a list of indices in the list of points
# np_expr tells us how to turn a numpy array into an Expression; may be either
#     numpy_array_list_expr which instantiates a List of List (slow), or
#     NumpyArrayListExpr which wraps a numpy array and lazily instatiates .elements iff requested
def grid_to_graphics_complex(xs, ys, zs, np_expr):
    
    n = math.prod(xs.shape)
    inxs = np.arange(n).reshape(xs.shape)                                                       # shape = (nx,ny)
    quads = np.stack([inxs[:-1,:-1], inxs[:-1,1:], inxs[1:,1:], inxs[1:,:-1]]).T.reshape(-1, 4) # shape = ((nx-1)*(nx-1), 4)
    xyzs = np.stack([xs, ys, zs]).transpose(1,2,0).reshape(-1,3)                                # shape = (nx*ny, 3)

    # ugh - indices in Polygon are 1-based
    quads += 1

    quads_expr = np_expr(quads)
    xyzs_expr = np_expr(xyzs)
    poly_expr = mcs.Expression(mcs.SymbolPolygon, quads_expr)
    gc_expr = mcs.Expression(mcs.SymbolGraphicsComplex, xyzs_expr, poly_expr)
    result = mcs.Expression(mcs.SymbolGraphics3D, gc_expr)
    
    return result

def eval_Plot3D(fe, expr):
    xs, ys, zs = eval_plot3d_xyzs(fe, expr)
    graphics = grid_to_graphics_complex(xs, ys, zs, mcs.NumpyArrayListExpression)
    # append rules to the graphics
    # TODO: only pass through the ones we don't consume ourselfs?
    # TODO: is modifying elements like this legit?
    graphics.elements = graphics.elements + tuple(util.get_rules(expr))
    return graphics

# previous slower implementations retained only for timing purposes
# uncomment for timing by overriding eval_Plot3D 
# CAREFUL!
###from ev_slow1 import eval_Plot3D
###from ev_slow2 import eval_Plot3D

# TODO: this is temporary until I figure out how to hook eval_Plot3D into expr.evaluate
funs = {
    "Demo`Plot3D": eval_Plot3D,
}
def eval_expr(fe, expr, quiet=False):
    if not hasattr(expr, "head"):
        return expr
    with util.Timer(f"eval {expr.head}"):
        if str(expr.head) in funs:
            result = funs[str(expr.head)](fe, expr)
        else:
            result = expr.evaluate(fe.session.evaluation)
    #util.prt(result)
    return result


