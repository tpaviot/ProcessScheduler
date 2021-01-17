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

from typing import Union
from z3 import Int, BoolRef, ArithRef

from processscheduler.base import _NamedUIDObject
import processscheduler.context as ps_context

class Indicator(_NamedUIDObject):
    """ an performance indicator, can be evaluated after the solver has finished solving,
    or being optimized (Max or Min) *before* calling the solver. """
    def __init__(self, name: str, expression: Union[BoolRef, ArithRef]) -> None:
        super().__init__(name)
        # scheduled start, end and duration set to 0 by default
        # be set after the solver is called
        if not isinstance(expression, (BoolRef, ArithRef)):
            raise TypeError('the indicator expression must be either a BoolRef or ArithRef.')
        self.name = name
        self.indicator_variable = Int('Indicator_%s' % name)
        # by default the scheduled value is set to None
        # set by the solver
        self.scheduled_value = None

        self.add_assertion(self.indicator_variable == expression)

        ps_context.main_context.add_indicator(self)

class BuiltinIndicator(_NamedUIDObject):
    """ a set of builtin objectives """
    def __init__(self, name:str) -> None:
        super().__init__(name)

        ps_context.main_context.add_indicator(self)

class Objective(_NamedUIDObject):
    def __init__(self, name:str, target: Union[ArithRef, Indicator]) -> None:
        super().__init__(name)
        if not isinstance(target, (ArithRef, Indicator)):
            raise TypeError('the indicator expression must be either a BoolRef, ArithRef or Indicator instance.')
        if isinstance(target, Indicator):
            self.target = target.indicator_variable
        else:
            self.target = target

        ps_context.main_context.add_objective(self)

class MaximizeObjective(Objective):
    def __init__(self, name:str, target: Union[ArithRef, Indicator]) -> None:
        super().__init__(name, target)

class MinimizeObjective(Objective):
    def __init__(self, name:str, target: Union[ArithRef, Indicator]) -> None:
        super().__init__(name, target)
