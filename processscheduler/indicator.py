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

from typing import Any, Dict, Optional, Union, Tuple, List, Literal
import uuid

import z3

from pydantic import Field, model_serializer

from processscheduler.base import NamedUIDObject
from processscheduler.task import Task
from processscheduler.resource import Worker, CumulativeWorker
from processscheduler.cost import ConstantCostFunction
from processscheduler.buffer import ConcurrentBuffer, NonConcurrentBuffer
from processscheduler.util import get_minimum, get_maximum
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
        tardiness_v = []
        for t in tasks:
            # tardiness in terms of time units
            tardiness_v.append(z3.If(t.due_date >= t._end, 0, t._end - t.due_date))
        expression = z3.Sum(tardiness_v)
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
            task_is_tardy = z3.Bool(f"{t.name}_is_tardy")
            tardiness_v.append(t._end > t.due_date)
        expression = z3.Sum(tardiness_v)
        self.append_z3_assertion(self._indicator_variable == expression)


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
                if isinstance(res.cost, ConstantCostFunction):
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
