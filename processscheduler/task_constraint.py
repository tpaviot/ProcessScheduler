"""Task constraints and related classes."""

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
from typing import Optional

from z3 import And, Bool, BoolRef, If, Implies, Not, Or, PbEq, PbGe, PbLe, Xor

from processscheduler.base import _Constraint
from processscheduler.util import sort_no_duplicates

#
# Tasks constraints for two or more classes
#
class TaskPrecedence(_Constraint):
    """Task precedence relation"""

    def __init__(
        self,
        task_before,
        task_after,
        offset=0,
        kind="lax",
        optional: Optional[bool] = False,
    ):
        """kind might be either LAX/STRICT/TIGHT
        Semantics : task after will start at least after offset periods
        task_before is finished.
        LAX constraint: task1_before_end + offset <= task_after_start
        STRICT constraint: task1_before_end + offset < task_after_start
        TIGHT constraint: task1_before_end + offset == task_after_start
        """
        super().__init__(optional)

        if kind not in ["lax", "strict", "tight"]:
            raise ValueError("kind must either be 'lax', 'strict' or 'tight'")

        if not isinstance(offset, int) or offset < 0:
            raise ValueError("offset must be a positive integer")

        self.offset = offset
        self.kind = kind

        lower = task_before.end + offset if offset > 0 else task_before.end
        upper = task_after.start

        if kind == "lax":
            scheduled_assertion = lower <= upper
        elif kind == "strict":
            scheduled_assertion = lower < upper
        else:  # kind == 'tight':
            scheduled_assertion = lower == upper

        if task_before.optional or task_after.optional:
            # both tasks must be scheduled so that the precedence constraint applies
            self.set_assertions(
                Implies(
                    And(task_before.scheduled, task_after.scheduled),
                    scheduled_assertion,
                )
            )
        else:
            self.set_assertions(scheduled_assertion)


class TasksStartSynced(_Constraint):
    """Two tasks that must start at the same time"""

    def __init__(self, task_1, task_2, optional: Optional[bool] = False) -> None:
        super().__init__(optional)

        scheduled_assertion = task_1.start == task_2.start

        if task_1.optional or task_2.optional:
            # both tasks must be scheduled so that the startsynced constraint applies
            self.set_assertions(
                Implies(And(task_1.scheduled, task_2.scheduled), scheduled_assertion)
            )
        else:
            self.set_assertions(scheduled_assertion)


class TasksEndSynced(_Constraint):
    """Two tasks that must complete at the same time"""

    def __init__(self, task_1, task_2, optional: Optional[bool] = False) -> None:
        super().__init__(optional)

        scheduled_assertion = task_1.end == task_2.end

        if task_1.optional or task_2.optional:
            # both tasks must be scheduled so that the endsynced constraint applies
            self.set_assertions(
                Implies(And(task_1.scheduled, task_2.scheduled), scheduled_assertion)
            )
        else:
            self.set_assertions(scheduled_assertion)


class TasksDontOverlap(_Constraint):
    """Two tasks must not overlap, i.e. one needs to be completed before
    the other can be processed"""

    def __init__(self, task_1, task_2, optional: Optional[bool] = False) -> None:
        super().__init__(optional)

        scheduled_assertion = Xor(
            task_2.start >= task_1.end, task_1.start >= task_2.end
        )

        if task_1.optional or task_2.optional:
            # if one task is not scheduledboth tasks must be scheduled so that the not overlap constraint applies
            self.set_assertions(
                Implies(And(task_1.scheduled, task_2.scheduled), scheduled_assertion)
            )
        else:
            self.set_assertions(scheduled_assertion)


