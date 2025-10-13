from dataclasses import dataclass

import plotly.graph_objects as go

import util

# TODO: x and y range
# TODO: merge these!


@dataclass
class Options:
    axes: tuple
    width: int
    height: int
    x_range: tuple | None = None
    y_range: tuple | None = None
    z_range: tuple | None = None
    showscale: bool = False
    colorscale: str = "viridis"


def plot2d(lines, points, options: Options):

    def axis(show, range):
        if show:
            axis = dict(ticks="outside", showgrid=False, linecolor="black")
        else:
            axis = dict(showline=False, showgrid=False, ticks=None, showticklabels=False, showspikes=False)
        if range:
            axis["range"] = range
        print("xxx axis", axis)
        return axis

    figure = go.FigureWidget(
        layout = go.Layout(
            margin = dict(l=0, r=0, t=0, b=0),
            plot_bgcolor='rgba(0,0,0,0)',
            #xaxis = dict(ticks="inside", showgrid=False, linecolor="black", range=(0,30)),
            #yaxis = dict(showline=False, ticks=None, showticklabels=False),
            xaxis = axis(options.axes[0], options.x_range),
            yaxis = axis(options.axes[1], options.y_range),
            width=options.width,
            height=options.height,
        )
    )

    figure.add_trace(go.Scatter(
        x = points[:,0], y = points[:,1],
        mode='markers', marker=dict(color='black', size=8)
    ))

    return figure


def plot3d(xyzs, ijks, showscale, colorscale, axes, width, height, z_range):

    with util.Timer("mesh"):
        mesh = go.Mesh3d(
            x=xyzs[:,0], y=xyzs[:,1], z=xyzs[:,2],
            i=ijks[:,0], j=ijks[:,1], k=ijks[:,2],
            showscale=showscale, colorscale=colorscale, colorbar=dict(thickness=10), intensity=xyzs[:,2],
            #hoverinfo="skip"
            hoverinfo="none"
        )
    
    with util.Timer("figure"):
        showspikes = True # the projected lines on the axes box
        figure = go.FigureWidget(
            #data = [mesh],
            layout = go.Layout(
                margin = dict(l=0, r=0, t=0, b=0),
                scene = dict(
                    xaxis = dict(title="x", visible=axes, showspikes=showspikes), # TODO: name
                    yaxis = dict(title="y", visible=axes, showspikes=showspikes), # TODO: name
                    zaxis = dict(title="z", visible=axes, showspikes=showspikes), # TODO: name
                ),
                width=width,
                height=height
            )
        )
        figure.add_trace(mesh)

        # TODO: x_range and y_range
        if z_range:
            figure.update_layout(scene = dict(zaxis = dict(range=z_range)))
        """
        opts = dict(
            showbackground=False,
            showgrid=False,  # Hide grid lines
            zeroline=True,  # Hide the zero line
            showline=True,   # Show the axis line (edge)
            mirror="all",      # Mirror the axis line on the opposite side
            color="red",
            linecolor="red",
            zerolinecolor="red"

        )
        figure.update_layout(scene=dict(xaxis=opts, yaxis=opts, zaxis=opts))
        """


    return figure
