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
# this program. z3.If not, see <http://www.gnu.org/licenses/>.

from datetime import timedelta, datetime
import json
import uuid
from typing import Dict, List, Union, Any, Tuple

from pydantic import Field, PositiveInt

import z3

from processscheduler.base import NamedUIDObject
import processscheduler.base
from processscheduler.task import (
    Task,
    FixedDurationTask,
    ZeroDurationTask,
    VariableDurationTask,
)
from processscheduler.cost import (
    ConstantCostFunction,
    LinearCostFunction,
    PolynomialCostFunction,
    GeneralCostFunction,
)
from processscheduler.objective import (
    Indicator,
    IndicatorFromMathExpression,
    IndicatorResourceUtilization,
    IndicatorResourceCost,
    Objective,
    MaximizeObjective,
    MinimizeObjective,
)
from processscheduler.resource import Resource, Worker, CumulativeWorker, SelectWorkers
from processscheduler.constraint import Constraint
from processscheduler.buffer import Buffer

_object_types = {
    "FixedDurationTask": FixedDurationTask,
    "ZeroDurationTask": ZeroDurationTask,
    "VariableDurationTask": VariableDurationTask,
    "Worker": Worker,
    "CumulativeWorker": CumulativeWorker,
    "SelectWorkers": SelectWorkers,
}


