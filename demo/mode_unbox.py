import ev
import graphics
import mcs
import mode

# TODO: input "2 I" gives weird result - guess not correctly formatting complex numbers - where at??
# TODO: -x becomes + -1*x; special case that?
# TODO: order out is not same as order in 
# TODO: a little convoluted - refactor
# TODO: hacks like power to do Sqrt probably wouldn't be needed if TraditionalForm worked

def _layout_expr(fe, expr, outer_precedence=0):
    
    # temp hack until we get Demo`Plot3D integrated and ev.eval_expr goes away
    # and these are already evaluted by the time we get here
    if hasattr(expr, "head") and str(expr.head) in ev.funs:
        expr = ev.eval_expr(fe, expr)

    # foo, this gets max recursion depth exceeded
    #expr = mcs.Expression(mcs.SymbolTraditionalForm, expr).evaluate(fe.session.evaluation)

    def list_op(expr, op, inner):
        return op.join(inner)

    def unary_op(expr, op, inner):
        return op + inner[0]

    # eval turns sqrt(x) to x^(1/2), so special-case that and display as sqrt
    def power(expr, op, inner):
        # TODO: this picks up x^0.5 as well - is that ok?
        # Sqrt[x] per se comes back as mathics.core.atoms.Rational with value sympy.core.numbers.Half
        # this does not seem to support comparison with float, but does support subtract, so we do that
        #if hasattr(expr.elements[1], "value") and expr.elements[1].value and expr.elements[1].value-0.5==0:
        if getattr(expr.elements[1], "value", None) and expr.elements[1].value-0.5==0:
            return unary_op(expr, "\\sqrt", inner)
        else:
            return list_op(expr, op, inner)

    ops = {

        mcs.SymbolPlus: (list_op, "+", 0, 0),
        mcs.SymbolTimes: (list_op, " ", 1, 1),
        mcs.SymbolPower: (power, "^", 2, 0),

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
        # TODO: baslines aren't quite aligned for math and non-math
        inner = [wrap_math(i) for i in inner]
        result = [ctx(str(op)), "[", inner[0]]
        for i in inner[1:]:
            result.extend([",", i])
        result.append("]")
        return mode.row(result)

    if not hasattr(expr, "head"):
        if hasattr(expr, "value"):
            if isinstance(expr.value, str):
                result = mode.wrap(expr.value)
            else:
                result = str(expr.value)
        elif expr in constants:
            result = constants[expr]
        else:
            result = ctx(str(expr))
    elif expr.head in ops:
        fun, op, op_precedence, inner_precedence = ops[expr.head]
        inner = [_layout_expr(fe, e, inner_precedence) for e in expr.elements]
        # TODO: should this be str vs html or non-html vs html?
        if not all(isinstance(i, str) for i in inner):
            result = non_math(expr.head, inner)
        else:
            result = fun(expr, op, ["{" + i + "}" for i in inner])
            if op_precedence < outer_precedence:
                result = "(" + result + ")"
    elif expr.head in graphics.layout_funs:
        result = graphics.layout_funs[expr.head](fe, expr)                
    else:
        inner = [_layout_expr(fe, e) for e in expr.elements]
        result = non_math(expr.head, inner)

    return result

def wrap_math(s):
    return mode.latex(s) if isinstance(s, str) else s

def layout_expr(fe, expr):
    result = _layout_expr(fe, expr)
    result = wrap_math(result)
    return result
