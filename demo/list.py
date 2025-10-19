

#
# Lazily evaluated list expressions
# copied from WIP update to mathics-core list.py
#

import abc
import numpy as np
from typing import Sequence, Tuple, cast
import traceback

from mathics.core.convert.python import from_python
from mathics.core.list import ListExpression
from mathics.core.expression import ExpressionCache
from mathics.core.element import BaseElement, ElementsProperties

import util

# TODO: not sure how useful it is to have separated this out:
# several additonal overrides that require value to be numeric
# are needed in NumpyArrayListExpression to avoid instantiating ._elements

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

    # needed to avoid instantiating ._elements
    def _build_elements_properties(self):
        self.elements_properties =  ElementsProperties(True, True, True)

    # needed to avoid instantiating ._elements
    def _rebuild_cache(self):
        self._cache = ExpressionCache(0, [], [])
        return self._cache

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

    def __init__(self, value: np.ndarray, level = 0):
        # TODO: np.ndarray is not assignable to Sequence because nominal vs structural, but I think this is safe
        # also since .value is declared Sequence typechecker will complain if user tries to modify the array
        # even though arrays allow it; I guess this is a good thing
        super().__init__(cast(Sequence,value))
        self.level = level

    # needed to avoid instantiating ._elements
    def is_numeric(self):
        return True

    # needed to avoid instantiating ._elements
    def element_order(self):
        return (GENERAL_NUMERIC_EXPRESSION_SORT_KEY, self.head, len(self.values), self.value, 1)

    # lazy computation of elements from numpy array
    def _make_elements(self) -> Tuple[BaseElement, ...]:
        #traceback.print_stack()
        #print("INSTANTIATING")
        with util.Timer("INSTANTIATING" if self.level == 0 else None):
            def np_to_m(v) -> BaseElement | NumpyArrayListExpression:
                if isinstance(v, np.ndarray):
                    return NumpyArrayListExpression(v, self.level + 1)
                else:
                    return from_python(v.item())
            return tuple(np_to_m(v) for v in self.value)
