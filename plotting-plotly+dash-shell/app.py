import time
import threading
import collections 
import itertools
import webbrowser
import inspect

# pip install numpy dash plotly pywebview
import webview
import numpy as np
import dash
import werkzeug
import plotly.graph_objects as go

# pick one
debug = False
#debug = True

# pick a method for displaying plots
browser = "webview" # pop up a new window with an embedded webview (essentially a standalone browser)
#browser = "webbrowser" # ask the default system browser to display plot

# slider spec to be passed to manipulate
S = collections.namedtuple("S", ["name", "lo", "init", "hi", "step"])

# plotting axis spec to be passed to plot3d et al
A = collections.namedtuple("A", ["name", "lo", "hi", "count"])

class Plotting:

    def __init__(self, shell_loop):

        # map from plot names to plot layouts, one per plot
        self.plots = {}

        # create dash app and specify initial layout, which is empty
        # save for a Location component which causes the desired plot to be displayed
        # as detailed below
        self.app = dash.Dash(__name__)
        self.app.layout = dash.html.Div([dash.dcc.Location(id="url")], id="page-content")
        self.app.enable_dev_tools(debug = debug, dev_tools_silence_routes_logging = not debug)

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

        # start server on its own thread, allowing something else to run on main thread
        # make_server picks a free port because we passed 0 as port number
        self.server = werkzeug.serving.make_server("127.0.0.1", 0, self.app.server)
        server_thread = threading.Thread(target = self.server.serve_forever)
        server_thread.start()
        print("using port", self.server.server_port)

        # start our "shell loop" on its own thread, allowing something else to run on main thread
        threading.Thread(target = lambda: shell_loop(self)).start()

        if browser == "webview":
            # webview needs to run on main thread :( and blocks, so we start other things on their own thread above
            # webview needs a window before we can call start() :(, so we make a hidden one
            # real windows will be provided later
            webview.create_window("hidden", hidden=True)
            webview.start()

        # keep serving
        server_thread.join()


    # show() calls the supplied plot() function to get a plotly figure,
    # then computes the layout for the plot,
    # including sliders as specified to re-compute the plot by calling plot() as the sliders change
    # stores the computed layout in self.plots under the name plot0, plot1, ...,
    # then opens a browser window to fetch and display the layout using the url /plotx
    def show(self, plot, sliders = []):
        
        # plot0, plot1, ...
        plot_name = f"plot{len(self.plots)}"

        # component ids have to be unique across the entire app,
        # so we make them unique by using this function to prepend the plot name
        id = lambda id_name: f"{plot_name}-{id_name}"

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
        self.plots[plot_name] = dash.html.Div([
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

        # display a browser window that fetches the current plot
        url = f"http://127.0.0.1:{self.server.server_port}/{plot_name}"
        print("showing", url)
        if browser == "webview":
            offset = 50 * len(self.plots)
            webview.create_window(plot_name, url, x=100+offset, y=100+offset, width=600, height=600)
        elif browser == "webbrowser":
            webbrowser.open_new(url)


    # implement something like Mathematica Plot3D
    # see examples below
    def plot3d(self, f, xlims, ylims, zlims = None, show = False):

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

        if show:
            self.show(plot)
        else:
            return plot()
    
    # implement something like Mathematica Manipulate
    # see examples below
    def manipulate(self, plot, *sliders):
        self.show(plot, sliders)


# this is a standin for the read-eval-print loop of the shell
# except here we just call some plotting functions
# if you squint you'll see that these look like the corresponding Mathematica functions,
# the main difference being instead of passing in code we pass in a callback that executes the code
def shell_loop(plotting):

    # function to be plotted
    def ripples(x, y, amp, freq):
        r = x**2 + y**2
        return np.sin(r * freq) / (np.sqrt(r) + 1) * amp
    
    # plot the function at fixed values of freq and amp
    plotting.plot3d(
        lambda x, y: ripples(x, y, amp=1, freq=1),
        A("x", -3, 3, 200), # x axis spec
        A("y", -3, 3, 200), # y axis spec
        show=True
    )

    # plot the function with sliders to adjust freq and amp
    plotting.manipulate(
        lambda amp, freq: plotting.plot3d(
            lambda x, y: ripples(x, y, amp, freq),
            A("x", -3, 3, 200), # x axis spec
            A("y", -3, 3, 200), # y axis spec
            zlims=[-1, 1],      # z axis limits
        ),
        S("freq", 0.1, 1.0, 2.0, 0.2), # freq slider spec
        S("amp", 0.0, 1.2, 2.0, 0.2),  # amp slider spec
    )


# set up plotting, then call shell_loop
Plotting(shell_loop)
