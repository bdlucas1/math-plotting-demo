(* TBD, not ready yet *)
ListPlot3D[
    Flatten[
        Table[
            {r Cos[\[Theta]], r Sin[\[Theta]], Sin[5 r + 3 \[Theta]]/(1 + r^2)},
            {r, 0.2, 2, 2 / 5},
            {\[Theta], 0, 2 \[Pi], 2 \[Pi] / 5}
        ],
        1
    ],
    Mesh -> None,
    PlotTheme -> "Detailed",
    ColorFunction -> "Rainbow"
]

