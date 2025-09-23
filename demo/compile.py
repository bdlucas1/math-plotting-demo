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
        raise Exception(f"gamma with {len(gamma)} args")

def to_python_expr(expr, lib = "np"):

    funs = {
        mcs.SymbolSin: f"{lib}.sin",
        mcs.SymbolCos: f"{lib}.cos",
        mcs.SymbolSqrt: f"{lib}.sqrt",
        mcs.SymbolAbs: f"{lib}.abs",

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
        #print("xxx fun", expr.head)
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

def my_compile(evaluation, expr, arg_names, lib = "np"):
    expr = expr.evaluate(evaluation) # pick up e.g. parameters for Plot. TODO: is this the right place?
    python_expr = to_python_expr(expr, lib)
    python_arg_names = [n.split("`")[-1] for n in arg_names]
    arg_list = ','.join(python_arg_names)
    python_def = f"lambda {arg_list}: {python_expr}"
    f = eval(python_def)
    return f
