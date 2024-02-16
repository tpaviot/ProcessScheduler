"""Resource constraints and related classes."""

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

from typing import Literal, Union, Dict, Tuple, List
import uuid

import z3

from pydantic import Field

from processscheduler.resource import Worker, CumulativeWorker, SelectWorkers
from processscheduler.constraint import ResourceConstraint
from processscheduler.util import sort_no_duplicates
from processscheduler.task import (
    VariableDurationTask,
    FixedDurationInterruptibleTask,
    Task,
)


class WorkLoad(ResourceConstraint):
    """
    A WorkLoad constraint restricts the number of tasks that can be executed on a resource
    during a certain time period. The resource can be a single Worker or a CumulativeWorker.

    Parameters:
    - resource: The resource for which the workload constraint is defined.
    - dict_time_intervals_and_bound: A dictionary that maps interval tuples to integer bounds.
      For example, {(1,20):6, (50,60):2} specifies that the resource can use no more than 6 slots
      in the interval (1,20), and no more than 2 slots in the interval (50,60).
    - kind (str, optional): Specifies whether the constraint is exact, a minimum, or a maximum (default is "max").
    - optional (bool, optional): Whether the constraint is optional (default is False).
    """

    resource: Union[Worker, CumulativeWorker]
    dict_time_intervals_and_bound: Dict[Tuple[int, int], int]
    kind: Literal["exact", "max", "min"] = Field(default="max")

    def __init__(self, **data) -> None:
        """
        Initialize a WorkLoad constraint.

        :param resource: The resource for which the workload constraint is defined.
        :param dict_time_intervals_and_bound: A dictionary that maps interval tuples to integer bounds.
          For example, {(1,20):6, (50,60):2} specifies that the resource can use no more than 6 slots
          in the interval (1,20), and no more than 2 slots in the interval (50,60).
        :param kind: Specifies whether the constraint is exact, a minimum, or a maximum (default is "max").
        :param optional: Whether the constraint is optional (default is False).
        """
        super().__init__(**data)

        if isinstance(self.resource, Worker):
            workers = [self.resource]
        elif isinstance(self.resource, CumulativeWorker):
            workers = self.resource._cumulative_workers

        resource_assigned = False

        for time_interval in self.dict_time_intervals_and_bound:
            number_of_time_slots = self.dict_time_intervals_and_bound[time_interval]

            time_interval_lower_bound, time_interval_upper_bound = time_interval

            durations = []

            for worker in workers:
                # for this task, the logic expression is that any of its start or end must be
                # between two consecutive intervals
                for start_task_i, end_task_i in worker.get_busy_intervals():
                    resource_assigned = True
                    # this variable allows to compute the occupation
                    # of the resource during the time interval
                    dur = z3.Int(
                        f"Overlap_{time_interval_lower_bound}_{time_interval_upper_bound}_{uuid.uuid4().hex[:8]}"
                    )
                    # prevent solutions where duration would be negative
                    self.set_z3_assertions(dur >= 0)
                    # 4 different cases to take into account
                    cond1 = z3.And(
                        start_task_i >= time_interval_lower_bound,
                        end_task_i <= time_interval_upper_bound,
                    )
                    asst1 = z3.Implies(cond1, dur == end_task_i - start_task_i)
                    self.set_z3_assertions(asst1)
                    # overlap at lower bound
                    cond2 = z3.And(
                        start_task_i < time_interval_lower_bound,
                        end_task_i > time_interval_lower_bound,
                    )
                    asst2 = z3.Implies(
                        cond2, dur == end_task_i - time_interval_lower_bound
                    )
                    self.set_z3_assertions(asst2)
                    # overlap at upper bound
                    cond3 = z3.And(
                        start_task_i < time_interval_upper_bound,
                        end_task_i > time_interval_upper_bound,
                    )
                    asst3 = z3.Implies(
                        cond3, dur == time_interval_upper_bound - start_task_i
                    )
                    self.set_z3_assertions(asst3)
                    # all overlap
                    cond4 = z3.And(
                        start_task_i < time_interval_lower_bound,
                        end_task_i > time_interval_upper_bound,
                    )
                    asst4 = z3.Implies(
                        cond4,
                        dur == time_interval_upper_bound - time_interval_lower_bound,
                    )
                    self.set_z3_assertions(asst4)

                    # make these constraints mutual: no overlap
                    self.set_z3_assertions(
                        z3.Implies(
                            z3.Not(z3.Or([cond1, cond2, cond3, cond4])), dur == 0
                        )
                    )

                    # finally, store this variable in the duratins list
                    durations.append(dur)

            if not resource_assigned:
                raise AssertionError(
                    "The resource is not assigned to any task. Please first assign the resource to one or more tasks, and then add the WorkLoad constraint."
                )

            # workload constraint depends on the kind
            if self.kind == "exact":
                workload_constraint = z3.Sum(durations) == number_of_time_slots
            elif self.kind == "max":
                workload_constraint = z3.Sum(durations) <= number_of_time_slots
            elif self.kind == "min":
                workload_constraint = z3.Sum(durations) >= number_of_time_slots

            self.set_z3_assertions(workload_constraint)


