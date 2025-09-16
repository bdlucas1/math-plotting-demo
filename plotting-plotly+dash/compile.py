import math
import numpy as np
import scipy

def to_python_expr(expr, lib = "np"):

    funs = {
        "System`Sin": f"{lib}.sin",
        "System`Cos": f"{lib}.cos",
        "System`Sqrt": f"{lib}.sqrt",
        "System`Abs": f"{lib}.abs",
        # TOOD: eval turns System`... into HypergeometricPFQ; need polyfill for that
        "My`Hypergeometric1F1": "scipy.special.hyp1f1",
    }

    listfuns = {
        "System`Plus": "sum", # TODO: np.sum?
        "System`Times": "math.prod" # TODO: np.prod?

    }

    binops = {
        "System`Power": "**",
    }

    if not hasattr(expr, "head"):
        if str(expr).startswith("Global`"):
            result = str(expr).split("`")[-1]
        elif str(expr) == "System`I" or str(expr) == "I":
            result = "1j"
        else:
            result = str(expr)
    elif str(expr.head) in funs:
        fun = funs[str(expr.head)]
        args = (to_python_expr(e,lib) for e in expr.elements)
        result = f"{fun}({",".join(args)})"
    elif str(expr.head) in listfuns:
        fun = listfuns[str(expr.head)]
        args = (to_python_expr(e,lib) for e in expr.elements)
        result = f"{fun}([{",".join(args)}])"
    elif str(expr.head) in binops:
        arg1 = to_python_expr(expr.elements[0],lib)
        arg2 = to_python_expr(expr.elements[1],lib)
        result = f"({arg1}{binops[str(expr.head)]}{arg2})"
    else:
        raise Exception(f"Unknown head {expr.head}")
    #print("compile", expr, "->", result)
    return result

def my_compile(expr, arg_names, lib = "np"):
    python_expr = to_python_expr(expr, lib)
    python_arg_names = [n.split("`")[-1] for n in arg_names]
    arg_list = ','.join(python_arg_names)
    python_def = f"lambda {arg_list}: {python_expr}"
    f = eval(python_def)
    return f
