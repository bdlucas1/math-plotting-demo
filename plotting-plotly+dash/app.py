import math
import time
import threading
import collections 
import itertools
import webbrowser
import inspect
import atexit
import argparse

# pip install numpy dash plotly pywebview
import webview
import numpy as np
import scipy
import mathics.session
import dash
import werkzeug
import plotly.graph_objects as go


parser = argparse.ArgumentParser(description="Graphics demo")
parser.add_argument("--debug", action="store_true")
parser.add_argument("--fe", choices=["shell", "browser"], default="shell")
parser.add_argument("--browser", choices=["webview", "webbrowser"], default="webview")
args = parser.parse_args()

# load a url into a browser, using either:
# webview - pop up new standalone window using pywebview
# webbrowser - instruct system browser to open a new window
class Browser():

    def __init__(self):
        self.n = 0

    def show(self, url):
        # display a browser window that fetches the current plot
        print("showing", url)
        if args.browser == "webview":
            offset = 50 * self.n
            self.n += 1
            webview.create_window(url, url, x=100+offset, y=100+offset, width=600, height=800)
        elif args.browser == "webbrowser":
            webbrowser.open_new(url)

    def start(self):
        if args.browser == "webview":
            # webview needs to run on main thread :( and blocks, so we start other things on their own thread
            # webview needs a window before we can call start() :(, so we make a hidden one
            # real windows will be provided later
            webview.create_window("hidden", hidden=True)
            webview.start()
        elif args.browser == "webbrowser":
            time.sleep(1e6)

    #atexit.register(start)


#
# util
#

# pretty print expr
def pp(expr, indent=1):
    if not hasattr(expr, "elements"):
        print("  " * indent + str(expr))
    else:
        print("  " * indent + str(expr.head))
        for elt in expr.elements:
            pp(elt, indent + 1)

def to_python_expr(expr, lib = "np"):

    funs = {
        "System`Sin": f"{lib}.sin",
        "System`Cos": f"{lib}.cos",
        "System`Sqrt": f"{lib}.sqrt",
        "System`Abs": f"{lib}.abs",
        "System`Hypergeometric1F1": "scipy.special.hyp1f1",
    }

    listfuns = {
        "System`Plus": "sum", # TODO: np.sum?
        "System`Times": "math.prod" # TODO: np.prod?

    }

    binops = {
        "System`Power": "**",
    }

    if not hasattr(expr, "head"):
        if str(expr).startswith("Global`"):
            return str(expr).split("`")[-1]
        elif str(expr) == "System`I":
            return "1j"
        else:
            return str(expr)
    elif str(expr.head) in funs:
        fun = funs[str(expr.head)]
        args = (to_python_expr(e,lib) for e in expr.elements)
        return f"{fun}({",".join(args)})"
    elif str(expr.head) in listfuns:
        fun = listfuns[str(expr.head)]
        args = (to_python_expr(e,lib) for e in expr.elements)
        return f"{fun}([{",".join(args)}])"
    elif str(expr.head) in binops:
        arg1 = to_python_expr(expr.elements[0],lib)
        arg2 = to_python_expr(expr.elements[1],lib)
        return f"({arg1}{binops[str(expr.head)]}{arg2})"
    else:
        raise Exception(f"Unknown head {expr.head}")

def my_compile(expr, arg_names, lib = "np"):
    python_expr = to_python_expr(expr, lib)
    python_arg_names = [n.split("`")[-1] for n in arg_names]
    arg_list = ','.join(python_arg_names)
    python_def = f"lambda {arg_list}: {python_expr}"
    f = eval(python_def)
    return f

# compute a unique id for use in html
ids = collections.defaultdict(lambda: 0)
def uid(s):
    ids[s] += 1
    return f"{s}-{ids[s]}"


#
# given a Plot3D expression, compute a layout
# 

def layout_Plot3D(fe, expr, values = {}):

    start = time.time()

    # Plot3D arg exprs
    fun_expr = expr.elements[0]
    xlims_expr = expr.elements[1]
    ylims_expr = expr.elements[2]
    zlims_expr = expr.elements[3] if len(expr.elements) > 3 else None
        
    # compile fun
    fun_args = [str(xlims_expr.elements[0]), str(ylims_expr.elements[0])] + list(values.keys())
    fun = my_compile(fun_expr, fun_args)

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
    layout = dash.html.Div ([
        dash.dcc.Markdown(f"${title}$", mathjax=True) if fancy else dash.html.Div(title, className="title"),
        dash.dcc.Graph(figure=figure, className="graph")
    ], className="plot")

    print(f"Plot3D_layout {(time.time()-start)*1000:.1f} ms")

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



#
# Computer a layaout 
#

def layout_expr(fe, expr, values = {}):
    if str(expr.head) == "System`Plot3D":
        return layout_Plot3D(fe, expr, values)
    elif str(expr.head) == "Global`Manipulate":
        return layout_Manipulate(fe, expr)

#
# 
#

demos = [
    "Plot3D[Sin[x^2+y^2] / Sqrt[x^2+y^2+1], {x,-3,3,200}, {y,-3,3,200}]",
    #]; [
    """
        Manipulate[
            Plot3D[Sin[(x^2+y^2)*freq] / Sqrt[x^2+y^2+1] * amp, {x,-3,3,200}, {y,-3,3,200}, {-1,1}],
            {freq, 0.1, 1.0, 2.0, 0.2}, (* freq slider spec *)
            {amp, 0.0, 1.2, 2.0, 0.2}  (* amp slider spec *)
        ]
    """,
    """
        Manipulate[
            Plot3D[Abs[Hypergeometric1F1[a, b, (x + I y)^2]], {x, -2, 2, 200}, {y, -2, 2, 200}, {0, 14}],
            {a, 0.5, 1, 1.5, 0.1}, (* a slider spec *)
            {b, 1.5, 2, 2.5, 0.1}  (* b slider spec *)
        ]
    """,
]

