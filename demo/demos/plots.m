Grid[{{
    Hold[Manipulate[
        Plot[Sin[x*f], {x,0,10}, PlotPoints->10],
        {{f,1.0}, 0.1, 2.0, 0.2}
    ]]
}, {
    Plot3D[
        Sin[x]*Cos[y],
        {x,0,10}, {y,0,10},
        PlotPoints->{200,200},
        Axes -> {True,True,True}
    ]
}, {
    NumberLinePlot[{1,3,4}]
}}]
