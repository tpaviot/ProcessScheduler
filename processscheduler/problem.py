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
)
from processscheduler.resource import Resource, Worker, CumulativeWorker, SelectWorkers
from processscheduler.constraint import *
from processscheduler.task_constraint import *
from processscheduler.resource_constraint import *
from processscheduler.first_order_logic import Not, Or, And, Xor, Implies, IfThenElse
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

    constraints: Dict[
        str,
        Union[
            ConstraintFromExpression,
            ForceApplyNOptionalConstraints,
            # resource constraints
            SameWorkers,
            DistinctWorkers,
            WorkLoad,
            ResourceUnavailable,
            ResourceTasksDistance,
            # tasks constraints
            TaskGroup,
            UnorderedTaskGroup,
            OrderedTaskGroup,
            TaskPrecedence,
            TasksStartSynced,
            TasksEndSynced,
            TasksDontOverlap,
            TasksContiguous,
            TaskStartAt,
            TaskStartAfter,
            TaskEndAt,
            TaskEndBefore,
            OptionalTaskConditionSchedule,
            OptionalTasksDependency,
            ForceScheduleNOptionalTasks,
            ScheduleNTasksInTimeIntervals,
            # task buffers
            TaskUnloadBuffer,
            TaskLoadBuffer,
            # first order logic constraints
            Not,
            Or,
            And,
            Xor,
            Implies,
            IfThenElse,
        ],
    ] = Field(default={})

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
            self.append_z3_assertion(self._horizon <= self.horizon)

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

    def add_constraint(self, constraint: Constraint) -> None:
        """Add a constraint to the problem. A constraint can be either
        a z3 assertion or a processscheduler Constraint instance."""
        if constraint.name in self.constraints:
            raise ValueError(
                f"a Constraint instance with the name {constraint.name} already exists."
            )
        self.constraints[constraint.name] = constraint

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
