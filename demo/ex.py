import numpy as np

import mcs

#
# expression helpers
#

value = lambda expr, default=None: getattr(expr, "value", default)

list_expr = lambda *a: mcs.ListExpression(*a, literal_values = a)

def get_rules(expr):
    for e in expr.elements:
        if hasattr(e, "head") and e.head == mcs.SymbolRule:
            yield e

def get_rule_values(expr):
    for rule in get_rules(expr):
        yield rule.elements[0], rule.elements[1].to_python()

# instantiate an actual nested List structure from a numpy array
# this is slow
def numpy_array_list_expr(v, mathics_type):
    #print("xxx nale", mathics_type)
    if isinstance(v, np.ndarray):
        return mcs.ListExpression(*(numpy_array_list_expr(vv, mathics_type) for vv in v), literal_values = v)
    else:
        # numpy scalar as mathics type
        return mathics_type(v.item())

#
# quacks like a List Expression, but only lazily generates elements if you really insist
# those in the know can look at .value, which is an np array, for an efficient shortcut
# that avoids ever constructing the List per se
# TODO: what else is needed to make this really quack like a List Expression
#

class LazyListExpression(mcs.ListExpression):

    def __init__(self, value):

        super().__init__(None, literal_values = value)

        # will be lazily computed if requested
        # subclass must provide self._make_elements for this purpose
        self.__elements = None

    @property
    def _elements(self):
        if not self.__elements:
            self._make_elements()
        return self.__elements

    @_elements.setter
    def _elements(self, e):
        self.__elements = e


# python complex to mathics Complex
# does this already exist somewhere?
def py_to_m_complex(v):
    return mcs.Complex(mcs.Real(v.real), mcs.Real(v.imag))

np_to_m = {t: mcs.Integer for t in ("int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64")}
np_to_m |= {t: mcs.Real for t in ("float16", "float32", "float64")}
np_to_m |= {t: py_to_m_complex for t in ("complex64", "complex128")}

class NumpyArrayListExpression(LazyListExpression):

    def __init__(self, value):

        super().__init__(value)

        # compute mathics type corresponding to np array type
        # do this up front so we fail early on unsupported types
        try:
            self.np_to_m = np_to_m[str(value.dtype)]
        except:
            raise TypeError(f"Unsupported numpy type {value.dtype}")

    # lazy computation of elements
    def _make_elements(self):
        def np_to_m(v):
            if isinstance(v, np.ndarray):
                return NumpyArrayListExpression(v)
            else:
                return self.np_to_m(v.item())
        self._elements = [np_to_m(v) for v in self.value]


if __name__ == "__main__":

    a = np.array([1, 2, 3])
    b = np.array([[1, 2], [3, 4]])
    c = np.array([[17.5, 18.5], [2.2, 3.3]])
    d = np.array([17j+3])

    for x in [a, b, c, d]:
        l = NumpyArrayListExpression(x)
        print(l.np_to_m, l)


