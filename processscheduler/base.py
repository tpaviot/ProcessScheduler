"""This module contains fundamental classes/functions that are used everywhere in the project."""

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

from typing import List
import uuid

from z3 import BoolRef

#
# Utility functions
#
def is_strict_positive_integer(value: int) -> bool:
    """ Return True if the parameter value is an integer > 0 """
    return isinstance(value, int) and value > 0

def is_positive_integer(value: int) -> bool:
    """ Return True if the parameter value is an integer >= 0 """
    return isinstance(value, int) and value >= 0

#
# _NamedUIDObject, name and uid for hashing
#
class _NamedUIDObject:
    """ The base object for most ProcessScheduler classes"""
    def __init__(self, name: str) -> None:
        """ The base name for all ProcessScheduler objects.

        Provides an assertions list, a uniqueid.

        Args:
            name: the object name. It must be unique
        """
        # check name type
        if not isinstance(name, str):
            raise TypeError('name must be a str instance')
        # the object name
        self.name = name # type: str

        # unique identifier
        self.uid = uuid.uuid4().int # type: int

        # SMT assertions
        # start and end integer values must be positive
        self.assertions = [] # type: List[BoolRef]

    def __hash__(self) -> int:
        return self.uid

    def __eq__(self, other) -> bool:
        return self.uid == other.uid

    def __repr__(self) -> str:
        return self.name

    def add_assertion(self, z3_assertion: BoolRef) -> None:
        """
        Add a z3 assertion to the list of assertions to be satisfied.

        Args:
            z3_assertion: the z3 assertion
        """
        self.assertions.append(z3_assertion)

    def get_assertions(self) -> List[BoolRef]:
        """ Return the assertions list """
        return self.assertions

class _Constraint(_NamedUIDObject):
    """ The base class for all constraints """
    def __init__(self):
        super().__init__(name='')
