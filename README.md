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

    Plot3D       slow current Plot3D
    Demo`Plot3D  fast demo Plot3D
    PlotPoints
    PlotRange
    Graphics3D

Supported soon:

    Row
    Grid
    Plot
    Graphics
