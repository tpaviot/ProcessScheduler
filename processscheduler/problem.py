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
import json
import uuid
from typing import List, Union, Any, Tuple

from pydantic import Field, PositiveInt

from z3 import And, BoolRef, If, Int, Or, Sum, Implies, ArithRef

from processscheduler.base import NamedUIDObject
import processscheduler.base
from processscheduler.task import (
    Task,
    FixedDurationTask,
    ZeroDurationTask,
    VariableDurationTask,
)
from processscheduler.cost import ConstantCostPerPeriod, PolynomialCostFunction
from processscheduler.objective import (
    Indicator,
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

    horizon: Union[PositiveInt, ArithRef] = Field(default=None)
    delta_time: timedelta = Field(default=None)
    start_time: datetime = Field(default=None)
    end_time: datetime = Field(default=None)

    tasks: List[
        Union[FixedDurationTask, VariableDurationTask, ZeroDurationTask]
    ] = Field(default=[])
    workers: List[Worker] = Field(default=[])
    select_workers: List[SelectWorkers] = Field(default=[])
    cumulative_workers: List[CumulativeWorker] = Field(default=[])
    constraints: List[Constraint] = Field(default=[])
    # z3_assertions: List[BoolRef]=Field(default=[])
    indicators: List[Indicator] = Field(default=[])
    objectives: List[Union[Indicator, ArithRef]] = Field(default=[])
    buffers: List[Buffer] = Field(default=[])

    def __init__(self, **data) -> None:
        super().__init__(**data)

        # the active problem, where all will be stored
        processscheduler.base.active_problem = self

        # define the horizon variable
        self._horizon = Int("horizon")
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
        # first find the class to instanciate
        s_type = s["type"]
        if not s_type in _object_types:
            raise AssertionError(f"{s_type} type not known")

        # create and return the object
        return _object_types[s_type].model_validate_json(json_string)

    def add_indicator(self, indicator: Indicator) -> bool:
        """Add an indicatr to the problem"""
        if indicator not in self.indicators:
            self.indicators.append(indicator)
        else:
            warnings.warn(f"indicator {indicator} already part of the problem")
            return False
        return True

    def add_task(self, task: Task) -> int:
        """Add a single task to the problem. There must not be two tasks with the same name"""
        if task.name in [t.name for t in self.tasks]:
            raise ValueError(f"a task with the name {task.name} already exists.")
        self.tasks.append(task)
        return len(self.tasks)

    def add_resource_worker(self, worker: Worker) -> None:
        """Add a single resource to the problem"""
        if worker.name in [t.name for t in self.workers]:
            raise ValueError(f"a worker with the name {worker.name} already exists.")
        self.workers.append(worker)

    def add_resource_select_workers(self, resource: SelectWorkers) -> None:
        """Add a single resource to the problem"""
        self.select_workers.append(resource)

    def add_resource_cumulative_worker(self, resource: CumulativeWorker) -> None:
        """Add a single resource to the problem"""
        self.cumulative_workers.append(resource)

    def add_constraint(self, constraint: Constraint) -> None:
        """Add a constraint to the problem. A constraint can be either
        a z3 assertion or a processscheduler Constraint instance."""
        if isinstance(constraint, Constraint):
            if constraint not in self.constraints:
                self.constraints.append(constraint)
            else:
                raise AssertionError("constraint already added to the problem.")
        elif isinstance(constraint, BoolRef):
            self.append_z3_assertion(
                constraint
            )  # self.z3_assertions.append(constraint)
        else:
            raise TypeError(
                "You must provide either a _Constraint or BoolRef instance."
            )

    def add_objective(self, objective: Objective) -> None:
        """Add an optimization objective"""
        self.objectives.append(objective)

    def add_buffer(self, buffer: Buffer) -> None:
        """Add a single task to the problem. There must not be two tasks with the same name"""
        if buffer.name in [b.name for b in self.buffers]:
            raise ValueError(f"a buffer with the name {buffer.name} already exists.")
        self.buffers.append(buffer)

    def add_indicator_number_tasks_assigned(self, resource: Resource):
        """compute the number of tasks as resource is assigned"""
        # this list contains
        scheduled_tasks = [
            If(start > -1, 1, 0) for start, end in resource._busy_intervals.values()
        ]

        nb_tasks_assigned_indicator_variable = Sum(scheduled_tasks)
        return Indicator(
            name=f"Nb Tasks Assigned ({resource.name})",
            expression=nb_tasks_assigned_indicator_variable,
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

            for interv_low, interv_up in res._busy_intervals.values():
                # Constant cost per period
                if isinstance(res.cost, ConstantCostPerPeriod):
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
                for res in resource._cumulative_workers:
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
            name=f"Total Cost ({resource_names})", expression=cost_indicator_variable
        )
        return cost_indicator

    def add_indicator_resource_utilization(self, resource: Resource) -> Indicator:
        """Compute the total utilization of a single resource.

        The percentage is rounded to an int value.
        """
        durations = [
            interv_up - interv_low
            for interv_low, interv_up in resource._busy_intervals.values()
        ]
        if self.horizon is not None:
            utilization = Sum(durations) * int(100 / self.horizon)
        else:
            utilization = (Sum(durations) * 100) / self._horizon  # in percentage
        return Indicator(
            name=f"Utilization ({resource.name})",
            expression=utilization,
            bounds=(0, 100),
        )

    def maximize_indicator(self, indicator: Indicator) -> MaximizeObjective:
        """Maximize indicator"""
        return MaximizeObjective(name="CustomizedMaximizeIndicator", target=indicator)

    def minimize_indicator(self, indicator: Indicator) -> MinimizeObjective:
        """Minimize indicator"""
        return MinimizeObjective(name="CustomizedMinimizeIndicator", target=indicator)

    #
    # Optimization objectives
    #
    def add_objective_makespan(self, weight=1) -> Union[ArithRef, Indicator]:
        """makespan objective"""
        MinimizeObjective(name="MakeSpan", target=self._horizon, weight=weight)
        return self._horizon

    def add_objective_resource_utilization(
        self, resource: Resource, weight: int = 1
    ) -> Union[ArithRef, Indicator]:
        """Maximize resource occupation."""
        resource_utilization_indicator = self.add_indicator_resource_utilization(
            resource
        )
        MaximizeObjective(
            name="MaximizeResourceUtilization",
            target=resource_utilization_indicator,
            weight=weight,
        )
        return resource_utilization_indicator

    def add_objective_resource_cost(
        self, list_of_resources: List[Resource], weight: int = 1
    ) -> Union[ArithRef, Indicator]:
        """minimise the cost of selected resources"""
        cost_indicator = self.add_indicator_resource_cost(list_of_resources)
        MinimizeObjective(
            name="MinimizeResourceCost", target=cost_indicator, weight=weight
        )
        return cost_indicator

    def add_objective_priorities(self, weight: int = 1) -> Union[ArithRef, Indicator]:
        """optimize the solution such that all task with a higher
        priority value are scheduled before other tasks"""
        all_priorities = []
        # for task in self._context.tasks:
        for task in self.tasks:
            if task.optional:
                all_priorities.append(task._end * task.priority * task._scheduled)
            else:
                all_priorities.append(task._end * task.priority)
        priority_sum = Sum(all_priorities)
        priority_indicator = Indicator(name="TotalPriority", expression=priority_sum)
        MinimizeObjective(
            name="MinimizePriority", target=priority_indicator, weight=weight
        )
        return priority_indicator

    def add_objective_start_latest(
        self, weight: int = 1, list_of_tasks: Union[List[Task], None] = None
    ) -> Union[ArithRef, Indicator]:
        """maximize the minimum start time, i.e. all the tasks
        are scheduled as late as possible"""
        if list_of_tasks is None:
            list_of_tasks = self.tasks
        mini = Int("SmallestStartTime")
        smallest_start_time = Indicator(name="SmallestStartTime", expression=mini)
        smallest_start_time.append_z3_assertion(
            Or([mini == task._start for task in list_of_tasks])
        )
        for tsk in list_of_tasks:
            smallest_start_time.append_z3_assertion(mini <= tsk._start)
        MaximizeObjective(name="StartLatest", target=smallest_start_time, weight=weight)
        return smallest_start_time

    def add_objective_start_earliest(
        self, weight: int = 1, list_of_tasks: Union[List[Task], None] = None
    ) -> Union[ArithRef, Indicator]:
        """minimize the greatest start time, i.e. tasks are schedules
        as early as possible"""
        if list_of_tasks is None:
            list_of_tasks = self.tasks
        maxi = Int("GreatestStartTime")
        greatest_start_time = Indicator(name="GreatestStartTime", expression=maxi)
        greatest_start_time.append_z3_assertion(
            Or([maxi == task._start for task in list_of_tasks])
        )
        for tsk in list_of_tasks:
            greatest_start_time.append_z3_assertion(maxi >= tsk._start)
        MinimizeObjective(
            name="StartEarliest", target=greatest_start_time, weight=weight
        )
        return greatest_start_time

    def add_objective_flowtime(
        self, weight: int = 1, list_of_tasks: Union[List[Task], None] = None
    ) -> Union[ArithRef, Indicator]:
        """the flowtime is the sum of all ends, minimize. Be carful that
        it is contradictory with makespan"""
        if list_of_tasks is None:
            list_of_tasks = self.tasks
        task_ends = []
        for task in list_of_tasks:
            if task.optional:
                task_ends.append(task._end * task._scheduled)
            else:
                task_ends.append(task._end)
        flow_time_expr = Sum(task_ends)
        flow_time = Indicator(name="Flowtime", expression=flow_time_expr)
        MinimizeObjective(name="Flowtime", target=flow_time, weight=weight)
        return flow_time

    def add_objective_flowtime_single_resource(
        self,
        resource: Union[Worker, CumulativeWorker],
        time_interval: Union[Tuple[int, int], None] = None,
        weight: int = 1,
    ) -> Union[ArithRef, Indicator]:
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
        flowtime = Int(f"FlowtimeSingleResource{resource.name}_{uid}")

        flowtime_single_resource_indicator = Indicator(
            name=f"FlowTime({resource.name}:{lower_bound}:{upper_bound})",
            expression=flowtime,
        )
        # find the max end time in the time_interval
        maxi = Int(f"GreatestTaskEndTimeInTimePeriodForResource{resource.name}_{uid}")

        asst_max = [
            Implies(
                And(task._end <= upper_bound, task._start >= lower_bound),
                maxi == task._end,
            )
            for task in resource._busy_intervals
        ]
        flowtime_single_resource_indicator.append_z3_assertion(Or(asst_max))
        for task in resource._busy_intervals:
            flowtime_single_resource_indicator.append_z3_assertion(
                Implies(
                    And(task._end <= upper_bound, task._start >= lower_bound),
                    maxi >= task._end,
                )
            )

        # and the mini
        mini = Int(f"SmallestTaskEndTimeInTimePeriodForResource{resource.name}_{uid}")

        asst_min = [
            Implies(
                And(task._end <= upper_bound, task._start <= lower_bound),
                mini == task._start,
            )
            for task in resource._busy_intervals
        ]
        flowtime_single_resource_indicator.append_z3_assertion(Or(asst_min))
        for task in resource._busy_intervals:
            flowtime_single_resource_indicator.append_z3_assertion(
                Implies(
                    And(task._end <= upper_bound, task._start >= lower_bound),
                    mini <= task._start,
                )
            )

        # the quantity to optimize
        flowtime_single_resource_indicator.append_z3_assertion(flowtime == maxi - mini)
        flowtime_single_resource_indicator.append_z3_assertion(flowtime >= 0)

        MinimizeObjective(
            name="FlowtimeSingleResource",
            target=flowtime_single_resource_indicator,
            weight=weight,
        )
        return flowtime_single_resource_indicator
