(* mixed non-math, math, and graphics *)
(* TODO: mathjax makes nested exponents too small? can it be tweaked? *)
Foo[
    x+y, x+y^2^3^4^x,
    Demo`Plot3D[Sin[x]*Cos[y], {x,-3,3}, {y,-3,3}, PlotPoints -> {200,200}, ImageSize->100, Axes->False]

]
