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

from typing import Union

from z3 import And, Xor, Or, Not, If, Implies, BoolRef

from processscheduler.base import _NamedUIDObject

#
# Utility functions
#
def _get_assertions(constraint: Union[BoolRef, _NamedUIDObject]) -> BoolRef:
    if isinstance(constraint, BoolRef):
        assertion = constraint
    elif isinstance(constraint, _NamedUIDObject):
        assertion = constraint.get_assertions()
    else:
        raise TypeError("constraint must either be a _NamedUIDObject or BoolRef instance")
    return assertion

#
# Nested boolean operators for _NamedUIDObject objects
# or BoolRef
#
def not_(constraint: Union[BoolRef, _NamedUIDObject]) -> BoolRef:
    """ a boolean not over a _NamedUIDObject, returns
    the negation of all assertions """
    return Not(And(_get_assertions(constraint)))

def or_(constraint_1: Union[BoolRef, _NamedUIDObject],
        constraint_2: Union[BoolRef, _NamedUIDObject]) -> BoolRef:
    """ returns a boolean or between a and b assertions"""
    return Or(And(_get_assertions(constraint_1)),
              And(_get_assertions(constraint_2)))

def and_(constraint_1: Union[BoolRef, _NamedUIDObject],
         constraint_2: Union[BoolRef, _NamedUIDObject]) -> BoolRef:
    """ return a boolean and between tasks assertions """
    return And(And(_get_assertions(constraint_1)), And(_get_assertions(constraint_2)))

def xor_(constraint_1: Union[BoolRef, _NamedUIDObject],
         constraint_2: Union[BoolRef, _NamedUIDObject]) -> BoolRef:
    """ return a boolean xor between tasks assertions """
    return Xor(And(_get_assertions(constraint_1)), And(_get_assertions(constraint_2)))

#
# Logical consequence
#
def implies(constraint_1: Union[BoolRef, _NamedUIDObject],
            constraint_2: Union[BoolRef, _NamedUIDObject]) -> BoolRef:
    """ return a boolean xor between tasks assertions """
    print(type(constraint_1))
    print(type(constraint_2))
    return Implies(And(_get_assertions(constraint_1)), And(_get_assertions(constraint_2)))

#
# If/then/else
#
def if_then_else(constraint_if: Union[BoolRef, _NamedUIDObject],
                 constraint_then: Union[BoolRef, _NamedUIDObject],
                 constraint_else: Union[BoolRef, _NamedUIDObject]) -> BoolRef:
    """ return a boolean xor between tasks assertions """
    return If(And(_get_assertions(constraint_if)),
              And(_get_assertions(constraint_then)),
              And(_get_assertions(constraint_else)))
