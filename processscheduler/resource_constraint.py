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

from typing import Optional
import uuid

from z3 import And, Implies, Int, Not, Or, Sum, Xor

from processscheduler.resource import Worker, CumulativeWorker
from processscheduler.constraint import ResourceConstraint
from processscheduler.util import sort_no_duplicates


def assert_resource_is_worker_or_cumulative_worker(resource):
    if not isinstance(resource, (Worker, CumulativeWorker)):
        raise TypeError(
            f"you passed a {type(resource)} object. resource must be either a Worker or CumulativeWorker."
        )


class WorkLoad(ResourceConstraint):
    """
    A WorkLoad constraint restricts the number of tasks that can be executed on a resource
    during a certain time period. The resource can be a single Worker or a CumulativeWorker.

    The list of time intervals is specified as a dict mapping interval tuples to integer bounds.
    For example, {(1,20):6, (50,60):2} specifies that the resource can use no more than 6 slots
    in the interval (1,20), and no more than 2 slots in the interval (50,60).

    The kind parameter specifies whether the constraint is exact, a minimum, or a maximum.
    """

    def __init__(
        self,
        resource,
        dict_time_intervals_and_bound,
        kind: Optional[str] = "max",
        optional: Optional[bool] = False,
    ) -> None:
        super().__init__(optional)

        if kind not in ["exact", "max", "min"]:
            raise ValueError("kind must either be 'exact', 'min' or 'max'")

        assert_resource_is_worker_or_cumulative_worker(resource)

        self.dict_time_intervals_and_bound = dict_time_intervals_and_bound
        self.resource = resource
        self.kind = kind

        if isinstance(resource, Worker):
            workers = [resource]
        elif isinstance(resource, CumulativeWorker):
            workers = resource.cumulative_workers

        resource_assigned = False

        for time_interval in dict_time_intervals_and_bound:
            number_of_time_slots = dict_time_intervals_and_bound[time_interval]

            time_interval_lower_bound, time_interval_upper_bound = time_interval

            durations = []

            for worker in workers:
                # for this task, the logic expression is that any of its start or end must be
                # between two consecutive intervals
                for start_task_i, end_task_i in worker.get_busy_intervals():
                    resource_assigned = True
                    # this variable allows to compute the occupation
                    # of the resource during the time interval
                    dur = Int(
                        f"Overlap_{time_interval_lower_bound}_{time_interval_upper_bound}_{uuid.uuid4().hex[:8]}"
                    )
                    # prevent solutions where duration would be negative
                    self.set_z3_assertions(dur >= 0)
                    # 4 different cases to take into account
                    cond1 = And(
                        start_task_i >= time_interval_lower_bound,
                        end_task_i <= time_interval_upper_bound,
                    )
                    asst1 = Implies(cond1, dur == end_task_i - start_task_i)
                    self.set_z3_assertions(asst1)
                    # overlap at lower bound
                    cond2 = And(
                        start_task_i < time_interval_lower_bound,
                        end_task_i > time_interval_lower_bound,
                    )
                    asst2 = Implies(
                        cond2, dur == end_task_i - time_interval_lower_bound
                    )
                    self.set_z3_assertions(asst2)
                    # overlap at upper bound
                    cond3 = And(
                        start_task_i < time_interval_upper_bound,
                        end_task_i > time_interval_upper_bound,
                    )
                    asst3 = Implies(
                        cond3, dur == time_interval_upper_bound - start_task_i
                    )
                    self.set_z3_assertions(asst3)
                    # all overlap
                    cond4 = And(
                        start_task_i < time_interval_lower_bound,
                        end_task_i > time_interval_upper_bound,
                    )
                    asst4 = Implies(
                        cond4,
                        dur == time_interval_upper_bound - time_interval_lower_bound,
                    )
                    self.set_z3_assertions(asst4)

                    # make these constraints mutual: no overlap
                    self.set_z3_assertions(
                        Implies(Not(Or([cond1, cond2, cond3, cond4])), dur == 0)
                    )

                    # finally, store this variable in the duratins list
                    durations.append(dur)

            if not resource_assigned:
                raise AssertionError(
                    "The resource is not assigned to any task. Please first assign the resource to one or more tasks, and then add the WorkLoad constraint."
                )

            # workload constraint depends on the kind
            if kind == "exact":
                workload_constraint = Sum(durations) == number_of_time_slots
            elif kind == "max":
                workload_constraint = Sum(durations) <= number_of_time_slots
            elif kind == "min":
                workload_constraint = Sum(durations) >= number_of_time_slots

            self.set_z3_assertions(workload_constraint)


