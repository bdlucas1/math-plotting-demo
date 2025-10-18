import ipywidgets as ipw
import ipywidgets.embed
import threading
import traceback
import util
import werkzeug

import mcs

def to_html(layout):

    import json
    from ipywidgets import IntSlider
    from ipywidgets.embed import embed_data

    data = embed_data(views=[layout])

    html_template = """
    <html>
      <head>

        <title>Widget export</title>

        <!-- Load RequireJS, used by the IPywidgets for dependency management -->
        <script 
          src="https://cdnjs.cloudflare.com/ajax/libs/require.js/2.3.4/require.min.js" 
          integrity="sha256-Ae2Vz/4ePdIu6ZyI/5ZGsYnb+m0JlOmKPjt6XZ9JJkA=" 
          crossorigin="anonymous">
        </script>

        <!-- Load IPywidgets bundle for embedding. -->
        <script
          data-jupyter-widgets-cdn="https://cdn.jsdelivr.net/npm/"
          src="https://unpkg.com/@jupyter-widgets/html-manager@*/dist/embed-amd.js" 
          crossorigin="anonymous">
        </script>

        <!-- The state of all the widget models on the page -->
        <script type="application/vnd.jupyter.widget-state+json">
          {manager_state}
        </script>
      </head>

      <body>

        <h1>Widget export</h1>

        <div id="first-slider-widget">
          <!-- This script tag will be replaced by the view's DOM tree -->
          <script type="application/vnd.jupyter.widget-view+json">
            {widget_views[0]}
          </script>
        </div>


      </body>
    </html>
    """

    manager_state = json.dumps(data['manager_state'])
    widget_views = [json.dumps(view) for view in data['view_specs']]
    rendered_template = html_template.format(manager_state=manager_state, widget_views=widget_views)
    with open('export.html', 'w') as fp:
        fp.write(rendered_template)    


# common to ShellFrontEnd and BrowserFrontEnd
class IpyFrontEnd:

    def __init__(self):

        """
        # start server on its own thread, allowing something else to run on main thread
        # pass it self.app.server which is a Flask WSGI compliant app so could be hooked to any WSGI compliant server
        # make_server picks a free port because we passed 0 as port number
        self.server = werkzeug.serving.make_server("127.0.0.1", 0, self.app.server)
        threading.Thread(target = self.server.serve_forever).start()
        print("using port", self.server.server_port)
        """

        # everybody needs a Mathics session
        self.session = mcs.MathicsSession()


