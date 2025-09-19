import math
import numpy as np
import scipy

import mat

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
        mat.SymbolSin: f"{lib}.sin",
        mat.SymbolCos: f"{lib}.cos",
        mat.SymbolSqrt: f"{lib}.sqrt",
        mat.SymbolAbs: f"{lib}.abs",
        # TOOD: eval turns System`... into HypergeometricPFQ; need polyfill for that
        mat.Symbol("My`Hypergeometric1F1"): "scipy.special.hyp1f1",
        mat.SymbolHypergeometricPFQ: "hyppfq", # TODO is this defined in some import?
        mat.SymbolGamma: "gamma",
    }

    listfuns = {
        mat.SymbolList: "list",
        mat.SymbolPlus: "sum", # TODO: np.sum?
        mat.SymbolTimes: "math.prod", # TODO: np.prod?
    }

    binops = {
        mat.SymbolPower: "**",
    }

    symbols = {
        mat.SymbolI: "1j",
        mat.SymbolE: f"{lib}.e"
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

def my_compile(evaluation, expr, arg_names, lib = "np"):
    expr = expr.evaluate(evaluation) # pick up e.g. parameters for Plot. TODO: is this the right place?
    python_expr = to_python_expr(expr, lib)
    python_arg_names = [n.split("`")[-1] for n in arg_names]
    arg_list = ','.join(python_arg_names)
    python_def = f"lambda {arg_list}: {python_expr}"
    f = eval(python_def)
    return f
