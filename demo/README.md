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

* ev_slow1.py: vectorized computation of the expr to be plotted is a
  massive win.

* ev_slow2.py: switching to the more efficient representation using
  GraphicsComplex is a minor win.

* ev.py: but more importantly GraphicsComplex is amenable to
  representation as a pair of numpy arrays, with the full Expression
  structure only lazily instantiated if requested.  This
  implementation in is by orders of magnitude the fastest, and the
  only one capable of useful performance for Manipulate.

