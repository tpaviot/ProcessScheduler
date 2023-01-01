"""The context related module."""

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

from typing import List, Union
import warnings

from z3 import BoolRef, ArithRef

from processscheduler.constraint import Constraint


class SchedulingContext:
    """A class that contains all related data resource, tasks etc.

    The methods defined in this class ensures
    """

    def __init__(self):
        # set and clear variables
        self.clear()

    def clear(self):
        """Initialize context content"""
        # the list of tasks to be scheduled in this scenario
        self.tasks = []  # type: List[Task]
        # the list of resources of type Worker available in this scenario
        #
        # Resources
        #
        self.resources = []  # type: List[Resource]
        # the list of resources of type Worker available in this scenario
        self.select_workers = []  # type: List[SelectWorkers]
        # the list of resources of type Worker available in this scenario
        self.cumulative_workers = []  # type: List[CumulativeWorker]
        # list of all constraints
        self.constraints = []  # type: List[Constraint]
        # the list of z3 assertions
        self.z3_assertions = []  # type: List[BoolRef]
        # list of define indicators
        self.indicators = []  # type: List[Indicator]
        # list of objectives
        self.objectives = []  # type: List[Union[Indicator, ArithRef]]
        # list of buffers
        self.buffers = []  # type: List[Buffer]

    def add_indicator(self, indicator: "Indicator") -> bool:
        """Add an indicatr to the problem"""
        if indicator not in self.indicators:
            self.indicators.append(indicator)
        else:
            warnings.warn(f"indicator {indicator} already part of the problem")
            return False
        return True

    def add_task(self, task: "Task") -> int:
        """Add a single task to the problem. There must not be two tasks with the same name"""
        if task.name in [t.name for t in self.tasks]:
            raise ValueError(f"a task with the name {task.name} already exists.")
        self.tasks.append(task)
        return len(self.tasks)

    def add_resource(self, resource: "Worker") -> None:
        """Add a single resource to the problem"""
        if resource.name in [t.name for t in self.resources]:
            raise ValueError(
                f"a resource with the name {resource.name} already exists."
            )
        self.resources.append(resource)

    def add_resource_select_workers(self, resource: "SelectWorker") -> None:
        """Add a single resource to the problem"""
        self.select_workers.append(resource)

    def add_resource_cumulative_worker(self, resource: "SelectWorker") -> None:
        """Add a single resource to the problem"""
        if resource.name in [t.name for t in self.select_workers]:
            raise ValueError(
                f"a resource with the name {resource.name} already exists."
            )
        self.cumulative_workers.append(resource)

    def append_z3_assertion(self, z3_asst):
        self.z3_assertions.append(z3_asst)

    def add_constraint(self, constraint: Constraint) -> None:
        """Add a constraint to the problem. A constraint can be either
        a z3 assertion or a processscheduler Constraint instance."""
        if isinstance(constraint, Constraint):
            if constraint not in self.constraints:
                self.constraints.append(constraint)
            else:
                raise AssertionError("constraint already added to the problem.")
        elif isinstance(constraint, BoolRef):
            self.z3_assertions.append(constraint)
        else:
            raise TypeError(
                "You must provide either a _Constraint or BoolRef instance."
            )

    def add_objective(self, objective: "Objective") -> None:
        """Add an optimization objective"""
        self.objectives.append(objective)

    def add_buffer(self, buffer: "Buffer") -> None:
        """Add a single task to the problem. There must not be two tasks with the same name"""
        if buffer.name in [b.name for b in self.buffers]:
            raise ValueError(f"a buffer with the name {buffer.name} already exists.")
        self.buffers.append(buffer)


# Define a global context
# None by default
# the scheduling problem will set this variable
main_context = None


def clear_main_context() -> None:
    """Clear current context"""
    if main_context is not None:
        main_context.clear()
