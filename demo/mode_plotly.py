import plotly.graph_objects as go

import util

def mesh3d_plot(xyzs, ijks, showscale, colorscale, axes, width, height, z_range):

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
            data = [mesh],
            layout = go.Layout(
                margin = dict(l=0, r=0, t=0, b=0),
                scene = dict(
                    xaxis = dict(title="x", visible=axes, showspikes=showspikes), # TODO: name
                    yaxis = dict(title="y", visible=axes, showspikes=showspikes), # TODO: name
                    zaxis = dict(title="z", visible=axes, showspikes=showspikes), # TODO: name
                    aspectmode="cube"
                ),
                width=width,
                height=height
            )
        )
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
