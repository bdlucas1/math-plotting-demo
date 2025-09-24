Installation

    pip install numpy dash plotly pywebview

Run demos with shell front end or browser front end:

    python demo/fe.py --fe shell --run demos
    python demo/fe.py --fe browser --run demos

After running the demos and displaying the results, the front ends
then accept more input expressions. Try for example:

    (* current implementation takes 10 sec on 50x50 grid *)
    Plot3D[Sin[x] * Cos[y], {x,0,10}, {y,0,10}, PlotPoints->{50,50}]

    (* demo implementation takes 35 ms on 200x200 grid *)
    Demo`Plot3D[Sin[x] * Cos[y], {x,0,10}, {y,0,10}, PlotPoints->{200,200}]

Supported now to some degree:

    Row[{item, ...}] where items can be graphics or other expr (displayed as text for now)
    Grid[{{item, ...}, ...}]
    Plot3D - slow current Plot3D
    Demo`Plot3D - fast demo Plot3D
    Graphics3D
    PlotPoints -> n or {xn, yn}
    PlotRange -> {xspec, yspec, zspec}, where spec is Automatic or {lo,hi}
    PlotLegends -> BarLegend[name] where name is a Plotly colorscale name
    ColorFunction => name where name is a Plotly colorscale name
    Axes -> True or False
    some rudimentary math formatting (see demo, jax.m, jax.py for details)

Supported soon:

    Plot
    Graphics
