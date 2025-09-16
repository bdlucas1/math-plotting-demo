import collections 
import itertools
import math
import numpy as np

from mathics.core.atoms import Integer, Real
from mathics.core.expression import Expression
from mathics.core.list import ListExpression
from mathics.core.symbols import Symbol
import dash
import plotly.graph_objects as go

import compile
import util

# compute a unique id for use in html
ids = collections.defaultdict(lambda: 0)
def uid(s):
    ids[s] += 1
    return f"{s}-{ids[s]}"


#
# given a Plot3D expression, compute a layout
# 

def layout_Plot3D(fe, expr, values = {}):

    # Plot3D arg exprs
    fun_expr = expr.elements[0]
    xlims_expr = expr.elements[1]
    ylims_expr = expr.elements[2]
    zlims_expr = expr.elements[3] if len(expr.elements) > 3 else None
        
    # compile fun
    fun_args = [str(xlims_expr.elements[0]), str(ylims_expr.elements[0])] + list(values.keys())
    fun = compile.my_compile(fun_expr, fun_args)

    # parse xlims, construct namedtuple
    A = collections.namedtuple("A", ["name", "lo", "hi", "count"])
    def to_python_axis_spec(expr):
        return A(str(expr.elements[0]).split("`")[-1], *[e.to_python() for e in expr.elements[1:]])
    xlims = to_python_axis_spec(xlims_expr)
    ylims = to_python_axis_spec(ylims_expr)

    # parse zlims
    zlims = [zlims_expr.elements[0].value, zlims_expr.elements[1].value] if zlims_expr else None

    # compute xs and ys
    xs = np.linspace(xlims.lo, xlims.hi, xlims.count)
    ys = np.linspace(ylims.lo, ylims.hi, ylims.count)
    xs, ys = np.meshgrid(xs, ys)

    # compute zs from xs and ys using compiled function
    zs = fun(**({xlims.name: xs, ylims.name: ys} | values))

    # https://github.com/Mathics3/mathics-django/blob/master/mathics_django/web/format.py#L40-L135
    fancy = False # the fancy latex formatting isn't that great
    title = fe.session.evaluation.format_output(fun_expr, "latex" if fancy else "text")

    # plot it
    util.start_timer("figure")
    figure = go.Figure(
        data = [go.Surface(x=xs, y=ys, z=zs, colorscale="Viridis", colorbar=dict(thickness=10))],
        layout = go.Layout(
            margin = dict(l=0, r=0, t=0, b=0),
            scene = dict(
                xaxis_title=xlims.name,
                yaxis_title=ylims.name,
                #zaxis_title="z",
                aspectmode="cube"
            )
        )
    )
    if zlims:
        figure.update_layout(scene = dict(zaxis = dict(range=zlims)))
    util.stop_timer()

    util.start_timer("layout")
    layout = dash.html.Div ([
        dash.dcc.Markdown(f"${title}$", mathjax=True) if fancy else dash.html.Div(title, className="title"),
        dash.dcc.Graph(figure=figure, className="graph")
    ], className="plot")
    util.stop_timer()

    return layout


#
# given a Manipulate expression, compute a layout
#
# note that this calls layout_expr on unevaluated, uncompiled target_expr, like Plot3D, on every slider move
# Plot3D then compiles the expr, which means we are re-compiling every time the slider moves
# we could lift that compilation into Manipulate by compiling target_expr,
# but timings in Plot3D show that would be practically meaningless for performance,
# and it would complicate the implementation
# 

