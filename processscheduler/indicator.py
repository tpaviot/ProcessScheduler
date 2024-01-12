"""Objective and indicator definition."""

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

from typing import Dict, Optional, Union, Tuple, List

import z3

from pydantic import Field, model_serializer

from processscheduler.base import NamedUIDObject
from processscheduler.task import Task
from processscheduler.resource import Worker, CumulativeWorker
from processscheduler.function import ConstantFunction
from processscheduler.buffer import ConcurrentBuffer, NonConcurrentBuffer
from processscheduler.util import get_minimum, get_maximum
from processscheduler.util import sort_no_duplicates

import processscheduler.base


class Indicator(NamedUIDObject):
    """A performance indicator, can be evaluated after the solver has finished solving,
    or being optimized (Max or Min) *before* calling the solver."""

    # -- Bound --
    # None if not bounded
    # (lower_bound, None), (None, upper_bound) if one-side bounded
    # (lower_bound, upper_bound) if full bounded
    bounds: Tuple[int, int] = Field(default=None)

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self._indicator_variable = z3.Int(f"Indicator_{self.name}")

        processscheduler.base.active_problem.add_indicator(self)


class IndicatorFromMathExpression(Indicator):
    """an performance indicator, can be evaluated after the solver has finished solving,
    or being optimized (Max or Min) *before* calling the solver."""

    # -- Bound --
    # None if not bounded
    # (lower_bound, None), (None, upper_bound) if only one-side bounded
    # (lower_bound, upper_bound) if full bounded
    expression: Union[int, float, z3.BoolRef, z3.ArithRef] = Field(default=None)
    bounds: Tuple[int, int] = Field(default=None)

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self.append_z3_assertion(self._indicator_variable == self.expression)


class IndicatorResourceUtilization(Indicator):
    """Compute the total utilization of a single resource.

    The percentage is rounded to an int value.
    """

    resource: Union[Worker, CumulativeWorker]

    def __init__(self, **data) -> None:
        super().__init__(**data)

        self.name = f"Utilization ({self.resource.name})"
        self.bounds = (0, 100)

        durations = [
            interv_up - interv_low
            for interv_low, interv_up in self.resource._busy_intervals.values()
        ]

        predefined_horiz = processscheduler.base.active_problem.horizon
        z3_var_horiz = processscheduler.base.active_problem._horizon  # the z3 var

        if predefined_horiz is not None:
            expression = z3.Sum(durations) * int(100 / predefined_horiz)
        else:
            expression = (z3.Sum(durations) * 100) / z3_var_horiz

        self.append_z3_assertion(self._indicator_variable == expression)


class IndicatorNumberTasksAssigned(Indicator):
    """compute the number of tasks as resource is assigned"""

    resource: Union[Worker, CumulativeWorker]

    def __init__(self, **data) -> None:
        super().__init__(**data)

        self.name = f"Nb Tasks Assigned ({self.resource.name})"
        # this list contains
        scheduled_tasks = [
            z3.If(start > -1, 1, 0)
            for start, end in self.resource._busy_intervals.values()
        ]

        expression = z3.Sum(scheduled_tasks)
        self.append_z3_assertion(self._indicator_variable == expression)


class IndicatorTardiness(Indicator):
    """The weighted sum of total tardiness for the selected tasks"""

    list_of_tasks: Union[List[Task], None] = Field(default=None)

    def __init__(self, **data) -> None:
        super().__init__(**data)

        if self.list_of_tasks is None:
            tasks = processscheduler.base.active_problem.tasks.values()
            self.name = "Total tardiness"
        else:
            tasks = self.list_of_tasks
            self.name = f"Tardiness({','.join(t.name for t in self.list_of_tasks)})"
        weighted_tardiness_v = []
        for t in tasks:
            # tardiness in terms of time units
            weighted_tardiness_v.append(
                z3.If(
                    z3.And(t.due_date >= t._end, t._scheduled),
                    0,
                    (t._end - t.due_date) * t.priority,
                )
            )
        expression = z3.Sum(weighted_tardiness_v)
        self.append_z3_assertion(self._indicator_variable == expression)


class IndicatorEarliness(Indicator):
    """In practice, it may occur that if job j is completed before its due date dj an earliness
    penalty is incurred. The earliness of job j is deﬁned as
    Ej = max(dj − Cj , 0)."""

    list_of_tasks: Union[List[Task], None] = Field(default=None)

    def __init__(self, **data) -> None:
        super().__init__(**data)

        if self.list_of_tasks is None:
            tasks = processscheduler.base.active_problem.tasks.values()
            self.name = "Total earliness"
        else:
            tasks = self.list_of_tasks
            self.name = f"Earliness({','.join(t.name for t in self.list_of_tasks)})"
        earliness_v = []
        for t in tasks:
            earliness_v.append(z3.If(t.due_date - t._end >= 0, t.due_date - t._end, 0))
        expression = z3.Sum(earliness_v)
        self.append_z3_assertion(self._indicator_variable == expression)


class IndicatorNumberOfTardyTasks(Indicator):
    list_of_tasks: Union[List[Task], None] = Field(default=None)

    def __init__(self, **data) -> None:
        super().__init__(**data)

        if self.list_of_tasks is None:
            tasks = processscheduler.base.active_problem.tasks.values()
            self.name = "Total tardiness"
        else:
            tasks = self.list_of_tasks
            self.name = (
                f"NumberOfTardyTasks({','.join(t.name for t in self.list_of_tasks)})"
            )
        tardiness_v = []
        for t in tasks:
            tardiness_v.append(t._end > t.due_date)
        number_of_tardy_tasks = z3.Sum(tardiness_v)
        self.append_z3_assertion(self._indicator_variable == number_of_tardy_tasks)


