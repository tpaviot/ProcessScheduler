"""First order logic operators, implies, if/then/else."""

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

from typing import Union, List

from z3 import And, Xor, Or, Not, If, Implies, BoolRef

from processscheduler.base import _NamedUIDObject

#
# Utility functions
#
def _get_assertions(constraint: Union[BoolRef, _NamedUIDObject]) -> BoolRef:
    """Take a BoolRef or any _NamedUID and returns the assertions for this object."""
    if isinstance(constraint, BoolRef):
        assertion = constraint
    elif isinstance(constraint, _NamedUIDObject):
        assertion = constraint.get_assertions()
    else:
        raise TypeError(
            "constraint must either be a _NamedUIDObject or BoolRef instance"
        )
    return assertion


def _constraints_to_list_of_assertions(list_of_constraints) -> List[BoolRef]:
    """Convert a list of constraints or assertions to a list of assertions."""
    list_of_boolrefs_to_return = []
    for constraint in list_of_constraints:
        assertions = _get_assertions(constraint)
        if isinstance(assertions, list):
            list_of_boolrefs_to_return.extend(assertions)
        elif isinstance(assertions, BoolRef):
            list_of_boolrefs_to_return.append(assertions)
    return list_of_boolrefs_to_return


#
# Nested boolean operators for _NamedUIDObject objects
# or BoolRef
#
def not_(constraint: Union[BoolRef, _NamedUIDObject]) -> BoolRef:
    """Boolean negation of the constraint."""
    return Not(And(_get_assertions(constraint)))


def or_(list_of_constraints: List[Union[BoolRef, _NamedUIDObject]]) -> BoolRef:
    """Boolean 'or' between a list of assertions or constraints.

    At least one assertion in the list must be satisfied.
    """
    return Or(_constraints_to_list_of_assertions(list_of_constraints))


def and_(list_of_constraints: List[Union[BoolRef, _NamedUIDObject]]) -> BoolRef:
    """Boolean 'and' between a list of assertions or constraints.

    All assertions must be satisfied.
    """
    return And(_constraints_to_list_of_assertions(list_of_constraints))


def xor_(list_of_constraints: List[Union[BoolRef, _NamedUIDObject]]) -> BoolRef:
    """Boolean 'xor' between two assertions or constraints.

    One assertion must be satisfied, the other is not satisfied. The list of constraint
    must have exactly 2 elements.
    """
    if len(list_of_constraints) != 2:
        raise TypeError(
            "You list size must be 2. Be sure you have 2 constraints in the list."
        )

    constraint_1 = list_of_constraints[0]
    constraint_2 = list_of_constraints[1]

    return Xor(And(_get_assertions(constraint_1)), And(_get_assertions(constraint_2)))


#
# Logical consequence
#
def implies(
    condition: Union[BoolRef, _NamedUIDObject],
    consequence_list_of_constraints: List[Union[BoolRef, _NamedUIDObject]],
) -> BoolRef:
    """Return an implie instance

    Args:
        condition: a constraint or a boolref
        consequence_list_of_constraints: a list of all implications if condition is True
    """
    return Implies(
        And(_get_assertions(condition)),
        And(_constraints_to_list_of_assertions(consequence_list_of_constraints)),
    )


#
# If/then/else
#
def if_then_else(
    condition: Union[BoolRef, _NamedUIDObject],
    then_list_of_constraints: List[Union[BoolRef, _NamedUIDObject]],
    else_list_of_constraints: List[Union[BoolRef, _NamedUIDObject]],
) -> BoolRef:
    """If/Then/Else statement.

    Args:
        condition: a constraint or a boolref
        then_list_of_constraints: a list of all implications if condition is True
        else_list_of_constraints: a list of all implications if condition is False
    """
    return If(
        And(_get_assertions(condition)),
        And(_constraints_to_list_of_assertions(then_list_of_constraints)),
        And(_constraints_to_list_of_assertions(else_list_of_constraints)),
    )
