import dash
import itertools
import numpy as np
import time

import mcs
import mode
import util

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

    # assign row and column using variables that are picked up by css
    # TODO: comprehension?
    flat_grid_content = []
    for row_number, row in enumerate(grid_content):
        for col_number, cell in enumerate(row):
            if not hasattr(cell, "style"):
                cell.style = {}
            cell.style["--row"] = str(row_number+1)
            cell.style["--col"] = str(col_number+1)
            flat_grid_content.append(cell)

    layout = dash.html.Div(flat_grid_content, className="m-grid")
    return layout

def graph(figure, height):
    # TODO: figure out whether the current mix of explicit style and implicit css is the cleanest way to do this
    # the corresponding code for ipy widgets seems a bit simpler and cleaner...
    layout = dash.html.Div ([
        dash.dcc.Graph(figure=figure, config={'displayModeBar': False}, className="m-graph")
    ], className="m-plot", style=dict(height=f"{height}px"))
    return layout

#
# a panel is a target item (e.g. a plot) and a list of sliders
# implements the layout for Manipulate
#

# each element is a callback for a given panel that takes
# a list of slider values and returns a new layout for the target
panels = []
pending_values = []

# wire up the sliders for a given panel by matching slider and target panel_number
# this pattern does the wiring for all panels
def register_callbacks(app):

    @app.callback(
        dash.Output(dict(type="poll", panel_number=dash.MATCH), "disabled"),
        dash.Input(dict(type="slider", panel_number=dash.MATCH, index=dash.ALL), "value"),
        prevent_initial_call=True
    )
    def update(values):
        panel_number = dash.ctx.inputs_list[0][0]["id"]["panel_number"]        
        pending_values[panel_number] = values
        return False

    @app.callback(
        dash.Output(dict(type="target", panel_number=dash.MATCH), "children"),
        dash.Input(dict(type="poll", panel_number=dash.MATCH), "n_intervals"),
        prevent_initial_call=True
    )
    def update(n_intervals):

        panel_number = dash.ctx.outputs_list["id"]["panel_number"]
        values = pending_values[panel_number]
        if not values:
            print("not updating")
            raise dash.exceptions.PreventUpdate
        pending_values[panel_number] = None

        with util.Timer("slider update"):
            eval_and_layout = panels[panel_number]
            result = eval_and_layout(values)

        return result

def panel(init_target_layout, sliders, eval_and_layout):

    panel_number = len(panels)
    panels.append(eval_and_layout)
    pending_values.append(None)

    # compute a slider layout from a slider spec (S namedtuple)
    def slider_layout(s, inx):
        # TODO: handling of tick marks and step needs work; this code is just for demo purposes
        slider_id = dict(type="slider", panel_number=panel_number, index=inx)
        marks = {value: f"{value:g}" for value in np.arange(s.lo, s.hi, s.step)}
        return [
            dash.html.Label(s.name),
            dash.dcc.Slider(id=slider_id, marks=marks, min=s.lo, max=s.hi, step=s.step/10, value=s.init, updatemode="drag"),
            #dash.dcc.Store(id=store_id, data=dict(gen=0))
        ]
    slider_layouts = list(itertools.chain(*[slider_layout(s, inx) for inx, s in enumerate(sliders)]))

    # put the target and sliders together
    target_id = dict(type="target", panel_number=panel_number)
    poll_id = dict(type="poll", panel_number=panel_number)
    layout = dash.html.Div([
        dash.html.Div(init_target_layout, id=target_id),
        dash.html.Div(slider_layouts, className="m-sliders"),
        dash.dcc.Interval(id=poll_id, interval=100, disabled=True)
    ], className="m-manipulate")
    return layout

#
# use in a layout to arrange for js to be executed after the layout is loaded
# see code for examples
#
# TODO: this is a bit hacky - can we do better?
#

def exec_js(js):
    import dash_extensions # causes problems in some env, only import if used
    import urllib
    params = urllib.parse.urlencode(dict(js=js))
    url = f"/assets/exec_js.js?{params}"
    return dash_extensions.DeferScript(src=url)


#
# TODO: this is temp for demo - should be handled by custom kernel
# TODO: this starts a new Dash server for every evaluation
# probably not what is wanted - use something like ShellFrontEnd?
def eval(s):
    expr = mode.the_fe.session.parse(s)
    app = dash.Dash()
    register_callbacks(app)
    app.layout = mode.layout_expr(mode.the_fe, expr)
    app.run(mode = "inline")
    return None


