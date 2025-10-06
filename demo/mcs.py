#
# symbols etc. are hidden away in a confusing array of packages and modules,
# and also not a big fan of the from...import... pattern, so hide that all away here
#


from mathics.core.symbols import Symbol, SymbolList, SymbolPlus, SymbolTimes, SymbolPower, SymbolList
from mathics.core.systemsymbols import SymbolSin, SymbolCos, SymbolSqrt, SymbolAbs, SymbolGamma, \
    SymbolRule, SymbolI, SymbolE, SymbolPi, SymbolRow, SymbolGrid, \
    SymbolMakeBoxes, SymbolTraditionalForm, SymbolStandardForm, SymbolRowBox, SymbolFractionBox, SymbolSqrtBox, \
    SymbolSuperscriptBox, SymbolHold


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
SymbolAxes = Symbol("System`Axes")
SymbolColorFunction = Symbol("System`ColorFunction")
SymbolPlotLegends = Symbol("Global`PlotLegends") # TODO: move to System
SymbolBarLegend = Symbol("Global`BarLegend") # TODO: move to System
SymbolImageSize = Symbol("System`ImageSize")

SymbolManipulate = Symbol("Global`Manipulate") # TODO: move to System
SymbolGraphics3D = Symbol("System`Graphics3D")
SymbolGraphics = Symbol("System`Graphics")
SymbolGraphicsComplex = Symbol("System`GraphicsComplex") # TODO: move to System
SymbolLine = Symbol("System`Line")
SymbolPolygon = Symbol("System`Polygon")

SymbolTemplateBox = Symbol("System`TemplateBox")
SymbolTagBox = Symbol("System`TagBox")
SymbolGridBox = Symbol("System`GridBox")
