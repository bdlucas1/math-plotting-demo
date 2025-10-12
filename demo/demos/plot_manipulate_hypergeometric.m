(*
 TODO: System`Hypergeometric1F1 gets rewritten to varous functions involving gamma, bessel, etc.
 need to build those out in compile.py to handle
 for now just use Demo`Hypergeomtric which compile knows about but mathics evaluate doesn't
*)

(* TODO: remove hold as soon as Manipulate is defined properly *)
Hold[Manipulate[
    Plot3D[
        Demo`Hypergeometric1F1[a, b, (x + I y)^2], {x, -2, 2}, {y, -2, 2},
        PlotPoints -> {200,200}, PlotRange -> {Automatic, Automatic, {-5,14}},
        ColorFunction->"rainbow", PlotLegends->BarLegend["rainbow"]
    ],
    {{a,1}, 0.5, 1.5, 0.1}, (* a slider spec *)
    {{b,2}, 1.5, 2.5, 0.1}  (* b slider spec *)
]]
