(*
Original input:
    Row[{
        a b Sin[x],
        Plot3D[
            x-y, {x,0,1}, {y,0,1},
            PlotPoints->{2,2}, Axes->True, ImageSize->150
        ],
        Grid[{{x,Sqrt[x]},{x^2,x y}}]
}]

Boxed for output:
*)

TemplateBox[
    {
        RowBox[{"a","","b","", RowBox[{"Sin","[","x","]"}]}],
        System`Graphics3D[
            System`GraphicsComplex[
                {{0,0,0},{1,0,1},{0,1,-1},{1,1,0}}, 
                System`Polygon[{{1,2,4,3}}]
            ],
            Axes->True, ImageSize->150
        ],
        TagBox[
            GridBox[
                {{"x",SqrtBox["x"]},{SuperscriptBox["x","2"],RowBox[{"x","","y"}]}},
                AutoDelete->False, GridBoxItemSize->{"Columns"->{{Automatic}},"Rows"->{{Automatic}}}
            ],
            "Grid"
        ]
    },
    "RowDefault"
]
