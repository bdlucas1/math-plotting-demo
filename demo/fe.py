import argparse
import re
import threading
import traceback

import dash
import webbrowser
import webview
import werkzeug

import ev
import lay
import mat
import util

#
# 
#

plot_sin_old_200   = "Plot3D[Sin[x^2+y^2] / Sqrt[x^2+y^2+1], {x,-3,3}, {y,-3,3}, PlotPoints -> {200,200}, MaxRecursion -> -1]"
plot_sin_old_20   = "Plot3D[Sin[x^2+y^2] / Sqrt[x^2+y^2+1], {x,-3,3}, {y,-3,3}, PlotPoints -> {20,20}, MaxRecursion -> -1]"

plot_sin = """
Demo`Plot3D[
   Sin[x^2+y^2] / Sqrt[x^2+y^2+1], {x,-3,3}, {y,-3,3},
   PlotPoints -> {200,200}
]
"""

plot_manipulate_sin = """
Manipulate[
    Demo`Plot3D[
        Sin[(x^2+y^2)*freq] / Sqrt[x^2+y^2+1] * amp, {x,-3,3}, {y,-3,3},
        PlotPoints -> {200,200}, PlotRange -> {Automatic, Automatic, {-0.25,0.5}}
    ],
    {{freq,1.0}, 0.1, 2.0, 0.2}, (* freq slider spec *)
    {{amp,1.0}, 0.0, 2.0, 0.2}  (* amp slider spec *)
]
"""

# TODO: System`Hypergeometric1F1 gets rewritten to varous functions involving gamma, bessel, etc.
# need to build those out in compile.py to handle
# for now just use Demo`Hypergeomtric which compile knows about but mathics evaluate doesn't
plot_manipulate_hypergeometric = """
Manipulate[
    Demo`Plot3D[
        Demo`Hypergeometric1F1[a, b, (x + I y)^2], {x, -2, 2}, {y, -2, 2},
        PlotPoints -> {200,200}, PlotRange -> {Automatic, Automatic, {-5,14}},
    ],
    {{a,1}, 0.5, 1.5, 0.1}, (* a slider spec *)
    {{b,2}, 1.5, 2.5, 0.1}  (* b slider spec *)
]
"""

test_gc1 = """
    Graphics3D[GraphicsComplex[
        {{0, 0, 0}, {2, 0, 0}, {2, 2, 0}, {0, 2, 0}, {1, 1, 2}},
        Polygon[{{1, 2, 5}, {2, 3, 5}, {3, 4, 5}, {4, 1, 5}}]
    ]]
"""

# TODO: display has a triangle and a quad - why?
test_gc2 = """
    Graphics3D[GraphicsComplex[
        {{0, 0, 0}, {2, 0, 0}, {2, 2, 0}, {0, 2, 0}, {1, 1, 2}},
        Polygon[{{1, 2, 3, 4}, {1, 2, 4, 5}}]
    ]]
"""

run = dict(

    demos = [
        plot_sin,
        plot_manipulate_sin,
        plot_manipulate_hypergeometric
    ],

    tests = [
        plot_sin_old_20,
        plot_sin,
        plot_manipulate_sin,
        plot_manipulate_hypergeometric,
        test_gc1,
        test_gc2
    ],

    # run multiple times, take fastest
    timing = [
        #plot_sin_old_200, plot_sin_old_200,
        plot_sin, plot_sin, plot_sin, 
        #plot_manipulate_sin, plot_manipulate_sin, plot_manipulate_sin,
        #plot_manipulate_hypergeometric, plot_manipulate_hypergeometric, plot_manipulate_hypergeometric,
    ],

    dev = [
        #"Demo`Plot3D[Sin[x], {x,0,10}, {y,0,10}, PlotPoints->{200,200}]",
        "Plot3D[Sin[x], {x,0,10}, {y,0,10}, PlotPoints->{20,20}]",
    ]
)


#
#
#

