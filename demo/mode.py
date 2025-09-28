import itertools
import numpy as np

import util

use_dash = True

if use_dash:

    import dash

    def graph(figure, size):
        layout = dash.html.Div ([
            #dash.dcc.Markdown(f"${title}$", mathjax=True) if fancy else dash.html.Div(title, className="m-title"),
            dash.dcc.Graph(figure=figure, className="m-graph")
        ], className="m-plot")
        if size:
            layout.style = dict(width=f"{size}pt", height=f"{size}pt")
        return layout

    def wrap(s):
        layout = dash.html.Div(s)
        return layout

    def latex(s):
        layout = dash.dcc.Markdown("$"+s+"$", mathjax=True)        
        return layout

    # TODO: just a one-row grid?
    def row(ls):
        layout = dash.html.Div(ls, className="m-row")
        return layout

    def grid(grid_content):
        layout = dash.html.Div(grid_content, className="m-grid")
        return layout

    #
    # a panel is a target item (e.g. a plot) and a list of sliders
    # implements the layout for Manipulate
    #

    # each element is (slider, eval_and_layout) pair
    panels = []

    def register_callbacks(fe):

        @fe.app.callback(
            dash.Output(dict(type="target", panel_number=dash.MATCH), "children"),
            dash.Input(dict(type="slider", panel_number=dash.MATCH, index=dash.ALL), "value"),
            prevent_initial_call=True
        )
        def update(values):
            with util.Timer("slider update"):
                panel_number = dash.ctx.outputs_list["id"]["panel_number"]
                sliders, eval_and_layout = panels[panel_number]
                result = eval_and_layout({s.name: a for s, a in zip(sliders, values)})
            return result

    def panel(init_target_layout, sliders, eval_and_layout):

        panel_number = len(panels)
        panels.append((sliders, eval_and_layout))

        # compute a slider layout from a slider spec (S namedtuple)
        def slider_layout(s, inx):
            # TODO: handling of tick marks and step needs work; this code is just for demo purposes
            slider_id = dict(type="slider", panel_number=panel_number, index=inx)
            marks = {value: f"{value:g}" for value in np.arange(s.lo, s.hi, s.step)}
            return [
                dash.html.Label(s.name),
                dash.dcc.Slider(id=slider_id, marks=marks, min=s.lo, max=s.hi, step=s.step/10, value=s.init, updatemode="drag")
            ]
        slider_layouts = list(itertools.chain(*[slider_layout(s, inx) for inx, s in enumerate(sliders)]))

        target_id = dict(type="target", panel_number=panel_number)
        layout = dash.html.Div([
            dash.html.Div(init_target_layout, id=target_id),
            dash.html.Div(slider_layouts, className="m-sliders")
        ], className="m-manipulate")
        return layout
        
