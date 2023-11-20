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

from processscheduler.base import NamedUIDObject

from pydantic import Field

from z3 import ArithRef


class Cost(NamedUIDObject):
    """The base class for cost definition, to be assigned to a resource"""

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self._cost_function = lambda x: 0  # default returns 0

    def set_cost_function(self, f: Callable):
        self._cost_function = f

    def __call__(self, value):
        """compute the value of the cost function for a given value"""
        to_return = self._cost_function(value)
        # check if there is a ToReal conversion in the function
        # this may occur if the cost function is not linear
        # and this would result in an unexpected computation
        if "ToReal" in f"{to_return}":
            raise AssertionError(
                "Warning: ToReal conversion, the cost function must be linear."
            )
        return to_return

    def plot(self, interval, show_plot=False) -> None:
        """Plot the cost curve using matplotlib."""
        try:
            import matplotlib.pyplot as plt
        except ImportError as exc:
            raise ModuleNotFoundError("matplotlib is not installed.") from exc

        try:
            import numpy as np
        except ImportError as exc:
            raise ModuleNotFoundError("numpy is not installed.") from exc

        lower_bound, upper_bound = interval
        x = np.linspace(lower_bound, upper_bound, 1000)
        y = [self.cost_function(x_) for x_ in x]
        plt.plot(x, y, label="Cost function")

        plt.legend()
        plt.grid(True)
        plt.xlabel("x")
        plt.ylabel("y")

        if show_plot:
            plt.show()


class ConstantCostFunction(Cost):
    value: Union[int, float]

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self.set_cost_function(lambda x: self.value)


class LinearCostFunction(Cost):
    """A linear cost function:
    C(x) = slope * x + intercept
    """

    slope: Union[ArithRef, int, float]
    intercept: Union[ArithRef, int, float]

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self.set_cost_function(lambda x: self.slope * x + self.intercept)


class PolynomialCostFunction(Cost):
    """A cost function under a polynomial form.
    C(x) = a_n * x^n + a_{n-1} * x^(n-1) + ... + a_0"""

    coefficients: List[Union[ArithRef, int, float]]

    def __init__(self, **data) -> None:
        super().__init__(**data)

        def compute_cost(x):
            result = self.coefficients[-1]
            v = x
            for i in range(len(self.coefficients) - 2, -1, -1):
                if self.coefficients[i] != 0:
                    result += self.coefficients[i] * v
                v = v * x
            return result

        self.set_cost_function(compute_cost)


class GeneralCostFunction(Cost):
    func: Callable

    def __init__(self, **data) -> None:
        super().__init__(**data)

        self.set_cost_function(self.func)
