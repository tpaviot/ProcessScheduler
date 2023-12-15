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
from processscheduler.function import ConstantFunction
from processscheduler.buffer import ConcurrentBuffer, NonConcurrentBuffer
from processscheduler.util import get_minimum, get_maximum
from processscheduler.indicator import (
    Indicator,
    IndicatorResourceUtilization,
    IndicatorResourceCost,
    IndicatorFromMathExpression,
    IndicatorMaxBufferLevel,
)

import processscheduler.base


class Objective(NamedUIDObject):
    """Base class for an optimization problem"""

    target: Union[z3.ArithRef, Indicator] = Field(default=None)
    weight: int = Field(default=1)
    kind: Literal["minimize", "maximize"]

    def __init__(self, **data) -> None:
        super().__init__(**data)

        if isinstance(self.target, Indicator):
            self._target = self.target._indicator_variable
            self._bounds = self.target.bounds
        else:
            self._target = self.target
            self._bounds = None

        processscheduler.base.active_problem.add_objective(self)


class ObjectiveMaximizeIndicator(Objective):
    def __init__(self, **data) -> None:
        target = data["target"]
        weight = data["weight"]
        super().__init__(name=f"Maximize{target.name}", weight=weight, kind="maximize")


class ObjectiveMinimizeIndicator(Objective):
    def __init__(self, **data) -> None:
        target = data["target"]
        weight = data["weight"]
        super().__init__(
            name=f"Minimize{target.name}", weight=weight, kind="minimimize"
        )


class ObjectiveMinimizeMakespan(Objective):
    """The makespan, deﬁned as max(C1 , . . . , Cn ), is equivalent
    to the completion time of the last job to leave the system. A minimum makespan
    usually implies a good utilization of the machine(s)."""

    def __init__(self, **data) -> None:
        super().__init__(
            name="MinimizeMakeSpan",
            target=processscheduler.base.active_problem._horizon,
            kind="minimize",
        )

    @model_serializer
    def ser_model(self) -> Dict[str, Any]:
        return {
            "type": "ObjectiveMinimizeMakespan",
        }


class ObjectiveMaximizeResourceUtilization(Objective):
    """Maximize resource occupation."""

    def __init__(self, **data) -> None:
        resource_utilization_indicator = IndicatorResourceUtilization(
            resource=data["resource"]
        )
        super().__init__(
            name="MaximizeResourceUtilization",
            target=resource_utilization_indicator,
            kind="maximize",
        )


class ObjectiveMinimizeResourceCost(Objective):
    """Minimise the total cost of selected resources"""

    def __init__(self, **data) -> None:
        lor = data["list_of_resources"]
        cost_indicator = IndicatorResourceCost(list_of_resources=lor)
        instance_name = f"MinimizeResourceCost{''.join([r.name for r in lor])}"
        super().__init__(name=instance_name, target=cost_indicator, kind="minimize")
        self._lor = lor

    @model_serializer
    def ser_model(self) -> Dict[str, Any]:
        return {
            "type": "ObjectiveMinimizeResourceCost",
            "list_of_resources": [r.name for r in self._lor],
        }


class ObjectiveTasksStartLatest(Objective):
    """maximize the minimum start time, i.e. all the tasks
    are scheduled as late as possible"""

    def __init__(self, **data) -> None:
        if "list_of_tasks" in data:
            list_of_tasks = data["list_of_tasks"]
        else:
            list_of_tasks = None

        if list_of_tasks is None:
            list_of_tasks = processscheduler.base.active_problem.tasks.values()

        smallest_start_time = z3.Int("SmallestStartTimeVar")
        # create related indicator
        mini_start_time_indicator = IndicatorFromMathExpression(
            name="MinimumStartTime", expression=smallest_start_time
        )

        # compute the minimum of start times for all tasks
        assertions = get_minimum(
            smallest_start_time, [task._start for task in list_of_tasks]
        )
        mini_start_time_indicator.append_z3_list_of_assertions(assertions)

        # and finally maximize this smallest start time
        super().__init__(
            name="MaximizeStartLatest",
            target=mini_start_time_indicator,
            kind="maximize",
        )


class ObjectiveTasksStartEarliest(Objective):
    """This is the dual of the completion weighted times
    but for task starts."""

    def __init__(self, **data) -> None:
        all_priorities = []
        for task in processscheduler.base.active_problem.tasks.values():
            if task.optional:
                all_priorities.append(task._start * task.priority * task._scheduled)
            else:
                all_priorities.append(task._start * task.priority)
        priority_sum = z3.Sum(all_priorities)
        priority_indicator = IndicatorFromMathExpression(
            name="WeightedStartTimes", expression=priority_sum
        )
        super().__init__(
            name="MinimizeWeightedStartTimes",
            target=priority_indicator,
            kind="minimize",
        )


class ObjectiveMinimizeGreatestStartTime(Objective):
    """minimize the greatest start time, i.e. tasks are schedules
    as early as possible"""

    def __init__(self, **data) -> None:
        if "list_of_tasks" in data:
            list_of_tasks = data["list_of_tasks"]
        else:
            list_of_tasks = None

        if list_of_tasks is None:
            list_of_tasks = processscheduler.base.active_problem.tasks.values()

        greatest_start_time = z3.Int("GreatestStartTime")
        greatest_start_time_indicator = IndicatorFromMathExpression(
            name="GreatestStartTime", expression=greatest_start_time
        )

        # compute the maximum of start times for all tasks
        assertions = get_maximum(
            greatest_start_time, [task._start for task in list_of_tasks]
        )
        greatest_start_time_indicator.append_z3_list_of_assertions(assertions)

        super().__init__(
            name="StartEarliest", target=greatest_start_time_indicator, kind="minimize"
        )


