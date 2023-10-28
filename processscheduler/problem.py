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
import uuid
from typing import List, Optional, Union

from pydantic import Field

from z3 import And, BoolRef, If, Int, Or, Sum, Implies, ArithRef

from processscheduler.base import _NamedUIDObject
from processscheduler.util import is_strict_positive_integer
from processscheduler.objective import Indicator, MaximizeObjective, MinimizeObjective
from processscheduler.resource import Resource, CumulativeWorker
from processscheduler.cost import ConstantCostPerPeriod, PolynomialCostFunction
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

    horizon: int = Field(default=None)
    delta_time: Optional[timedelta] = (None,)
    start_time: Optional[datetime] = (None,)
    end_time: Optional[datetime] = (None,)

    def __init__(self, **data) -> None:
        super().__init__(**data)
        # the problem context, where all will be stored
        # at creation
        self._context = ps_context.SchedulingContext()
        # set this context as global
        ps_context.main_context = self._context

        # store the horizon value to be exported to json
        self._horizon_defined_value = self.horizon
        # define the horizon variable
        self._horizon = Int("horizon")
        if is_strict_positive_integer(self.horizon):
            self._context.add_constraint(self._horizon <= self._horizon_defined_value)
        elif self.horizon is not None:
            raise TypeError("horizon must either be a strict positive integer or None")

    def add_constraint(self, constraint: BoolRef) -> None:
        self._context.add_constraint(constraint)

    def add_indicator_number_tasks_assigned(self, resource: Resource):
        """compute the number of tasks as resource is assigned"""
        # this list contains
        scheduled_tasks = [
            If(start > -1, 1, 0) for start, end in resource.busy_intervals.values()
        ]

        nb_tasks_assigned_indicator_variable = Sum(scheduled_tasks)
        return Indicator(
            f"Nb Tasks Assigned ({resource.name})",
            nb_tasks_assigned_indicator_variable,
        )

    def add_indicator_resource_cost(
        self, list_of_resources: List[Resource]
    ) -> Indicator:
        """compute the total cost of a set of resources"""
        constant_costs = []
        variable_costs = []

        def get_resource_cost(res):
            """for the given resource, compute cost from busy intervals
            For a constant cost"""
            local_constant_costs = []
            local_variable_costs = []

            for interv_low, interv_up in res.busy_intervals.values():
                # Constant cost per period
                if isinstance(res.cost, ConstantCostPerPeriod):
                    # res.cost(interv_up), res.cost(interv_low)
                    # or res.cost.value give the same result because the function is constant
                    cost_for_this_period = res.cost(interv_up)
                    if cost_for_this_period == 0:
                        continue
                    elif cost_for_this_period == 1:
                        period_cost = interv_up - interv_low
                    else:
                        period_cost = res.cost(interv_up) * (interv_up - interv_low)
                    local_constant_costs.append(period_cost)
                # Polynomial cost. Compute the area of the trapeze
                # The division by 2 is performed only once, a few lines below,
                # after the sum is computed.
                if isinstance(res.cost, PolynomialCostFunction):
                    period_cost = (res.cost(interv_low) + res.cost(interv_up)) * (
                        interv_up - interv_low
                    )
                    local_variable_costs.append(period_cost)
            return local_constant_costs, local_variable_costs

        for resource in list_of_resources:
            if isinstance(resource, CumulativeWorker):
                for res in resource.cumulative_workers:
                    loc_cst_cst, loc_var_cst = get_resource_cost(res)
                    constant_costs.extend(loc_cst_cst)
                    variable_costs.extend(loc_var_cst)
            else:  # for a single worker
                loc_cst_cst, loc_var_cst = get_resource_cost(resource)
                constant_costs.extend(loc_cst_cst)
                variable_costs.extend(loc_var_cst)

        resource_names = ",".join([resource.name for resource in list_of_resources])
        # TODO: what if we multiply the line below by 2? This would remove a division
        # by 2, and make the cost computation linear if costs are linear
        cost_indicator_variable = Sum(constant_costs) + Sum(variable_costs) / 2
        cost_indicator = Indicator(
            f"Total Cost ({resource_names})", cost_indicator_variable
        )
        return cost_indicator

    def add_indicator_resource_utilization(self, resource: Resource) -> Indicator:
        """Compute the total utilization of a single resource.

        The percentage is rounded to an int value.
        """
        durations = [
            interv_up - interv_low
            for interv_low, interv_up in resource.busy_intervals.values()
        ]
        if self.horizon_defined_value is not None:
            utilization = Sum(durations) * int(100 / self.horizon_defined_value)
        else:
            utilization = (Sum(durations) * 100) / self.horizon  # in percentage
        return Indicator(f"Utilization ({resource.name})", utilization, bounds=(0, 100))

    def maximize_indicator(self, indicator: Indicator) -> MaximizeObjective:
        """Maximize indicator"""
        return MaximizeObjective("", indicator)

    def minimize_indicator(self, indicator: Indicator) -> MinimizeObjective:
        """Minimize indicator"""
        return MinimizeObjective("", indicator)

    #
    # Optimization objectives
    #
    def add_objective_makespan(self, weight=1) -> Union[ArithRef, Indicator]:
        """makespan objective"""
        MinimizeObjective("MakeSpan", self.horizon, weight)
        return self.horizon

    def add_objective_resource_utilization(
        self, resource: Resource, weight=1
    ) -> Union[ArithRef, Indicator]:
        """Maximize resource occupation."""
        resource_utilization_indicator = self.add_indicator_resource_utilization(
            resource
        )
        MaximizeObjective("", resource_utilization_indicator, weight)
        return resource_utilization_indicator

    def add_objective_resource_cost(
        self, list_of_resources: List[Resource], weight=1
    ) -> Union[ArithRef, Indicator]:
        """minimise the cost of selected resources"""
        cost_indicator = self.add_indicator_resource_cost(list_of_resources)
        MinimizeObjective("", cost_indicator, weight)
        return cost_indicator

    def add_objective_priorities(self, weight=1) -> Union[ArithRef, Indicator]:
        """optimize the solution such that all task with a higher
        priority value are scheduled before other tasks"""
        all_priorities = []
        for task in self.context.tasks:
            if task.optional:
                all_priorities.append(task.end * task.priority * task.scheduled)
            else:
                all_priorities.append(task.end * task.priority)
        priority_sum = Sum(all_priorities)
        priority_indicator = Indicator("PriorityTotal", priority_sum)
        MinimizeObjective("", priority_indicator, weight)
        return priority_indicator

    def add_objective_start_latest(self, weight=1) -> Union[ArithRef, Indicator]:
        """maximize the minimum start time, i.e. all the tasks
        are scheduled as late as possible"""
        mini = Int("SmallestStartTime")
        smallest_start_time = Indicator("SmallestStartTime", mini)
        smallest_start_time.append_z3_assertion(
            Or([mini == task.start for task in self.context.tasks])
        )
        for tsk in self.context.tasks:
            smallest_start_time.append_z3_assertion(mini <= tsk.start)
        MaximizeObjective("", smallest_start_time, weight)
        return smallest_start_time

    def add_objective_start_earliest(self, weight=1) -> Union[ArithRef, Indicator]:
        """minimize the greatest start time, i.e. tasks are schedules
        as early as possible"""
        maxi = Int("GreatestStartTime")
        greatest_start_time = Indicator("GreatestStartTime", maxi)
        greatest_start_time.append_z3_assertion(
            Or([maxi == task.start for task in self.context.tasks])
        )
        for tsk in self.context.tasks:
            greatest_start_time.append_z3_assertion(maxi >= tsk.start)
        MinimizeObjective("", greatest_start_time, weight)
        return greatest_start_time

    def add_objective_flowtime(self, weight=1) -> Union[ArithRef, Indicator]:
        """the flowtime is the sum of all ends, minimize. Be carful that
        it is contradictory with makespan"""
        task_ends = []
        for task in self.context.tasks:
            if task.optional:
                task_ends.append(task.end * task.scheduled)
            else:
                task_ends.append(task.end)
        flow_time_expr = Sum(task_ends)
        flow_time = Indicator("FlowTime", flow_time_expr)
        MinimizeObjective("", flow_time, weight)
        return flow_time

    def add_objective_flowtime_single_resource(
        self, resource, time_interval=None, weight=1
    ) -> Union[ArithRef, Indicator]:
        """Optimize flowtime for a single resource, for all the tasks scheduled in the
        time interval provided. Is ever no time interval is passed to the function, the
        flowtime is minimized for all the tasks scheduled in the workplan."""
        if time_interval is not None:
            lower_bound, upper_bound = time_interval
        else:
            lower_bound = 0
            upper_bound = self.horizon
        uid = uuid.uuid4().hex
        # for this resource, we look for the minimal starting time of scheduled tasks
        # as well as the maximum
        flowtime = Int(f"FlowtimeSingleResource{resource.name}_{uid}")

        flowtime_single_resource_indicator = Indicator(
            f"FlowTime({resource.name}:{lower_bound}:{upper_bound})", flowtime
        )
        # find the max end time in the time_interval
        maxi = Int(f"GreatestTaskEndTimeInTimePeriodForResource{resource.name}_{uid}")

        asst_max = [
            Implies(
                And(task.end <= upper_bound, task.start >= lower_bound),
                maxi == task.end,
            )
            for task in resource.busy_intervals
        ]
        flowtime_single_resource_indicator.append_z3_assertion(Or(asst_max))
        for task in resource.busy_intervals:
            flowtime_single_resource_indicator.append_z3_assertion(
                Implies(
                    And(task.end <= upper_bound, task.start >= lower_bound),
                    maxi >= task.end,
                )
            )

        # and the mini
        mini = Int(f"SmallestTaskEndTimeInTimePeriodForResource{resource.name}_{uid}")

        asst_min = [
            Implies(
                And(task.end <= upper_bound, task.start <= lower_bound),
                mini == task.start,
            )
            for task in resource.busy_intervals
        ]
        flowtime_single_resource_indicator.append_z3_assertion(Or(asst_min))
        for task in resource.busy_intervals:
            flowtime_single_resource_indicator.append_z3_assertion(
                Implies(
                    And(task.end <= upper_bound, task.start >= lower_bound),
                    mini <= task.start,
                )
            )

        # the quantity to optimize
        flowtime_single_resource_indicator.append_z3_assertion(flowtime == maxi - mini)
        flowtime_single_resource_indicator.append_z3_assertion(flowtime >= 0)

        MinimizeObjective("", flowtime_single_resource_indicator, weight)
        return flowtime_single_resource_indicator
