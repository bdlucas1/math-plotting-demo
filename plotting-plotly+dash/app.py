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
            webview.create_window(url, url, x=100+offset, y=100+offset, width=600, height=600)
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
# provides functions that return Dash layouts corresponding to various Mathematica graphical functions
# like plot3d, manipulate, ...
#

# slider spec to be passed to manipulate
S = collections.namedtuple("S", ["name", "lo", "init", "hi", "step"])

# plotting axis spec to be passed to plot3d et al
A = collections.namedtuple("A", ["name", "lo", "hi", "count"])

class Layout:

    def __init__(self):
        self.n = 0

    # we need a pointer to the app in order to register callbacks for things like sliders
    def set_app(self, app):
        self.app = app

    def _layout(self, make_figure, sliders = []):

        # component ids have to be unique across the entire app,
        # so we make them unique by using this function to prepend a unique prefix
        self.n += 1
        id = lambda id_name: f"g{self.n}-{id_name}"

        # compute a slider from a slider spec (S namedtuple)
        def slider(s):
            # TODO: handling of tick marks and step needs work; this code is just for demo purposes
            marks = {value: f"{value:g}" for value in np.arange(s.lo, s.hi, s.step)}
            return [
                dash.html.Label(s.name),
                dash.dcc.Slider(
                    id=id(s.name), marks=marks, updatemode="drag",
                    min=s.lo, max=s.hi, step=s.step/10, value=s.init,
                )
            ]

        # TODO: do this via initial update? that doesn't work though if there are no sliders...
        init_values = {s.name: s.init for s in sliders}

        # compute the layout for the plot and store it in self.plots under plot_name
        layout = dash.html.Div([
            dash.dcc.Graph(id=id("figure"), figure=make_figure(init_values), className="graph"),
            dash.html.Div(list(itertools.chain(*[slider(s) for s in sliders])), className="sliders")
        ], className="plot")
        
        # define callbacks for the sliders
        # whenever any slider moves we call make_figure() passing it the slider values
        # to recompute the plot for the new slider values
        if sliders:
            @self.app.callback(
                dash.Output(id("figure"), "figure"),
                *(dash.Input(id(s.name), "value") for s in sliders),
                prevent_initial_call=True
            )
            def update(*args):
                return make_figure({s.name: value for s, value in zip(sliders,args)})

        return layout



    
    # implement something like Mathematica Plot3D
    # see examples below
    def plot3d(self, fun_expr, xlims, ylims, zlims = None, top_level = False, vals = {}):

        xs = np.linspace(xlims.lo, xlims.hi, xlims.count)
        ys = np.linspace(ylims.lo, ylims.hi, ylims.count)
        xs, ys = np.meshgrid(xs, ys)
        zs = interpreter.eval(fun_expr, vals | {xlims.name: xs, ylims.name: ys})

        # fake it
        #title = inspect.getsource(f)
        #title = title[title.index(":")+1 : title.rindex(",")]
        title = "xxx"

        def plot(_): # TODO: do we really want to ignore the arg?
            figure = go.Figure(
                data = [go.Surface(x=xs, y=ys, z=zs, colorscale="Viridis", colorbar=dict(thickness=10))],
                layout = go.Layout(
                    title = dict(
                        text = title,
                        y = 0.9
                    ),
                    margin = dict(l=0, r=0, t=60, b=0),
                    scene = dict(
                        xaxis_title="x",
                        yaxis_title="y",
                        zaxis_title="z",
                        aspectmode="cube"
                    ),
                )
            )
            if zlims:
                figure.update_layout(scene = dict(zaxis = dict(range=zlims)))
            return figure

        # TODO: this seems more convoluted than necessary?
        # is the whole thing with passing a function to self._layout the right way to do it,
        #     or is it just an artifact of the previous demo that used lambda
        if top_level:
            return self._layout(plot, [])
        else:
            return plot({}) # TODO: do we really need to pass an arg?


    def manipulate(self, plot_expr, *sliders):


        def make_figure(vals):
            return self.layout(plot_expr, top_level=False, vals=vals)
        # TODO: is plot callback the best way to do _layout?
        return self._layout(make_figure, sliders)

    # construct an A (axis spec Python object) from Mathics expr like {x,0,10,200}
    def to_python_axis_spec(self, expr):
        return A(str(expr.elements[0]).split("`")[1], *[e.to_python() for e in expr.elements[1:]])

    def layout(self, expr, top_level=True, vals={}):

        if str(expr.head) == "System`Plot3D":

            # TODO: embed self.plot3d here?
            return self.plot3d(
                expr.elements[0],
                self.to_python_axis_spec(expr.elements[1]),
                self.to_python_axis_spec(expr.elements[2]),
                top_level=top_level,
                vals=vals
            )

        elif str(expr.head) == "Global`Manipulate":

            # TODO: sliders from expr
            # TODO: add zlim
            # TODO: embed self.manipulate here?
            return self.manipulate(
                expr.elements[0],
                S("freq", 0.1, 1.0, 2.0, 0.2),
                S("amp", 0.0, 1.2, 2.0, 0.2)
            )



