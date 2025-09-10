import time
import math
import numpy as np

from typing import Optional
from math import cos, isinf, isnan, pi, sqrt

# this needs pip install llvmlite to work
from mathics.compile import CompileArg, CompileError, _compile, real_type
from mathics.core.expression import Expression
from mathics.core.symbols import SymbolN, SymbolTrue
from mathics.core.atoms import Integer, Integer0, Real
from mathics.builtin.scoping import dynamic_scoping
from mathics.session import MathicsSession
from mathics.builtin.numeric import chop

# https://github.com/Mathics3/mathics-core/blob/master/mathics/eval/drawing/plot.py
def compile_quiet_function(expr, arg_names, evaluation, has_compile, list_is_expected: bool = False):
    """
    Given an expression return a quiet callable version.
    Compiles the expression where possible.
    """
    if has_compile and not list_is_expected:
        try:
            cfunc = _compile(
                expr, [CompileArg(arg_name, real_type) for arg_name in arg_names]
            )
        except CompileError as e:
            print(e)
            pass
        else:
            def quiet_cf(*args):
                try:
                    result = cfunc(*args)
                    if not (isnan(result) or isinf(result)):
                        return result
                except Exception:
                    pass
                return None

            return quiet_cf

    expr: Optional[Type[BaseElement]] = Expression(SymbolN, expr).evaluate(evaluation)

    def quiet_f(*args):
        old_quiet_all = evaluation.quiet_all
        evaluation.quiet_all = True
        vars = {arg_name: Real(arg) for arg_name, arg in zip(arg_names, args)}
        value = dynamic_scoping(expr.evaluate, vars, evaluation)
        evaluation.quiet_all = old_quiet_all
        if list_is_expected:
            if value.has_form("List", None):
                value = [extract_pyreal(item) for item in value.elements]
                if any(item is None for item in value):
                    return None
                return value
            else:
                return None
        else:
            value = extract_pyreal(value)
            if value is None or isinf(value) or isnan(value):
                return None
            return value

    return quiet_f

def extract_pyreal(value) -> Optional[float]:
    if isinstance(value, (Real, Integer)):
        return chop(value).round_to_float()
    return None


#
# my quick hack compilation to python expr
# lib argument determines whether to use np or math lib for things like sin and sqrt
#

def to_python_expr(expr, lib = "np"):

    funs = {
        "System`Sin": f"{lib}.sin",
        "System`Cos": f"{lib}.cos",
        "System`Sqrt": f"{lib}.sqrt"
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
            return str(expr).split("`")[1]
        else:
            return str(expr)
    elif str(expr.head) in funs:
        fun = funs[str(expr.head)]
        args = (to_python_expr(e,lib) for e in expr.elements)
        return f"{fun}({",".join(args)})"
    elif str(expr.head) in listfuns:
        fun = listfuns[str(expr.head)]
        args = (to_python_expr(e,lib) for e in expr.elements)
        return f"{fun}([{",".join(args)}])"
    elif str(expr.head) in binops:
        arg1 = to_python_expr(expr.elements[0],lib)
        arg2 = to_python_expr(expr.elements[1],lib)
        return f"({arg1}{binops[str(expr.head)]}{arg2})"
    else:
        raise Exception(f"Unknown head {expr.head}")

def my_compile(expr, arg_names, lib = "np"):
    python_expr = to_python_expr(expr, lib)
    python_arg_names = [n.split("`")[1] for n in arg_names]
    arg_list = ','.join(python_arg_names)
    python_def = f"lambda {arg_list}: {python_expr}"
    f = eval(python_def)
    return f

#
#
#

def choose_compile(expr, arg_names, method):
    if method == "none":
        return compile_quiet_function(expr, arg_names, session.evaluation, False)
    elif method == "llvm":
        return compile_quiet_function(expr, arg_names, session.evaluation, True)
    elif method == "python_math":
        return my_compile(expr, arg_names, "math")
    elif method == "python_np" or method == "python_np_vec":
        return my_compile(expr, arg_names, "np")

#
#
#

session = MathicsSession()


expr_str = "Sin[(x^2+y^2)*freq]*amp"
#expr_str = "Sin[(x^2+y^2)*freq] / Sqrt[x^2+y^2+1] * amp"

expr = session.parse(expr_str)

#method = "none"   #  9985 ms,  15838 ms
#method = "llvm"   # 14 ms, 15749 ms
#method = "python_math" # 10 ms, 16 ms
#method = "python_np" # 20 ms, 37 ms
method = "python_np_vec" # 0.3 ms, 0.4 ms (0.2 ms @ n=10)

fun = choose_compile(expr, ["Global`x", "Global`y", "Global`freq", "Global`amp"], method)

# 40000 points (like a 200x200 grid)
xs = np.linspace(0, 10, 40000)
ys = np.linspace(0, 10, 40000)

def timefun(f, n=1):
    start = time.time()
    for i in range(n):
        f()
    print(f"{(time.time()-start)/n*1000:.3f} ms")

def f():
    if method == "python_np_vec":
        fun(xs, ys, 1.5, 1.2)
    else:
        for x, y in zip(xs, ys):
            fun(float(x), float(y), 1.5, 1.2)

timefun(f, n=1)
