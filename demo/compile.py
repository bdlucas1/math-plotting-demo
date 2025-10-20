"""
Cheap and cheerful demo compilaton function that compiles a Mathics expression
into a Python expression using numpy functions that take numpy arrays as arguments.
Used by plot.demo_eval_plot3d for efficient computation of functions to be plotted.

TODO: An alternative might be to find all the places where mpmath or sympy are used
to evaluate something and teach them instead to call numpy if args are numpy array(s).
For the Plot3D case this would give essentially the same performance because
essentially all the execution time is being spent in numpy, and relatively speaking
very little is spent in the non-numpy part of the expression evaluation, so the
conversion to a Python expression is actually buying very little in terms of
performance - essentially all the perform gain comes from using
Python vectorized functions.
"""

import math
import numpy as np
import scipy

import mcs

def hyppfq(p, q, x):
    if len(p) == 1 and len(q) == 1:
        return scipy.special.hyp1f1(p[0], q[0], x)
    else:
        raise Exception(f"can't handle hyppfq({p}, {q}, x)")

def gamma(*args):
    if len(args) == 1:
        return scipy.special.gamma(args[0])
    elif len(args) == 2:
        a, x = args
        return scipy.special.gammainc(a, np.abs(x)) # TODO: is np.abs correct?
    else:
        raise Exception(f"gamma with {len(args)} args")

def arctan(*args):
    if len(args) == 1:
        return np.arctan(args[0])
    elif len(args) == 2:
        return np.arctan2(*args)
    else:
        raise Exception(f"arctan with {len(args)} args")


def to_python_expr(expr, lib = "np"):

    # TODO: to build this out, look for
    # mpmath_name
    # symbol_name
    # Greater etc. from mathics.builtin.testing_expressions.equality_inequality
    # If from mathics.builtin.procedural
    # Plus from mathics.builtin.arithfns
    # what else?

    funs = {

        # TODO: this can generate discontinuous plots - need mechanism for segmented results?
        # This is a more general problem though - compare Plot[If[x>0.1, 1, -1],{x,-1,1}] in Mathematica vs Mathics
        mcs.SymbolIf: f"{lib}.where",

        mcs.SymbolSin: f"{lib}.sin",
        mcs.SymbolCos: f"{lib}.cos",
        mcs.SymbolSqrt: f"{lib}.sqrt",
        mcs.SymbolAbs: f"{lib}.abs",
        mcs.SymbolArcTan: "arctan",

        # just do Hypergemetric, no simplification
        mcs.Symbol("Demo`Hypergeometric1F1"): "scipy.special.hyp1f1",

        # following are subtitutions made in evaluating System`Hypergeometric1F1
        mcs.SymbolHypergeometricPFQ: "hyppfq", # TODO is this defined in some import?
        mcs.SymbolGamma: "gamma",
        # System`exp_polar
        # System`BesselI
    }

    listfuns = {
        mcs.SymbolList: "list",
        mcs.SymbolPlus: "sum", # TODO: np.sum?
        mcs.SymbolTimes: "math.prod", # TODO: np.prod?
    }

    binops = {
        mcs.SymbolPower: "**",
        mcs.SymbolGreater: ">",
    }

    symbols = {
        mcs.SymbolI: "1j",
        mcs.SymbolE: f"{lib}.e"
    }

    if not hasattr(expr, "head"):
        if str(expr).startswith("Global`"):
            result = str(expr).split("`")[-1]
        elif expr in symbols:
            result = symbols[expr]
        elif str(expr) == "I":
            # TODO: where does this come from??
            result = "1j"
        else:
            result = str(expr)
    elif expr.head in funs:
        fun = funs[expr.head]
        args = (to_python_expr(e,lib) for e in expr.elements)
        result = f"{fun}({",".join(args)})"
    elif expr.head in listfuns:
        fun = listfuns[expr.head]
        args = (to_python_expr(e,lib) for e in expr.elements)
        result = f"{fun}([{",".join(args)}])"
    elif expr.head in binops:
        arg1 = to_python_expr(expr.elements[0],lib)
        arg2 = to_python_expr(expr.elements[1],lib)
        result = f"({arg1}{binops[expr.head]}{arg2})"
    else:
        raise Exception(f"Unknown head {expr.head} in {expr}")
    #print("compile", expr, "->", result)
    return result

def demo_compile(evaluation, expr, arg_names, lib = "np"):
    python_expr = to_python_expr(expr, lib)
    python_arg_names = [n.split("`")[-1] for n in arg_names]
    arg_list = ','.join(python_arg_names)
    python_def = f"lambda {arg_list}: {python_expr}"
    f = eval(python_def)
    return f
