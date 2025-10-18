"""
Compute a layout for Row, Grid, graphics, and equations.
Graphics layouts are delegated to graphics.layout_funs.
Main entry point here is expression_layout.

A layout is a data structure that a front-end can display.
The layout is constructed here and in graphics.py by calling
mode.grid, mode.row, mode.plot, mode.manipulate, etc.
These will be functions from either mode_dash or mode_ipy,
depending on which widget set is needed for the current front end.
So the net result will be either a dash or ipywidgets data structure
that can be displayed by the front-end.
"""

import graphics
import mcs
import mode
import util

import mathics.core.formatter as fmt

def join(fe, expr, sep):
    return "{" + sep.join(_box_expr_layout(fe, e) for e in expr.elements) + "}"

def wrap_math(s):
    return mode.latex(s) if isinstance(s, str) else s

# Concatenate latex strings as much as possible, allowing latex to handle the layout.
# Where not possible use a object (dash or ipywidgets) representing an html layout.
#
# The return value of this function is either
#   * a single string containing latex if everything can be handled in latex, or
#   * a layout object representing html elements that will form a baseline-aligned row,
#     some of which might be contain latex to be rendered by mathjax
# 
def row_box(fe, expr):
    
    parts = []
    s = ""

    # surprise! unlike a RowBox Expression, a RowBox object has elements that are not in a list!
    #for e in expr.elements[0]:
    for e in expr.elements:
        l = _box_expr_layout(fe, e)
        if isinstance(l,str):
            s += l
        else:
            if s:
                parts.append(s)
                s = ""
            parts.append(l)
    if s:
        parts.append(s)

    if len(parts) == 1:
        return parts[0]
    else:
        return mode.row(list(wrap_math(p) for p in parts))

def style_box(fe, expr):
    # TODO: handle this appropriately
    return _box_expr_layout(fe, expr.elements[0])

def template_box(fe, expr):
    return row_box(fe, expr)

def tag_box(fe, expr):
    #util.prt(expr.elements[0])
    return _box_expr_layout(fe, expr.elements[0])

def grid_box(fe, expr):

    def do(e):
        layout = _box_expr_layout(fe, e)
        layout = wrap_math(layout)
        return layout

    # arrange in a ragged array
    grid_content = [[do(cell) for cell in row] for row in expr.elements[0]]
    layout = mode.grid(grid_content)
    return layout

layout_funs = {
    mcs.SymbolTemplateBox: template_box,
    mcs.SymbolTagBox: tag_box,
    mcs.SymbolRowBox: row_box,
    mcs.SymbolGridBox: grid_box,
}

special = {
    "Sin": "\\sin",
    "Cos": "\\cos",
}

#
# Takes boxed input, and uses the tables and functions above to compute a layout from the boxes.
# The general strategy is to allow latex (mathjax) do as much of the layout as possible,
# but where that isn't possible to use html primitives via mode_ipy or mode_dash.
#
# This function returns a string if it is latex output that can be concatenated with other latex output
# otherwise it returns an object of some kind (via mode_ipy or mode_dash) representing an html layout.
#

def _box_expr_layout(fe, expr):

    #util.print_stack_reversed()
    #print("xxx _box_expr_layout", type(expr))

    def try_latex():
        try:
            return fmt.boxes_to_format(expr, "latex")
        except:
            return None

    if getattr(expr, "head", None) in layout_funs:
        return layout_funs[expr.head](fe, expr)
    elif getattr(expr, "head", None) in graphics.layout_funs:
        return graphics.layout_funs[expr.head](fe, expr)
    elif isinstance(expr,mcs.String):
        if expr.value in special:
            value = special[expr.value]
        elif len(expr.value) >= 2 and expr.value[0] == '"' and expr.value[-1] == '"':
            # strip quotes - surprising they're still present?
            value = f"\\mathsf{{\\mbox{{{expr.value[1:-1]}}}}}"
        elif len(expr.value) > 1:
            value = f"\\mathop{{\\mbox{{{expr.value}}}}}"
        else:
            value = expr.value
        return value
    elif not hasattr(expr, "head"):
        return str(expr)
    elif value := try_latex():
        return value
    else:
        raise Exception(f"Don't know how to lay out {expr.head}")


#
# our main entry point
# given an expr compute a layout
#
# TODO: missing from ToBoxes - not needed for now...
#     GraphicsComplex -> ??? GraphicsComplexBox (check W)
#

def expression_layout(fe, expr):

    #print("xxx before boxing:"); util.prt(expr)

    # TODO: is this a hack? is it needed?
    if str(getattr(expr, "head", None)).endswith("Box"):
        boxed = expr
    else:
        form = mcs.SymbolTraditionalForm
        boxed = mcs.Expression(mcs.Symbol("System`ToBoxes"), expr, form).evaluate(fe.session.evaluation)

    #print("after boxing:"); util.prt(boxed)

    # compute a layout, which will either be a string containing latex,
    # or an object representing an html layout
    layout = _box_expr_layout(fe, boxed)

    # if it's a latex string, wrap it in an object that represents an html element that invokes mathjax
    layout = wrap_math(layout)

    return layout
