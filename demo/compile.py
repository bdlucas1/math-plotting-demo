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
    mcs.SymbolNull: "None",
    mcs.SymbolPi: "math.pi"
}

def strip_context(s):
    return str(s).split("`")[-1]


# Scope rules are different from Python, so we explicitly
# manage scope. All variable access and update go through here.
# TODO: check whether these scope rules are really correct

class Scope:

    # initialize the scope with a name, a parent scope,
    # and a set of initial values as kwargs
    def __init__(self, name, parent, **kwargs):
        self.name = name
        self.parent = parent
        for n, v in kwargs.items():
            setattr(self, n, v)
            
    # determine what scope attr should be resolved in
    def scope(self, attr):
        if hasattr(self, attr):
            return self
        elif self.parent is not None:
            return self.parent.scope(attr)
        else:
            raise Exception(f"Variable {attr} not found in an any scope")

    # get the value of an attr from this or parent scope
    def get(self, attr):
        scope = self.scope(attr)
        return getattr(scope, attr)

    # set the attr to a new value and return the new value
    # for things like =, AddTo, etc.
    # TODO: check this
    def set(self, attr, value):
        scope = self.scope(attr)
        setattr(scope, attr, value)
        return value

    # set the attr to a new value and return the old value
    # for things like Increment
    # TODO: check this
    def set_old(self, attr, value):
        scope = self.scope(attr)
        old = getattr(scope, attr)
        setattr(scope, attr, value)
        return old

# Sequential constructs like CompoundExpression, Module, and For also have a value,
# unlike Python. So we implement them as a function that executes a series of statements,
# then the compiled code calls the function to execute the statements and get a value.
# Main entry point is to_python_expr which collects a series of statements and returns
# string which is the code to get the value of that expression, which will be function call
# that executes the statements and gets the value.
#
# TODO: check the above description

class Ctx:

    fun_number = 0

    def __init__(self, kind, has_scope=False, parent_scope=None, arg_names=[], scope_vars=[]):

        self.name = Ctx.next_identifier(kind)
        self.arg_names = arg_names
        self.value = f"{self.name}(__)"

        if has_scope:
            vals = ", ".join(f"{n}={v}" for n, v in scope_vars)
            self.stmts = [f"__ = Scope('{self.name}', {parent_scope}, {vals})"]
        else:
            self.stmts = []
        
    def next_identifier(s="fun"):
        Ctx.fun_number += 1
        return f"__{s}{Ctx.fun_number}"

    def append_stmt(self, stmt_expr):
        value = self.to_python_expr(stmt_expr)
        self.stmts.append(value)

    def emit(self, parent):
        arg_names = ["__", *(strip_context(n) for n in self.arg_names)]
        parent.stmts.append(f"def {self.name}({", ".join(arg_names)}):")
        if len(self.stmts) and not isinstance(self.stmts[-1], (list,tuple)):
            self.stmts[-1] = "return " + str(self.stmts[-1])
        else:
            print("xxx not returning", self.stmts)
        parent.stmts.append(self.stmts)

    def to_python_expr(self, expr):

        # helper for update operators like =, +=, *=, ++, et.
        def update(expr, update, method):
            target = strip_context(expr.elements[0])
            rhs = self.to_python_expr(expr.elements[1]) if len(expr.elements) > 1 else None
            lhs = self.to_python_expr(expr.elements[0])
            value = update.format(lhs=lhs, rhs=rhs)
            result = f"__.{method}('{target}', {value})"
            return result

        if not hasattr(expr, "head"):
            if str(expr).startswith("Global`"):
                var = str(expr).split("`")[-1]
                result = f"__.get('{var}')"
            elif expr in symbols:
                result = symbols[expr]
            elif str(expr) == "I":
                # TODO: where does this come from??
                result = "1j"
            else:
                result = str(expr)

        elif expr.head == mcs.SymbolModule:

            #head = expr.elements[0]
            body = expr.elements[1]

            scope_vars = []
            for e in expr.elements[0].elements:
                if hasattr(e, "head") and e.head == mcs.SymbolSet:
                    var = strip_context(str(e.elements[0]))
                    val = self.to_python_expr(e.elements[1])
                elif isinstance(e, mcs.Symbol):
                    var = strip_context(str(e))
                    val = "None"
                else:
                    # TODO: proper terminology?
                    # TODO: what else does this accept
                    raise Exception(f"Don't understand head element {str(e)} in {module}")
                scope_vars.append((var, val))

            ctx = Ctx("module", True, "__", [], scope_vars)
            ctx.append_stmt(body)
            ctx.emit(self)
            return ctx.value

        elif expr.head == mcs.SymbolCompoundExpression:

            ctx = Ctx("compound")
            for e in expr.elements:
                ctx.append_stmt(e)
            ctx.emit(self)
            return ctx.value

            return f"{fun}()"            

        elif expr.head == mcs.SymbolFor:

            ctx = Ctx("for")

            init = self.to_python_expr(expr.elements[0])
            test = self.to_python_expr(expr.elements[1])
            incr = self.to_python_expr(expr.elements[2])
            body = self.to_python_expr(expr.elements[3])

            ctx.stmts.extend([
                init,
                f"while {test}:", [
                    f"{ctx.name} = {body}",
                    incr
                ],
                ctx.name
            ])

            ctx.emit(self)

            return ctx.value

        # TODO: make this a table?
        elif expr.head == mcs.SymbolSet:
            result = update(expr, "{rhs}", "set")
        elif expr.head == mcs.SymbolIncrement:
            result = update(expr, "{lhs}+1", "set_old")
        elif expr.head == mcs.SymbolAddTo:
            result = update(expr, "{lhs}+{rhs}", "set")
        elif expr.head == mcs.SymbolTimesBy:
            result = update(expr, "{lhs}*{rhs}", "set")
        elif expr.head == mcs.SymbolDivideBy:
            result = update(expr, "{lhs}/{rhs}", "set")

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

    ctx = Ctx("compiled", True, None, arg_names, zip(arg_names, arg_names))
    ctx.append_stmt(expr)

    # TODO: hokey - rework
    dummy = Ctx("dummy")
    ctx.emit(dummy)
    code = dummy.stmts_to_string()

    #print("xxx compiling:"); util.prt(expr)
    #print("xxx compiled:"); print(code)

    # compute the top-level function
    ns = locals()
    exec(code, globals(), ns)

    # top-level compiled function expects a scope, so we supply None
    # TODO: cleaner way to do this?
    def fun(**kwargs):
        result = ns[ctx.name](None, **kwargs)
        #print("xxx result", type(result), result.shape, result.dtype)
        return result

    return fun

