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

import z3

from processscheduler.constraint import Constraint


#
# Utility functions
#
def _get_assertions(constraint: Union[z3.BoolRef, Constraint]) -> z3.BoolRef:
    """Take a z3.BoolRef or any Constraint and returns the assertions for this object."""
    if isinstance(constraint, z3.BoolRef):
        assertion = constraint
    else:  # Constraint
        # tag this constraint as defined from an expression
        constraint.set_created_from_assertion()
        assertion = constraint.get_z3_assertions()

    return assertion


def _constraints_to_list_of_assertions(list_of_constraints) -> List[z3.BoolRef]:
    """Convert a list of constraints or assertions to a list of assertions."""
    list_of_boolrefs_to_return = []
    for constraint in list_of_constraints:
        assertions = _get_assertions(constraint)
        if isinstance(assertions, list):
            list_of_boolrefs_to_return.extend(assertions)
        elif isinstance(assertions, z3.BoolRef):
            list_of_boolrefs_to_return.append(assertions)
    return list_of_boolrefs_to_return


#
# Nested boolean operators for Constraint objects
# or z3.BoolRef
#
class Not(Constraint):
    """A solver class"""

    constraint: Union[z3.BoolRef, Constraint]

    def __init__(self, **data) -> None:
        super().__init__(**data)

        asst = z3.Not(z3.And(_get_assertions(self.constraint)))

        self.set_z3_assertions(asst)


class Or(Constraint):
    """A solver class"""

    list_of_constraints: List[Union[z3.BoolRef, Constraint]]

    def __init__(self, **data) -> None:
        super().__init__(**data)

        asst = z3.Or(_constraints_to_list_of_assertions(self.list_of_constraints))

        self.set_z3_assertions(asst)


class And(Constraint):
    """A solver class"""

    list_of_constraints: List[Union[z3.BoolRef, Constraint]]

    def __init__(self, **data) -> None:
        super().__init__(**data)

        asst = z3.And(_constraints_to_list_of_assertions(self.list_of_constraints))

        self.set_z3_assertions(asst)


class Xor(Constraint):
    """Boolean 'xor' between two assertions or constraints.
    One assertion must be satisfied, the other is not satisfied. The list of constraint
    must have exactly 2 elements.
    """

    constraint_1: Union[z3.BoolRef, Constraint]
    constraint_2: Union[z3.BoolRef, Constraint]

    def __init__(self, **data) -> None:
        super().__init__(**data)

        asst = z3.Xor(
            z3.And(_get_assertions(self.constraint_1)),
            z3.And(_get_assertions(self.constraint_2)),
        )

        self.set_z3_assertions(asst)


class Implies(Constraint):
    """Boolean 'xor' between two assertions or constraints.
    One assertion must be satisfied, the other is not satisfied. The list of constraint
    must have exactly 2 elements.
    """

    condition: Union[z3.BoolRef, bool]
    list_of_constraints: List[Union[z3.BoolRef, Constraint]]

    def __init__(self, **data) -> None:
        super().__init__(**data)
        asst = z3.Implies(
            self.condition,
            z3.And(_constraints_to_list_of_assertions(self.list_of_constraints)),
        )
        self.set_z3_assertions(asst)


class IfThenElse(Constraint):
    """Boolean 'xor' between two assertions or constraints.
    One assertion must be satisfied, the other is not satisfied. The list of constraint
    must have exactly 2 elements.
    """

    condition: Union[z3.BoolRef, bool]
    then_list_of_constraints: List[Union[z3.BoolRef, Constraint]]
    else_list_of_constraints: List[Union[z3.BoolRef, Constraint]]

    def __init__(self, **data) -> None:
        super().__init__(**data)
        asst = z3.If(
            self.condition,
            z3.And(_constraints_to_list_of_assertions(self.then_list_of_constraints)),
            z3.And(_constraints_to_list_of_assertions(self.else_list_of_constraints)),
        )
        self.set_z3_assertions(asst)
