import ev
import ex

def eval_Plot3Dv3(fe, expr):
    xs, ys, zs = ev.eval_plot3d_xyzs(fe, expr)
    result = ev.grid_to_graphics_complex(xs, ys, zs, ex.numpy_array_list_expr)
    return result

