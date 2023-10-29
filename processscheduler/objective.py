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

from processscheduler.base import _NamedUIDObject
import processscheduler.context as ps_context

from pydantic import Field


class Indicator(_NamedUIDObject):
    """an performance indicator, can be evaluated after the solver has finished solving,
    or being optimized (Max or Min) *before* calling the solver."""

    # -- Bound --
    # None if not bounded
    # (lower_bound, None), (None, upper_bound) if only one-side bounded
    # (lower_bound, upper_bound) if full bounded
    expression: Union[BoolRef, ArithRef]
    bounds: Tuple[Optional[int]] = Field(default=None)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self._indicator_variable = Int(f"Indicator_{self.name}")
        # by default the scheduled value is set to None
        # set by the solver
        self._scheduled_value = None

        self.append_z3_assertion(self._indicator_variable == self.expression)

        ps_context.main_context.add_indicator(self)


class Objective(_NamedUIDObject):
    target: Union[ArithRef, Indicator]

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data) -> None:
        super().__init__(**data)
        if not isinstance(target, (ArithRef, Indicator)):
            raise TypeError(
                "the indicator expression must be either a BoolRef, ArithRef or Indicator instance."
            )
        if isinstance(target, Indicator):
            self._target = self.target.indicator_variable
            self._bounds = self.target.bounds
        else:
            self._target = self.target
            self._bounds = None
        ps_context.main_context.add_objective(self)


class MaximizeObjective(Objective):
    weight: int = Field(default=1)

    def __init__(self, **data) -> None:
        super().__init__(**data)


class MinimizeObjective(Objective):
    weight: int = Field(default=1)

    def __init__(self, **data) -> None:
        super().__init__(**data)