class TasksContiguous(_Constraint):
    """A list of tasks are scheduled contiguously."""

    def __init__(self, list_of_tasks, optional: Optional[bool] = False) -> None:
        super().__init__(optional)

        starts = [t.start for t in list_of_tasks]
        ends = [t.end for t in list_of_tasks]
        # sort both lists
        sorted_starts, c1 = sort_no_duplicates(starts)
        sorted_ends, c2 = sort_no_duplicates(ends)
        for c in c1 + c2:
            self.set_assertions(c)
        # from now, starts and ends are sorted in asc order
        # the space between two consecutive tasks is the sorted_start[i+1]-sorted_end[i]
        # we just have to constraint this variable
        for i in range(1, len(sorted_starts)):
            asst = sorted_starts[i] == sorted_ends[i - 1]
            #  anothe set of conditions, related to the time periods
            condition_only_scheduled_tasks = And(
                sorted_ends[i - 1] >= 0, sorted_starts[i] >= 0
            )
            # finally create the constraint
            new_cstr = Implies(Or(condition_only_scheduled_tasks), asst)
            self.set_assertions(new_cstr)


#
# Task constraints for one single task
#
class TaskStartAt(_Constraint):
    """One task must start at the desired time"""

    def __init__(self, task, value: int, optional: Optional[bool] = False) -> None:
        super().__init__(optional)
        self.value = value

        scheduled_assertion = task.start == value

        if task.optional:
            self.set_assertions(Implies(task.scheduled, scheduled_assertion))
        else:
            self.set_assertions(scheduled_assertion)


class TaskStartAfterStrict(_Constraint):
    """task.start > value"""

    def __init__(self, task, value: int, optional: Optional[bool] = False) -> None:
        super().__init__(optional)
        self.value = value

        scheduled_assertion = task.start > value

        if task.optional:
            self.set_assertions(Implies(task.scheduled, scheduled_assertion))
        else:
            self.set_assertions(scheduled_assertion)


class TaskStartAfterLax(_Constraint):
    """task.start >= value"""

    def __init__(self, task, value: int, optional: Optional[bool] = False) -> None:
        super().__init__(optional)
        self.value = value

        scheduled_assertion = task.start >= value

        if task.optional:
            self.set_assertions(Implies(task.scheduled, scheduled_assertion))
        else:
            self.set_assertions(scheduled_assertion)


class TaskEndAt(_Constraint):
    """On task must complete at the desired time"""

    def __init__(self, task, value: int, optional: Optional[bool] = False) -> None:
        super().__init__(optional)
        self.value = value

        scheduled_assertion = task.end == value

        if task.optional:
            self.set_assertions(Implies(task.scheduled, scheduled_assertion))
        else:
            self.set_assertions(scheduled_assertion)


class TaskEndBeforeStrict(_Constraint):
    """task.end < value"""

    def __init__(self, task, value: int, optional: Optional[bool] = False) -> None:
        super().__init__(optional)
        self.value = value

        scheduled_assertion = task.end < value

        if task.optional:
            self.set_assertions(Implies(task.scheduled, scheduled_assertion))
        else:
            self.set_assertions(scheduled_assertion)


class TaskEndBeforeLax(_Constraint):
    """task.end <= value"""

    def __init__(self, task, value: int, optional: Optional[bool] = False) -> None:
        super().__init__(optional)
        self.value = value

        scheduled_assertion = task.end <= value

        if task.optional:
            self.set_assertions(Implies(task.scheduled, scheduled_assertion))
        else:
            self.set_assertions(scheduled_assertion)


#
# Optional classes only constraints
#
class OptionalTaskConditionSchedule(_Constraint):
    """An optional task that is scheduled only if a condition is fulfilled."""

    def __init__(
        self, task, condition: BoolRef, optional: Optional[bool] = False
    ) -> None:
        super().__init__(optional)

        if not task.optional:
            raise TypeError("Task %s must be optional." % task.name)

        self.set_assertions(
            If(condition, task.scheduled == True, task.scheduled == False)
        )


class OptionalTasksDependency(_Constraint):
    """task_2 is scheduled if and only if task_1 is scheduled"""

    def __init__(self, task_1, task_2, optional: Optional[bool] = False) -> None:
        super().__init__(optional)

        if not task_2.optional:
            raise TypeError("Task %s must be optional." % task_2.name)

        self.set_assertions(task_1.scheduled == task_2.scheduled)


