import numpy as np

import mathics.core.list as mlist
import mathics.core.symbols as msym

#
# expression helpers
#

value = lambda expr, default=None: getattr(expr, "value", default)

list_expr = lambda *a: mlist.ListExpression(*a, literal_values = a)

def get_rules(expr):
    for e in expr.elements:
        if hasattr(e, "head") and str(e.head) == "System`Rule":
            yield e

# TODO: symbol instead of str
def get_rule_values(expr):
    for rule in get_rules(expr):
        yield str(rule.elements[0]), rule.elements[1].to_python()

# instantiate an actual nested List structure from a numpy array
# this is slow
def numpy_array_list_expr(v, mathics_type):
    if isinstance(v, np.ndarray):
        return mlist.ListExpression(*(numpy_array_list_expr(vv, mathics_type) for vv in v), literal_values = v)
    else:
        # numpy scalar as mathics type
        return mathics_type(v.item())

# quacks like a List Expression, but only lazily generates elements if you really insist
# those in the know can look at .value, which is an np array, for an efficient shortcut
# that avoids ever constructing the List per se
# TODO: what else is needed to make this really quack like a List Expression
class NumpyArrayListExpr:

    def __init__(self, value, mathics_type):
        self.head = msym.Symbol("System`List") # TODO use import
        self.value = value
        self.mathics_type = mathics_type
        self._elements = None

    @property
    def elements(self):
        if not self._elements:
            # if call really really needs .elements we'll compute them here
            # but it's more efficient to just look at .value
            # TODO: this instantiates whole nested list structure on first reference
            # should we likewise lazily evaluate each element of the list in the case of >1-d arrays?
            self._elements = numpy_array_list_expr(self.value, self.mathics_type).elements
        return self._elements


