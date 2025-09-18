import collections 
import itertools
import numpy as np

import mathics.core.atoms as mca

import dash
import plotly.graph_objects as go

import ev
import ex
import util

#
# Functions related to processing expressions for display using dash and plotly
# by computing a dash layout
#

# compute a unique id for use in html
ids = collections.defaultdict(lambda: 0)
def uid(s):
    ids[s] += 1
    return f"{s}-{ids[s]}"


#
# given a Manipulate Expression, compute a layout
#
# note that on every slider move this evaluates target_expr (e.g. Plot3D),
# which then compiles its expr (e.g. Sin etc.) on every slider move
# we could lift that compilation into Manipulate by compiling target_expr,
# but timings show that would be practically meaningless for performance,
# and it would complicate the implementation
# 
def layout_Manipulate(fe, expr):

    target_expr = expr.elements[0]
    slider_exprs = expr.elements[1:]

    # parse slider specs
    S = collections.namedtuple("S", ["name", "lo", "init", "hi", "step", "id"])
    def slider(e):
        spec = e.to_python()
        v, lo, hi = spec[0:3]
        step = spec[3] if len(spec) > 3 else (hi-lo)/10 # TODO: better default step
        v, init = v if isinstance(v, (list,tuple)) else (v, lo)
        v = str(v).split("`")[-1] # strip off namespace pfx
        spec = S(v, lo, init, hi, step, uid("slider"))
        return spec
    sliders = [slider(e) for e in slider_exprs]

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

    # compute a layout for the target_expr given a set of values
    def eval_and_layout(values):
        # TODO: always Global?
        # TODO: always Real?
        # TODO: best order for replace_vars and eval?
        expr = target_expr.replace_vars({"Global`"+n: mca.Real(v) for n, v in values.items()})
        expr = ev.eval_expr(fe, expr)
        layout = layout_expr(fe, expr)
        return layout

    # compute initial layout including target_expr and slider
    init_target_layout = eval_and_layout(init_values)
    slider_layouts = list(itertools.chain(*[slider_layout(s) for s in sliders]))
    layout = dash.html.Div([
        dash.html.Div(init_target_layout, id=target_id),
        dash.html.Div(slider_layouts, className="sliders")
    ], className="manipulate")
        
    # set timer display for slider updates after initial display
    util.timer_level = 1 # to see top-level timings as sliders move
    #util.timer_level = 0 # no timings as sliders move

    # define callbacks for the sliders
    print("xxx adding sliders", sliders)
    @fe.app.callback(
        dash.Output(target_id, "children"),
        *(dash.Input(s.id, "value") for s in sliders),
        prevent_initial_call=True
    )
    def update(*args):
        util.start_timer("slider update")
        result = eval_and_layout({s.name: a for s, a in zip(sliders, args)})
        util.stop_timer()
        return result

    return layout


#
# compute a layout for a Graphics3D object, such as returned by Plot3D
#
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
                    if isinstance(polys, ex.NumpyArrayListExpr):
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
            pass

        elif str(g.head) == "System`List":
            for gg in g.elements:
                handle_g(gg)

        else:
            raise Exception(f"Unknown head {g.head}")

    for g in expr.elements:
        handle_g(g)

    # process options
    x_range = y_range = z_range = None
    for name, value in ex.get_rule_values(expr):
        if name == "System`PlotRange":
            x_range, y_range, z_range = [v if isinstance(v, (tuple,list)) else None for v in value]

    util.start_timer("construct xyz and ijk arrays")
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
    # TODO: x_range and y_range
    if z_range:
        figure.update_layout(scene = dict(zaxis = dict(range=z_range)))
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
# Compute a layout 
#

def layout_expr(fe, expr):
    util.start_timer(f"layout {str(expr.head)}")
    # TODO: System `Manipulate
    if str(expr.head) == "Global`Manipulate":
        result = layout_Manipulate(fe, expr)
    elif str(expr.head) == "System`Graphics3D":
        result = layout_Graphics3D(fe, expr)
    else:
        raise Exception(f"Unknown head {expr.head} in layout_expr")
    util.stop_timer()
    return result

