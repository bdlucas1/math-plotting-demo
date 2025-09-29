import ipywidgets as ipw

import jax
import mcs
import mode
import util

def row(ls):
    return ipw.HBox(ls, layout=ipw.Layout(align_items='baseline'))

def latex(s):
    return ipw.Label(value="$"+s+"$") if isinstance(s, str) else s    

# grid seems to need this wrapped in a box
# TODO: make this baseline aligned - see stupid css trick in app.css
# use ipw.html to emit a style sheet somewhere - maybe in the first output??
def graph(figure):
    return ipw.HBox([figure], layout=ipw.Layout(align_items='baseline'))

def wrap(s):
    return ipw.Label(value=s)

def grid(grid_content):

    n_rows = len(grid_content)
    n_cols = max(len(row) for row in grid_content)
    # TODO: unfortunately our use of "layout" conflicts with this use of layout
    # our use of layout derives from dash, so maybe we could find another term...
    lay = ipw.Layout(
        #align_items = "baseline", # vertically
        # TODO: for now until we get baseline working
        align_items = "center", # vertically
        justify_items = "center", # horizontally
    )
    layout = ipw.GridspecLayout(n_rows, n_cols, layout=lay)

    # assign
    for row_number, row in enumerate(grid_content):
        for col_number, cell in enumerate(row):
            layout[row_number, col_number] = cell

    # this keeps the grid from expanding horizontally, not sure why
    # TODO: but grid columns are all same width, based on max column width - is that what we want?
    layout = ipw.HBox([layout])

    return layout


def panel(init_target_layout, sliders, eval_and_layout):

    # TODO: for some reason tbd update is called once, and once only, on initialization; not sure how that happens
    # but that means that the init_target_layout is wasted work - so consider moving init_target_layout
    # computation into mode.panel
    def update(change):
        target_layout = eval_and_layout([s.value for s in sliders])
        target.children = (target_layout,)

    def slider_layout(s):
        slider = ipw.widget_float.FloatSlider(
            description=s.name, min=s.lo, max=s.hi, step=s.step/10, value=s.init,
            layout = ipw.Layout(width="100%")
        )
        slider.observe(update, names="value")
        return slider
    sliders = [slider_layout(s) for s in sliders]

    target = ipw.VBox([])
    layout = ipw.VBox([target, *sliders], layout=ipw.Layout(width="min-content"))

    return layout


#
# TODO: this is temp for demo - should be handled by custom kernel
# TODO: this starts a new Dash server for every evaluation
# probably not what is wanted - use something like ShellFrontEnd?
def ev(s):
    expr = mode.the_fe.session.parse(s)
    layout = jax.layout_expr(mode.the_fe, expr)
    display(layout)
    return None
