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

    #atexit.register(start)


#
# provides functions that return Dash layouts for corresponding to various Mathematica graphical functions
# like plot3d, manipulate, ...
#

# slider spec to be passed to manipulate
S = collections.namedtuple("S", ["name", "lo", "init", "hi", "step"])

# plotting axis spec to be passed to plot3d et al
A = collections.namedtuple("A", ["name", "lo", "hi", "count"])

class Graphics:

    def __init__(self):
        self.n = 0

    # we need a pointer to the app in order to register callbacks for things like sliders
    def set_app(self, app):
        self.app = app

    def layout(self, plot, sliders = []):

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
        init_values = [s.init for s in sliders]

        # compute the layout for the plot and store it in self.plots under plot_name
        layout = dash.html.Div([
            dash.dcc.Graph(id=id("figure"), figure=plot(*init_values), className="graph"),
            dash.html.Div(list(itertools.chain(*[slider(s) for s in sliders])), className="sliders")
        ], className="plot")
        
        # define callbacks for the sliders
        # whenever any slider moves we call plot() passing it the slider values
        # to recompute the plot for the new slider values
        if sliders:
            @self.app.callback(
                dash.Output(id("figure"), "figure"),
                *(dash.Input(id(s.name), "value") for s in sliders),
                prevent_initial_call=True
            )
            def update(*args):
                return plot(**{s.name: value for s, value in zip(sliders,args)})

        return layout


    # implement something like Mathematica Plot3D
    # see examples below
    def plot3d(self, f, xlims, ylims, zlims = None, top_level = False):

        xs = np.linspace(xlims.lo, xlims.hi, xlims.count)
        ys = np.linspace(ylims.lo, ylims.hi, ylims.count)
        xs, ys = np.meshgrid(xs, ys)
        zs = f(**{xlims.name: xs, ylims.name: ys})

        # fake it
        title = inspect.getsource(f)
        title = title[title.index(":")+1 : title.rindex(",")]

        def plot():
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

        if top_level:
            return self.layout(plot, [])
        else:
            return plot()

    
    # implement something like Mathematica Manipulate
    # see examples below
    def manipulate(self, plot, *sliders):
        return self.layout(plot, sliders)
        

#
# standin for mathics interpreter
# takes string expressions, returns layouts
# called by front end to handle user input and get an output layout to display
# 
# to simplify the demo, instead of accepting actual math expressions,
# we just accept a fixed set of strings "a", "b", ... and call Graphics
# to get a layout to return to the front end
#
class Interpreter:

    def compute(self, input):
        
        # function to be plotted
        def ripples(x, y, amp, freq):
            r = x**2 + y**2
            return np.sin(r * freq) / (np.sqrt(r) + 1) * amp

        if input == "a":

            # plot the function at fixed values of freq and amp
            return graphics.plot3d(
                lambda x, y: ripples(x, y, amp=1, freq=1),
                A("x", -3, 3, 200), # x axis spec
                A("y", -3, 3, 200), # y axis spec
                top_level=True
            )

        elif input == "b":
            
            # plot the function with sliders to adjust freq and amp
            return graphics.manipulate(
                lambda amp, freq: graphics.plot3d(
                    lambda x, y: ripples(x, y, amp, freq),
                    A("x", -3, 3, 200), # x axis spec
                    A("y", -3, 3, 200), # y axis spec
                    zlims=[-1, 1],      # z axis limits
                ),
                S("freq", 0.1, 1.0, 2.0, 0.2), # freq slider spec
                S("amp", 0.0, 1.2, 2.0, 0.2),  # amp slider spec
            )


# common to ShellFrontEnd and BrowserFrontEnd
class DashFrontEnd:

    def __init__(self):

        # create app, set options
        self.app = dash.Dash(__name__)
        self.app.enable_dev_tools(debug = args.debug, dev_tools_silence_routes_logging = not args.debug)

        # this allows graphics to register callbacks for things like sliders
        graphics.set_app(self.app)

        # start server on its own thread, allowing something else to run on main thread
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
        self.app.layout =  dash.html.Div([dash.dcc.Location(id="url")], id="page-content")

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

        # TODO: actual REPL loop
        # this is a standin for the read-eval-print loop of the shell
        # except here we just call some plotting functions to automate things
        for s in ["a", "b"]:
            layout = interpreter.compute(s)
            plot_name = f"plot{len(self.plots)}"
            self.plots[plot_name] = layout
            url = f"http://127.0.0.1:{self.server.server_port}/{plot_name}"
            browser.show(url)

# accept expressions from an input field, display expressions in an output box
class BrowserFrontEnd(DashFrontEnd):

    def pair(self, n=0):

        in_id = f"in-{n}"
        out_id = f"out-{n}"

        layout = dash.html.Div([
            dash.html.Label(f"in {n}"),
            dash.dcc.Input(id=in_id, type="text", value="", debounce=True, spellCheck=False),
            dash.html.Label(f"out {n}"),
            dash.html.Div(id=out_id)
        ])

        @self.app.callback(
            dash.Output(out_id, "children"),
            dash.Input(in_id, "value")
        )
        def update_output_div(input_value):
            graphics_layout = interpreter.compute(input_value)
            return graphics_layout

        return layout

    def __init__(self):

        # initialize app and start server
        super().__init__()

        # initial layout is input f
        self.app.layout = self.pair()

        # point a browser at our page
        url = f"http://127.0.0.1:{self.server.server_port}"
        browser.show(url)


browser = Browser()
graphics = Graphics()
interpreter = Interpreter()
front_end = ShellFrontEnd if args.fe=="shell" else BrowserFrontEnd
threading.Thread(target = front_end).start()
browser.start()

