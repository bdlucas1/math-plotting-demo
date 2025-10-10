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

#
# Lazily evaluated list expressions
# copied from WIP update to mathics-core list.py
#

import abc
from typing import Sequence, Tuple, cast

from mathics.core.list import ListExpression
from mathics.core.element import BaseElement


class LazyListExpression(ListExpression, abc.ABC):

    """
    A ListExpression with a supplied value that represents a list in
    some way, but no supplied elements. The elements will be
    instantiated on demand from the value. This allows the value to be
    stored and used efficiently but at the same to present a normal
    ListExpression view if required.
    """

    def __init__(self, value: Sequence) -> None:

        # we are a ListExpression with no .elements but a .value
        super().__init__(literal_values = value)

        # will be lazily computed if requested
        # subclass must provide self._make_elements for this purpose
        self.__elements: Tuple[BaseElement, ...] | None = None

    @abc.abstractmethod
    def _make_elements(self) -> Tuple[BaseElement, ...]:
        pass

    # TODO: pyrefly gives us side-eye here becase we're overriding a member attribute with a property
    # (but mypy and pyright do not complain...)
    # the justification I turned up with a little googling was that properties can violate the substitution principle
    # because they can change performance or semantics (e.g. by raising exceptions)
    # personally I don't buy it because the same is true of any overriden method, and if that is a concern of the type
    # system then exceptions and performance characteristics should be part of the type signatures of attributes and methods
    # and the ability to slide in a property to replace an attribute is kind of a core benefit of properties

    @property
    def _elements(self) -> Tuple[BaseElement, ...]:
        if not self.__elements:
            self.__elements = self._make_elements()
        return self.__elements

    @_elements.setter
    def _elements(self, e) -> None:
        self.__elements = e

    # this is primarily for testing
    @property
    def is_instantiated(self) -> bool:
        return self.__elements is not None



class NumpyArrayListExpression(LazyListExpression):

    """
    A lazily instantiated ListExpression backed by a numpy array.
    This allows data to be efficiently stored, transmitted, and
    accessed efficiently as a numpy array by a collaborating source
    and recipient, only instantiating the inefficent elements
    representation if required by some third party.
    """

    def __init__(self, value: np.ndarray):
        # TODO: np.ndarray is not assignable to Sequence because nominal vs structural, but I think this is safe
        # also since .value is declared Sequence typechecker will complain if user tries to modify the array
        # even though arrays allow it; I guess this is a good thing
        super().__init__(cast(Sequence,value))

    # lazy computation of elements from numpy array
    def _make_elements(self) -> Tuple[BaseElement, ...]:
        def np_to_m(v) -> BaseElement | NumpyArrayListExpression:
            if isinstance(v, np.ndarray):
                return NumpyArrayListExpression(v)
            else:
                return from_python(v.item())
        return tuple(np_to_m(v) for v in self.value)
    