def layout_Manipulate(fe, expr):

    target_expr = expr.elements[0]
    slider_exprs = expr.elements[1:]

    # TODO: clean this up
    S = collections.namedtuple("S", ["name", "lo", "init", "hi", "step", "id"])
    def val(e):
        if str(e).startswith("Global`"):
            return str(e).split("`")[-1]
        else:
            return e.value
    sliders = [S(*[val(e) for e in s.elements], uid("slider")) for s in slider_exprs]

    # compute a slider layout from a slider spec (S namedtuple)
    def slider_layout(s):
        # TODO: handling of tick marks and step needs work; this code is just for demo purposes
        marks = {value: f"{value:g}" for value in np.arange(s.lo, s.hi, s.step)}
        return [
            dash.html.Label(s.name),
            dash.dcc.Slider(
                id=s.id, marks=marks, updatemode="drag",
                min=s.lo, max=s.hi, step=s.step/10, value=s.init,
            )
        ]

    # compute the layout for the plot
    target_id = uid("target")
    init_values = {s.name: s.init for s in sliders}

    in_progress_stuff = False
    #in_progress_stuff = True
    if in_progress_stuff:
        # NEXT: get this to work
        def eval_and_layout(values):
            for name, value in values.items():
                fe.session.evaluation.parse_evaluate(f"{name}->{value}")
            result = eval_expr(fe, target_expr)
            layout = layout_expr(fe, result, {})
        init_target_layout = eval_and_layout(init_values)
    else:
        init_target_layout = layout_expr(fe, target_expr, init_values)

    
    slider_layouts = list(itertools.chain(*[slider_layout(s) for s in sliders]))
    layout = dash.html.Div([
        dash.html.Div(init_target_layout, id=target_id),
        dash.html.Div(slider_layouts, className="sliders")
    ], className="manipulate")
        
    # define callbacks for the sliders
    @fe.app.callback(
        dash.Output(target_id, "children"),
        *(dash.Input(s.id, "value") for s in sliders),
        prevent_initial_call=True
    )
    def update(*args):
        return layout_expr(fe, target_expr, {s.name: a for s, a in zip(sliders, args)})

    return layout


def layout_Graphics3D(fe, expr):

    xyzs = []
    ijks = []

    def handle_g(g):

        if str(g.head) == "System`Polygon":
            poly = [p.value for p in g.elements[0].elements]
            i = len(xyzs)
            xyzs.extend(poly)
            ijks.append([i+1,i+2,i+3]) # ugh - 1-based to match GraphicsComplex Polygon

        elif str(g.head) == "System`Line":
            line = [p.value for p in g.elements[0].elements]

        elif str(g.head) == "Global`GraphicsComplex": # TODO: should be system

            util.start_timer("xyzs")
            xyzs.extend(g.elements[0].value)
            util.stop_timer()

            def handle_c(c):

                if str(c.head) == "System`Polygon":

                    polys = c.elements[0]
                    if isinstance(polys, NumpyArrayListExpr):
                        util.start_timer("ijks from NumpyArrayListExpr")
                        # use advanced indexing to break the polygons down into triangles
                        ngon = polys.value.shape[1]
                        for i in range(1, ngon-1):
                            inx = [0, i, i+1]
                            tris = polys.value[:, inx]
                            ijks.extend(tris)
                        util.stop_timer()

                    else:
                        util.start_timer("ijks from mathics List of polys")
                        for poly in polys.elements:
                            for j, k in zip(poly.elements[1:-1], poly.elements[2:]):
                                ijks.append([poly.elements[0].value, j.value, k.value])
                        util.stop_timer()

                else:
                    raise Exception(f"Unknown head {c.head} in GraphicsComplex")

            for c in g.elements[1:]:
                handle_c(c)

        elif str(g.head) == "System`Rule":
            # TODO
            pass

        elif str(g.head) == "System`List":
            for gg in g.elements:
                handle_g(gg)

        else:
            raise Exception(f"Unknown head {g.head}")

    for g in expr.elements:
        handle_g(g)


    util.start_timer("ijk arrays")
    xyzs = np.array(xyzs)
    ijks = np.array(ijks) - 1 # ugh - indices in Polygon are 1-based
    util.stop_timer()

    util.start_timer("mesh")
    mesh = go.Mesh3d(
        x=xyzs[:,0], y=xyzs[:,1], z=xyzs[:,2],
        i=ijks[:,0], j=ijks[:,1], k=ijks[:,2],
        showscale=True, colorscale="Viridis", colorbar=dict(thickness=10), intensity=xyzs[:,2],
    )
    util.stop_timer()
    
    util.start_timer("figure")
    #figure = go.Figure(data=[mesh])
    figure = go.Figure(
        data = [mesh],
        layout = go.Layout(
            margin = dict(l=0, r=0, t=0, b=0),
            scene = dict(
                xaxis_title="x", # TODO: xlims.name - from a rule?
                yaxis_title="y", # TODO: ylims.name - from a rule?
                #zaxis_title="z",
                aspectmode="cube"
            )
        )
    )
    """
    TODO zlims
    if zlims:
        figure.update_layout(scene = dict(zaxis = dict(range=zlims)))
    """
    util.stop_timer()

    """
            colorbar=dict(title=dict(text='z')),
            colorscale=[[0, 'gold'],
                        [0.5, 'mediumturquoise'],
                        [1, 'magenta']],
            # Intensity of each vertex, which will be interpolated and color-coded
            intensity=[0, 0.33, 0.66, 1],
            showscale=True
    """

    util.start_timer("layout")
    layout = dash.html.Div ([
        #dash.dcc.Markdown(f"${title}$", mathjax=True) if fancy else dash.html.Div(title, className="title"),
        dash.dcc.Graph(figure=figure, className="graph")
    ], className="plot")
    util.stop_timer()

    return layout

