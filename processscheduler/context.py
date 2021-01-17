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

from typing import Dict, List, Union
import warnings

from z3 import BoolRef, ArithRef

from processscheduler.task_constraint import _Constraint

class SchedulingContext:
    """ A class that contains all related data resource, tasks etc.

    The methods defined in this class ensures
    """
    def __init__(self):
        # set and clear variables
        self.clear()

    def clear(self):
        # the list of tasks to be scheduled in this scenario
        self.tasks = [] # type: Dict[str, Task]
        # the list of resources available in this scenario
        self.resources = [] # type: Dict[str, _Resource]
        # the constraints are defined in the scenario
        self.constraints = [] # type: List[BoolRef]
        # list of define indicators
        self.indicators = [] # type: List[Indicator]
        self.objectives = [] # type: List[Union[Indicator, ArithRef]]

    def add_indicator(self, indicator) -> bool:
        """ add an indicatr to the problem """
        if indicator not in self.indicators:
            self.indicators.append(indicator)
        else:
            warnings.warn('indicator %s already part of the problem' % indicator)
            return False
        return True

    def add_task(self, task) -> None:
        """ add a single task to the problem. There must not be two tasks with the same name """
        all_task_names = [t.name for t in self.tasks]
        if task.name in all_task_names:
            raise ValueError('a task with the name %s already exists.' % task.name)
        self.tasks.append(task)

    def add_resource(self, resource) -> None:
        """ add a single resource to the problem """
        all_resource_names = [t.name for t in self.resources]
        if resource.name in all_resource_names:
            raise ValueError('a resource with the name %s already exists.' % resource.name)
        self.resources.append(resource)

    def add_constraint(self, constraint) -> None:
        """ add a constraint to the problem """
        if isinstance(constraint, _Constraint):
            self.constraints.append(constraint.get_assertions())
        elif isinstance(constraint, BoolRef):
            self.constraints.append(constraint)
        else:
            raise TypeError("You must provide either a _Constraint or BoolRef instance.")

    def add_objective(self, objective) -> None:
        self.objectives.append(objective)


# Define a global context
# None by default
# the scheduling problem will set
# this variable
main_context = None

def clear_main_context() -> None:
    main_context.clear()