class ResourceUnavailable(ResourceConstraint):
    """
    This constraint sets the unavailability of a resource in terms of time intervals.

    Parameters:
    - resource: The resource for which unavailability is defined.
    - list_of_time_intervals: A list of time intervals during which the resource is unavailable for any task.
      For example, [(0, 2), (5, 8)] represents time intervals from 0 to 2 and from 5 to 8.
    - optional (bool, optional): Whether the constraint is optional (default is False).
    """

    resource: Union[Worker, CumulativeWorker]
    list_of_time_intervals: List[Tuple[int, int]]

    def __init__(self, **data) -> None:
        """
        Initialize a ResourceUnavailable constraint.

        :param resource: The resource for which unavailability is defined.
        :param list_of_time_intervals: A list of time intervals during which the resource is unavailable for any task.
          For example, [(0, 2), (5, 8)] represents time intervals from 0 to 2 and from 5 to 8.
        :param optional: Whether the constraint is optional (default is False).
        """
        super().__init__(**data)

        # for each interval we create a task 'UnavailableResource%i'
        if isinstance(self.resource, Worker):
            workers = [self.resource]
        elif isinstance(self.resource, CumulativeWorker):
            workers = self.resource._cumulative_workers

        resource_assigned = False

        for interval_lower_bound, interval_upper_bound in self.list_of_time_intervals:
            # add constraints on each busy interval
            for worker in workers:
                for start_task_i, end_task_i in worker.get_busy_intervals():
                    resource_assigned = True
                    self.set_z3_assertions(
                        z3.Or(
                            start_task_i >= interval_upper_bound,
                            end_task_i <= interval_lower_bound,
                        )
                    )

        if not resource_assigned:
            raise AssertionError(
                "The resource is not assigned to any task. Please first assign the resource to one or more tasks, and then add the ResourceUnavailable constraint."
            )


