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

from datetime import timedelta, datetime
from typing import List, Optional

from z3 import BoolRef, Int, Or, Sum

from processscheduler.base import _NamedUIDObject, is_strict_positive_integer
from processscheduler.objective import (Indicator, MaximizeObjective,
                                        MinimizeObjective, BuiltinIndicator)
from processscheduler.resource import _Resource, CumulativeWorker

import processscheduler.context as ps_context

class SchedulingProblem(_NamedUIDObject):
    """A scheduling problem

    :param name: the problem name, a string type
    :param horizon: an optional integer, the final instant of the timeline
    :param delta_time: an optional timedelta object
    :param start_time: an optional datetime object
    :param end_time: an optional datetime object
    :param datetime_format: an optional string

    """
    def __init__(self, name: str,
                 horizon: Optional[int] = None,
                 delta_time: Optional[timedelta] = None,
                 start_time: Optional[datetime] = None,
                 end_time: Optional[datetime] = None
                 ):
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

        # check time data
        if delta_time is not None and not isinstance(delta_time, timedelta):
            raise TypeError('delta_time must be a timedelta instance')
        if start_time is not None and not isinstance(start_time, datetime):
            raise TypeError('start_time must be a datetime instance')
        if end_time is not None and not isinstance(end_time, datetime):
            raise TypeError('delta_time must be a datetime instance')

        self.delta_time = delta_time
        self.start_time = start_time
        self.end_time = end_time

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

        def get_resource_cost(res):
            p = []
            for interv_low, interv_up in res.busy_intervals.values():
                partial_cost_contribution = res.cost_per_period * (interv_up - interv_low)
                p.append(partial_cost_contribution)
            return p

        for resource in list_of_resources:
            if isinstance(resource, CumulativeWorker):
                for res in resource.cumulative_workers:
                    partial_costs.extend(get_resource_cost(res))
            else: # for a single worker
                partial_costs.extend(get_resource_cost(resource))

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
            durations.append(interv_up - interv_low)
        utilization = (Sum(durations) * 100) / self.horizon  # in percentage
        utilization_indicator = Indicator('Utilization (%s)' % resource.name,
                                           utilization)
        return utilization_indicator

    def add_objective_resource_utilization(self, resource: _Resource) -> MaximizeObjective:
        """Maximize resource occupation."""
        resource_utilization_indicator = self.add_indicator_resource_utilization(resource)
        return self.maximize_indicator(resource_utilization_indicator)

    def add_objective_resource_cost(self, list_of_resources: List[_Resource]) -> MinimizeObjective:
        """ minimise the cost of selected resources
        """
        cost_indicator = self.add_indicator_resource_cost(list_of_resources)
        return self.minimize_indicator(cost_indicator)

    def add_objective_priorities(self) -> MinimizeObjective:
        """ optimize the solution such that all task with a higher
        priority value are scheduled before other tasks """
        all_priorities = []
        for task in self.context.tasks:
            if task.optional:
                all_priorities.append(task.end * task.priority * task.scheduled)
            else:
                all_priorities.append(task.end * task.priority)
        priority_sum = Sum(all_priorities)
        priority_indicator = Indicator('PriorityTotal', priority_sum)
        return self.minimize_indicator(priority_indicator)

    def add_objective_start_latest(self) -> MaximizeObjective:
        """ maximize the minimum start time, i.e. all the tasks
        are scheduled as late as possible """
        mini = Int('SmallestStartTime')
        smallest_start_time = BuiltinIndicator('SmallestStartTime')
        smallest_start_time.add_assertion(Or([mini == task.start for task in self.context.tasks]))
        for tsk in self.context.tasks:
            smallest_start_time.add_assertion(mini <= tsk.start)
        smallest_start_time.indicator_variable = mini
        return self.maximize_indicator(mini)

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
        greatest_start_time = BuiltinIndicator('GreatestStartTime')
        greatest_start_time.add_assertion(Or([maxi == task.start for task in self.context.tasks]))
        for tsk in self.context.tasks:
            greatest_start_time.add_assertion(maxi >= tsk.start)
        greatest_start_time.indicator_variable = maxi
        return self.minimize_indicator(maxi)

    def add_objective_flowtime(self) -> MinimizeObjective:
        """ the flowtime is the sum of all ends, minimize. Be carful that
        it is contradictory with makespan """
        task_ends = []
        for task in self.context.tasks:
            if task.optional:
                task_ends.append(task.end * task.scheduled)
            else:
                task_ends.append(task.end)
        flow_time_expr = Sum(task_ends)
        smallest_start_time_indicator = Indicator('FlowTime', flow_time_expr)
        return self.minimize_indicator(smallest_start_time_indicator)
