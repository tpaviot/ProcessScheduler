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

from typing import List, Optional
import uuid
import warnings

from z3 import BoolRef, Bool, Implies, PbGe, PbEq, PbLe
from processscheduler.base import _NamedUIDObject, is_positive_integer

class _Cost(_NamedUIDObject):
    """ The base class for cost definition, to be assigned to a resource instance"""
    def __init__(self):
        super().__init__('')

        self.optional = False  # optional does not apply for the _Cost object
        # by default, this constraint has to be applied
        self.applied = True

    def set_assertions(self, list_of_z3_assertions: List[BoolRef]) -> None:
        """Take a list of constraint to satisfy. If the constraint is optional then
        the list of z3 assertions apply under the condition that the applied flag
        is set to True.
        """
        if self.optional:
            self.applied = Bool('constraint_%s_applied' % self.uid)
            self.add_assertion(Implies(self.applied, list_of_z3_assertions))
        else:
            self.applied = True
            self.add_assertion(list_of_z3_assertions)

class ConstantCostPerPeriod(_Cost):
    def __init__(self, value: int) -> None:
        super().__init__()
        if not is_positive_integer(value):
            raise ValueError('the cost per period must be a positive integer')
        self.value = value

class PolynomialCostFunction(_Cost):
    def __init__(self, function: callable) -> None:
        super().__init__()
        if not callable(function):
            raise TypeError('function must be a callable')
        self.f = function

    def __call__(self, value):
        """ compute the value of the cost function for a given value"""
        return self.f(value)
