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


def axis(show, range, title):
    axis = dict(showspikes=False, ticks="outside", range=range, title=title, linecolor="black")
    if not show:
        axis |= dict(visible=False, showline=False, ticks=None, showticklabels=False)
    return axis

def plot2d(lines, points, options: Options):


    figure = go.FigureWidget(
        layout = go.Layout(
            margin = dict(l=0, r=0, t=0, b=0),
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis = axis(options.axes[0], options.x_range, None),
            yaxis = axis(options.axes[1], options.y_range, None),
            width=options.width,
            height=options.height,
        )
    )

    figure.add_trace(go.Scatter(
        x = points[:,0], y = points[:,1],
        mode='markers', marker=dict(color='black', size=8)
    ))

    return figure


def plot3d(xyzs, ijks, options):

    with util.Timer("figure"):
        figure = go.FigureWidget(
            layout = go.Layout(
                margin = dict(l=0, r=0, t=0, b=0),
                scene = dict(
                    xaxis = axis(options.axes[0], range=options.x_range, title="x"),
                    yaxis = axis(options.axes[1], range=options.y_range, title="y"),
                    zaxis = axis(options.axes[2], range=options.z_range, title="z"),
                ),
                width=options.width,
                height=options.height
            )
        )

    with util.Timer("mesh"):
        mesh = go.Mesh3d(
            x=xyzs[:,0], y=xyzs[:,1], z=xyzs[:,2],
            i=ijks[:,0], j=ijks[:,1], k=ijks[:,2],
            showscale=options.showscale, colorscale=options.colorscale, colorbar=dict(thickness=10), intensity=xyzs[:,2],
            #hoverinfo="skip"
            hoverinfo="none"
        )
        figure.add_trace(mesh)



    return figure
