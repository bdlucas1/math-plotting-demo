(* TODO: display has a triangle and a quad - why? *)
Graphics3D[
    GraphicsComplex[
        {{0, 0, 0}, {2, 0, 0}, {2, 2, 0}, {0, 2, 0}, {1, 1, 2}},
        Polygon[{{1, 2, 3, 4}, {1, 2, 4, 5}}]
    ]
]
