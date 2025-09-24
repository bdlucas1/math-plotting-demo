import dash

import ev
import lay
import mcs

# TODO: input "2 I" gives weird result - guess not correctly formatting complex numbers - where at??
# TODO: -x becomes + -1*x; special case that?
# TODO: Sqrt[x] becomes x^(1/2); special case that?
# TODO: order out is not same as order in 
# TODO: a little convoluted - refactor

def xlate(fe, expr, outer_precedence=0):
    
    # temp hack until we get Demo`Plot3D integrated and ev.eval_expr goes away
    # and these are already evaluted by the time we get here
    if hasattr(expr, "head") and str(expr.head) in ev.funs:
        expr = ev.eval_expr(fe, expr)

    def list_op(expr, op, inner):
        return op.join(inner)

    def unary_op(expr, op, inner):
        return op + inner[0]

    ops = {

        mcs.SymbolPlus: (list_op, "+", 0, 0),
        mcs.SymbolTimes: (list_op, " ", 1, 1),
        mcs.SymbolPower: (list_op, "^", 2, 0),

        mcs.SymbolSqrt: (unary_op, "\\sqrt", 0, 0),
        mcs.SymbolSin: (unary_op, "\\sin", 0, 1),
        mcs.SymbolCos: (unary_op, "\\cos", 0, 1),
    }

    constants = {
        mcs.SymbolPi: "\\pi"
    }

    # TODO: correctly handle contexts
    def ctx(s):
        parts = s.split("`")
        if parts[0] in ["Global", "System"]:
            result = parts[1]
        else:
            result = str(expr)
        return result

    def non_math(op, inner):
        inner = [dash.dcc.Markdown("$"+i+"$", mathjax=True) if isinstance(i,str) else i for i in inner]
        result = [ctx(str(op)), "[", inner[0]]
        for i in inner[1:]:
            result.extend([",", i])
        result.append("]")
        # TODO: use css instead of style
        return dash.html.Div(result, style=dict(display="flex"))

    if not hasattr(expr, "head"):
        if hasattr(expr, "value"):
            if isinstance(expr.value, str):
                result = dash.html.Div(expr.value)
            else:
                result = str(expr.value)
        elif expr in constants:
            result = constants[expr]
        else:
            result = ctx(str(expr))
    elif expr.head in ops:
        fun, op, op_precedence, inner_precedence = ops[expr.head]
        inner = [xlate(fe, e, inner_precedence) for e in expr.elements]
        # TODO: should this be str vs html or non-html vs html?
        if not all(isinstance(i, str) for i in inner):
            result = non_math(expr.head, inner)
        else:
            result = fun(expr, op, ["{" + i + "}" for i in inner])
            if op_precedence < outer_precedence:
                result = "(" + result + ")"
    elif expr.head in lay.layout_funs:
        result = lay.layout_funs[expr.head](fe, expr)                
    else:
        inner = [xlate(fe, e) for e in expr.elements]
        result = non_math(expr.head, inner)

    return result

def layout_expr(fe, expr):

    result = xlate(fe, expr)
    if isinstance(result, str):
        result = dash.dcc.Markdown("$" + result + "$", mathjax=True)
    return result
