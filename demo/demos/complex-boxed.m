(* Row[{Grid[{{x,Sqrt[x]},{x^2,x y}}], a b Sin[x]}] *)
TemplateBox[
    {
        TagBox[
            GridBox[
                {{"x",SqrtBox["x"]},{SuperscriptBox["x","2"],RowBox[{"x","","y"}]}},
                AutoDelete->False, GridBoxItemSize->{"Columns"->{{Automatic}},"Rows"->{{Automatic}}}
            ],
            "Grid"
        ],
        RowBox[{"a","","b","", RowBox[{"Sin","[","x","]"}]}]
    },
    "RowDefault"
]
