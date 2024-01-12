"""Task constraints and related classes."""

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
# this program. z3.If not, see <http://www.gnu.org/licenses/>.

from typing import List, Tuple, Union

from pydantic import Field, PositiveInt

from processscheduler.constraint import IndicatorConstraint
from processscheduler.objective import Indicator


class IndicatorTarget(IndicatorConstraint):
    indicator: Indicator
    value: int

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self.append_z3_assertion(self.indicator._indicator_variable == self.value)


class IndicatorBounds(IndicatorConstraint):
    indicator: Indicator
    lower_bound: int = Field(default=None)
    upper_bound: int = Field(default=None)

    def __init__(self, **data) -> None:
        super().__init__(**data)

        if self.lower_bound is None and self.upper_bound is None:
            raise AssertionError(
                "lower and upper bounds cannot be set to None, either one of them must be set"
            )

        if self.lower_bound is not None:
            self.append_z3_assertion(
                self.indicator._indicator_variable >= self.lower_bound
            )
        if self.upper_bound is not None:
            self.append_z3_assertion(
                self.indicator._indicator_variable <= self.upper_bound
            )
