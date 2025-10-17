import graphics
import mcs
import mode
import util

def join(fe, expr, sep):
    return "{" + sep.join(_layout_box_expr(fe, e) for e in expr.elements) + "}"

def wrap_math(s):
    return mode.latex(s) if isinstance(s, str) else s

# concatenate latex strings as much as possible, allowing latex to handle the layout
# where not possible use an object representing an html layout
#
# the result is either
#   * a single string containing latex if everything can be handled in latex, or
#   * a layout object representing html elements that will form a baseline-aligned row,
#     some of which might be contain latex to be rendered by mathjax
# 
def row_box(fe, expr):
    
    parts = []
    s = ""

    #for e in expr.elements[0]:
    for e in expr.elements: # unlike a RowBox Expression, a RowBox object has elements that are not in a list!
        l = _layout_box_expr(fe, e)
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
    return _layout_box_expr(fe, expr.elements[0])

def fraction_box(fe, expr):
    # TODO: latex \frac?
    return join(fe, expr, "/")

def sqrt_box(fe, expr):
    return f"\\sqrt{{{_layout_box_expr(fe,expr.elements[0])}}}"

def superscript_box(fe, expr):
    return join(fe, expr, "^")

def template_box(fe, expr):
    return row_box(fe, expr)

def tag_box(fe, expr):
    #util.prt(expr.elements[0])
    return _layout_box_expr(fe, expr.elements[0])

def grid_box(fe, expr):

    def do(e):
        layout = _layout_box_expr(fe, e)
        layout = wrap_math(layout)
        return layout

    # arrange in a ragged array
    grid_content = [[do(cell) for cell in row] for row in expr.elements[0]]
    layout = mode.grid(grid_content)
    return layout

# TODO: temp for demo
# allows Hold on box expressions as input forms to bypass evaluation
# why are they being modified by evaluation anyway?
def hold(fe, expr):
    #util.prt(expr.elements[0])
    return _layout_box_expr(fe, expr.elements[0])

box_types = {

    mcs.SymbolHold: hold,

    #mcs.SymbolStyleBox: style_box,
    mcs.SymbolTemplateBox: template_box,
    mcs.SymbolTagBox: tag_box,
    mcs.SymbolRowBox: row_box,
    mcs.SymbolGridBox: grid_box,

    # TODO: can these be handled by mathics.core.formatter.boxes_to_format(expr, "latex") instead?
    mcs.SymbolFractionBox: fraction_box,
    mcs.SymbolSqrtBox: sqrt_box,
    mcs.SymbolSuperscriptBox: superscript_box,
}

special = {
    "Sin": "\\sin",
    "Cos": "\\cos",
}

#
# takes boxed input, and uses the tables and functions above to compute a layout from the boxes
# the general strategy is to allow latex (mathjax) do as much of the layout as possible
# but where that isn't possible to use html primitives via mode_ipy or mode_dash
#
# this function returns a string if it is latex output that can be concatenated with other latex output
# otherwise it returns an object of some kind (via mode_ipy or mode_dash) representing an html layout
#

def _layout_box_expr(fe, expr):

    #util.print_stack_reversed()
    #print("xxx _layout_box_expr", type(expr))

    if getattr(expr, "head", None) in box_types:
        return box_types[expr.head](fe, expr)
    elif getattr(expr, "head", None) in graphics.layout_funs:
        return graphics.layout_funs[expr.head](fe, expr)
    #elif latex := try_latex(expr):
    #    value = latex
    elif hasattr(expr, "value"):
        # TODO: actually everything is a string by this point, I think...
        value = expr.value
        if isinstance(value,str):
            if value in special:
                value = special[value]
            elif len(value) > 1:
                # strip quotes - surprising they're still present?
                if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
                    value = value[1:-1]
                value = f"\\mathop{{\\mbox{{{value}}}}}"
        else:
            value = str(expr.value)
        return value
    elif not hasattr(expr, "head"):
        return str(expr)
    else:
        raise Exception(f"{expr.head} is not a box")

# our main entry point
# given an expr compute a layout

#
# TODO: missing from ToBoxes - not needed for now...
#     GraphicsComplex -> ??? GraphicsComplexBox (check W)
#     Manipulate - need at least defn like Plot3D that does HOLD_FIRST
#

def layout_expr(fe, expr):

    # box it if needed
    # TODO: just look for ...Box in str(head)?
    if getattr(expr, "head", None) in box_types:
        boxed = expr
    else:
        form = mcs.SymbolTraditionalForm
        boxed = mcs.Expression(mcs.Symbol("System`ToBoxes"), expr, form).evaluate(fe.session.evaluation)

    #print("after boxing:"); util.prt(boxed)

    # compute a layout, which will either be a string containing latex,
    # or an object representing an html layout
    layout = _layout_box_expr(fe, boxed)

    # if it's a latex string, wrap it in an object that represents an html element that invokes mathjax
    layout = wrap_math(layout)

    return layout
