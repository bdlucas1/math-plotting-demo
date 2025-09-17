import argparse
import re
import threading

from mathics.session import MathicsSession
import dash
import webbrowser
import webview
import werkzeug

import ev
import util

#
# 
#

dp3d   = "Plot3D[Sin[x^2+y^2], {x,-3,3}, {y,-3,3}, PlotPoints -> {50,50}]"
dp3dv2 = "My`Plot3Dv2[Sin[x^2+y^2] / Sqrt[x^2+y^2+1], {x,-3,3}, {y,-3,3}, PlotPoints -> {200,200}]"
dp3dv3 = "My`Plot3Dv3[Sin[x^2+y^2] / Sqrt[x^2+y^2+1], {x,-3,3}, {y,-3,3}, PlotPoints -> {200,200}]"
dp3dv4 = "My`Plot3Dv4[Sin[x^2+y^2] / Sqrt[x^2+y^2+1], {x,-3,3}, {y,-3,3}, PlotPoints -> {200,200}]"
dmp3ds = """
    Manipulate[
        My`Plot3D[Sin[(x^2+y^2)*freq] / Sqrt[x^2+y^2+1] * amp, {x,-3,3,200}, {y,-3,3,200}, {-1,1}],
        {freq, 0.1, 1.0, 2.0, 0.2}, (* freq slider spec *)
        {amp, 0.0, 1.2, 2.0, 0.2}  (* amp slider spec *)
     ]
"""
dmp3dv4s = """
    Manipulate[
        My`Plot3Dv4[Sin[(x^2+y^2)*freq] / Sqrt[x^2+y^2+1] * amp, {x,-3,3}, {y,-3,3}, PlotPoints -> {200,200}],
        {freq, 0.1, 1.0, 2.0, 0.2}, (* freq slider spec *)
        {amp, 0.0, 1.0, 2.0, 0.2}  (* amp slider spec *)
     ]
"""
dmp3dv4h = """
    Manipulate[
        My`Plot3Dv4[Abs[My`Hypergeometric1F1[a, b, (x + I y)^2]], {x, -2, 2}, {y, -2, 2}, {1, 14, PlotPoints -> {200,200}}}],
        {a, 0.5, 1, 1.5, 0.1}, (* a slider spec *)
        {b, 1.5, 2, 2.5, 0.1}  (* b slider spec *)
    ]
"""
testgc1 = """
    Graphics3D[GraphicsComplex[
        {{0, 0, 0}, {2, 0, 0}, {2, 2, 0}, {0, 2, 0}, {1, 1, 2}},
        Polygon[{{1, 2, 5}, {2, 3, 5}, {3, 4, 5}, {4, 1, 5}}]
    ]]
"""
# TODO: display has a triangle and a quad - why?
testgc2 = """
    Graphics3D[GraphicsComplex[
        {{0, 0, 0}, {2, 0, 0}, {2, 2, 0}, {0, 2, 0}, {1, 1, 2}},
        Polygon[{{1, 2, 3, 4}, {1, 2, 4, 5}}]
    ]]
"""

demos = [
    #                                                                                  eval  layout   total (ms)
    #dp3d,   # Plot3D Sin 50x50           current, generates G3D slowly                10026     181   10207
    #dp3dv1, # Plot3Dv1 Sin/Sqrt 200x200  send Plot3D unmodified to layout                 0      26      26
    dp3dv2, # Plot3Dv2 Sin/Sqrt 200x200  G3D, individual polys, no GraphicsComplex      439      71     510
    dp3dv3, # Plot3Dv2 Sin/Sqrt 200x200  G3D, GraphicsComplex, numpy_array_list_expr    303     104     407
    dp3dv4, # Plot3Dv2 Sin/Sqrt 200x200  G3D, GraphicsComplex, NumpyArrayListExpr         1      15      16
    #testgc1,
    #testgc2,
    dmp3dv4s, # Man Plot3Dv4 Sin/Sqrt 200x200
    #dmp3dv4h, # Man Plot3Dv4 HypGeo 200x200
]

#
#
#

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
        #print("showing", url)
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

        # everybody needs a Mathics session
        self.session = MathicsSession()



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

            p = re.sub("[ \n]+", " ", s)
            if len(p) > 80:
                p = p[0:80] + "..."
            print("===", p)

            expr = self.session.parse(s)

            util.start_timer(f"total {expr.head}")
            expr = ev.eval_expr(self, expr)
            layout = ev.layout_expr(self, expr)
            util.stop_timer()

            plot_name = f"plot{len(self.plots)}"
            self.plots[plot_name] = layout
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
            # TODO: this is funky
            input_value = input_value.strip()
            if input_value in "abc":
                input_value = demos["abc".index(input_value)]
            expr = self.session.parse(input_value)
            layout = layout_expr(self, expr)
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
