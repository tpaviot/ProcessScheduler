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

from z3 import And, Implies, Int, Sum, Xor

from processscheduler.resource import Worker, CumulativeWorker
from processscheduler.base import _Constraint


class ResourceCapacity(_Constraint):
    """ set a mini/maxi/exact number of slots a resource can be scheduled."""
    def __init__(self, resource,
                       dict_time_intervals_limits,
                       kind: Optional[str] = 'atmost',
                       optional: Optional[bool] = False) -> None:
        """Capacity constraints can be used to restrict the number tasks which are executed during a certain time period.
        The resource can be a single Worker or a CumulativeWorker.

        The list of time_intervals is a dict such as:
        [(1,20):6, (50,60):2] which means: in the interval (1,20), the resource might not use
        more than 6 slots. And no more than 2 time slots in the interval (50, 60)

        kind: optional string, default to 'atmost', can be 'atleast' or 'exact'
        """
        super().__init__()

        self.optional = optional

        if kind not in ['exact', 'atmost', 'atleast']:
            raise ValueError("kind must either be 'exact', 'atleast' or 'atmost'")

        if isinstance(resource, Worker):
            workers = [resource]
        elif isinstance(resource, CumulativeWorker):
            workers = resource.cumulative_workers

        for time_interval in dict_time_intervals_limits:
            number_of_time_slots = dict_time_intervals_limits[time_interval]
            lower_bound, upper_bound = time_interval
            for worker in workers:
                durations = []
                # for this task, the logic expression is that any of its start or end must be
                # between two consecutive intervals
                for start_task_i, end_task_i in worker.get_busy_intervals():
                    # this variable allows to compute the occupation
                    # of the resource during the time interval
                    dur = Int('Duration_%s' % uuid.uuid4().int)
                    # prevent solutions where duration would be negative
                    self.set_applied_not_applied_assertions(dur >= 0)
                    # 4 different cases to take into account
                    asst1 = Implies(And(start_task_i >= lower_bound,
                                        end_task_i <= upper_bound),
                                    dur == end_task_i - start_task_i)
                    self.set_applied_not_applied_assertions(asst1)
                    # overlap at lower bound
                    asst2 = Implies(And(start_task_i < lower_bound,
                                        end_task_i > lower_bound),
                                    dur == end_task_i - lower_bound)
                    self.set_applied_not_applied_assertions(asst2)
                    # overlap at upper bound
                    asst3 = Implies(And(start_task_i < upper_bound,
                                        end_task_i > upper_bound),
                                    dur == upper_bound - start_task_i)
                    self.set_applied_not_applied_assertions(asst3)
                    # all overlap
                    asst4 = Implies(And(start_task_i < lower_bound,
                                        end_task_i > upper_bound),
                                    dur == upper_bound - lower_bound)
                    self.set_applied_not_applied_assertions(asst4)

                    durations.append(dur)

            # capacity constraint depends on the kind
            if kind == 'exact':
                capa_constrt = Sum(durations) == number_of_time_slots
            elif kind == 'atmost':
                capa_constrt = Sum(durations) <= number_of_time_slots
            elif kind == 'atleast':
                capa_constrt = Sum(durations) >= number_of_time_slots

            self.set_applied_not_applied_assertions(capa_constrt)


class ResourceUnavailable(_Constraint):
    """ set unavailablity or a resource, in terms of busy intervals
    """
    def __init__(self,
                 resource,
                 list_of_time_intervals,
                 optional: Optional[bool] = False) -> None:
        """

        :param resource: the resource
        :param list_of_intervals: periods for which the resource is unavailable for any task.
        for example [(0, 2), (5, 8)]
        """
        super().__init__()

        self.optional = optional

        # for each interval we create a task 'UnavailableResource%i'
        if isinstance(resource, Worker):
            workers = [resource]
        elif isinstance(resource, CumulativeWorker):
            workers = resource.cumulative_workers

        for interval_lower_bound, interval_upper_bound in list_of_time_intervals:
            # add constraints on each busy interval
            for worker in workers:
                for start_task_i, end_task_i in worker.get_busy_intervals():
                    self.set_applied_not_applied_assertions(Xor(start_task_i >= interval_upper_bound,
                                                                end_task_i <= interval_lower_bound))


#
# SelectWorker specific constraints
#
class AllSameSelected(_Constraint):
    """ Selected workers by both AlternateWorkers are constrained to
    be the same
    """
    def __init__(self, alternate_workers_1, alternate_workers_2,
                 optional: Optional[bool] = False):
        super().__init__()
        # we check resources in alt work 1, if it is present in
        # Select worker 2 as well, then add a constraint
        for res_work_1 in alternate_workers_1.selection_dict:
            if res_work_1 in alternate_workers_2.selection_dict:
                self.set_applied_not_applied_assertions(alternate_workers_1.selection_dict[res_work_1] == alternate_workers_2.selection_dict[res_work_1])


class AllDifferentSelected(_Constraint):
    """ Selected workers by both AlternateWorkers are constrained to
    be the same
    """
    def __init__(self, alternate_workers_1, alternate_workers_2,
                 optional: Optional[bool] = False):
        super().__init__()
        # we check resources in alt work 1, if it is present in
        # alterna worker 2 as well, then add a constraint
        for res_work_1 in alternate_workers_1.selection_dict:
            if res_work_1 in alternate_workers_2.selection_dict:
                self.set_applied_not_applied_assertions(alternate_workers_1.selection_dict[res_work_1] != alternate_workers_2.selection_dict[res_work_1])