# read expressions from terminal, display results in a browser winddow
# not ready - may never be ...
class XXXShellFrontEnd(IpyFrontEnd):

    def __init__(self):

        # initialize app and start server
        super().__init__()

        # map from plot names to plot layouts, one per plot
        self.plots = {}

        """
        # initial layout is empty save for a Location component
        # which causes the desired plot to be displayed as detailed below
        self.app.layout = dash.html.Div([dash.dcc.Location(id="url")], id="shell-front-end")

        # to display plot x browser is instructed to fetch url with path /plotx 
        # when browser fetches /plotx, it is served the initial (empty) layout defined above
        # then the dcc.Location component in that layout triggers this callback,
        # which receives the path /plotx of the loaded url
        # and updates the shell-front-end div of the initial (empty) layout with the actual layout for /plotx
        @self.app.callback(
            dash.Output("shell-front-end", "children"), # we update the shell-front-end layout with the layout for plot x
            dash.Input("url", "pathname")            # we receive the url path /plotx
        )
        def layout_for_path(path):
            # returning this value updates shell-front-end div with layout for plotx
            return self.plots[path[1:]]
        """

        def handle_input(s):

            layout = None

            with util.Timer(f"total parse+eval+layout"):
                try:
                    expr = self.session.parse(s)
                    if expr:
                        expr = expr.evaluate(self.session.evaluation)
                        layout = lt.expression_to_layout(self, expr)
                except Exception as e:
                    if args.run == "dev" or mode.debug:
                        traceback.print_exc()
                    else:
                        print("ERROR:", e)

            # graphicical output, if any
            if layout:
                plot_name = f"plot{len(self.plots)}"
                self.plots[plot_name] = layout
                to_html(layout); exit()
                #print(open("/tmp/ipy.html").read())
                exit()

                #url = f"http://127.0.0.1:{self.server.server_port}/{plot_name}"
                #browser.show(url)

            # text output
            if getattr(expr, "head", None) in set([mcs.SymbolGraphics, mcs.SymbolGraphics3D]):
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
class BrowserFrontEnd(IpyFrontEnd):

    def __init__(self):

        # initialize app and start server
        super().__init__()

        # initial layout is --run input plus a blank pair
        self.pair_number = 0
        self.top_id ="browser-front-end"
        init_pairs = [self.pair(input, self.process_input(input)) for input in run[args.run]] if args.run else []
        self.app.layout = dash.html.Div([*init_pairs, self.pair()], id=self.top_id)

        # when the hidden pair-button is "clicked", process the pair-in input and update the pair-out div
        @self.app.callback(
            dash.Output(dict(type="pair-out", pair_number=dash.MATCH), "children"),
            dash.Input(dict(type="pair-button", pair_number=dash.MATCH), "n_clicks"),
            dash.State(dict(type="pair-in", pair_number=dash.MATCH), "value"),
            prevent_initial_call = True
        )
        def update_pair_output(_, input_value):
            return self.process_input(input_value)

        # when any pair-out changes, if it's the last pair, append a new fresh pair to self.top_id
        @self.app.callback(
            dash.Output(self.top_id, "children"),
            dash.Input(dict(type="pair-out", pair_number=dash.ALL), "children"),
            prevent_initial_call = True
        )
        def append_new_pair(_):
            if dash.ctx.triggered_id and dash.ctx.triggered_id["pair_number"] == self.pair_number:
                patch = dash.Patch()
                patch.append(self.pair())
                return patch
            raise dash.exceptions.PreventUpdate
            
        # point a browser at our page
        if args.fe == "jupyter":
            self.app.run(jupyter_mode="inline")
        else:
            url = f"http://127.0.0.1:{self.server.server_port}"
            browser.show(url)
            

    def process_input(self, s):

        result = None

        with util.Timer(f"total parse+eval+layout"):
            try:
                expr = self.session.parse(s)
                if expr:
                    expr = expr.evaluate(self.session.evaluation)
                    result = lt.expression_to_layout(self, expr)
            except Exception as e:
                if args.run == "dev" or mode.debug:
                    traceback.print_exc()
                else:
                    print(e)

        # text output
        if not result:
            if getattr(expr, "head", None) in set([mcs.SymbolGraphics, mcs.SymbolGraphics3D]):
                result = str(expr.head)
            else:
                # TODO: how to get this to output Sin instead of System`Sin etc.
                result = str(expr)

        return result

    # creates a layout for an input field and an output div
    # optionally pre-populates the output div (used for the demos - otherwise output starts out empty)
    def pair(self, input="", output=None):

        self.pair_number += 1
        pair_id = f"pair-{self.pair_number}"
        in_id =     dict(type="pair-in",     pair_number=self.pair_number)
        button_id = dict(type="pair-button", pair_number=self.pair_number)
        out_id =    dict(type="pair-out",    pair_number=self.pair_number)

        # create an input field, a div to hold output, a hidden button, and a number label
        # that is used to signal that the user has pressed shift-enter
        # TODO: can we get rid of hidden button by making tweak_pair more sophisticated?
        instructions = "Type expression followed by shift-enter"
        layout = dash.html.Div([
            dash.dcc.Textarea(id=in_id, value=input.strip(), placeholder=instructions, spellCheck=False, className="m-input"),
            dash.html.Button(id=button_id, hidden=True),
            dash.html.Div(output, id=out_id, className="m-output"),
            dash.html.Div(str(self.pair_number), className="m-number"),
            # run tweak_pair (from assets/tweaks.js) to tweak the behavior of the pair:
            #    shift-enter in textarea clicks the button
            #    resize textarea height on every input
            mode.exec_js(f"tweak_pair('{pair_id}')"),

        ], id=pair_id, className="m-pair")

        return layout

"""    
