Installation

    pip install numpy dash plotly pywebview

Run demo with "shell" front end - does not actually take input but
rather pops up two windows with graphics

    python demo/fe.py --fe shell --run demos

After running the demos and displaying the results, the demo front end
goes into a REPL loop so you can enter expressions. Try for example

    (* current implementation takes 10 sec on 50x50 grid *)
    Plot3D[Sin[x] * Cos[y], {x,0,10}, {y,0,10}, PlotPoints->{50,50}]

    (* demo implementation takes 35 ms on 200x200 grid *)
    Demo`Plot3D[Sin[x] * Cos[y], {x,0,10}, {y,0,10}, PlotPoints->{200,200}]

Run demo with "browser" front end. Displays a window that accepts an
"expression" string, which must be either "a" or "b", and "evaluates"
the expression and displays the resulting graphics. There's only one
field for now; you can change it and press shift-enter again to see a
different plot.

    python demo/fe.py --fe browser --run demos

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
