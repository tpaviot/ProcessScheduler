# Copyright (c) 2020-2021 Thomas Paviot (tpaviot@gmail.com)
#
# This file is part of ProcessScheduler.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.

from typing import Callable, Union, List
import warnings

from processscheduler.base import NamedUIDObject

import z3


class Function(NamedUIDObject):
    """The base class for function definition, to be used for cost or penalties"""

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self._function = lambda x: 0  # default returns 0

    def set_function(self, f: Callable):
        self._function = f

    def __call__(self, value):
        """compute the value of the cost function for a given value"""
        to_return = self._function(value)
        # check if there is a ToReal conversion in the function
        # this may occur if the cost function is not linear
        # and this would result in an unexpected computation
        if "ToReal" in f"{to_return}":
            warnings.warn(
                "ToReal conversion in the cost function, might result in computation issues.",
                UserWarning,
            )
        return to_return


class ConstantFunction(Function):
    value: Union[int, float]

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self.set_function(lambda x: self.value)


class LinearFunction(Function):
    """A linear function:
    F(x) = slope * x + intercept
    """

    slope: Union[z3.ArithRef, int, float]
    intercept: Union[z3.ArithRef, int, float]

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self.set_function(lambda x: self.slope * x + self.intercept)


class PolynomialFunction(Function):
    """A cost function under a polynomial form.
    C(x) = a_n * x^n + a_{n-1} * x^(n-1) + ... + a_0"""

    coefficients: List[Union[z3.ArithRef, int, float]]

    def __init__(self, **data) -> None:
        super().__init__(**data)

        def _compute(x):
            result = self.coefficients[-1]
            v = x
            for i in range(len(self.coefficients) - 2, -1, -1):
                if self.coefficients[i] != 0:
                    result += self.coefficients[i] * v
                v = v * x
            return result

        self.set_function(_compute)


class GeneralFunction(Function):
    """A function defined from a python function"""

    function: Callable

    def __init__(self, **data) -> None:
        super().__init__(**data)

        self.set_function(self.function)
