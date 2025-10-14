import os

#
# symbols etc. are hidden away in a confusing array of packages and modules,
# and also not a big fan of the from...import... pattern, so hide that all away here
# for now, to make writing the demo a bit easier
#


from mathics.core.symbols import Symbol, SymbolList, SymbolPlus, SymbolTimes, SymbolPower, SymbolList
from mathics.core.systemsymbols import SymbolSin, SymbolCos, SymbolSqrt, SymbolAbs, SymbolGamma, \
    SymbolRule, SymbolI, SymbolE, SymbolPi, SymbolRow, SymbolGrid, \
    SymbolMakeBoxes, SymbolTraditionalForm, SymbolStandardForm, SymbolRowBox, SymbolFractionBox, SymbolSqrtBox, \
    SymbolSuperscriptBox, SymbolHold
from mathics.core.attributes import A_HOLD_FIRST, A_PROTECTED


from mathics.core.atoms import Integer, Real, Complex
from mathics.core.list import ListExpression
from mathics.core.expression import Expression
from mathics.session import MathicsSession, Evaluation

# choose whether to use NALE from mathics.core.list or from ext
# use the former once merged; otherwise use the latter
if os.getenv("DEMO_USE_MATHICS", False):
    print("using mathics version of NALE")
    from mathics.core.list import NumpyArrayListExpression
else:
    print("using demo version of NALE")
    from list import NumpyArrayListExpression

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
SymbolAspectRatio = Symbol("System`AspectRatio")

SymbolManipulate = Symbol("Global`Manipulate") # TODO: move to System
SymbolGraphics3D = Symbol("System`Graphics3D")
SymbolGraphics = Symbol("System`Graphics")
SymbolGraphicsComplex = Symbol("System`GraphicsComplex") # TODO: move to System
SymbolLine = Symbol("System`Line")
SymbolPoint = Symbol("System`Point")
SymbolPolygon = Symbol("System`Polygon")

SymbolTemplateBox = Symbol("System`TemplateBox")
SymbolTagBox = Symbol("System`TagBox")
SymbolGridBox = Symbol("System`GridBox")
