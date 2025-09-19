from mathics.core.symbols import Symbol, SymbolList, SymbolPlus, SymbolTimes, SymbolPower
from mathics.core.systemsymbols import SymbolSin, SymbolCos, SymbolSqrt, SymbolAbs, SymbolGamma

from mathics.core.atoms import Integer, Real
from mathics.core.list import ListExpression
from mathics.core.expression import Expression
from mathics.session import MathicsSession


# where to find these?
SymbolList = Symbol("System`List")
SymbolI = Symbol("I")
SymbolE = Symbol("E")
SymbolPolygon = Symbol("System`Polygon")
SymbolGraphicsComplex = Symbol("Global`GraphicsComplex") # TODO: System
SymbolGraphics3D = Symbol("System`Graphics3D")
SymbolHypergeometricPFQ = Symbol("System`HypergeometricPFQ")
