(*
 * TODO: BarLegend sometimes comes through as expr, sometimes tuple
 * this case is opposite one of the .m files that uses BarLegend
 * maybe has to do with the evaluation hack we are using?
 *)

Demo`Plot3D[
    Sin[x^2+y^2] / Sqrt[x^2+y^2+1], {x,-3,3}, {y,-3,3},
    PlotPoints -> {200,200}, Axes->False,
    ImageSize -> 200,
    ColorFunction->"viridis", PlotLegends->BarLegend["rainbow"]
]
