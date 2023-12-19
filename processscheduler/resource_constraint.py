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
            workers = self.resource.cumulative_workers

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
            workers = self.resource.cumulative_workers

        resource_assigned = False

        for interval_lower_bound, interval_upper_bound in self.list_of_time_intervals:
            # add constraints on each busy interval
            for worker in workers:
                for start_task_i, end_task_i in worker.get_busy_intervals():
                    resource_assigned = True
                    self.set_z3_assertions(
                        z3.Xor(
                            start_task_i >= interval_upper_bound,
                            end_task_i <= interval_lower_bound,
                        )
                    )

        if not resource_assigned:
            raise AssertionError(
                "The resource is not assigned to any task. Please first assign the resource to one or more tasks, and then add the ResourceUnavailable constraint."
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
