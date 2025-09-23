Manipulate[
    Demo`Plot3D[
        Sin[(x^2+y^2)*freq] / Sqrt[x^2+y^2+1] * amp, {x,-3,3}, {y,-3,3},
        PlotPoints -> {200,200}, PlotRange -> {Automatic, Automatic, {-0.25,0.5}}
    ],
    {{freq,1.0}, 0.1, 2.0, 0.2}, (* freq slider spec *)
    {{amp,1.0}, 0.0, 2.0, 0.2}  (* amp slider spec *)
]