class IndicatorMaximumLateness(Indicator):
    """The maximum lateness in a group of tasks"""

    list_of_tasks: Union[List[Task], None] = Field(default=None)

    def __init__(self, **data) -> None:
        super().__init__(**data)

        if self.list_of_tasks is None:
            tasks = processscheduler.base.active_problem.tasks.values()
            self.name = "MaximumLateness"
        else:
            tasks = self.list_of_tasks
            self.name = (
                f"MaximumLateness({','.join(t.name for t in self.list_of_tasks)})"
            )
        latenesses = [t._end - t.due_date for t in tasks]

        self.append_z3_list_of_assertions(
            get_maximum(self._indicator_variable, latenesses)
        )


class IndicatorResourceCost(Indicator):
    """compute the total cost of a set of resources"""

    list_of_resources: List[Union[Worker, CumulativeWorker]]

    def __init__(self, **data) -> None:
        super().__init__(**data)

        self.name = (
            f"Total Cost ({','.join(res.name for res in self.list_of_resources)})"
        )

        constant_costs = []
        variable_costs = []

        def get_resource_cost(res):
            """for the given resource, compute cost from busy intervals
            For a constant cost"""
            local_constant_costs = []
            local_variable_costs = []

            for interv_low, interv_up in res._busy_intervals.values():
                # Constant cost per period
                if isinstance(res.cost, ConstantFunction):
                    # res.cost(interv_up), res.cost(interv_low)
                    # or res.cost.value give the same result because the function is constant
                    cost_for_this_period = res.cost(interv_up)
                    if cost_for_this_period == 0:
                        continue
                    if cost_for_this_period == 1:
                        period_cost = interv_up - interv_low
                    else:
                        period_cost = res.cost(interv_up) * (interv_up - interv_low)
                    local_constant_costs.append(period_cost)
                # non linear cost. Compute the area of the trapeze
                # The division by 2 is performed only once, a few lines below,
                # after the sum is computed.
                else:
                    period_cost = (res.cost(interv_low) + res.cost(interv_up)) * (
                        interv_up - interv_low
                    )
                    local_variable_costs.append(period_cost)
            return local_constant_costs, local_variable_costs

        for resource in self.list_of_resources:
            if isinstance(resource, CumulativeWorker):
                for res in resource._cumulative_workers:
                    loc_cst_cst, loc_var_cst = get_resource_cost(res)
                    constant_costs.extend(loc_cst_cst)
                    variable_costs.extend(loc_var_cst)
            else:  # for a single worker
                loc_cst_cst, loc_var_cst = get_resource_cost(resource)
                constant_costs.extend(loc_cst_cst)
                variable_costs.extend(loc_var_cst)

        # TODO: what if we multiply the line below by 2? This would remove a division
        # by 2, and make the cost computation linear if costs are linear
        expression = z3.Sum(constant_costs) + z3.Sum(variable_costs) / 2
        self.append_z3_assertion(self._indicator_variable == expression)


class IndicatorResourceIdle(Indicator):
    resource: Union[Worker, CumulativeWorker]

    def __init__(self, **data) -> None:
        super().__init__(**data)

        self.name = f"ResourceIdle{self.resource.name}"

        starts = []
        ends = []
        for start_var, end_var in self.resource._busy_intervals.values():
            starts.append(start_var)
            ends.append(end_var)
        # sort both lists
        sorted_starts, c1 = sort_no_duplicates(starts)
        sorted_ends, c2 = sort_no_duplicates(ends)
        self.append_z3_list_of_assertions(c1 + c2)
        # from now, starts and ends are sorted in asc order
        # the space between two consecutive tasks is the sorted_start[i+1]-sorted_end[i]
        # we just have to constraint this variable
        diffs = []
        for i in range(1, len(sorted_starts)):
            condition_only_scheduled_tasks = z3.And(
                sorted_ends[i - 1] >= 0, sorted_starts[i] >= 0
            )
            new_diff = z3.If(
                condition_only_scheduled_tasks, sorted_starts[i] - sorted_ends[i - 1], 0
            )
            diffs.append(new_diff)

        self.append_z3_assertion(self._indicator_variable == z3.Sum(diffs))


class IndicatorMaxBufferLevel(Indicator):
    """The maximum level of a buffer, along the whole schedule lifetime"""

    buffer: Union[ConcurrentBuffer, NonConcurrentBuffer]

    def __init__(self, **data) -> None:
        super().__init__(**data)

        self.name = f"MaximizeBuffer{self.buffer.name}Level"

        self.append_z3_list_of_assertions(
            get_maximum(self._indicator_variable, self.buffer._buffer_states)
        )


class IndicatorMinBufferLevel(Indicator):
    """The maximum level of a buffer, along the whole schedule lifetime"""

    buffer: Union[ConcurrentBuffer, NonConcurrentBuffer]

    def __init__(self, **data) -> None:
        super().__init__(**data)

        self.name = f"Mini {self.buffer.name} level"

        self.append_z3_list_of_assertions(
            get_minimum(self._indicator_variable, self.buffer._buffer_states)
        )
