""" ProcessScheduler, Copyright 2020 Thomas Paviot (tpaviot@gmail.com)

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.
"""

from typing import List
import uuid

from z3 import BoolRef

#
# Utility functions
#
def is_strict_positive_integer(value: int) -> bool:
    return isinstance(value, int) and value > 0

def is_positive_integer(value: int) -> bool:
    return isinstance(value, int) and value >= 0

#
# _NamedUIDObject, name and uid for hashing
#
class _NamedUIDObject:
    """ The base object for most ProcessScheduler classes"""
    def __init__(self, name: str) -> None:
        """
        Instanciation of a _NamedUIDObject

        :param name: the instance name, provided as a string.
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

    def add_assertion(self, z3_assertion: BoolRef):
        """ add a z3 assertion to be satisfied """
        self.assertions.append(z3_assertion)

    def get_assertions(self) -> List[BoolRef]:
        """ return the assertions list """
        return self.assertions