#
# Computer a layaout 
#

def layout_expr(fe, expr, values = {}):
    util.start_timer(f"layout {str(expr.head)}")
    if str(expr.head) == "My`Plot3D":
        result = layout_Plot3D(fe, expr, values)
    elif str(expr.head) == "Global`Manipulate":
        result = layout_Manipulate(fe, expr)
    elif str(expr.head) == "System`Graphics3D":
        result = layout_Graphics3D(fe, expr)
    else:
        raise Exception(f"Unknown head {expr.head} in layout_expr")
    util.stop_timer()
    return result

#
#
#

# https://github.com/Mathics3/mathics-core/blob/master/mathics/eval/drawing/plot.py
# https://github.com/Mathics3/mathics-core/blob/master/mathics/eval/drawing/plot3d.py

def eval_Plot3Dv1(fe, expr):
    result = Expression(Symbol("My`Plot3D"), *expr.elements)    
    return result

def eval_plot3d(fe, expr, grid_to_expr):

    # Plot3D arg exprs
    fun_expr = expr.elements[0]
    xlims_expr = expr.elements[1]
    ylims_expr = expr.elements[2]
        
    x_points = y_points = 10 # default
    for e in expr.elements[3:]:
        if hasattr(e, "head") and str(e.head) == "System`Rule":
            if str(e.elements[0]) == "System`PlotPoints":
                pp = e.elements[1].value
                if isinstance(pp, (tuple,list)):
                    x_points, y_points = pp
                else:
                    x_points = y_points = pp

    # compile fun
    values = {} # TODO: how to pass in values as expected by Manipulate
    fun_args = [str(xlims_expr.elements[0]), str(ylims_expr.elements[0])] + list(values.keys())
    fun = compile.my_compile(fun_expr, fun_args)

    # parse xlims, construct namedtuple
    # TODO: namedtuple probably not needed any more
    A = collections.namedtuple("A", ["name", "lo", "hi", "count"])
    def to_python_axis_spec(expr, pts):
        return A(str(expr.elements[0]).split("`")[-1], *[e.to_python() for e in expr.elements[1:]], pts)
    xlims = to_python_axis_spec(xlims_expr, x_points)
    ylims = to_python_axis_spec(ylims_expr, y_points)

    # parse zlims
    #zlims = [zlims_expr.elements[0].value, zlims_expr.elements[1].value] if zlims_expr else None

    # compute xs and ys
    xs = np.linspace(xlims.lo, xlims.hi, xlims.count)
    ys = np.linspace(ylims.lo, ylims.hi, ylims.count)
    xs, ys = np.meshgrid(xs, ys)

    # compute zs from xs and ys using compiled function
    zs = fun(**({xlims.name: xs, ylims.name: ys} | values))

    return grid_to_expr(xs, ys, zs)

list_expr = lambda *a: ListExpression(*a, literal_values = a)

