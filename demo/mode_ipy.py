import ipywidgets as ipw
import time

import mcs
import mode
import util

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

def graph(figure, height):
    figure._config = dict(displayModeBar = False)
    center_baseline = ipw.HBox([], layout=ipw.Layout(width="0", height=f"{height/2}px"))
    layout = ipw.HBox([center_baseline, figure])
    return layout
                      
last_slider_update = None

def panel(init_target_layout, sliders, eval_and_layout):

    # TODO: for some reason tbd update is called once, and once only, on initialization; not sure how that happens
    # but that means that the init_target_layout is wasted work - so consider moving init_target_layout
    # computation into mode.panel
    def update(change):

        global last_slider_update
        if last_slider_update and not util.Timer.quiet:
            print(f"between slider updates: {(time.time()-last_slider_update)*1000:.1f}")

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

    target = ipw.VBox([])
    layout = ipw.VBox([target, *sliders], layout=ipw.Layout(width="min-content"))

    return layout


#
# TODO: this is temp for demo - should be handled by custom kernel
# TODO: this starts a new Dash server for every evaluation
# probably not what is wanted - use something like ShellFrontEnd?
def eval(s):
    expr = mode.the_fe.session.parse(s)
    layout = mode.layout_expr(mode.the_fe, expr)
    display(layout)
    return None