class SchedulingProblem(NamedUIDObject):
    """A scheduling problem

    :param name: the problem name, a string type
    :param horizon: an optional integer, the final instant of the timeline
    :param delta_time: an optional timedelta object
    :param start_time: an optional datetime object
    :param end_time: an optional datetime object
    :param datetime_format: an optional string

    """

    horizon: Union[PositiveInt, z3.ArithRef] = Field(default=None)
    delta_time: timedelta = Field(default=None)
    start_time: datetime = Field(default=None)
    end_time: datetime = Field(default=None)

    tasks: Dict[
        str, Union[FixedDurationTask, VariableDurationTask, ZeroDurationTask]
    ] = Field(default={})

    workers: Dict[str, Worker] = Field(default={})

    select_workers: Dict[str, SelectWorkers] = Field(default={})

    cumulative_workers: Dict[str, CumulativeWorker] = Field(default={})

    constraints: List[Constraint] = Field(default=[])

    indicators: Dict[str, Indicator] = Field(default={})

    objectives: Dict[str, Union[Indicator, z3.ArithRef]] = Field(default={})

    buffers: List[Buffer] = Field(default=[])

    def __init__(self, **data) -> None:
        super().__init__(**data)

        # the active problem, where all will be stored
        processscheduler.base.active_problem = self

        # define the horizon variable
        self._horizon = z3.Int("horizon")
        if self.horizon is not None:
            self.add_constraint(self._horizon <= self.horizon)

    def add_from_json_file(self, filename: str):
        """take filename and returns the object"""
        with open(filename, "r") as f:
            return self.add_from_json(f.read())

    def add_from_json(self, json_string: str) -> Any:
        """takes a json string an returns the object.
        Example of json string:
        {'name': 'W2', 'type': 'Worker', 'productivity': 1, 'cost': None}
        """
        s = json.loads(json_string)
        # first find the class to instantiate
        s_type = s["type"]
        if not s_type in _object_types:
            raise AssertionError(f"{s_type} type not known")

        # create and return the object
        return _object_types[s_type].model_validate_json(json_string)

    def add_task(self, task: Task) -> int:
        """Add a single task to the problem. There must not be two tasks with the same name"""
        if task.name in self.tasks:
            raise ValueError(
                f"a Task instance with the name {task.name} already exists."
            )
        self.tasks[task.name] = task
        return len(self.tasks)

    def add_resource_worker(self, worker: Worker) -> None:
        """Add a single resource to the problem"""
        if worker.name in self.workers:
            raise ValueError(
                f"a Worker instance with the name {worker.name} already exists."
            )
        self.workers[worker.name] = worker

    def add_resource_select_workers(self, select_workers: SelectWorkers) -> None:
        """Add a Worker to the problem"""
        if select_workers.name in self.select_workers:
            raise ValueError(
                f"a wSelectWorkers instance with the name {select_workers.name} already exists."
            )
        self.select_workers[select_workers.name] = select_workers

    def add_resource_cumulative_worker(
        self, cumulative_worker: CumulativeWorker
    ) -> None:
        """Add a CumulativeWorker to the problem"""
        if cumulative_worker.name in self.cumulative_workers:
            raise ValueError(
                f"a CumulativeWorker instance with the name {cumulative_worker.name} already exists."
            )
        self.cumulative_workers[cumulative_worker.name] = cumulative_worker

    def add_constraint(self, constraint: Union[Constraint, z3.BoolRef]) -> None:
        """Add a constraint to the problem. A constraint can be either
        a z3 assertion or a processscheduler Constraint instance."""
        if isinstance(constraint, Constraint):
            if constraint not in self.constraints:
                self.constraints.append(constraint)
            else:
                raise AssertionError("constraint already added to the problem.")
        elif isinstance(constraint, z3.BoolRef):
            self.append_z3_assertion(
                constraint
            )  # self.z3_assertions.append(constraint)
        else:
            raise TypeError(
                "You must provide either a _Constraint or z3.BoolRef instance."
            )

    def add_indicator(self, indicator: Indicator) -> bool:
        """Add an indicator to the problem"""
        if indicator.name in self.indicators:
            raise ValueError(
                f"an Indicator instance with the name {indicator.name} already exists."
            )
        self.indicators[indicator.name] = indicator

    def add_objective(self, objective: Objective) -> None:
        """Add an optimization objective"""
        if objective.name in self.objectives:
            raise ValueError(
                f"an Objective instance with the name {objective.name} already exists."
            )
        self.objectives[objective.name] = objective

    def add_buffer(self, buffer: Buffer) -> None:
        """Add a single task to the problem. There must not be two tasks with the same name"""
        if buffer.name in [b.name for b in self.buffers]:
            raise ValueError(f"a buffer with the name {buffer.name} already exists.")
        self.buffers.append(buffer)

    def maximize_indicator(self, indicator: Indicator) -> MaximizeObjective:
        """Maximize indicator"""
        return MaximizeObjective(name="CustomizedMaximizeIndicator", target=indicator)

    def minimize_indicator(self, indicator: Indicator) -> MinimizeObjective:
        """Minimize indicator"""
        return MinimizeObjective(name="CustomizedMinimizeIndicator", target=indicator)

    #
    # Optimization objectives
    #
    # def add_objective_makespan(self, weight=1) -> Union[z3.ArithRef, Indicator]:
    #     """makespan objective"""
    #     MinimizeObjective(name="MakeSpan", target=self._horizon, weight=weight)
    #     return self._horizon

    def add_objective_resource_utilization(
        self, resource: Resource, weight: int = 1
    ) -> Union[z3.ArithRef, Indicator]:
        """Maximize resource occupation."""
        resource_utilization_indicator = IndicatorResourceUtilization(resource=resource)
        MaximizeObjective(
            name="MaximizeResourceUtilization",
            target=resource_utilization_indicator,
            weight=weight,
        )
        return resource_utilization_indicator

    def add_objective_resource_cost(
        self, list_of_resources: List[Union[Worker, CumulativeWorker]], weight: int = 1
    ) -> Union[z3.ArithRef, Indicator]:
        """minimise the cost of selected resources"""
        cost_indicator = IndicatorResourceCost(list_of_resources=list_of_resources)
        MinimizeObjective(
            name="MinimizeResourceCost", target=cost_indicator, weight=weight
        )
        return cost_indicator

    def add_objective_priorities(
        self, weight: int = 1
    ) -> Union[z3.ArithRef, Indicator]:
        """optimize the solution such that all task with a higher
        priority value are scheduled before other tasks"""
        all_priorities = []
        # for task in self._context.tasks:
        for task in self.tasks.values():
            if task.optional:
                all_priorities.append(task._end * task.priority * task._scheduled)
            else:
                all_priorities.append(task._end * task.priority)
        priority_sum = z3.Sum(all_priorities)
        priority_indicator = IndicatorFromMathExpression(
            name="TotalPriority", expression=priority_sum
        )
        MinimizeObjective(
            name="MinimizePriority", target=priority_indicator, weight=weight
        )
        return priority_indicator

    def add_objective_start_latest(
        self, weight: int = 1, list_of_tasks: Union[List[Task], None] = None
    ) -> Union[z3.ArithRef, Indicator]:
        """maximize the minimum start time, i.e. all the tasks
        are scheduled as late as possible"""
        if list_of_tasks is None:
            list_of_tasks = self.tasks.values()
        mini = z3.Int("SmallestStartTime")
        smallest_start_time = IndicatorFromMathExpression(
            name="SmallestStartTime", expression=mini
        )
        smallest_start_time.append_z3_assertion(
            z3.Or([mini == task._start for task in list_of_tasks])
        )
        for tsk in list_of_tasks:
            smallest_start_time.append_z3_assertion(mini <= tsk._start)
        MaximizeObjective(name="StartLatest", target=smallest_start_time, weight=weight)
        return smallest_start_time

    def add_objective_start_earliest(
        self, weight: int = 1, list_of_tasks: Union[List[Task], None] = None
    ) -> Union[z3.ArithRef, Indicator]:
        """minimize the greatest start time, i.e. tasks are schedules
        as early as possible"""
        if list_of_tasks is None:
            list_of_tasks = self.tasks.values()
        maxi = z3.Int("GreatestStartTime")
        greatest_start_time = IndicatorFromMathExpression(
            name="GreatestStartTime", expression=maxi
        )
        greatest_start_time.append_z3_assertion(
            z3.Or([maxi == task._start for task in list_of_tasks])
        )
        for tsk in list_of_tasks:
            greatest_start_time.append_z3_assertion(maxi >= tsk._start)
        MinimizeObjective(
            name="StartEarliest", target=greatest_start_time, weight=weight
        )
        return greatest_start_time

    def add_objective_flowtime(
        self, weight: int = 1, list_of_tasks: Union[List[Task], None] = None
    ) -> Union[z3.ArithRef, Indicator]:
        """the flowtime is the sum of all ends, minimize. Be careful that
        it is contradictory with makespan"""
        if list_of_tasks is None:
            list_of_tasks = self.tasks.values()
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
        MinimizeObjective(name="Flowtime", target=flow_time, weight=weight)
        return flow_time

    def add_objective_flowtime_single_resource(
        self,
        resource: Union[Worker, CumulativeWorker],
        time_interval: Union[Tuple[int, int], None] = None,
        weight: int = 1,
    ) -> Union[z3.ArithRef, Indicator]:
        """Optimize flowtime for a single resource, for all the tasks scheduled in the
        time interval provided. Is ever no time interval is passed to the function, the
        flowtime is minimized for all the tasks scheduled in the workplan."""
        if time_interval is not None:
            lower_bound, upper_bound = time_interval
        else:
            lower_bound = 0
            upper_bound = self._horizon
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

        MinimizeObjective(
            name=f"ObjectiveFlowtimeSingleResource({resource.name}:{lower_bound}:{upper_bound})",
            target=flowtime_single_resource_indicator,
            weight=weight,
        )

        return flowtime_single_resource_indicator
