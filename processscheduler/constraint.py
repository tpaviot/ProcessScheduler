"""Task constraints and related classes."""

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

from typing import Optional, List

from z3 import Bool, BoolRef, Implies, PbEq, PbGe, PbLe
from processscheduler.base import _NamedUIDObject
import processscheduler.context as ps_context

#
# Base Constraint class
#
class Constraint(_NamedUIDObject):
    """The base class for all constraints, including Task and Resource constraints."""

    def __init__(self, optional):
        super().__init__("")

        self.optional = optional

        # by default, we dont know if the constraint is created from
        # an assertion
        self.created_from_assertion = False

        # by default, this constraint has to be applied
        if self.optional:
            self.applied = Bool(f"constraint_{self.uid}_applied")
        else:
            self.applied = True

        # store this constraint into the current context
        ps_context.main_context.add_constraint(self)

    def set_created_from_assertion(self) -> None:
        """Set the flag created_from_assertion True. This flag must be set to True
        if, for example, a constraint is defined from the expression:
        ps.not_(ps.TaskStartAt(task_1, 0))
        thus, the Task task_1 assertions must not be add to the z3 solver.
        """
        self.created_from_assertion = True

    def set_z3_assertions(self, list_of_z3_assertions: List[BoolRef]) -> None:
        """Each constraint comes with a set of z3 assertions
        to satisfy."""
        if self.optional:
            self.append_z3_assertion(Implies(self.applied, list_of_z3_assertions))
        else:
            self.append_z3_assertion(list_of_z3_assertions)


class ResourceConstraint(Constraint):
    """Constraint that applies on a Resource (typically a Worker)"""


class TaskConstraint(Constraint):
    """Constraint that applies on a Task"""


#
# A Generic constraint that applies to both Resource or Task
#
class ForceApplyNOptionalConstraints(Constraint):
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
                    f"The constraint {constraint.name} must explicitly be set as optional."
                )

        # all scheduled variables to take into account
        applied_vars = [
            constraint.applied for constraint in list_of_optional_constraints
        ]

        asst = problem_function[kind](
            [(applied, True) for applied in applied_vars], nb_constraints_to_apply
        )
        self.set_z3_assertions(asst)