class ObjectiveMinimizeFlowtime(Objective):
    """This objective is also known as minimizing the 'Total Weighted Completion Time'

    o = Σ C j

    Be careful that it is contradictory with the minimize makespan objective."""

    def __init__(self, **data) -> None:
        if "list_of_tasks" in data:
            list_of_tasks = data["list_of_tasks"]
        else:
            list_of_tasks = None

        if list_of_tasks is None:
            list_of_tasks = processscheduler.base.active_problem.tasks.values()
        task_ends = []
        for task in list_of_tasks:
            if task.optional:
                task_ends.append(task._end * task._scheduled)
            else:
                task_ends.append(task._end)
        flow_time_expr = z3.Sum(task_ends)
        flow_time = IndicatorFromMathExpression(
            name="Flowtime", expression=flow_time_expr
        )
        super().__init__(name="Flowtime", target=flow_time, kind="minimize")


class ObjectivePriorities(Objective):
    """This objective is also known as minimizing the 'Total Weighted Completion Time'.

    o = Σ wj C j

    According to this rule, the jobs are ordered in decreasing order of wj/pj ,
    where wj is the weight for task j, denoted priority in our case, and pj
    is the"""

    def __init__(self, **data) -> None:
        all_priorities = []
        for task in processscheduler.base.active_problem.tasks.values():
            if task.optional:
                all_priorities.append(task._end * task.priority * task._scheduled)
            else:
                all_priorities.append(task._end * task.priority)
        priority_sum = z3.Sum(all_priorities)
        priority_indicator = IndicatorFromMathExpression(
            name="TotalPriority", expression=priority_sum
        )
        super().__init__(
            name="MinimizePriority", target=priority_indicator, kind="minimize"
        )

    @model_serializer
    def ser_model(self) -> Dict[str, Any]:
        return {
            "type": "ObjectivePriorities",
        }


class ObjectiveMinimizeFlowtimeSingleResource(Objective):
    """Optimize flowtime for a single resource, for all the tasks scheduled in the
    time interval provided. Is ever no time interval is passed to the function, the
    flowtime is minimized for all the tasks scheduled in the workplan."""

    def __init__(self, **data) -> None:
        resource = data["resource"]

        if "time_interval" in data:
            time_interval = data["time_interval"]
        else:
            time_interval = None

        if time_interval is not None:
            lower_bound, upper_bound = time_interval
        else:
            lower_bound = 0
            upper_bound = processscheduler.base.active_problem._horizon

        uid = uuid.uuid4().hex
        # for this resource, we look for the minimal starting time of scheduled tasks
        # as well as the maximum
        flowtime = z3.Int(f"FlowtimeSingleResource{resource.name}_{uid}")

        flowtime_single_resource_indicator = IndicatorFromMathExpression(
            name=f"FlowTimeSingleResource({resource.name}:{lower_bound}:{upper_bound})",
            expression=flowtime,
        )
        # find the max end time in the time_interval
        maxi = z3.Int(
            f"GreatestTaskEndTimeInTimePeriodForResource{resource.name}_{uid}"
        )

        asst_max = [
            z3.Implies(
                z3.And(task._end <= upper_bound, task._start >= lower_bound),
                maxi == task._end,
            )
            for task in resource._busy_intervals
        ]
        flowtime_single_resource_indicator.append_z3_assertion(z3.Or(asst_max))
        for task in resource._busy_intervals:
            flowtime_single_resource_indicator.append_z3_assertion(
                z3.Implies(
                    z3.And(task._end <= upper_bound, task._start >= lower_bound),
                    maxi >= task._end,
                )
            )

        # and the mini
        mini = z3.Int(
            f"SmallestTaskEndTimeInTimePeriodForResource{resource.name}_{uid}"
        )

        asst_min = [
            z3.Implies(
                z3.And(task._end <= upper_bound, task._start <= lower_bound),
                mini == task._start,
            )
            for task in resource._busy_intervals
        ]
        flowtime_single_resource_indicator.append_z3_assertion(z3.Or(asst_min))
        for task in resource._busy_intervals:
            flowtime_single_resource_indicator.append_z3_assertion(
                z3.Implies(
                    z3.And(task._end <= upper_bound, task._start >= lower_bound),
                    mini <= task._start,
                )
            )

        # the quantity to optimize
        flowtime_single_resource_indicator.append_z3_assertion(flowtime == maxi - mini)
        flowtime_single_resource_indicator.append_z3_assertion(flowtime >= 0)

        super().__init__(
            name=f"ObjectiveFlowtimeSingleResource({resource.name}:{lower_bound}:{upper_bound})",
            target=flowtime_single_resource_indicator,
            kind="minimize",
        )


class ObjectiveMaximizeMaxBufferLevel(Objective):
    def __init__(self, **data) -> None:
        buffer = data["buffer"]
        # create related indicator
        indic_max_buffer_level = IndicatorMaxBufferLevel(buffer=buffer)

        # and finally maximize this smallest start time
        super().__init__(
            name="MaximizeBufferLevel",
            target=indic_max_buffer_level,
            kind="maximize",
        )


class ObjectiveMinimizeMaxBufferLevel(Objective):
    def __init__(self, **data) -> None:
        buffer = data["buffer"]
        # create related indicator
        indic_max_buffer_level = IndicatorMaxBufferLevel(buffer=buffer)

        # and finally maximize this smallest start time
        super().__init__(
            name="MinimizeBufferLevel",
            target=indic_max_buffer_level,
            kind="minimize",
        )