class ResourcePeriodicallyUnavailable(ResourceConstraint):
    """
    This constraint sets the unavailability of a resource in terms of time intervals in one period.

    Parameters:
    - resource: The resource for which unavailability is defined.
    - list_of_time_intervals: A list of time intervals *in one period* during which the resource is unavailable for any task.
      For example, [(0, 2), (5, 8)] represents time intervals from 0 to 2 and from 5 to 8 in one period.
    - period: The length of one period after which to repeat the list of time intervals.
      For example, setting this to 5 with [(2, 4)] gives unavailabilities at (2, 4), (7, 9), (12, 14), ...
    - start: The start after which repeating the list of time intervals is active (default is 0).
    - offset: The shift of the repeated list of time intervals (default is 0).
      It might be desired to set also the start parameter to the same value, as otherwise the pattern shifts in from the left or the right into the schedule.
    - end: The end until which repeating the list of time intervals is activate (default is None).
    - optional (bool, optional): Whether the constraint is optional (default is False).
    """

    resource: Union[Worker, CumulativeWorker]
    list_of_time_intervals: List[Tuple[int, int]]
    period: int
    start: int = 0
    offset: int = 0
    end: Union[int, None] = None

    def __init__(self, **data):
        """
        Initialize a ResourceUnavailable constraint.

        :param resource: The resource for which unavailability is defined.
        :param list_of_time_intervals: A list of time intervals *in one period* during which the resource is unavailable for any task.
          For example, [(0, 2), (5, 8)] represents time intervals from 0 to 2 and from 5 to 8.
        :param period: The length of one period after which to repeat the list of time intervals.
          For example, setting this to 5 with [(2, 4)] gives unavailabilities at (2, 4), (7, 9), (12, 14), ...
        :param start: The start after which repeating the list of time intervals is active (default is 0).
        :param offset: The shift of the repeated list of time intervals (default is 0).
          It might be desired to set also the start parameter to the same value, as otherwise the pattern shifts in from the left or the right into the schedule.
        :param end: The end until which repeating the list of time intervals is activate (default is None).
        :param optional: Whether the constraint is optional (default is False).
        """
        super().__init__(**data)

        if isinstance(self.resource, Worker):
            workers = [self.resource]
        elif isinstance(self.resource, CumulativeWorker):
            workers = self.resource._cumulative_workers

        resource_assigned = False

        for interval_lower_bound, interval_upper_bound in self.list_of_time_intervals:
            for worker in workers:
                for start_task_i, end_task_i in worker.get_busy_intervals():
                    resource_assigned = True
                    duration = end_task_i - start_task_i
                    conds = [
                        z3.Xor(
                            (start_task_i - self.offset) % self.period
                            >= interval_upper_bound,
                            (start_task_i - self.offset) % self.period + duration
                            <= interval_lower_bound,
                        )
                    ]

                    if self.start > 0:
                        conds.append(end_task_i <= self.start)
                    if self.end is not None:
                        conds.append(start_task_i >= self.end)

                    if len(conds) > 1:
                        self.set_z3_assertions(z3.Or(*conds))
                    else:
                        self.set_z3_assertions(*conds)

        if not resource_assigned:
            raise AssertionError(
                "The resource is not assigned to any task. Please first assign the resource to one or more tasks, and then add the ResourcePeriodicallyUnavailable constraint."
            )


class ResourceInterrupted(ResourceConstraint):
    """
    This constraint sets the interrupts of a resource in terms of time intervals.

    Parameters:
    - resource: The resource for which interrupts are defined.
    - list_of_time_intervals: A list of time intervals during which the resource is interrupting any task.
      For example, [(0, 2), (5, 8)] represents time intervals from 0 to 2 and from 5 to 8.
    - optional (bool, optional): Whether the constraint is optional (default is False).
    """

    resource: Union[Worker, CumulativeWorker]
    list_of_time_intervals: List[Tuple[int, int]]

    def __init__(self, **data) -> None:
        """
        Initialize a ResourceInterrupted constraint.

        :param resource: The resource for which interrupts are defined.
        :param list_of_time_intervals: A list of time intervals during which the resource is interrupting any task.
          For example, [(0, 2), (5, 8)] represents time intervals from 0 to 2 and from 5 to 8.
        :param optional: Whether the constraint is optional (default is False).
        """
        super().__init__(**data)

        if isinstance(self.resource, Worker):
            workers = [self.resource]
        elif isinstance(self.resource, CumulativeWorker):
            workers = self.resource._cumulative_workers

        resource_assigned = False

        for worker in workers:
            conds = []
            for task, (start_task_i, end_task_i) in worker._busy_intervals.items():
                resource_assigned = True
                overlaps = []

                is_interruptible = isinstance(task, VariableDurationTask)
                is_fixed_interruptible = isinstance(
                    task, FixedDurationInterruptibleTask
                )

                for (
                    interval_lower_bound,
                    interval_upper_bound,
                ) in self.list_of_time_intervals:
                    overlap_condition = z3.Not(
                        z3.Xor(
                            start_task_i >= interval_upper_bound,
                            end_task_i <= interval_lower_bound,
                        )
                    )
                    overlap = z3.If(
                        overlap_condition,
                        interval_upper_bound - interval_lower_bound,
                        0,
                    )
                    overlaps.append(overlap)

                    if is_interruptible:
                        # just make sure that the task does not start or end within the time interval...
                        conds.extend(
                            [
                                z3.Xor(
                                    start_task_i < interval_lower_bound,
                                    start_task_i >= interval_upper_bound,
                                ),
                                z3.Xor(
                                    end_task_i <= interval_lower_bound,
                                    end_task_i > interval_upper_bound,
                                ),
                            ]
                        )
                    else:
                        # ...otherwise make sure the task does not overlap with the time interval
                        conds.append(
                            z3.Xor(
                                start_task_i >= interval_upper_bound,
                                end_task_i <= interval_lower_bound,
                            )
                        )

                if is_interruptible:
                    # add assertions for task duration based on the total count of overlapped periods
                    total_overlap = z3.Sum(*overlaps)
                    conds.append(task._duration >= task.min_duration + total_overlap)
                    if task.max_duration is not None:
                        conds.append(
                            task._duration <= task.max_duration + total_overlap
                        )
                elif is_fixed_interruptible:
                    total_overlap = z3.Sum(*overlaps)
                    conds.append(task._overlap == total_overlap)

            # TODO: remove AND, as the solver does that anyways?
            self.set_z3_assertions(z3.And(*conds))

        if not resource_assigned:
            raise AssertionError(
                "The resource is not assigned to any task. Please first assign the resource to one or more tasks, and then add the ResourceInterrupted constraint."
            )


