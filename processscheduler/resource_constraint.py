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

import uuid

from processscheduler.task import UnavailabilityTask
from processscheduler.base import _Constraint

#
# SameWorkers constraint
#
class AllSameSelected(_Constraint):
    """ Selected workers by both AlternateWorkers are constrained to
    be the same
    """
    def __init__(self, alternate_workers_1, alternate_workers_2):
        super().__init__()
        # we check resources in alt work 1, if it is present in
        # Select worker 2 as well, then add a constraint
        for res_work_1 in alternate_workers_1.selection_dict:
            if res_work_1 in alternate_workers_2.selection_dict:
                self.add_assertion(alternate_workers_1.selection_dict[res_work_1] == alternate_workers_2.selection_dict[res_work_1])

class AllDifferentSelected(_Constraint):
    """ Selected workers by both AlternateWorkers are constrained to
    be the same
    """
    def __init__(self, alternate_workers_1, alternate_workers_2):
        super().__init__()
        # we check resources in alt work 1, if it is present in
        # alterna worker 2 as well, then add a constraint
        for res_work_1 in alternate_workers_1.selection_dict:
            if res_work_1 in alternate_workers_2.selection_dict:
                self.add_assertion(alternate_workers_1.selection_dict[res_work_1] != alternate_workers_2.selection_dict[res_work_1])

class ResourceUnavailable(_Constraint):
    """ set unavailablity or a resource, in terms of busy intervals
    """
    def __init__(self, resource, list_of_intervals):
        """

        :param resource: the resource
        :param list_of_intervals: periods for which the resource is unavailable for any task.
        for example [(0, 2), (5, 8)]
        """
        super().__init__()
        # for each interval we create a task 'UnavailableResource%i'
        for interval_lower_bound, interval_upper_bound in list_of_intervals:
            new_t = UnavailabilityTask('%sNotAvailable%i' % (resource.name, uuid.uuid4().int),
                                       duration = interval_upper_bound - interval_lower_bound)
            # add this resource to the task
            self.add_assertion(new_t.start == interval_lower_bound)
            self.add_assertion(new_t.end == interval_upper_bound)
            new_t.add_required_resource(resource)
