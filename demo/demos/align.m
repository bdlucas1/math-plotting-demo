(* mixed non-math, math, and graphics *)
Foo[
    x+y, x+y^2,
    Plot3D[Sin[x]*Cos[y], {x,-3,3}, {y,-3,3}, PlotPoints -> {200,200}, ImageSize->100, Axes->False],
    "x",
    "Foo", x, A, B, "A", "B"
]
