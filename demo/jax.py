import dash

import mcs

class NotMath(Exception): pass

# TODO: input "2 I" gives weird result - guess not correctly formatting complex numbers - where at??

def xlate(expr, outer_precedence=0):
    
    list_ops = {
        mcs.SymbolPlus: ("+", 0, 0),
        mcs.SymbolTimes: (" ", 1, 1),
        mcs.SymbolPower: ("^", 2, 0),
        # TODO: -x becomes + -1*x; special case that?
    }

    unary_ops = {
        # TODO: Sqrt[x] becomes x^(1/2); special case that?
        mcs.SymbolSqrt: ("\\sqrt", 0, 0),
        mcs.SymbolSin: ("\\sin", 0, 1),
        mcs.SymbolCos: ("\\cos", 0, 1),
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
    elif expr.head in list_ops:
        op, op_precedence, inner_precedence = list_ops[expr.head]
        result = op.join([xlate(e,inner_precedence) for e in expr.elements])
        if op_precedence < outer_precedence:
            result = "(" + result + ")"
    elif expr.head in unary_ops:
        # TODO: reafactor to share code with above
        op, op_precedence, inner_precedence = unary_ops[expr.head]
        result = op + xlate(expr.elements[0], inner_precedence)
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
