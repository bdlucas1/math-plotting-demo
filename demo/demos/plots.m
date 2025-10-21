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
}, {
    (* funky swirl, example courtesy of ChatGPT *)
    Manipulate[
        Plot3D[
            Sin[5 Sqrt[x^2 + y^2] + n ArcTan[x, y]] / (1 + (x^2 + y^2)),
            {x, -2, 2}, {y, -2, 2},
            PlotRange -> {System`Automatic, System`Automatic, {-2,2}},
            ColorFunction -> "Rainbow"
        ],
        {{n,3},0,5,1}
    ]
}, {
    (* fractal-ish landscape, example courtesy of ChatGPT *)
    Manipulate[
        Plot3D[
            Module[
                {z = 0, i, freq, amp},
                freq = 1;
                amp = 1;
                (* TODO: n==0 doesn't work - need to accept scalar z=0 in plot and promote to array *)
                For[i = 1, i <= n, i++,
                    z += amp * Sin[freq x] * Cos[freq y];
                    freq *= fmul;
                    amp /= adiv;
                ];
                z
            ],
            (* TODO: Pi doesn't work - I think we need to N[...] these exprs *)
            {x, -3, 3}, {y, -3, 3}
        ],
        {{n,6}, 1, 10, 1},
        {{fmul,2}, 1, 3, 0.1},
        {{adiv,2}, 1, 3, 0.1}
    ]
}}]