class ResourcePeriodicallyInterrupted(ResourceConstraint):
    """
    This constraint sets the interrupts of a resource in terms of time intervals.

    Parameters:
    - resource: The resource for which interrupts are defined.
    - list_of_time_intervals: A list of time intervals during which the resource is interrupting any task.
      For example, [(0, 2), (5, 8)] represents time intervals from 0 to 2 and from 5 to 8.
    - optional (bool, optional): Whether the constraint is optional (default is False).
    - period: The length of one period after which to repeat the list of time intervals.
      For example, setting this to 5 with [(2, 4)] gives unavailabilities at (2, 4), (7, 9), (12, 14), ...
    - start: The start after which repeating the list of time intervals is active (default is 0).
    - offset: The shift of the repeated list of time intervals (default is 0).
      It might be desired to set also the start parameter to the same value, as otherwise the pattern shifts in from the left or the right into the schedule.
    - end: The end until which repeating the list of time intervals is activate (default is None).
    - optional (bool, optional): Whether the constraint is optional (default is False).
    """

    resource: Union[Worker, CumulativeWorker]
    list_of_time_intervals: List[Tuple[int, int]]
    period: int
    start: int = 0
    offset: int = 0
    end: Union[int, None] = None

    def __init__(self, **data) -> None:
        """
        Initialize a ResourceInterrupted constraint.

        :param resource: The resource for which interrupts are defined.
        :param list_of_time_intervals: A list of time intervals during which the resource is interrupting any task.
          For example, [(0, 2), (5, 8)] represents time intervals from 0 to 2 and from 5 to 8.
        :param optional: Whether the constraint is optional (default is False).
        :param period: The length of one period after which to repeat the list of time intervals.
          For example, setting this to 5 with [(2, 4)] gives unavailabilities at (2, 4), (7, 9), (12, 14), ...
        :param start: The start after which repeating the list of time intervals is active (default is 0).
        :param offset: The shift of the repeated list of time intervals (default is 0).
          It might be desired to set also the start parameter to the same value, as otherwise the pattern shifts in from the left or the right into the schedule.
        :param end: The end until which repeating the list of time intervals is activate (default is None).
        :param optional: Whether the constraint is optional (default is False).
        """
        super().__init__(**data)

        if isinstance(self.resource, Worker):
            workers = [self.resource]
        elif isinstance(self.resource, CumulativeWorker):
            workers = self.resource._cumulative_workers

        resource_assigned = False

        for worker in workers:
            conds = []
            for task, (start_task_i, end_task_i) in worker._busy_intervals.items():
                resource_assigned = True
                overlaps = []

                # check if the task allows variable duration
                is_interruptible = isinstance(task, VariableDurationTask)
                is_fixed_interruptible = isinstance(
                    task, FixedDurationInterruptibleTask
                )

                duration = end_task_i - start_task_i
                folded_start_task_i = (start_task_i - self.offset) % self.period
                folded_end_task_i = (end_task_i - self.offset) % self.period

                for (
                    interval_lower_bound,
                    interval_upper_bound,
                ) in self.list_of_time_intervals:
                    # intervals need to be defined in one period
                    if interval_upper_bound > self.period:
                        raise AssertionError(
                            f"interval ({interval_lower_bound}, {interval_upper_bound}) exceeds period {self.period}"
                        )

                    # if true, the folded task overlaps with the time interval in the first period
                    crossing_condition = z3.Not(
                        z3.Xor(
                            # folded task is completely before the first time interval
                            z3.And(
                                folded_start_task_i <= interval_lower_bound,
                                folded_start_task_i + duration % self.period
                                <= interval_lower_bound,
                            ),
                            # folded task is completely between the first and second time interval
                            z3.And(
                                folded_start_task_i >= interval_upper_bound,
                                folded_start_task_i + duration % self.period
                                <= interval_lower_bound + self.period,
                            ),
                        )
                    )

                    # if true, the task overlaps with at least one time interval
                    overlap_condition = z3.Or(
                        crossing_condition,
                        # task does not fit between two intervals
                        duration
                        > interval_lower_bound + self.period - interval_upper_bound,
                    )

                    # adjust the number of crossed time intervals
                    crossings = z3.If(
                        crossing_condition,
                        duration / self.period + 1,
                        duration / self.period,
                    )
                    # calculate the total overlap for this particular time interval
                    overlap = z3.If(
                        overlap_condition,
                        (interval_upper_bound - interval_lower_bound) * crossings,
                        0,
                    )
                    overlaps.append(overlap)

                    if is_interruptible or is_fixed_interruptible:
                        # just make sure that the task does not start or end within one of the time intervals...
                        conds.extend(
                            [
                                z3.Xor(
                                    folded_start_task_i < interval_lower_bound,
                                    folded_start_task_i >= interval_upper_bound,
                                ),
                                z3.Xor(
                                    folded_end_task_i <= interval_lower_bound,
                                    folded_end_task_i > interval_upper_bound,
                                ),
                            ]
                        )
                    else:
                        # ...otherwise make sure the task does not overlap with any of time intervals
                        conds.append(
                            z3.Xor(
                                folded_start_task_i >= interval_upper_bound,
                                folded_start_task_i + duration <= interval_lower_bound,
                            )
                        )

                if is_interruptible:
                    # add assertions for task duration based on the total count of overlapped periods
                    total_overlap = z3.Sum(*overlaps)
                    conds.append(task._duration >= task.min_duration + total_overlap)
                    if task.max_duration is not None:
                        conds.append(
                            task._duration <= task.max_duration + total_overlap
                        )
                elif is_fixed_interruptible:
                    total_overlap = z3.Sum(*overlaps)
                    conds.append(task._overlap == total_overlap)

            # TODO: add AND only of mask is set?
            core = z3.And(*conds)

            mask = [core]
            if self.start > 0:
                mask.append(end_task_i <= self.start)
            if self.end is not None:
                mask.append(start_task_i >= self.end)

            if len(mask) > 1:
                self.set_z3_assertions(z3.Or(*mask))
            else:
                self.set_z3_assertions(*mask)

        if not resource_assigned:
            raise AssertionError(
                "The resource is not assigned to any task. Please first assign the resource to one or more tasks, and then add the ResourcePeriodicallyInterrupted constraint."
            )


