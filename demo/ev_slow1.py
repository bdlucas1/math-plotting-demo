import numpy as np

from mathics.core.expression import Expression
from mathics.core.symbols import Symbol

import ev
import ex
import util

# List of Polygon each with its own list of x,y,z coordinates
def grid_to_graphics_poly_list(xs, ys, zs):

    # a=[1:,1:]   b=[1:,:-1]
    # c=[:-1:,1:] d=[:-1,:-1]
    xyzs = np.stack([xs, ys, zs], axis=-1)                                # shape = (nx,ny,3)
    tris1 = np.stack([xyzs[1:,1:], xyzs[1:,:-1], xyzs[:-1,:-1]], axis=-1) # abd, shape = (nx-1,ny-1,3,3)
    tris2 = np.stack([xyzs[1:,1:], xyzs[:-1,:-1], xyzs[:-1,1:]], axis=-1) # adc, shape = (nx-1,ny-1,3,3)
    tris = np.stack([tris1,tris2])                                        # shape = (2,nx-1,ny-1,3,3)
    tris = tris.reshape((-1,3,3)).transpose(0,2,1)                        # shape = (2*(nx-1)*(ny-1),3,3)

    # TODO: check this
    # ugh - indices in Polygon are 1-based
    tris += 1

    # this is the slow part
    # corresponding traversal at other end is similarly slow
    with util.Timer("construct G3D list of polys")
        result = Expression(mcss.Graphics3D, 
            Expression(mcss.List), *(
                Expression(mcss.Polygon, ex.list_expr(ex.list_expr(*p), ex.list_expr(*q), ex.list_expr(*r)))
                for p, q, r in tris
            ))
        )

    return result

def eval_Plot3D(fe, expr):
    xs, ys, zs = ev.eval_plot3d_xyzs(fe, expr)
    result = grid_to_graphics_poly_list(xs, ys, zs)
    return result

