## Running demo

* "shell" front-end - sparate window for each output

        pip install numpy dash plotly pywebview
        python demo/fe.py --fe shell --run demos

* browser front end - similar to a jupyter or mathematica notebook

        pip install numpy dash plotly pywebview
        python demo/fe.py --fe browser --run demos

* Jupyter notebook - run the following then execute cells in sequence.
  (Note that there is some boilerplate that will go away with better packaging)
 
        pip install numpy dash plotly pywebview
        pip install jupyterlab # maybe some other stuff too, not sure
        jupyter-lab demo.ipynb

* JupyterLite running under Pyodide in browser: open <a href="https://bdlucas1.github.io/math-plotting-demo">https://bdlucas1.github.io/math-plotting-demo</a>,
  then open demo.ipynb and execute cells in sequence.
  Give it a little time on first cell to load the required python packages.
  If something seems to break, try Help | Clear Browser Data.

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

    Demo`Plot
    Graphics

## UI options

Options for UI widgets like sliders, boxes, latex:

* ipywidgets - these are the native Jupyter (nee IPython) widgets with
  good integration into Jupyter notebooks, but uncertain possibility
  for standalone apps. Still investigating.

* dash - a set of widgets that are part of the Plotly package. Good
  support for standalone, can be integrated into Jupyter notebooks but
  the integration is not ideal and not sure if can be done in
  JupyterLite. Still investigating.

Hopefully we can find a way to use a single widget set for all
environments, but if necessary could use an adapter.

<table>
  <tr>
    <td>
    <th>ipywidgets+plotly</th>
    <th>dash+plotly</th>
  </tr>
  <tr>
    <td>jupyter</td>
    <td>good integration: cell output is saved and restored on opening
    the notebook; output cell is sized to fit output automatically.</td>
    <td>poor integration: 1) major: computed plot and layout is not
    saved and restored on opening the notebook, 2) minor: is embedded
    in an iframe of fixed size (could be fixable with a JS snipped to
    resize iframe to fit content).</td>
  </tr>
  <tr>
    <td>jupyterlite (pyodide)</td>
    <td>good integration</td>
    <td>tbd. ran into problems, not sure if can solve.</td>
  </tr>
  <tr>
    <td>shell</td>
    <td>tbd. may be possible by with voila</td>
    <td>works well</td>
  </tr>
  <tr>
    <td>browser</td>
    <td>tbd. is this needed given jupyter integration?</td>
    <td>works well</td>    
  </tr>
</table>

For completeness, I tried two options for plotting, with plotly the clear winner:

* plotly - integrates with ipywidgets or dash, and provides very good
  interactivity for orbit/pan/zoom in either environment.

* matplotlib - can be integrated with ipywidgets with poor performance
  for interactive orbit/pan/zoom; can be integrated with dash widgets
  with no support for interactive orbin/pan/zoom.




## Plotting performance

Timings for various Plot3D implementations to compute and display the following:

    Plot3D[Sin[x^2+y^2] / Sqrt[x^2+y^2+1], {x,-3,3}, {y,-3,3}, PlotPoints -> {200,200}]

Implementations tested:

* current: current Plot3D implementation. (Note: for this case set
  MaxRecursion->0 to just compute the triangles on a grid, otherwise
  it is far more expensive.) Generate a Graphics3D Expression
  containing a simple list of Polygons, specifically triangles.

        System`Graphics3D
          System`List
            System`Polygon
              System`List
                System`List -0.5 -0.5 0.9111336256668093
                System`List -2.0 -0.5 0.9604976327546424
                System`List -2.0 -2.0 0.9802371777165348
            System`Polygon
              ...

* ev_slow1.py: the mathics expression to be plotted is "compiled" to a
  Python expression which evalutes the function using np vectorized
  operations (np.sin, np.sqrt, +, /, etc.) instead of calling the
  function one point at a time.  (MaxRecursion is ignored for the new
  implementation as simply computing the plot on a higher resolution
  regular grid is more efficient.) Generates the same output structure
  as the preceding.
    
* ev_slow2.py: like the preceding, except generates a Graphics3D
  Expression using a GraphicsComplex, which consists of a List of xyz
  points, and a list of lists of indexes into the list of points
  representing polygons.
 
        System`Graphics3D
          Global`GraphicsComplex
            System`List
              System`List -3.0 -3.0 -0.01976282228346516
              System`List -1.5 -3.0 -0.039502367245357606
              ...
            System`Polygon
              System`List
                System`List 1 2 7 6
                System`List 6 7 12 11
                ...
    
* ev.py: like the preceding, except the two Lists of Lists are stored
  as two numpy 2-d arrays available in expr.value for the List, and
  expr.elements for those Lists is only instantiated on demand.

Timings (in ms):

                   eval  layout    total
    current       24020      76    24096
    ev_slow1.py     441      77      518
    ev_slow2.py     236      34      270
    ev.py             3      16       19

Intepretation:

* ev_slow1.py: vectorized evaluation of the expr to be plotted is a
  massive win.

* ev_slow2.py: switching to the more efficient representation using
  GraphicsComplex is a minor win.

* ev.py: but more importantly GraphicsComplex is amenable to
  representation as a pair of numpy arrays, with the full Expression
  structure only lazily instantiated if requested.  This
  implementation in is by orders of magnitude the fastest, and the
  only one capable of useful performance for Manipulate.


