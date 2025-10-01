#
# FAILED experiment - poor interactivity. Use mode_plotly
#

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

import ipywidgets as ipw

from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def mesh3d_plot(xyzs, ijks, showscale, colorscale, axes, width, height, z_range):

    faces = [[xyzs[i] for i in face] for face in ijks]
    #face = xyzs[ijks]
    poly3d = Poly3DCollection(faces)
    
    output = ipw.Output()
    with output:
        fig = plt.figure()
        #ax = fig.add_subplot(111, projection="3d")
        ax = fig.add_subplot(projection="3d")
        ax.add_collection(poly3d)
        ax.set_xlim(-10, 10)
        ax.set_ylim(-10, 10) 
        ax.set_zlim(-10, 10) 

        plt.show()

    return output
