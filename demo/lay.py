import collections 
import itertools
import numpy as np

import dash
import plotly.graph_objects as go

import ev
import ex
import jax
import mcs
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

def register_callbacks(fe):
    Panel.register_callback(fe)

#
# plot plus sliders
#
class Panel:

    panels = []

    # one callback handles all dynamically created panels and sliders
    # sliders are matched to their corresponding plot output by matching on panel_number
    def register_callback(fe):
        @fe.app.callback(
            dash.Output(dict(type="target", panel_number=dash.MATCH), "children"),
            dash.Input(dict(type="slider", panel_number=dash.MATCH, index=dash.ALL), "value"),
            prevent_initial_call=True
        )
        def update(values):
            with util.Timer("slider update"):
                panel_number = dash.ctx.outputs_list["id"]["panel_number"]
                panel = Panel.panels[panel_number]
                result = panel.eval_and_layout({s.name: a for s, a in zip(panel.sliders, values)})
            return result

    def __init__(self, fe, expr, slider_exprs):

        self.fe = fe
        self.expr = expr
        self.panel_number = len(Panel.panels)
        Panel.panels.append(self)

        # parse slider specs
        S = collections.namedtuple("S", ["name", "lo", "init", "hi", "step", "id"])
        def slider(e, inx):
            spec = e.to_python()
            v, lo, hi = spec[0:3]
            step = spec[3] if len(spec) > 3 else (hi-lo)/10 # TODO: better default step
            v, init = v if isinstance(v, (list,tuple)) else (v, lo)
            v = str(v).split("`")[-1] # strip off namespace pfx
            id = dict(type="slider", panel_number=self.panel_number, index=inx)
            spec = S(v, lo, init, hi, step, id)
            return spec
        self.sliders = [slider(e, inx) for inx, e in enumerate(slider_exprs)]

    # compute a layout for an expr given a set of values
    def eval_and_layout(self, values):
        # TODO: always Global?
        # TODO: always Real?
        # TODO: best order for replace_vars and eval?
        expr = self.expr.replace_vars({"Global`"+n: mcs.Real(v) for n, v in values.items()})
        expr = ev.eval_expr(self.fe, expr) # TODO: move this to __init__?
        layout = layout_expr(self.fe, expr)
        return layout

    def layout(self):

        # compute the layout for the plot
        target_id = dict(type="target", panel_number=self.panel_number)
        init_values = {s.name: s.init for s in self.sliders}

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

        # compute initial layout including target_expr and slider
        init_target_layout = self.eval_and_layout(init_values)
        slider_layouts = list(itertools.chain(*[slider_layout(s) for s in self.sliders]))
        layout = dash.html.Div([
            dash.html.Div(init_target_layout, id=target_id),
            dash.html.Div(slider_layouts, className="sliders")
        ], className="manipulate")

        return layout


def layout_Manipulate(fe, expr):

    target_expr = expr.elements[0]
    slider_exprs = expr.elements[1:]

    panel = Panel(fe, target_expr, slider_exprs)
    layout = panel.layout()
        
    # set timer display for slider updates after initial display
    util.Timer.level = 1 # to see top-level timings as sliders move
    #util.Timer.level = 0 # no timings as sliders move


    return layout


