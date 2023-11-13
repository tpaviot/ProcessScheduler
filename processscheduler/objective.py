"""Objective and indicator definition."""

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

from typing import Optional, Union, Tuple

from z3 import Int, BoolRef, ArithRef

from pydantic import Field

from processscheduler.base import NamedUIDObject
import processscheduler.base


class Indicator(NamedUIDObject):
    """an performance indicator, can be evaluated after the solver has finished solving,
    or being optimized (Max or Min) *before* calling the solver."""

    # -- Bound --
    # None if not bounded
    # (lower_bound, None), (None, upper_bound) if only one-side bounded
    # (lower_bound, upper_bound) if full bounded
    expression: Union[int, float, BoolRef, ArithRef]
    bounds: Optional[Tuple[int, int]] = Field(default=None)

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self._indicator_variable = Int(f"Indicator_{self.name}")
        # by default the scheduled value is set to None
        # set by the solver
        self._scheduled_value = None

        self.append_z3_assertion(self._indicator_variable == self.expression)
        processscheduler.base.active_problem.add_indicator(self)


class Objective(NamedUIDObject):
    target: Union[ArithRef, Indicator]

    def __init__(self, **data) -> None:
        super().__init__(**data)
        if not isinstance(self.target, (ArithRef, Indicator)):
            raise TypeError(
                "the indicator expression must be either a BoolRef, ArithRef or Indicator instance."
            )
        if isinstance(self.target, Indicator):
            self._target = self.target._indicator_variable
            self._bounds = self.target.bounds
        else:
            self._target = self.target
            self._bounds = None
        processscheduler.base.active_problem.add_objective(self)


class MaximizeObjective(Objective):
    weight: int = Field(default=1)

    def __init__(self, **data) -> None:
        super().__init__(**data)


class MinimizeObjective(Objective):
    weight: int = Field(default=1)

    def __init__(self, **data) -> None:
        super().__init__(**data)
