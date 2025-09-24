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

    # TODO: order out is not same as order in 

    if not hasattr(expr, "head"):
        if hasattr(expr, "value"):
            result = str(expr.value)
        elif expr in constants:
            result = constants[expr]
        else:
            # TODO: correctly handle contexts
            result = str(expr).split("`")[-1]
    elif expr.head in ops:
        fun, op, op_precedence, inner_precedence = ops[expr.head]
        result = fun(expr, op, [xlate(e, inner_precedence) for e in expr.elements])
        if op_precedence < outer_precedence:
            result = "(" + result + ")"
    else:
        raise NotMath(str(expr.head))

    return "{" + result + "}"

def to_math(expr):

    try:
        latex = "$" + xlate(expr) + "$"
        result = dash.dcc.Markdown(latex, mathjax=True)
        return result

    except NotMath as e:
        print("not math", e)
        return None