demos = [
    "Plot3D[Sin[x^2+y^2] / Sqrt[x^2+y^2+1], {x,-3,3,200}, {y,-3,3,200}]",
    """
        Manipulate[
            Plot3D[Sin[(x^2+y^2)*freq] / Sqrt[x^2+y^2+1] * amp, {x,-3,3,200}, {y,-3,3,200}],
            {freq, 0.1, 1.0, 2.0, 0.2}, (* freq slider spec *)
            {amp, 0.0, 1.2, 2.0, 0.2}  (* amp slider spec *)
        ]
    """
]



# TODO: move this up front
# TODO: add pp()

#
# standin for mathics interpreter
# takes string expressions, returns layouts
# called by front end to handle user input and get an output layout to display
# 
# to simplify the demo, instead of accepting actual math expressions,
# we just accept a fixed set of strings "a", "b", ... and call Layout
# to get a layout to return to the front end
#
class Interpreter:

    def __init__(self):
        self.session = mathics.session.MathicsSession()

    def parse(self, expr):
        return self.session.parse(expr)

    def to_python_expr(self, expr):

        funs = {
            "System`Sin": "np.sin",
            "System`Cos": "np.cos",
            "System`Sqrt": "np.sqrt"
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
                return str(expr).split("`")[1]
            else:
                return str(expr)
        elif str(expr.head) in funs:
            fun = funs[str(expr.head)]
            args = (self.to_python_expr(e) for e in expr.elements)
            return f"{fun}({",".join(args)})"
        elif str(expr.head) in listfuns:
            fun = listfuns[str(expr.head)]
            args = (self.to_python_expr(e) for e in expr.elements)
            return f"{fun}([{",".join(args)}])"
        elif str(expr.head) in binops:
            arg1 = self.to_python_expr(expr.elements[0])
            arg2 = self.to_python_expr(expr.elements[1])
            return f"({arg1}{binops[str(expr.head)]}{arg2})"
        else:
            raise Exception(f"Unknown head {expr.head}")

    def eval(self, expr, vals):
        python_expr = self.to_python_expr(expr)
        return eval(python_expr, globals(), vals)


# pretty print expr
def pp(expr, indent=1):
    if not hasattr(expr, "elements"):
        print("  " * indent + str(expr))
    else:
        print("  " * indent + str(expr.head))
        for elt in expr.elements:
            pp(elt, indent + 1)



# common to ShellFrontEnd and BrowserFrontEnd
class DashFrontEnd:

    def __init__(self):

        # create app, set options
        self.app = dash.Dash(__name__)
        self.app.enable_dev_tools(debug = args.debug, dev_tools_silence_routes_logging = not args.debug)

        # this allows layout to register callbacks for things like sliders
        layout.set_app(self.app)

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

        for s in demos:

            plot_name = f"plot{len(self.plots)}"
            expr = interpreter.parse(s)
            self.plots[plot_name] = layout.layout(expr)
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
layout = Layout()
interpreter = Interpreter()
front_end = ShellFrontEnd if args.fe=="shell" else BrowserFrontEnd
threading.Thread(target = front_end).start()
browser.start()

