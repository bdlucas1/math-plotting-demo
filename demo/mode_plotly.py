from dataclasses import dataclass

import plotly.graph_objects as go

import util

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

# compute axis options
def axis(show, range, title):
    axis = dict(showspikes=False, ticks="outside", range=range, title=title, linecolor="black")
    if not show:
        axis |= dict(visible=False, showline=False, ticks=None, showticklabels=False)
    return axis

def plot2d(lines, points, options: Options):

    # plot layout
    layout = go.Layout(
        margin = dict(l=0, r=0, t=0, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        width=options.width,
        height=options.height,
        xaxis = axis(options.axes[0], options.x_range, None),
        yaxis = axis(options.axes[1], options.y_range, None),
    )
    figure = go.FigureWidget(layout = layout)

    # add points
    if points is not None and len(points):
        with util.Timer("scatter points"):
            scatter_points = go.Scatter(
                x = points[:,0], y = points[:,1],
                mode='markers', marker=dict(color='black', size=8)
            )
            figure.add_trace(scatter_points)

    # add lines
    if lines is not None and len(lines):
        with util.Timer("scatter lines"):
            for line in lines:
                scatter_lines = go.Scatter(
                    x = line[:,0], y = line[:,1],
                    mode='lines', line=dict(color='black', width=1)
                )
                figure.add_trace(scatter_lines)

    return figure


def plot3d(xyzs, ijks, lines, points, options):

    # plot layout
    layout = go.Layout(
        margin = dict(l=0, r=0, t=0, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        width=options.width,
        height=options.height,
        scene = dict(
            xaxis = axis(options.axes[0], range=options.x_range, title="x"),
            yaxis = axis(options.axes[1], range=options.y_range, title="y"),
            zaxis = axis(options.axes[2], range=options.z_range, title="z"),
        )
    )
    figure = go.FigureWidget(layout = layout)

    # add mesh from xyzs, ijks
    with util.Timer("mesh"):
        mesh = go.Mesh3d(
            x=xyzs[:,0], y=xyzs[:,1], z=xyzs[:,2],
            i=ijks[:,0], j=ijks[:,1], k=ijks[:,2],
            showscale=options.showscale, colorscale=options.colorscale, colorbar=dict(thickness=10), intensity=xyzs[:,2],
            hoverinfo="none"
        )
        figure.add_trace(mesh)

    # TODO: points
    # TODO: lines

    return figure
