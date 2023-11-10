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

from typing import Callable

from processscheduler.base import _NamedUIDObject

from pydantic import Field


class Cost(_NamedUIDObject):
    """The base class for cost definition, to be assigned to a resource"""

    cost_function: Callable[[float], float] = Field(default=lambda x: 0)

    def __init__(self, **data) -> None:
        super().__init__(**data)

    def __call__(self, value):
        """compute the value of the cost function for a given value"""
        to_return = self.cost_function(value)
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


class ConstantCostPerPeriod(Cost):
    value: int  # TODO: should this be positive only?

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self.cost_function = lambda x: self.value


class PolynomialCostFunction(Cost):
    """A function of time under a polynomial form."""
