Grid[{
    {
        "This",
        Plot3D[
            Sin[x]*Cos[y], {x,0,10}, {y,0,10},
            PlotPoints->{200,200}, Axes->False, ImageSize->100
        ],

        "is a"
    },
    {
        Plot3D[
            Sin[(x^2+y^2)] / Sqrt[x^2+y^2+1], {x,-3,3}, {y,-3,3},
            PlotPoints->{200,200}, Axes->False, ImageSize->100
        ],
        "grid",
        x+y^2
    }
}]