class ForceScheduleNOptionalTasks(_Constraint):
    """Given a set of m different optional tasks, force the solver to schedule
    at at least/at most/exactly n tasks, with 0 < n <= m."""

    def __init__(
        self,
        list_of_optional_tasks,
        nb_tasks_to_schedule: Optional[int] = 1,
        kind: Optional[str] = "exact",
        optional: Optional[bool] = False,
    ) -> None:
        super().__init__(optional)

        problem_function = {"min": PbGe, "max": PbLe, "exact": PbEq}

        # first check that all tasks from the list_of_optional_tasks are
        # actually optional
        for task in list_of_optional_tasks:
            if not task.optional:
                raise TypeError(
                    "This class %s must excplicitely be set as optional." % task.name
                )
        # all scheduled variables to take into account
        sched_vars = [task.scheduled for task in list_of_optional_tasks]
        asst = problem_function[kind](
            [(scheduled, True) for scheduled in sched_vars], nb_tasks_to_schedule
        )
        self.set_assertions(asst)


class ScheduleNTasksInTimeIntervals(_Constraint):
    """Given a set of m different tasks, and a list of time intervals, schedule N tasks among m
    in this time interval"""

    def __init__(
        self,
        list_of_tasks,
        nb_tasks_to_schedule,
        list_of_time_intervals,
        kind: Optional[str] = "exact",
        optional: Optional[bool] = False,
    ) -> None:
        super().__init__(optional)

        problem_function = {"min": PbGe, "max": PbLe, "exact": PbEq}

        # first check that all tasks from the list_of_optional_tasks are
        # actually optional
        if not isinstance(list_of_tasks, list):
            raise TypeError("list_of_task must be a list")

        if not isinstance(list_of_time_intervals, list):
            raise TypeError("list_of_time_intervals must be a list of list")

        # count the number of tasks that re scheduled in this time interval
        all_bools = []
        for task in list_of_tasks:
            # for this task, the logic expression is that any of its start or end must be
            # between two consecutive intervals
            bools_for_this_task = []
            for time_interval in list_of_time_intervals:
                task_in_time_interval = Bool(
                    "InTimeIntervalTask_%s_%i" % (task.name, uuid.uuid4().int)
                )
                lower_bound, upper_bound = time_interval
                cstrs = [
                    task.start >= lower_bound,
                    task.end <= upper_bound,
                    Not(
                        And(task.start < lower_bound, task.end > lower_bound)
                    ),  # overlap at start
                    Not(
                        And(task.start < upper_bound, task.end > upper_bound)
                    ),  # overlap at end
                    Not(And(task.start < lower_bound, task.end > upper_bound)),
                ]  # full overlap
                asst = Implies(task_in_time_interval, And(cstrs))
                self.set_assertions(asst)
                bools_for_this_task.append(task_in_time_interval)
            # only one maximum bool to True from the previous possibilities
            asst_tsk = PbLe([(scheduled, True) for scheduled in bools_for_this_task], 1)
            self.set_assertions(asst_tsk)
            all_bools.extend(bools_for_this_task)

        # we also have to exclude all the other cases, where start or end can be between two intervals
        # then set the constraint for the number of tasks to schedule
        asst_pb = problem_function[kind](
            [(scheduled, True) for scheduled in all_bools], nb_tasks_to_schedule
        )
        self.set_assertions(asst_pb)


#
# Task buffer constraints
#
class TaskUnloadBuffer(_Constraint):
    """A tasks that unloads a buffer"""

    def __init__(
        self,
        task,
        buffer,
        quantity,
        optional: Optional[bool] = False,
    ) -> None:
        super().__init__(optional)
        self.quantity = quantity
        self.task = task
        self.buffer = buffer
        self.quantity = quantity

        buffer.add_unloading_task(task, quantity)


class TaskLoadBuffer(_Constraint):
    """A task that loads a buffer"""

    def __init__(
        self,
        task,
        buffer,
        quantity,
        optional: Optional[bool] = False,
    ) -> None:
        super().__init__(optional)
        self.quantity = quantity
        self.task = task
        self.buffer = buffer
        self.quantity = quantity

        buffer.add_loading_task(task, quantity)
