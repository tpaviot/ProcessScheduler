""" ProcessScheduler, Copyright 2020 Thomas Paviot (tpaviot@gmail.com)

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.
"""

from typing import List, Optional
import warnings

from z3 import Bool, Int, And, If

from processscheduler.base import _NamedUIDObject
from processscheduler.resource import _Resource, Worker, AlternativeWorkers

class Task(_NamedUIDObject):
    """ a Task object """
    def __init__(self, name: str) -> None:
        super().__init__(name)
        # scheduled start, end and duration set to 0 by default
        # be set after the solver is called
        self.scheduled_start = 0
        self.scheduled_end = 0
        self.scheduled_duration = 0
        self.scheduled_flag = False

        # required resources to perform the task
        self.required_resources = [] # type: List[_Resource]

        # assigned resource names, after the resolution is completed
        self.assigned_resources = [] # type: List[_Resource]

        # z3 Int variables
        self.start = Int('%s_start' % name)
        self.end = Int('%s_end' % name)
        self.scheduled = Bool('t%s_scheduled' % name)
        self.duration = Int('%s_duration' % name)

        # these two flags are set to True is there is a constraint
        # that set a lower or upper bound (e.g. a Precedence)
        # this is useful to reduce the number of assertions in z3
        # indeed if the task is lower_bounded by a precedence or
        # a StartAt, then there's no need to assert task.start >= 0
        self.lower_bounded = False
        # idem for the upper bound: no need to assert task.end <= horizon
        self.upper_bounded = False

        # optional flag, set to True if this task is optional, else True
        self.optional = False

    # Necessary to define _eq__ and __hash__ because of lgtm warnings of kind
    def __hash__(self) -> int:
        return self.uid

    def __eq__(self, other) -> Bool:
        return self.uid == other.uid

    def set_optional(self):
        self.optional = True

    def add_required_resource(self, resource: _Resource) -> bool:
        """ add a required resource to the current task, required does not
        mean it actually will be assigned """
        if not isinstance(resource, _Resource):
            raise TypeError('you must pass a Resource instance')
        if resource in self.required_resources:
            warnings.warn('This resource is already set as a required resource for this task')
            return False
        if isinstance(resource, AlternativeWorkers):
            # loop over each resource
            for worker in resource.list_of_workers:
                resource_maybe_busy_start = Int('%s_maybe_busy_%s_start' % (worker.name, self.name))
                resource_maybe_busy_end = Int('%s_maybe_busy_%s_end' % (worker.name, self.name))
                # create the busy interval for the resource
                worker.add_busy_interval((resource_maybe_busy_start, resource_maybe_busy_end))
                # add assertions. If worker is selected then sync the resource with the task
                selected_variable = resource.selection_dict[worker]
                length_assert = resource_maybe_busy_start + self.duration == resource_maybe_busy_end
                start_synced_assert = resource_maybe_busy_start ==  self.start
                schedule_as_usual = And(length_assert, start_synced_assert)
                # in the case the worker is selected
                # else: reject in the past !! (i.e. this resource will be scheduled in the past)
                # to a place where they cannot conflict with the schedule
                # and with a zero busy time, that mean they don't contribute in cost
                # or work amount
                move_to_past = And(resource_maybe_busy_start == -1, resource_maybe_busy_end == -1)
                # define the assertion ...
                assertion = If(selected_variable, schedule_as_usual, move_to_past)
                # ... and store it into the task assertions list
                self.add_assertion(assertion)
                # also, don't forget to add the AlternativeWorker assertion
                self.add_assertion(resource.selection_assertion)
                # finally, add each worker to the "required" resource list
                self.required_resources.append(worker)
        elif isinstance(resource, Worker):
            resource_busy_start = Int('%s_busy_%s_start' % (resource.name, self.name))
            resource_busy_end = Int('%s_busy_%s_end' % (resource.name, self.name))
            # create the busy interval for the resource
            resource.add_busy_interval((resource_busy_start, resource_busy_end))
            # set the busy resource to keep synced with the task
            self.add_assertion(resource_busy_start + self.duration == resource_busy_end)
            self.add_assertion(resource_busy_start ==  self.start)
            # finally, store this resource into the resource list
            self.required_resources.append(resource)
        return True

    def add_required_resources(self, list_of_resources):
        for resource in list_of_resources:
            self.add_required_resource(resource)

class ZeroDurationTask(Task):
    """ Task with a duration of 0, i.e. start==end. A ZeroDurationTask
    can have some resources required """
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.work_amount = 0
        # add an assertion: end = start because the duration is zero
        self.add_assertion(self.start == self.end)
        self.add_assertion(self.duration == 0)

class FixedDurationTask(Task):
    """ Task with constant duration """
    def __init__(self, name: str, duration: int, work_amount: Optional[float] = 0.):
        super().__init__(name)
        self.work_amount = work_amount
        # add an assertion: end = start + duration
        self.add_assertion(self.start + self.duration == self.end)
        self.add_assertion(self.duration == duration)

class VariableDurationTask(Task):
    """ Tasj with a priori unknown duration. its duration is computed by the solver """
    def __init__(self, name: str,
                 length_at_least: Optional[int] = 0,
                 length_at_most: Optional[int] = None,
                 work_amount: Optional[float] = 0.):
        super().__init__(name)
        self.length_at_least = length_at_least
        self.length_at_most = length_at_most
        self.work_amount = work_amount

        # set minimal duration
        self.add_assertion(self.duration >= length_at_least)

        if length_at_most is not None:
            self.add_assertion(self.duration <= length_at_most)

        # add an assertion: end = start + duration
        self.add_assertion(self.start + self.duration == self.end)
