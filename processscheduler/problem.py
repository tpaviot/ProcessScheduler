"""Problem definition and related classes."""

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
import warnings

from z3 import BoolRef, Int, Or, Sum

from processscheduler.base import _NamedUIDObject, is_strict_positive_integer
from processscheduler.objective import Indicator, MaximizeObjective, MinimizeObjective, BuiltinIndicator
from processscheduler.resource import _Resource

import processscheduler.context as ps_context

class SchedulingProblem(_NamedUIDObject):
    """A scheduling problem

    :param name: the problem name, a string type
    :param horizon: an optional integer, the final instant of the timeline
    """
    def __init__(self, name: str, horizon: Optional[int] = None):
        super().__init__(name)
        # the problem context, where all will be stored
        # at creation
        self.context = ps_context.SchedulingContext()
        # set this context as global
        ps_context.main_context = self.context

        # define the horizon variable
        self.horizon = Int('horizon')
        self.fixed_horizon = False  # set to True is horizon is fixed
        if is_strict_positive_integer(horizon):  # fixed_horizon
            self.context.add_constraint(self.horizon == horizon)
            self.fixed_horizon = True
        elif horizon is not None:
            raise TypeError('horizon must either be a strict positive integer or None')

    def add_constraint(self, constraint: BoolRef) -> None:
        self.context.add_constraint(constraint)

    def add_constraints(self, list_of_constraints: List[BoolRef]) -> None:
        """ adds constraints to the problem """
        for cstr in list_of_constraints:
            self.context.add_constraint(cstr)

    def add_objective_makespan(self) -> MinimizeObjective:
        """ makespan objective
        """
        if self.fixed_horizon:
            raise ValueError('Horizon constrained to be fixed, no horizon optimization possible.')
        return MinimizeObjective('MakeSpan', self.horizon)

    def add_indicator_resource_cost(self, list_of_resources: List[_Resource]) -> Indicator:
        """ compute the total cost of a set of resources """
        partial_costs = []
        for resource in list_of_resources:
            for interv_low, interv_up in resource.busy_intervals.values():
                partial_cost_contribution = resource.cost_per_period * (interv_up - interv_low)
                partial_costs.append(partial_cost_contribution)
        resource_names = ','.join([resource.name for resource in list_of_resources])
        cost_indicator_variable = Sum(partial_costs)
        cost_indicator = Indicator('Total Cost (%s)' % resource_names,
                                   cost_indicator_variable)
        return cost_indicator

    def add_indicator_resource_utilization(self, resource: _Resource) -> Indicator:
        """Compute the total utilization of a single resource.

        The percentage is rounded to an int value.
        """
        durations = []
        for interv_low, interv_up in resource.busy_intervals.values():
            duration = interv_up - interv_low
            durations.append(duration)
        utilization = (Sum(durations) * 100) / self.horizon  # in percentage
        utilization_indicator = Indicator('Uilization (%s)' % resource.name,
                                           utilization)
        return utilization_indicator

    def add_objective_resource_cost(self, list_of_resources: List[_Resource]) -> MinimizeObjective:
        """ minimise the cost of selected resources
        """
        cost_indicator = self.add_indicator_resource_cost(list_of_resources)
        return MinimizeObjective('PriorityObjective', cost_indicator)

    def add_objective_priorities(self) -> MinimizeObjective:
        """ optimize the solution such that all task with a higher
        priority value are scheduled before other tasks """
        priority_sum = Sum([task.end  * task.priority for task in self.context.tasks])
        priority_indicator = Indicator('PriorityTotal', priority_sum)
        return MinimizeObjective('PriorityObjective', priority_indicator)

    def add_objective_start_latest(self) -> MaximizeObjective:
        """ maximize the minimum start time, i.e. all the tasks
        are scheduled as late as possible """
        mini = Int('SmallestStartTime')
        a = BuiltinIndicator('GreatestStartTime')
        a.add_assertion(Or([mini == task.start for task in self.context.tasks]))
        for tsk in self.context.tasks:
            a.add_assertion(mini <= tsk.start)
        a.indicator_variable=mini
        return MaximizeObjective('SmallestStartTime', mini)

    def maximize_indicator(self, indicator: Indicator) -> MaximizeObjective:
        """Maximize indicator """
        return MaximizeObjective('', indicator)

    def minimize_indicator(self, indicator: Indicator) -> MinimizeObjective:
        """Minimize indicator"""
        return MinimizeObjective('', indicator)

    def add_objective_start_earliest(self) -> MinimizeObjective:
        """ minimize the greatest start time, i.e. tasks are schedules
        as early as possible """
        maxi = Int('GreatestStartTime')
        a = BuiltinIndicator('GreatestStartTime')
        a.add_assertion(Or([maxi == task.start for task in self.context.tasks]))
        for tsk in self.context.tasks:
            a.add_assertion(maxi >= tsk.start)
        a.indicator_variable=maxi
        return MinimizeObjective('GreatestStartTimeObjective', maxi)

    def add_objective_flowtime(self) -> MinimizeObjective:
        """ the flowtime is the sum of all ends, minimize. Be carful that
        it is contradictory with makespan """
        flow_time_expr = Sum([task.end for task in self.context.tasks])
        smallest_start_time_indicator = Indicator('FlowTime', flow_time_expr)
        return MinimizeObjective('FlowTimeObjective', smallest_start_time_indicator)
