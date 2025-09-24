import dash

import mcs

class NotMath(Exception): pass

# TODO: input "2 I" gives weird result - guess not correctly formatting complex numbers - where at??

def xlate(expr, outer_precedence=0):
    
    def list_op(expr, op, inner):
        return op.join(inner)

    def unary_op(expr, op, inner):
        return op + inner[0]

    ops = {

        mcs.SymbolPlus: (list_op, "+", 0, 0),
        mcs.SymbolTimes: (list_op, " ", 1, 1),
        mcs.SymbolPower: (list_op, "^", 2, 0),
        # TODO: -x becomes + -1*x; special case that?

        # TODO: Sqrt[x] becomes x^(1/2); special case that?
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

    # TODO: order out is not same as order in 

    if not hasattr(expr, "head"):
        if hasattr(expr, "value"):
            result = str(expr.value)
        elif expr in constants:
            result = constants[expr]
        else:
            result = ctx(str(expr))
    elif expr.head in ops:
        fun, op, op_precedence, inner_precedence = ops[expr.head]
        inner = [xlate(e, inner_precedence) for e in expr.elements]
        # TODO: should this be str vs html or non-html vs html?
        if not all(isinstance(i, str) for i in inner):
            result = non_math(expr.head, inner)
        else:
            result = fun(expr, op, ["{" + i + "}" for i in inner])
            if op_precedence < outer_precedence:
                result = "(" + result + ")"
    else:
        #raise NotMath(str(expr.head))
        inner = [xlate(e) for e in expr.elements]
        result = non_math(expr.head, inner)

    return result

def to_math(expr):

    try:
        result = xlate(expr)
        print("xxx result 1", result)
        if isinstance(result, str):
            result = dash.dcc.Markdown("$" + result + "$", mathjax=True)
        return result

    except NotMath as e:
        print("not math", e)
        return None
