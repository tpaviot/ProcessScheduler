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

from typing import List, Union, Literal

from pydantic import Field, PositiveInt, StrictBool

import z3

from processscheduler.base import NamedUIDObject
from processscheduler.resource import Resource, Worker, CumulativeWorker, SelectWorkers
import processscheduler.base


class Task(NamedUIDObject):
    """
    Base class representing tasks in an industrial scheduling system.

    Attributes:
        optional (StrictBool): Indicates whether the task is optional for scheduling optimization. When set to True, the scheduling algorithm may explore options to skip or reschedule this task. Defaults to False.

        work_amount (int): The amount of work associated with this task. This could represent processing time, workload, or other relevant metrics. Must be a non-negative integer. Defaults to 0.

        release_date (int): The release date of the task. This date signifies the earliest time the task can begin processing. Represented as a timestamp or date. Defaults to None, allowing for immediate processing upon scheduling.

        due_date (int) :
        priority (int): The priority of the task in the scheduling queue, aligning with concepts discussed by Michael Pinedo. Higher values indicate higher priority, making the task more critical in the scheduling process. Must be a non-negative integer. Defaults to 0.

    Note:
        - Tasks with higher priority values take precedence in scheduling.
        - A release date of None implies the task can start processing immediately upon scheduling.
        - The 'optional' flag, when set to True, allows the scheduling algorithm flexibility in handling the task for optimization purposes.
    """

    optional: StrictBool = Field(
        default=False, description="Whether or not the solver must schedule this task."
    )
    work_amount: int = Field(
        default=0,
        ge=0,
        description="The quantity of work that has to be done by this job.",
    )
    release_date: Union[int, None] = Field(
        default=None,
        description="The ready date, i.e. the earliest time the task can start its processing.",
    )
    due_date: Union[int, None] = Field(
        default=None,
        description="completion date (i.e., the date the job is promised to the customer). Completion of a job after its due date is allowed, but then a penalty is incurred. When a due date must be met it is referred to as a deadline",
    )
    due_date_is_deadline: StrictBool = Field(
        default=True,
        description="Due date is a deadline by default (scheduling after the deadline is not allowed. If False, a penalty function is used.",
    )
    priority: int = Field(
        default=1,
        ge=0,
        description="The priority of the task. The higher this parameter, the sooner the task is scheduled.",
    )

    def __init__(self, **data) -> None:
        super().__init__(**data)

        # workers required to process the task
        self._required_resources = (
            []
        )  # type: List[Union[Worker, CumulativeWorker, SelectWorkers]]

        # z3 Int variables
        self._start = z3.Int(f"{self.name}_start")  # type: z3.ArithRef
        self._end = z3.Int(f"{self.name}_end")  # type: z3.ArithRef

        # by default, the task is mandatory
        self._scheduled = True  # type: Union[bool, z3.BoolRef]

        # add this task to the current context
        if processscheduler.base.active_problem is None:
            raise AssertionError("No active problem. First create a SchedulingProblem")
        # the task_number is an integer that is incremented each time
        # a task is created. The first task has number 1, the second number 2 etc.
        self._task_number = processscheduler.base.active_problem.add_task(
            self
        )  # type: int

        # the release date
        if self.release_date is not None:
            if self.release_date > 0:  # other wise redundant constraint
                self.append_z3_assertion(self._start >= self.release_date)

        # the due date
        if self.due_date is not None:
            # two cases, if the dure_date is a deadline (True by default):
            if self.due_date_is_deadline:
                self.append_z3_assertion(self._end <= self.due_date)
            # TODO: Should implement a penalty function if the due_date can be delayed

    def add_required_resource(
        self, resource: Resource, dynamic=False, delay_in=0, early_out=0
    ) -> None:
        """
        Add a required resource to the current task.

        Args:
            resource: any of one of the Resource derivatives class (Worker, SelectWorkers etc.)
        z3.If dynamic flag (False by default) is set to True, then the resource is dynamic
        and can join the task any time between its start and end times.
        """
        if not isinstance(resource, Resource):
            raise TypeError("you must pass a Resource instance")

        if resource in self._required_resources:
            raise ValueError(
                f"resource {resource.name} already defined as a required resource for task {self.name}"
            )

        if isinstance(resource, CumulativeWorker):
            # in the case for a CumulativeWorker, select at least one worker
            resource = resource.get_select_workers()

        if isinstance(resource, SelectWorkers):
            # loop over each resource
            for worker in resource.list_of_workers:
                resource_maybe_busy_start = z3.Int(
                    f"{worker.name}_maybe_busy_{self.name}_start"
                )
                resource_maybe_busy_end = z3.Int(
                    f"{worker.name}_maybe_busy_{self.name}_end"
                )
                # create the busy interval for the resource
                worker.add_busy_interval(
                    self, (resource_maybe_busy_start, resource_maybe_busy_end)
                )
                # add assertions. z3.If worker is selected then sync the resource with the task
                selected_variable = resource._selection_dict[worker]
                schedule_as_usual = z3.And(
                    resource_maybe_busy_start == self._start,
                    resource_maybe_busy_end == self._end,
                )
                # in the case the worker is selected
                # move the busy interval to a single point in time, in the
                # past. This way, it does not conflict with tasks to be
                # actually scheduled.
                # This single point in time results in a zero duration time: related
                # task will not be considered when computing resource utilization or cost.
                single_point_in_past = (
                    processscheduler.base.active_problem.get_unique_negative_integer()
                )
                move_to_past = z3.And(
                    resource_maybe_busy_start == single_point_in_past,  # to past
                    resource_maybe_busy_end == single_point_in_past,
                )
                # define the assertion ...
                assertion = z3.If(selected_variable, schedule_as_usual, move_to_past)
                # ... and store it into the task assertions list
                self.append_z3_assertion(assertion)
                # finally, add each worker to the "required" resource list
                self._required_resources.append(worker)
            # also, don't forget to add the AlternativeWorker assertion
            self.append_z3_assertion(resource._selection_assertion)
        elif isinstance(resource, Worker):
            resource_busy_start = z3.Int(f"{resource.name}_busy_{self.name}_start")
            resource_busy_end = z3.Int(f"{resource.name}_busy_{self.name}_end")
            # create the busy interval for the resource
            resource.add_busy_interval(self, (resource_busy_start, resource_busy_end))
            # set the busy resource to keep synced with the task
            if dynamic:
                self.append_z3_assertion(resource_busy_end <= self._end)
                self.append_z3_assertion(resource_busy_start >= self._start)
            else:
                if early_out > 0:
                    self.append_z3_assertion(resource_busy_end == self._end - early_out)
                else:
                    self.append_z3_assertion(resource_busy_end == self._end)
                if delay_in > 0:
                    self.append_z3_assertion(
                        resource_busy_start == self._start + delay_in
                    )
                else:
                    self.append_z3_assertion(resource_busy_start == self._start)
            # finally, store this resource into the resource list
            self._required_resources.append(resource)

    def add_required_resources(
        self,
        list_of_resources: List[Union[Worker, CumulativeWorker, SelectWorkers]],
        dynamic=False,
    ) -> None:
        """
        Add a set of required resources to the current task.

        This method calls the add_required_resource method for each resource of the list.
        As a consequence, be aware this is not an atomic transaction.

        Args:
            list_of_resources: the list of resources to add.
        """
        for resource in list_of_resources:
            self.add_required_resource(resource, dynamic)

    def set_assertions(self, list_of_z3_assertions: List[z3.BoolRef]) -> None:
        """Take a list of constraint to satisfy. Create two cases: if the task is scheduled,
        nothing is done; if the task is optional, move task to the past"""
        if self.optional:  # in this case the previous assertions maybe skipped
            self._scheduled = z3.Bool(f"{self.name}_scheduled")
            # the first task is moved to -1, the second to -2
            # etc.
            point_in_past = -self._task_number
            if isinstance(self, VariableDurationTask):
                not_scheduled_assertion = z3.And(
                    self._start == point_in_past,  # to past
                    self._end == point_in_past,  # to past
                    self._duration == 0,
                )
            else:
                not_scheduled_assertion = z3.And(
                    self._start == point_in_past,  # to past
                    self._end == point_in_past,  # to past
                )
            self.append_z3_assertion(
                z3.If(
                    self._scheduled,
                    z3.And(list_of_z3_assertions),
                    not_scheduled_assertion,
                )
            )
        else:
            for asst in list_of_z3_assertions:
                self.append_z3_assertion(asst)


