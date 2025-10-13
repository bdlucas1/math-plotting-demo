Grid[{{
    Plot[Sin[x], {x,0,10}, PlotPoints->10]
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
