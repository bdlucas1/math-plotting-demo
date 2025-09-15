#
# 
#

dp3d   = "Plot3D[Sin[x^2+y^2], {x,-3,3}, {y,-3,3}, PlotPoints -> {50,50}]"
dp3dv1 = "My`Plot3Dv1[Sin[x^2+y^2] / Sqrt[x^2+y^2+1], {x,-3,3,200}, {y,-3,3,200}]"
dp3dv2 = "My`Plot3Dv2[Sin[x^2+y^2] / Sqrt[x^2+y^2+1], {x,-3,3}, {y,-3,3}, PlotPoints -> {200,200}]"
dp3dv3 = "My`Plot3Dv3[Sin[x^2+y^2] / Sqrt[x^2+y^2+1], {x,-3,3}, {y,-3,3}, PlotPoints -> {200,200}]"
dp3dv4 = "My`Plot3Dv4[Sin[x^2+y^2] / Sqrt[x^2+y^2+1], {x,-3,3}, {y,-3,3}, PlotPoints -> {200,200}]"
dmp3ds = """
    Manipulate[
        My`Plot3D[Sin[(x^2+y^2)*freq] / Sqrt[x^2+y^2+1] * amp, {x,-3,3,200}, {y,-3,3,200}, {-1,1}],
        {freq, 0.1, 1.0, 2.0, 0.2}, (* freq slider spec *)
        {amp, 0.0, 1.2, 2.0, 0.2}  (* amp slider spec *)
     ]
"""
dmp3dh = """
    Manipulate[
        My`Plot3D[Abs[My`Hypergeometric1F1[a, b, (x + I y)^2]], {x, -2, 2, 200}, {y, -2, 2, 200}, {0, 14}],
        {a, 0.5, 1, 1.5, 0.1}, (* a slider spec *)
        {b, 1.5, 2, 2.5, 0.1}  (* b slider spec *)
    ]
"""
testgc1 = """
    Graphics3D[GraphicsComplex[
        {{0, 0, 0}, {2, 0, 0}, {2, 2, 0}, {0, 2, 0}, {1, 1, 2}},
        Polygon[{{1, 2, 5}, {2, 3, 5}, {3, 4, 5}, {4, 1, 5}}]
    ]]
"""
# TODO: display has a triangle and a quad - why?
testgc2 = """
    Graphics3D[GraphicsComplex[
        {{0, 0, 0}, {2, 0, 0}, {2, 2, 0}, {0, 2, 0}, {1, 1, 2}},
        Polygon[{{1, 2, 3, 4}, {1, 2, 4, 5}}]
    ]]
"""


demos = [
    #                                                                                   eval layout  total (ms)
    #dp3d,   # Plot3D Sin 50x50           current, generates G3D slowly                10026    181   10207
    #dp3dv1, # Plot3Dv1 Sin/Sqrt 200x200  send Plot3D unmodified to layout                 0     26      26
    #dp3dv2, # Plot3Dv2 Sin/Sqrt 200x200  G3D, individual polys, no GraphicsComplex      433    622    1055
    #dp3dv3, # Plot3Dv2 Sin/Sqrt 200x200  G3D, GraphicsComplex, numpy_array_list_expr    252    247    495
    dp3dv4, # Plot3Dv2 Sin/Sqrt 200x200  G3D, GraphicsComplex, NumpyArrayListExpr                           
    #testgc1,
    #testgc2,
    #dmp3ds, # Man Plot3Dv1 Sin/Sqrt 200x200
    #dmp3dh, # Man Plot3Dv1 HypGeo 200x200
]