class ResourceNonDelay(ResourceConstraint):
    """All tasks processed by the resource are contiguous, there's no idle while an operation
    if waiting for processing"""

    resource: Union[Worker, CumulativeWorker]

    def __init__(self, **data) -> None:
        super().__init__(**data)
        starts = []
        ends = []
        for start_var, end_var in self.resource._busy_intervals.values():
            starts.append(start_var)
            ends.append(end_var)
        # sort both lists
        sorted_starts, c1 = sort_no_duplicates(starts)
        sorted_ends, c2 = sort_no_duplicates(ends)
        for c in c1 + c2:
            self.set_z3_assertions(c)
        # from now, starts and ends are sorted in asc order
        # the space between two consecutive tasks is the sorted_start[i+1]-sorted_end[i]
        # we just have to constraint this variable
        for i in range(1, len(sorted_starts)):
            asst = sorted_starts[i] == sorted_ends[i - 1]
            condition_only_scheduled_tasks = z3.And(
                sorted_ends[i - 1] >= 0, sorted_starts[i] >= 0
            )
            # finally create the constraint
            new_cstr = z3.Implies(condition_only_scheduled_tasks, asst)
            self.set_z3_assertions(new_cstr)


class ResourceTasksDistance(ResourceConstraint):
    """
    This constraint enforces a specific number of time unitary periods between tasks for a single resource.
    The constraint can be applied within specified time intervals.

    Parameters:
    - resource: The resource to which the constraint applies.
    - distance (int): The desired number of time unitary periods between tasks.
    - list_of_time_intervals (list, optional): A list of time intervals within which the constraint is restricted.
    - optional (bool, optional): Whether the constraint is optional (default is False).
    - mode (str, optional): The mode for enforcing the constraint - "exact" (default), "min", or "max".
    """

    resource: Union[Worker, CumulativeWorker]
    distance: int
    list_of_time_intervals: List[Tuple[int, int]] = Field(default=None)
    mode: Literal["min", "max", "exact"] = Field(default="exact")

    def __init__(self, **data) -> None:
        super().__init__(**data)
        starts = []
        ends = []
        for start_var, end_var in self.resource._busy_intervals.values():
            starts.append(start_var)
            ends.append(end_var)

        # check that the resource is assigned to at least two tasks
        if len(starts) < 2:
            raise AssertionError(
                "The resource has to be assigned to at least 2 tasks. ResourceTasksDistance constraint meaningless."
            )

        # sort both lists
        sorted_starts, c1 = sort_no_duplicates(starts)
        sorted_ends, c2 = sort_no_duplicates(ends)
        for c in c1 + c2:
            self.set_z3_assertions(c)
        # from now, starts and ends are sorted in asc order
        # the space between two consecutive tasks is the sorted_start[i+1]-sorted_end[i]
        # we just have to constraint this variable
        for i in range(1, len(sorted_starts)):
            if self.mode == "exact":
                asst = sorted_starts[i] - sorted_ends[i - 1] == self.distance
            elif self.mode == "max":
                asst = sorted_starts[i] - sorted_ends[i - 1] <= self.distance
            elif self.mode == "min":
                asst = sorted_starts[i] - sorted_ends[i - 1] >= self.distance
            #  another set of conditions, related to the time periods
            conditions = []
            if self.list_of_time_intervals is not None:
                conditions.extend(
                    z3.And(
                        sorted_starts[i] >= lower_bound,
                        sorted_ends[i - 1] >= lower_bound,
                        sorted_starts[i] <= upper_bound,
                        sorted_ends[i - 1] <= upper_bound,
                    )
                    for lower_bound, upper_bound in self.list_of_time_intervals
                )
            else:
                # add the constraint only if start and ends are positive integers,
                # that is to say they correspond to a scheduled optional task
                condition_only_scheduled_tasks = z3.And(
                    sorted_ends[i - 1] >= 0, sorted_starts[i] >= 0
                )
                conditions = [condition_only_scheduled_tasks]
            # finally create the constraint
            new_cstr = z3.Implies(z3.Or(conditions), asst)
            self.set_z3_assertions(new_cstr)