#
# compute a layout for a Graphics3D object, such as returned by Plot3D
#
def layout_Graphics3D(fe, expr):

    xyzs = []
    ijks = []

    def handle_g(g):

        if g.head == mcs.SymbolPolygon:
            poly = [p.value for p in g.elements[0].elements]
            i = len(xyzs)
            xyzs.extend(poly)
            ijks.append([i+1,i+2,i+3]) # ugh - 1-based to match GraphicsComplex Polygon

        elif g.head == mcs.SymbolLine:
            line = [p.value for p in g.elements[0].elements]

        elif g.head == mcs.SymbolGraphicsComplex:

            with util.Timer("xyzs"):
                xyzs.extend(g.elements[0].value)

            def handle_c(c):

                if c.head == mcs.SymbolPolygon:

                    polys = c.elements[0]
                    if isinstance(polys, ex.NumpyArrayListExpr):
                        with util.Timer("ijks from NumpyArrayListExpr"):
                            # use advanced indexing to break the polygons down into triangles
                            ngon = polys.value.shape[1]
                            for i in range(1, ngon-1):
                                inx = [0, i, i+1]
                                tris = polys.value[:, inx]
                                ijks.extend(tris)

                    else:
                        with util.Timer("ijks from mathics List of polys"):
                            for poly in polys.elements:
                                for j, k in zip(poly.elements[1:-1], poly.elements[2:]):
                                    ijks.append([poly.elements[0].value, j.value, k.value])

                else:
                    raise Exception(f"Unknown head {c.head} in GraphicsComplex")

            for c in g.elements[1:]:
                handle_c(c)

        elif g.head == mcs.SymbolRule:
            pass

        elif g.head == mcs.SymbolList:
            for gg in g.elements:
                handle_g(gg)

        else:
            raise Exception(f"Unknown head {g.head}")

    for g in expr.elements:
        handle_g(g)

    # process options
    x_range = y_range = z_range = None
    axes = True
    showscale = False
    colorscale = "viridis"
    size = None
    for sym, value in ex.get_rule_values(expr):
        if sym == mcs.SymbolPlotRange:
            if not isinstance(value, (list,tuple)):
                value = [value, value, value]
            x_range, y_range, z_range = [v if isinstance(v, (tuple,list)) else None for v in value]
        elif sym == mcs.SymbolAxes:
            axes = value
        elif sym == mcs.SymbolPlotLegends:
            # TODO: what if differs from ColorFunction->?
            # TODO: what if multiple legends requested?
            showscale = True
            # TODO: value sometimes comes through as expr, sometimes as tuple?
            if getattr(value, "head", None) == mcs.SymbolBarLegend:
                # TODO: for some reason value has literal quotes?
                colorscale = str(value.elements[0])[1:-1]
            elif isinstance(value, (tuple,list)):
                colorscale = value[0]
        elif sym == mcs.SymbolColorFunction:
            # TODO: for some reason value is coming through with literal quotes?
            # TODO: what if differs from PlotLegends?
            colorscale = value[1:-1]
        elif sym == mcs.SymbolImageSize:
            size = value
        else:
            # TODO: Plot is passing through all options even e.g. PlotPoints
            #print(f"option {sym} not recognized")
            pass

    with util.Timer("construct xyz and ijk arrays"):
        xyzs = np.array(xyzs)
        ijks = np.array(ijks) - 1 # ugh - indices in Polygon are 1-based

    with util.Timer("mesh"):
        mesh = go.Mesh3d(
            x=xyzs[:,0], y=xyzs[:,1], z=xyzs[:,2],
            i=ijks[:,0], j=ijks[:,1], k=ijks[:,2],
            showscale=showscale, colorscale=colorscale, colorbar=dict(thickness=10), intensity=xyzs[:,2],
        )
    
    with util.Timer("figure"):
        figure = go.Figure(
            data = [mesh],
            layout = go.Layout(
                margin = dict(l=0, r=0, t=0, b=0),
                scene = dict(
                    xaxis = dict(title="x", visible=axes), # TODO: name
                    yaxis = dict(title="y", visible=axes), # TODO: name
                    zaxis = dict(title="z", visible=axes), # TODO: name
                    aspectmode="cube"
                )
            )
        )
        # TODO: x_range and y_range
        if z_range:
            figure.update_layout(scene = dict(zaxis = dict(range=z_range)))

    with util.Timer("layout"):
        layout = dash.html.Div ([
            #dash.dcc.Markdown(f"${title}$", mathjax=True) if fancy else dash.html.Div(title, className="title"),
            dash.dcc.Graph(figure=figure, className="graph")
        ], className="plot")
        if size:
            layout.style = dict(width=f"{size}pt", height=f"{size}pt")

    return layout

def layout_Row(fe, expr):
    def do(e):
        # TODO: temp demo hack until we integrate Demo` into system and eliminate ev.eval_expr
        # then this will already have been done
        e = ev.eval_expr(fe, e)
        return layout_expr(fe, e)
    # TODO: expr.elements[1] is a separator
    layout = dash.html.Div([do(e) for e in expr.elements[0].elements], className="m-row")
    return layout

def layout_Grid(fe, expr):

    def do(e):
        # TODO: temp demo hack until we integrate Demo` into system and eliminate ev.eval_expr
        # then this will already have been done
        e = ev.eval_expr(fe, e)
        layout = layout_expr(fe, e)

        # assign row and column using variables that are picked up by css
        if not hasattr(layout, "style"):
            layout.style = {}
        layout.style["--row"] = str(row_number+1)
        layout.style["--col"] = str(col_number+1)

        return layout

    grid_content = []
    for row_number, row in enumerate(expr.elements[0]):
        for col_number, cell in enumerate(row.elements):
            grid_content.append(do(cell))

    layout = dash.html.Div(grid_content, className="m-grid")
    return layout

#
# Compute a layout 
#

layout_funs = {
    mcs.SymbolManipulate: layout_Manipulate,
    mcs.SymbolGraphics3D: layout_Graphics3D,
    mcs.SymbolRow: layout_Row,
    mcs.SymbolGrid: layout_Grid,
}

def layout_expr(fe, expr):
    # TODO: make the logic here less convoluted
    if not hasattr(expr, "head"):
        # TODO: works for demo, but is this correct in general?
        if hasattr(expr, "value") and isinstance(expr.value, str):
            return dash.html.Div(expr.value)
        else:
            # TODO: ok to use jax to handle everything but strings?
            # TODO: should also use jax to handle strings? rows? grids?
            return jax.to_math(expr)
    with util.Timer(f"layout {expr.head}"):
        if expr.head in layout_funs:
            # TODO: handle this the same way as the following `result :=` pattern?
            result = layout_funs[expr.head](fe, expr)
        elif result := jax.to_math(expr):
            pass
        else:
            raise Exception(f"Unknown head {expr.head} in layout_expr")
    return result

