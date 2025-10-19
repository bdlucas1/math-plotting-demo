Grid[{{
    Manipulate[
        Plot[Sin[x*f], {x,0,10}, PlotPoints->10],
        {{f,1.0}, 0.1, 2.0, 0.2}
    ]
}, {
    Manipulate[
        Plot3D[
            Sin[x]*Cos[y]*a,
            {x,0,10}, {y,0,10},
            PlotPoints->{200,200},
            Axes -> {True,True,True},
            PlotRange -> {Automatic, Automatic, {-2,2}}
        ],
        {{a,1}, 0, 2, 0.1}
    ]
}, {
    Manipulate[
        NumberLinePlot[{1,x,4}],
        {{x,2}, 1.0, 4.0, 0.1}
    ]
}, {
    ListStepPlot[{1, 1, 2, 3, 5, 8, 13, 21}]
}, {
    (* TODO: axes should be centered; maybe use plotly native polar plot for this? *)
    (* Interactive speed is marginal for this plot *)
    Manipulate[
        PolarPlot[
            Sqrt[t*a],
            {t, 0, 16 Pi},
            PlotRange -> {{-8,8}, {-8,8}}
        ],
        {{a,1}, 0.7, 1.3, 0.01}
     ]
}, {
    Manipulate[Plot[Sin[x],{x,0,a}],{{a,1},0,10,0.1}]
}, {
    Manipulate[
        Plot3D[
            Sin[x]*Cos[y],
            {x,0,xmax},
            {y,0,ymax}
        ],
        {{xmax,1},0,10,0.1},
        {{ymax,1},0,10,0.1}
    ]
}, {
    Manipulate[
        Plot[
            If[x > threshold, x, -x],
            {x,-1,1}
        ],
        {{threshold,0},-1,1,0.05}
    ]
}, {
    Manipulate[
        Plot3D[
            If[x y > threshold, x y, -x y],
            {x,-1,1},
            {y,-1,1}
        ],
        {{threshold,0},-1,1,0.05}
    ]
}}]
