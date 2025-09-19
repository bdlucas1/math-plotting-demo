from mathics.core.symbols import Symbol, SymbolList, SymbolPlus, SymbolTimes, SymbolPower, SymbolList
from mathics.core.systemsymbols import SymbolSin, SymbolCos, SymbolSqrt, SymbolAbs, SymbolGamma, SymbolRule, SymbolI, SymbolE

from mathics.core.atoms import Integer, Real
from mathics.core.list import ListExpression
from mathics.core.expression import Expression
from mathics.session import MathicsSession


#
# where to find these?
#

SymbolHypergeometricPFQ = Symbol("System`HypergeometricPFQ")

SymbolPlotPoints = Symbol("System`PlotPoints")
SymbolPlotRange = Symbol("System`PlotRange")

SymbolManipulate = Symbol("Global`Manipulate") # TODO: move to System
SymbolGraphics3D = Symbol("System`Graphics3D")
SymbolGraphicsComplex = Symbol("Global`GraphicsComplex") # TODO: move to System
SymbolLine = Symbol("System`Line")
SymbolPolygon = Symbol("System`Polygon")
