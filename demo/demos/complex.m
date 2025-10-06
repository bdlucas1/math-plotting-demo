(* Row[{Grid[{{x,Sqrt[x]},{x^2,x y}}], 34 a b Sin[x]}] *)

Hold[
    TemplateBox[
        {
            TagBox[
                GridBox[
                    {{"x",SqrtBox["x"]},{SuperscriptBox["x","2"],RowBox[{"x","","y"}]}},
                    AutoDelete->False,GridBoxItemSize->{"Columns"->{{Automatic}},"Rows"->{{Automatic}}}
                ],
                "Grid"],
            RowBox[{"34","","a","","b","",RowBox[{"Sin","[","x","]"}]}]
        },
        "RowDefault"
    ]
]