class ResourceUnavailable(ResourceConstraint):
    """set unavailablity or a resource, in terms of busy intervals"""

    def __init__(
        self, resource, list_of_time_intervals, optional: Optional[bool] = False
    ) -> None:
        """
        :param resource: the resource
        :param list_of_intervals: periods for which the resource is unavailable for any task.
        for example [(0, 2), (5, 8)]
        """
        super().__init__(optional)

        assert_resource_is_worker_or_cumulative_worker(resource)

        self.list_of_time_intervals = list_of_time_intervals
        self.resource = resource

        # for each interval we create a task 'UnavailableResource%i'
        if isinstance(resource, Worker):
            workers = [resource]
        elif isinstance(resource, CumulativeWorker):
            workers = resource.cumulative_workers

        resource_assigned = False

        for interval_lower_bound, interval_upper_bound in list_of_time_intervals:
            # add constraints on each busy interval
            for worker in workers:
                for start_task_i, end_task_i in worker.get_busy_intervals():
                    resource_assigned = True
                    self.set_z3_assertions(
                        Xor(
                            start_task_i >= interval_upper_bound,
                            end_task_i <= interval_lower_bound,
                        )
                    )

        if not resource_assigned:
            raise AssertionError(
                "The resource is not assigned to any task. Please first assign the resource to one or more tasks, and then add the ResourceUnavailable constraint."
            )


class ResourceTasksDistance(ResourceConstraint):
    """Force a minimal/exact/maximal number time unitary periods between tasks for a single resource. This
    distance constraint is restricted to a certain number of time intervals"""

    def __init__(
        self,
        resource,
        distance: int,
        list_of_time_intervals: Optional[list] = None,
        optional: Optional[bool] = False,
        mode: Optional[str] = "exact",
    ):
        if mode not in {"min", "max", "exact"}:
            raise Exception("Mode should be min, max or exact")

        assert_resource_is_worker_or_cumulative_worker(resource)

        super().__init__(optional)

        self.list_of_time_intervals = list_of_time_intervals
        self.resource = resource
        self.distance = distance
        self.mode = mode

        starts = []
        ends = []
        for start_var, end_var in resource.busy_intervals.values():
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
            if mode == "exact":
                asst = sorted_starts[i] - sorted_ends[i - 1] == distance
            elif mode == "max":
                asst = sorted_starts[i] - sorted_ends[i - 1] <= distance
            elif mode == "min":
                asst = sorted_starts[i] - sorted_ends[i - 1] >= distance
            #  another set of conditions, related to the time periods
            conditions = []
            if list_of_time_intervals is not None:
                conditions.extend(
                    And(
                        sorted_starts[i] >= lower_bound,
                        sorted_ends[i - 1] >= lower_bound,
                        sorted_starts[i] <= upper_bound,
                        sorted_ends[i - 1] <= upper_bound,
                    )
                    for lower_bound, upper_bound in list_of_time_intervals
                )
            else:
                # add the constraint only if start and ends are positive integers,
                # that is to say they correspond to a scheduled optional task
                condition_only_scheduled_tasks = And(
                    sorted_ends[i - 1] >= 0, sorted_starts[i] >= 0
                )
                conditions = [condition_only_scheduled_tasks]
            # finally create the constraint
            new_cstr = Implies(Or(conditions), asst)
            self.set_z3_assertions(new_cstr)


#
# SelectWorker specific constraints
#
class SameWorkers(ResourceConstraint):
    """Selected workers by both AlternateWorkers are constrained to
    be the same
    """

    def __init__(
        self, select_workers_1, select_workers_2, optional: Optional[bool] = False
    ):
        super().__init__(optional)

        self.select_workers_1 = select_workers_1
        self.select_workers_2 = select_workers_2

        # we check resources in alt work 1, if it is present in
        # Select worker 2 as well, then add a constraint
        for res_work_1 in select_workers_1.selection_dict:
            if res_work_1 in select_workers_2.selection_dict:
                self.set_z3_assertions(
                    select_workers_1.selection_dict[res_work_1]
                    == select_workers_2.selection_dict[res_work_1]
                )


class DistinctWorkers(ResourceConstraint):
    """Selected workers by both AlternateWorkers are constrained to
    be the same
    """

    def __init__(
        self, select_workers_1, select_workers_2, optional: Optional[bool] = False
    ):
        super().__init__(optional)

        self.select_workers_1 = select_workers_1
        self.select_workers_2 = select_workers_2

        # we check resources in alt work 1, if it is present in
        # alterna worker 2 as well, then add a constraint
        for res_work_1 in select_workers_1.selection_dict:
            if res_work_1 in select_workers_2.selection_dict:
                self.set_z3_assertions(
                    select_workers_1.selection_dict[res_work_1]
                    != select_workers_2.selection_dict[res_work_1]
                )