class ZeroDurationTask(Task):
    duration: Literal[0] = 0

    def __init__(self, **data) -> None:
        super().__init__(**data)
        # add an assertion: end = start because the duration is zero
        self.append_z3_assertion(self._start == self._end)


class FixedDurationTask(Task):
    """Task with constant duration.

    Args:
        name: the task name. It must be unique
        duration: the task duration as a number of periods
        work_amount: represent the quantity of work this task must produce
        priority: the task priority. The greater the priority, the sooner it will be scheduled
        optional: True if task schedule is optional, False otherwise (default)
    """

    duration: PositiveInt

    def __init__(self, **data) -> None:
        super().__init__(**data)
        assertions = [
            self._end - self._start == self.duration,
            self._start >= 0,
        ]

        self.set_assertions(assertions)


class VariableDurationTask(Task):
    """The duration can take any value, computed by the solver."""

    min_duration: int = Field(default=0, ge=0)
    max_duration: Union[PositiveInt, None] = Field(default=None)
    allowed_durations: Union[List[PositiveInt], None] = Field(default=None)

    def __init__(self, **data) -> None:
        super().__init__(**data)

        self._duration = z3.Int(f"{self.name}_duration")  # type: z3.ArithRef

        assertions = [
            self._start + self._duration == self._end,
            self._start >= 0,
            self._duration >= self.min_duration,
        ]

        if self.allowed_durations is not None:
            all_cstr = [
                self._duration == duration for duration in self.allowed_durations
            ]
            assertions.append(z3.Or(all_cstr))

        if self.max_duration is not None:
            assertions.append(self._duration <= self.max_duration)

        self.set_assertions(assertions)
