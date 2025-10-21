#
# use ipy widgets
# good for jupyter and jupyterlite(piodide) environments
#


import ipywidgets as ipw
import time

import layout as lt
import mcs
import mode
import util

# load our stylesheet, shared with dash mode for consistency
import IPython.display as ipd
try:
    file = open("assets/app.css")
except:
    file = open("app.css")
css = f"<style>{file.read()}</style>"
ipd.display(ipd.HTML(css))

def wrap(s):
    return ipw.Label(value=s)

def latex(s):
    return ipw.Label(value="$"+s+"$") if isinstance(s, str) else s    

def row(ls):
    ls = [ipw.Label(l) if isinstance(l,str) else l for l in ls]
    return ipw.HBox(ls, layout=ipw.Layout(align_items='baseline'))

def grid(grid_content):

    n_rows = len(grid_content)
    n_cols = max(len(row) for row in grid_content)
    # TODO: unfortunately our use of "layout" conflicts with this use of layout
    # our use of layout derives from dash, so maybe we could find another term...
    css = ipw.Layout(
        #align_items = "baseline", # vertically
        # TODO: for now until we get baseline working
        align_items = "center", # vertically
        justify_items = "center", # horizontally
        grid_template_columns = f"repeat({n_cols}, auto)",
    )
    children = [cell for row in grid_content for cell in row]
    layout = ipw.GridBox(layout=css, children=children)
    layout._dom_classes = ["m-grid"]

    # this keeps the grid from expanding horizontally, not sure why
    layout = ipw.HBox([layout])

    return layout

def graph(figure, height):
    figure._config = dict(displayModeBar = False)
    center_baseline = ipw.HBox([], layout=ipw.Layout(width="0", height=f"{height/2}px"))
    layout = ipw.HBox([center_baseline, figure])
    return layout
                      
last_slider_update = None

def manipulate(init_target_layout, sliders, eval_and_layout):

    def update(change):

        global last_slider_update
        if last_slider_update:
            pass
            #print(f"between slider updates: {(time.time()-last_slider_update)*1000:.1f}")

        with util.Timer("slider update"):
            target_layout = eval_and_layout([s.value for s in sliders])
            target.children = (target_layout,)

        last_slider_update = time.time()

    def slider_layout(s):
        slider = ipw.widget_float.FloatSlider(
            description=s.name, min=s.lo, max=s.hi, step=s.step/10, value=s.init,
            layout = ipw.Layout(width="100%")
        )
        slider.observe(update, names="value")
        return slider
    sliders = [slider_layout(s) for s in sliders]
    slider_box = ipw.VBox(sliders)
    slider_box._dom_classes = ["m-sliders"]

    target = ipw.VBox([init_target_layout])
    lay = ipw.Layout(width="min-content")
    layout = ipw.VBox([target, slider_box],  layout=lay)
    layout._dom_classes = ["m-manipulate"]

    return layout


#
# TODO: this is temp for demo - should be handled by custom kernel
# TODO: this starts a new Dash server for every evaluation
# probably not what is wanted - use something like ShellFrontEnd?
def eval(s):
    expr = mode.the_fe.session.parse(s)
    expr = expr.evaluate(mode.the_fe.session.evaluation)
    layout = lt.expression_to_layout(mode.the_fe, expr)
    display(layout)
    return None