# List of Polygon each with its own list of x,y,z coordinates
def grid_to_expr_poly_list(xs, ys, zs):

    # a=[1:,1:]   b=[1:,:-1]
    # c=[:-1:,1:] d=[:-1,:-1]
    xyzs = np.stack([xs, ys, zs], axis=-1)                                # shape = (nx,ny,3)
    tris1 = np.stack([xyzs[1:,1:], xyzs[1:,:-1], xyzs[:-1,:-1]], axis=-1) # abd, shape = (nx-1,ny-1,3,3)
    tris2 = np.stack([xyzs[1:,1:], xyzs[:-1,:-1], xyzs[:-1,1:]], axis=-1) # adc, shape = (nx-1,ny-1,3,3)
    tris = np.stack([tris1,tris2])                                        # shape = (2,nx-1,ny-1,3,3)
    tris = tris.reshape((-1,3,3)).transpose(0,2,1)                        # shape = (2*(nx-1)*(ny-1),3,3)

    # TODO: check this
    # ugh - indices in Polygon are 1-based
    tris += 1

    # this is the slow part
    # corresponding traversal at other end is similarly slow
    util.start_timer("construct G3D list of polys")
    result = Expression(Symbol("System`Graphics3D"), 
        Expression(Symbol("System`List"), *(
            Expression(Symbol("System`Polygon"), list_expr(list_expr(*p), list_expr(*q), list_expr(*r)))
            for p, q, r in tris
        ))
    )
    util.stop_timer()

    return result


# instantiate an actual nested List structure from a numpy array
# this is slow
def numpy_array_list_expr(v, mathics_type):
    if isinstance(v, np.ndarray):
        return ListExpression(*(numpy_array_list_expr(vv, mathics_type) for vv in v), literal_values = v)
    else:
        # numpy scalar as mathics type
        return mathics_type(v.item())

# quacks like a List Expression, but only lazily generates elements if you really insist
# those in the know can look at .value, which is an np array, for an efficient shortcut
# that avoids ever constructing the List per se
class NumpyArrayListExpr:

    def __init__(self, value, mathics_type):
        self.head = Symbol("System`List") # TODO use import
        self.value = value
        self.mathics_type = mathics_type
        self._elements = None

    @property
    def elements(self):
        if not self._elements:
            # if call really really needs .elements we'll compute them here
            # but it's more efficient to just look at .value
            # TODO: this instantiates whole nested list structure on first reference
            # should we likewise lazily evaluate each element of the list in the case of >1-d arrays?
            self._elements = numpy_array_list_expr(self.value, self.mathics_type).elements
        return self._elements

# GraphicsComplex with list of points, and list of polys, each poly a list of indices in the list of points
def grid_to_expr_complex(xs, ys, zs, np_expr):
    
    n = math.prod(xs.shape)
    inxs = np.arange(n).reshape(xs.shape)                                                       # shape = (nx,ny)
    quads = np.stack([inxs[:-1,:-1], inxs[:-1,1:], inxs[1:,1:], inxs[1:,:-1]]).T.reshape(-1, 4) # shape = ((nx-1)*(nx-1), 4)
    xyzs = np.stack([xs, ys, zs]).transpose(1,2,0).reshape(-1,3)                                # shape = (nx*ny, 3)

    # ugh - indices in Polygon are 1-based
    quads += 1

    quads_expr = np_expr(quads, Integer)
    xyzs_expr = np_expr(xyzs, Real)
    poly_expr = Expression(Symbol("System`Polygon"), quads_expr)
    gc_expr = Expression(Symbol("Global`GraphicsComplex"), xyzs_expr, poly_expr)
    result = Expression(Symbol("System`Graphics3D"), gc_expr)
        
    return result

def eval_Plot3Dv2(fe, expr):
    return eval_plot3d(fe, expr, grid_to_expr_poly_list)

def eval_Plot3Dv3(fe, expr):
    return eval_plot3d(fe, expr, lambda xs, ys, zs: grid_to_expr_complex(xs, ys, zs, numpy_array_list_expr))

def eval_Plot3Dv4(fe, expr):
    return eval_plot3d(fe, expr, lambda xs, ys, zs: grid_to_expr_complex(xs, ys, zs, NumpyArrayListExpr))


def eval_expr(fe, expr):
    util.start_timer(f"eval {expr.head}")
    funs = {
        "My`Plot3Dv1": eval_Plot3Dv1,
        "My`Plot3Dv2": eval_Plot3Dv2,
        "My`Plot3Dv3": eval_Plot3Dv3,
        "My`Plot3Dv4": eval_Plot3Dv4,
    }
    if str(expr.head) in funs:
        result = funs[str(expr.head)](fe, expr)
    else:
        result = expr.evaluate(fe.session.evaluation)
    util.stop_timer()
    return result


