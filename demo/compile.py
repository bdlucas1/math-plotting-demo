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
import util

# TODO: to build this out, look for
# mpmath_name
# symbol_name
# Greater etc. from mathics.builtin.testing_expressions.equality_inequality
# If from mathics.builtin.procedural
# Plus from mathics.builtin.arithfns
# what else?


lib="np"
#lib=math

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
    mcs.SymbolLessEqual: "<=",
}

symbols = {
    mcs.SymbolI: "1j",
    mcs.SymbolE: f"{lib}.e",
    mcs.SymbolNull: "None"
}

def strip_context(s):
    return str(s).split("`")[-1]

class Ctx:

    fun_number = 0

    def __init__(self):
        self.stmts = []

    def next_identifier(s="fun"):
        Ctx.fun_number += 1
        return f"__{s}{Ctx.fun_number}"

    def to_python_expr(self, expr):

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

        elif expr.head == mcs.SymbolModule:

            ctx = Ctx()
            fun = Ctx.next_identifier("module")
            def do(e):
                if isinstance(e, mcs.Symbol):
                    print("xxx just a var", type(e))
                    # just a variable, not a Set
                    return ctx.to_python_expr(e) + " = " + "..."
                else:
                    return ctx.to_python_expr(e)
            head = [do(e) for e in expr.elements[0].elements]
            value = (ctx.to_python_expr(expr.elements[1]))
            body = [*head, *ctx.stmts, f"return {value}"]
            self.stmts.append(f"def {fun}():")
            self.stmts.append(body)
            return f"{fun}()"            

        elif expr.head == mcs.SymbolCompoundExpression:

            # TODO: don't need a function here
            fun = Ctx.next_identifier("compound")
            def do(e):
                if hasattr(e,"head") and e.head == mcs.SymbolSet:
                    yield f"nonlocal {strip_context(e.elements[0])}"
                yield self.to_python_expr(e)
            body = list(s for e in expr.elements for s in do(e))
            print("xxx body", body)
            body[-1] = "return " + body[-1]
            self.stmts.append(f"def {fun}():")
            self.stmts.append(body)

            #self.stmts.extend(self.to_python_expr(e) for e in expr.elements)

            return f"{fun}()"            

        elif expr.head == mcs.SymbolFor:

            value = Ctx.next_identifier("for")

            init = self.to_python_expr(expr.elements[0])
            test = self.to_python_expr(expr.elements[1])
            incr = self.to_python_expr(expr.elements[2])
            body = self.to_python_expr(expr.elements[3])
            
            self.stmts.append(init)
            self.stmts.extend([f"while {test}:", [f"{value} = {body}", incr]])

            # TBD: is this the correct value?
            return value

        elif expr.head == mcs.SymbolSet:

            rhs = self.to_python_expr(expr.elements[1])
            result = f"{strip_context(expr.elements[0])} = {rhs}"
            return result

        elif expr.head == mcs.SymbolIncrement:

            # TODO - returns old value
            result = f"{strip_context(expr.elements[0])} += 1"            

        elif expr.head == mcs.SymbolAddTo:

            # TODO - returns new value
            by = self.to_python_expr(expr.elements[1])
            result = f"{strip_context(expr.elements[0])} += {by}"
            return result

        elif expr.head == mcs.SymbolTimesBy:

            # TODO - returns new value
            by = self.to_python_expr(expr.elements[1])
            result = f"{strip_context(expr.elements[0])} *= {by}"
            return result

        elif expr.head == mcs.SymbolDivideBy:

            # TODO - returns new value
            by = self.to_python_expr(expr.elements[1])
            result = f"{strip_context(expr.elements[0])} /= {by}"
            return result

        elif expr.head in funs:
            fun = funs[expr.head]
            args = (self.to_python_expr(e) for e in expr.elements)
            result = f"{fun}({",".join(args)})"
        elif expr.head in listfuns:
            fun = listfuns[expr.head]
            args = (self.to_python_expr(e) for e in expr.elements)
            result = f"{fun}([{",".join(args)}])"
        elif expr.head in binops:
            arg1 = self.to_python_expr(expr.elements[0])
            arg2 = self.to_python_expr(expr.elements[1])
            result = f"({arg1}{binops[expr.head]}{arg2})"
        else:
            raise Exception(f"Unknown head {expr.head} in {expr}")
        #print("compile", expr, "->", result)
        return result

    def stmts_to_string(self):
        def indent_stmts(stmts, indent=-1): # TODO: hmm
            if isinstance(stmts, str):
                yield f"{' ' * (4 * indent)}{stmts}"
            elif isinstance(stmts, (list,tuple)):
                for d in stmts:
                    yield from indent_stmts(d, indent = indent + 1)
        return "\n".join(indent_stmts(self.stmts))

def demo_compile(evaluation, expr, arg_names, lib = "np"):

    #Ctx.lib = lib # TODO: not actually hooked up

    # get the pieces
    ctx = Ctx()
    top_fun = Ctx.next_identifier("compiled")
    arg_list = ",".join(strip_context(n) for n in arg_names)
    python_expr = ctx.to_python_expr(expr)

    # put them together
    top = Ctx()
    top.stmts = [f"def {top_fun}({arg_list}):", [*ctx.stmts, f"return {python_expr}"]]
    top = top.stmts_to_string()

    #print("compiling:"); util.prt(expr)
    #print("compiled:"); print(top)

    # compute the top-level function
    ns = locals()
    exec(top, globals(), ns)
    return ns[top_fun]

