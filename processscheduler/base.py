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

from typing import List, Optional
import uuid
import warnings

from z3 import BoolRef, Bool, Implies, PbGe, PbEq, PbLe

#
# _NamedUIDObject, name and uid for hashing
#
class _NamedUIDObject:
    """The base object for most ProcessScheduler classes"""

    def __init__(self, name: str) -> None:
        """The base name for all ProcessScheduler objects.

        Provides an assertions list, a uniqueid.

        Args:
            name: the object name. It must be unique
        """
        # check name type
        if not isinstance(name, str):
            raise TypeError("name must be a str instance")
        # the object name
        self.name = name  # type: str

        # unique identifier
        self.uid = uuid.uuid4().int  # type: int

        # SMT assertions
        # start and end integer values must be positive
        self.assertions = []  # type: List[BoolRef]
        self.assertion_hashes = []

    def __hash__(self) -> int:
        return self.uid

    def __eq__(self, other) -> bool:
        return self.uid == other.uid

    def __repr__(self) -> str:
        """Print the object name, its uid and the assertions."""
        str_to_return = "%s(%s)\n%i assertion(s):\n" % (
            self.name,
            type(self),
            len(self.assertions),
        )
        assertions_str = "".join("%s" % ass for ass in self.assertions)
        return str_to_return + assertions_str

    def add_assertion(self, z3_assertion: BoolRef) -> bool:
        """
        Add a z3 assertion to the list of assertions to be satisfied.

        Args:
            z3_assertion: the z3 assertion
        """
        # check if the assertion is in the list
        # workaround to avoid heavy hash computations
        assertion_hash = hash(z3_assertion)
        if assertion_hash in self.assertion_hashes:
            warnings.warn("assertion %s already added." % z3_assertion)
            return False
        self.assertions.append(z3_assertion)
        self.assertion_hashes.append(assertion_hash)
        return True

    def get_assertions(self) -> List[BoolRef]:
        """Return the assertions list"""
        return self.assertions


class _Constraint(_NamedUIDObject):
    """The base class for all constraints, including Task and Resource constraints."""

    def __init__(self, optional):
        super().__init__("")

        self.optional = optional
        # by default, this constraint has to be applied
        self.applied = True

    def set_assertions(self, list_of_z3_assertions: List[BoolRef]) -> None:
        """Take a list of constraint to satisfy. If the constraint is optional then
        the list of z3 assertions apply under the condition that the applied flag
        is set to True.
        """
        if self.optional:
            self.applied = Bool("constraint_%s_applied" % self.uid)
            self.add_assertion(Implies(self.applied, list_of_z3_assertions))
        else:
            self.applied = True
            self.add_assertion(list_of_z3_assertions)


class ForceApplyNOptionalConstraints(_Constraint):
    """Given a set of m different optional constraints, force the solver to apply
    at at least/at most/exactly n tasks, with 0 < n <= m. Work for both
    Task and/or Resource constraints."""

    def __init__(
        self,
        list_of_optional_constraints,
        nb_constraints_to_apply: Optional[int] = 1,
        kind: Optional[str] = "exact",
        optional: Optional[bool] = False,
    ) -> None:
        super().__init__(optional)

        problem_function = {"min": PbGe, "max": PbLe, "exact": PbEq}

        # first check that all tasks from the list_of_optional_tasks are
        # actually optional
        for constraint in list_of_optional_constraints:
            if not constraint.optional:
                raise TypeError(
                    "The constraint %s must explicitly be set as optional."
                    % constraint.name
                )

        # all scheduled variables to take into account
        applied_vars = [
            constraint.applied for constraint in list_of_optional_constraints
        ]

        asst = problem_function[kind](
            [(applied, True) for applied in applied_vars], nb_constraints_to_apply
        )
        self.set_assertions(asst)