# common to ShellFrontEnd and BrowserFrontEnd
class DashFrontEnd:

    def __init__(self):

        # create app, set options
        self.app = dash.Dash(__name__, suppress_callback_exceptions=True)
        self.app.enable_dev_tools(debug = args.debug, dev_tools_silence_routes_logging = not args.debug)

        # start server on its own thread, allowing something else to run on main thread
        # pass it self.app.server which is a Flask WSGI compliant app so could be hooked to any WSGI compliant server
        # make_server picks a free port because we passed 0 as port number
        self.server = werkzeug.serving.make_server("127.0.0.1", 0, self.app.server)
        threading.Thread(target = self.server.serve_forever).start()
        print("using port", self.server.server_port)


# read expressions from terminal, display results in a browser winddow
class ShellFrontEnd(DashFrontEnd):

    def __init__(self):

        # initialize app and start server
        super().__init__()

        # map from plot names to plot layouts, one per plot
        self.plots = {}

        # initial layout is empty save for a Location component
        # which causes the desired plot to be displayed as detailed below
        self.app.layout = dash.html.Div([dash.dcc.Location(id="url")], id="page-content", className="shell-front-end")

        # to display plot x browser is instructed to fetch url with path /plotx 
        # when browser fetches /plotx, it is served the initial (empty) layout defined above
        # then the dcc.Location component in that layout triggers this callback,
        # which receives the path /plotx of the loaded url
        # and updates the page-content div of the initial (empty) layout with the actual layout for /plotx
        @self.app.callback(
            dash.Output("page-content", "children"), # we update the page-content layout with the layout for plot x
            dash.Input("url", "pathname")            # we receive the url path /plotx
        )
        def layout_for_path(path):
            # returning this value updates page-content div with layout for plotx
            return self.plots[path[1:]]

        # this is a standin for the read-eval-print loop of the shell
        # here we just evaluate the "expressions" "a" and "b" and display the resulting layout
        # TODO: print s on stdout
        # TODO: then actual REPL loop
        # TODO: add s as title

        self.session = mathics.session.MathicsSession()

        for s in demos:
            plot_name = f"plot{len(self.plots)}"
            expr = self.session.parse(s)
            self.plots[plot_name] = layout_expr(self, expr)
            url = f"http://127.0.0.1:{self.server.server_port}/{plot_name}"
            browser.show(url)

# accept expressions from an input field, display expressions in an output box
class BrowserFrontEnd(DashFrontEnd):

    # creates a layout for an input field and an output div
    def pair(self, n=0):

        in_id = f"in-{n}"
        trigger_id = in_id + "-trigger"
        out_id = f"out-{n}"
        pair_id = f"pair-{n}"

        # create an input field, a div to hold output, and a hidden button
        # to signal that the user has pressed shift-enter
        instructions = "Type one of a, b, c, ... followed by shift-enter"
        layout = dash.html.Div([
            dash.dcc.Textarea(id=in_id, value="", placeholder=instructions, spellCheck=False, className="input"),
            dash.html.Button("trigger", trigger_id, hidden=True),
            dash.html.Div([], id=out_id, className="output")
        ], id=pair_id, className="pair")

        # TODO: this only works for the first one
        # TextArea triggers callbacks on every keystroke, but we only want to know
        # when user has pressed shift-enter, so we add a client-side event listener to the input field
        # that listens for shift-enter and triggers a click event on the hidden button
        # also autosize textarea to exactly contain text
        self.app.clientside_callback(
            """
            (id) => {
                ta = document.getElementById(id)
                ta.addEventListener("keydown", (event) => {
                    if (event.key === "Enter" && event.shiftKey) {
                        event.preventDefault()
                        document.getElementById(id+"-trigger").click();
                    }
                })
                ta.addEventListener("input", (event) => {
                    ta.style.height = "auto"
                    ta.style.height = (ta.scrollHeight + 5) + "px"
                })
                return window.dash_clientside.no_update;
            }
            """,
            dash.Output(in_id, "id"),
            dash.Input(in_id, 'id')
        )

        # callback is triggered by "click" on the hidden button signalling the user has pressed shift-enter
        # it receives the value of the in_id textarea, asks the interpreter to evaluate it and compute a layout,
        # then updates the out_id div with the layout
        # commented out code would add another input+output pair, but the callback for shift-enter
        # only works for the first one, so don't add additional ones for now
        @self.app.callback(
            #dash.Output(self.top_id, "children"),
            dash.Output(out_id, "children"),
            dash.Input(trigger_id, "n_clicks"),
            dash.State(in_id, "value"),
            prevent_initial_call = True
        )
        def update_output_div(_, input_value):
            print("evaluating", input_value)
            #patch = dash.Patch()
            #patch.append(self.pair(n+1))
            #return (patch, layout)
            layout = interpreter.compute(input_value)
            return layout

        # return input+output pair
        return layout

    def __init__(self):

        # initialize app and start server
        super().__init__()

        # initial layout is an input+output pair
        self.top_id = "browser-front-end"
        self.app.layout = dash.html.Div([self.pair()], id=self.top_id)

        # point a browser at our page
        url = f"http://127.0.0.1:{self.server.server_port}"
        browser.show(url)


browser = Browser()
front_end = ShellFrontEnd if args.fe=="shell" else BrowserFrontEnd
threading.Thread(target = front_end).start()
browser.start()