#
# SelectWorker specific constraints
#
class SameWorkers(ResourceConstraint):
    """
    This constraint ensures that workers selected by two SelectWorker instances are the same.

    Parameters:
    - select_workers_1: The first set of selected workers.
    - select_workers_2: The second set of selected workers.
    - optional (bool, optional): Whether the constraint is optional (default is False).
    """

    select_workers_1: SelectWorkers
    select_workers_2: SelectWorkers

    def __init__(self, **data) -> None:
        super().__init__(**data)
        # Check for common resources in select_workers_1 and select_workers_2,
        # then add a constraint to ensure they are the same.
        for res_work_1 in self.select_workers_1._selection_dict:
            if res_work_1 in self.select_workers_2._selection_dict:
                self.set_z3_assertions(
                    self.select_workers_1._selection_dict[res_work_1]
                    == self.select_workers_2._selection_dict[res_work_1]
                )


class DistinctWorkers(ResourceConstraint):
    """
    This constraint ensures that workers selected by two SelectWorker instances are distinct.

    Parameters:
    - select_workers_1: The first set of selected workers.
    - select_workers_2: The second set of selected workers.
    - optional (bool, optional): Whether the constraint is optional (default is False).
    """

    select_workers_1: SelectWorkers
    select_workers_2: SelectWorkers

    def __init__(self, **data) -> None:
        super().__init__(**data)

        # Check for common resources in select_workers_1 and select_workers_2,
        # then add a constraint to ensure they are distinct.
        for res_work_1 in self.select_workers_1._selection_dict:
            if res_work_1 in self.select_workers_2._selection_dict:
                self.set_z3_assertions(
                    self.select_workers_1._selection_dict[res_work_1]
                    != self.select_workers_2._selection_dict[res_work_1]
                )
