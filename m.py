from mathics.session import MathicsSession
import mathics

# pretty print expr
def pp(expr, indent=1):
    if not hasattr(expr, "elements"):
        print("  " * indent + str(expr))
    else:
        print("  " * indent + str(expr.head))
        for elt in expr.elements:
            pp(elt, indent + 1)


expr = "Sin[3]"
#expr = "Plot[Sin[x], {x,0,10}]"
#expr = "Plot3D[Sin[x], {x,0,10}, {y,0,10}]"
#expr = "Manipulate[Plot3D[Sin[x], {x,0,10}, {y,0,10}]]"

session = MathicsSession(add_builtin=True, catch_interrupt=True)

help(mathics.core.systemsymbols.SymbolSin)

#res = session.evaluate(expr)
#res = session.parse(expr)
#res.evaluate()

print("xxx python", res.to_python())


#help(res)

print("=== result")
pp(res)
