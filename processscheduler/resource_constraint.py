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
from processscheduler.base import _Constraint
from processscheduler.util import sort_no_duplicates


class WorkLoad(_Constraint):
    """set a mini/maxi/exact number of slots a resource can be scheduled."""

    def __init__(
        self,
        resource,
        dict_time_intervals_and_bound,
        kind: Optional[str] = "max",
        optional: Optional[bool] = False,
    ) -> None:
        """WorkLoad constraints can be used to restrict the number tasks which are executed during a certain time period.
        The resource can be a single Worker or a CumulativeWorker.

        The list of time_intervals is a dict such as:
        [(1,20):6, (50,60):2] which means: in the interval (1,20), the resource might not use
        more than 6 slots. And no more than 2 time slots in the interval (50, 60)

        kind: optional string, default to 'max', can be 'min' or 'exact'
        """
        super().__init__(optional)

        if kind not in ["exact", "max", "min"]:
            raise ValueError("kind must either be 'exact', 'min' or 'max'")

        if isinstance(resource, Worker):
            workers = [resource]
        elif isinstance(resource, CumulativeWorker):
            workers = resource.cumulative_workers

        for time_interval in dict_time_intervals_and_bound:
            number_of_time_slots = dict_time_intervals_and_bound[time_interval]

            time_interval_lower_bound, time_interval_upper_bound = time_interval

            durations = []

            for worker in workers:
                # for this task, the logic expression is that any of its start or end must be
                # between two consecutive intervals
                for start_task_i, end_task_i in worker.get_busy_intervals():
                    # this variable allows to compute the occupation
                    # of the resource during the time interval
                    dur = Int(
                        "Overlap_%i_%i_%s"
                        % (
                            time_interval_lower_bound,
                            time_interval_upper_bound,
                            uuid.uuid4().hex[:8],
                        )
                    )
                    # prevent solutions where duration would be negative
                    self.set_assertions(dur >= 0)
                    # 4 different cases to take into account
                    cond1 = And(
                        start_task_i >= time_interval_lower_bound,
                        end_task_i <= time_interval_upper_bound,
                    )
                    asst1 = Implies(cond1, dur == end_task_i - start_task_i)
                    self.set_assertions(asst1)
                    # overlap at lower bound
                    cond2 = And(
                        start_task_i < time_interval_lower_bound,
                        end_task_i > time_interval_lower_bound,
                    )
                    asst2 = Implies(
                        cond2, dur == end_task_i - time_interval_lower_bound
                    )
                    self.set_assertions(asst2)
                    # overlap at upper bound
                    cond3 = And(
                        start_task_i < time_interval_upper_bound,
                        end_task_i > time_interval_upper_bound,
                    )
                    asst3 = Implies(
                        cond3, dur == time_interval_upper_bound - start_task_i
                    )
                    self.set_assertions(asst3)
                    # all overlap
                    cond4 = And(
                        start_task_i < time_interval_lower_bound,
                        end_task_i > time_interval_upper_bound,
                    )
                    asst4 = Implies(
                        cond4,
                        dur == time_interval_upper_bound - time_interval_lower_bound,
                    )
                    self.set_assertions(asst4)

                    # make these constraints mutual: no overlap
                    self.set_assertions(
                        Implies(Not(Or([cond1, cond2, cond3, cond4])), dur == 0)
                    )

                    # finally, store this variable in the duratins list
                    durations.append(dur)

            # workload constraint depends on the kind
            if kind == "exact":
                wl_constrt = Sum(durations) == number_of_time_slots
            elif kind == "max":
                wl_constrt = Sum(durations) <= number_of_time_slots
            elif kind == "min":
                wl_constrt = Sum(durations) >= number_of_time_slots

            self.set_assertions(wl_constrt)


class ResourceUnavailable(_Constraint):
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

        # for each interval we create a task 'UnavailableResource%i'
        if isinstance(resource, Worker):
            workers = [resource]
        elif isinstance(resource, CumulativeWorker):
            workers = resource.cumulative_workers

        for interval_lower_bound, interval_upper_bound in list_of_time_intervals:
            # add constraints on each busy interval
            for worker in workers:
                for start_task_i, end_task_i in worker.get_busy_intervals():
                    self.set_assertions(
                        Xor(
                            start_task_i >= interval_upper_bound,
                            end_task_i <= interval_lower_bound,
                        )
                    )


class ResourceTasksDistance(_Constraint):
    """Force a minimal/exact/maximal number time unitary periods between tasks for a single resource. This
    distance constraint is restricted to a certain number of time intervals"""

    def __init__(
        self,
        worker,
        distance: int,
        time_periods: Optional[list] = None,
        optional: Optional[bool] = False,
        mode: Optional[str] = "exact",
    ):
        if mode not in {"min", "max", "exact"}:
            raise Exception("Mode should be min, max or exact")

        super().__init__(optional)

        starts = []
        ends = []
        for start_var, end_var in worker.busy_intervals.values():
            starts.append(start_var)
            ends.append(end_var)
        # sort both lists
        sorted_starts, c1 = sort_no_duplicates(starts)
        sorted_ends, c2 = sort_no_duplicates(ends)
        for c in c1 + c2:
            self.set_assertions(c)
        # from now, starts and ends are sorted in asc order
        # the space between two consecutive tasks is the sorted_start[i+1]-sorted_end[i]
        # we just have to constraint this variable
        for i in range(1, len(sorted_starts)):
            if mode == "min":
                asst = sorted_starts[i] - sorted_ends[i - 1] >= distance
            elif mode == "max":
                asst = sorted_starts[i] - sorted_ends[i - 1] <= distance
            elif mode == "exact":
                asst = sorted_starts[i] - sorted_ends[i - 1] == distance
            #  anothe set of conditions, related to the time periods
            conditions = []
            if time_periods is not None:
                for (
                    lower_bound,
                    upper_bound,
                ) in time_periods:  # time_period should be a list also or a tuple
                    conditions.append(
                        And(
                            sorted_starts[i] >= lower_bound,
                            sorted_ends[i - 1] >= lower_bound,
                            sorted_starts[i] <= upper_bound,
                            sorted_ends[i - 1] <= upper_bound,
                        )
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
            self.set_assertions(new_cstr)


#
# SelectWorker specific constraints
#
class SameWorkers(_Constraint):
    """Selected workers by both AlternateWorkers are constrained to
    be the same
    """

    def __init__(
        self, alternate_workers_1, alternate_workers_2, optional: Optional[bool] = False
    ):
        super().__init__(optional)
        # we check resources in alt work 1, if it is present in
        # Select worker 2 as well, then add a constraint
        for res_work_1 in alternate_workers_1.selection_dict:
            if res_work_1 in alternate_workers_2.selection_dict:
                self.set_assertions(
                    alternate_workers_1.selection_dict[res_work_1]
                    == alternate_workers_2.selection_dict[res_work_1]
                )


class DistinctWorkers(_Constraint):
    """Selected workers by both AlternateWorkers are constrained to
    be the same
    """

    def __init__(
        self, alternate_workers_1, alternate_workers_2, optional: Optional[bool] = False
    ):
        super().__init__(optional)
        # we check resources in alt work 1, if it is present in
        # alterna worker 2 as well, then add a constraint
        for res_work_1 in alternate_workers_1.selection_dict:
            if res_work_1 in alternate_workers_2.selection_dict:
                self.set_assertions(
                    alternate_workers_1.selection_dict[res_work_1]
                    != alternate_workers_2.selection_dict[res_work_1]
                )
