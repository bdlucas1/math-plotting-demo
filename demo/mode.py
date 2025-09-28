use_dash = True

if use_dash:

    import dash

    def graph(figure, size):
        layout = dash.html.Div ([
            #dash.dcc.Markdown(f"${title}$", mathjax=True) if fancy else dash.html.Div(title, className="m-title"),
            dash.dcc.Graph(figure=figure, className="m-graph")
        ], className="m-plot")
        if size:
            layout.style = dict(width=f"{size}pt", height=f"{size}pt")
        return layout

    def wrap(s):
        layout = dash.html.Div(s)
        return layout

    # TODO: is this different from wrap(s)?
    def label(s):
        layout = dash.html.Label(s)
        return layout

    def latex(s):
        layout = dash.dcc.Markdown("$"+s+"$", mathjax=True)        
        return layout

    # TODO: just a one-row grid?
    def row(ls):
        layout = dash.html.Div(ls, className="m-row")
        return layout

    """
    def vbox(ls):
        layout = dash.html.Div(ls)
        return layout
    """

    def grid(grid_content):
        layout = dash.html.Div(grid_content, className="m-grid")
        return layout

    def manipulate_box(ls):
        layout = dash.html.Div(ls, className="m-manipulate")
        return layout

    # TODO: abstract away ids - pass in ref_num and an S, construct from that
    #   then pass same ref_num to id_box
    #   or maybe just have a slider_box that takes init_target_layout and a list of sliders and does the whole thing
    # TODO: combine sliders and id_box into a panel abstraction
    def slider(id, marks, lo, hi, step, init):
        layout = dash.dcc.Slider(id=id, marks=marks, min=lo, max=hi, step=step, value=init, updatemode="drag")
        return layout

    def id_box(l, id):
        layout = dash.html.Div(l, id=id)
        return layout

    def slider_box(ls):
        layout = dash.html.Div(ls, className="m-sliders")        
        return layout