parser = argparse.ArgumentParser(description="Graphics demo")
parser.add_argument("--debug", action="store_true")
parser.add_argument("--fe", choices=["shell", "browser"], default="shell")
parser.add_argument("--browser", choices=["webview", "webbrowser"], default="webview")
parser.add_argument("--run", choices=["demos","tests","timing","dev"], default=None)
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
        self.session = mat.MathicsSession()



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


        def handle_input(s):

            util.Timer.level = -1 # print all timings until told otherwise (e.g. by Manipulate)
            layout = None

            with util.Timer(f"total parse+eval+layout"):
                try:
                    expr = self.session.parse(s)
                    if expr:
                        expr = ev.eval_expr(self, expr)
                        layout = lay.layout_expr(self, expr)
                except Exception as e:
                    if args.run == "dev":
                        traceback.print_exc()
                    else:
                        print(e)

            # graphicical output, if any
            if layout:
                plot_name = f"plot{len(self.plots)}"
                self.plots[plot_name] = layout
                url = f"http://127.0.0.1:{self.server.server_port}/{plot_name}"
                browser.show(url)

            # text output
            if getattr(expr, "head") in set([mat.SymbolGraphics, mat.SymbolGraphics3D]):
                text_output = str(expr.head)
            else:
                # TODO: how to get this to output Sin instead of System`Sin etc.
                text_output = str(expr)
            print(f"\noutput> {text_output}")

        # demos, tests, etc.
        if args.run:
            for s in run[args.run]:
                print("input> ", s)
                handle_input(s)
                print("")

        # REPL loop
        while True:
            print("input> ", end="")
            s = input()
            handle_input(s)
            print("")


# accept expressions from an input field, display expressions in an output box
class BrowserFrontEnd(DashFrontEnd):

    def process_input(self, s):

        util.Timer.level = -1 # print all timings until told otherwise (e.g. by Manipulate)
        result = None

        with util.Timer(f"total parse+eval+layout"):
            try:
                expr = self.session.parse(s)
                if expr:
                    expr = ev.eval_expr(self, expr)
                    result = lay.layout_expr(self, expr)
            except Exception as e:
                if args.run == "dev":
                    traceback.print_exc()
                else:
                    print(e)

        # text output
        if not result:
            if getattr(expr, "head", None) in set([mat.SymbolGraphics, mat.SymbolGraphics3D]):
                result = str(expr.head)
            else:
                # TODO: how to get this to output Sin instead of System`Sin etc.
                result = str(expr)

        return result

    # creates a layout for an input field and an output div
    # optionally pre-populates the output div
    def pair(self, input="", output=None):

        self.pair_number += 1
        in_id = f"in-{self.pair_number}"
        trigger_id = in_id + "-trigger"
        out_id = f"out-{self.pair_number}"
        pair_id = f"pair-{self.pair_number}"

        # create an input field, a div to hold output, and a hidden button
        # to signal that the user has pressed shift-enter
        instructions = "Type expression followed by shift-enter"
        layout = dash.html.Div([
            dash.dcc.Textarea(id=in_id, value=input.strip(), placeholder=instructions, spellCheck=False, className="input"),
            dash.html.Button("trigger", trigger_id, hidden=True),
            dash.html.Div(output, id=out_id, className="output")
        ], id=pair_id, className="pair")

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
                function setHeight() {
                    ta.style.height = "auto"
                    ta.style.height = (ta.scrollHeight + 5) + "px"
                }
                ta.addEventListener("input", setHeight)
                setHeight()
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
            return self.process_input(input_value)

        return layout

    def __init__(self):

        # initialize app and start server
        super().__init__()

        # initial layout is --run input plus a blank pair
        self.pair_number = 0
        self.top_id = "browser-front-end"
        init_pairs = [self.pair(input, self.process_input(input)) for input in run[args.run]] if args.run else []
        self.app.layout = dash.html.Div([*init_pairs, self.pair()], id=self.top_id)

        # point a browser at our page
        url = f"http://127.0.0.1:{self.server.server_port}"
        browser.show(url)


browser = Browser()
front_end = ShellFrontEnd if args.fe=="shell" else BrowserFrontEnd
threading.Thread(target = front_end).start()
browser.start()
