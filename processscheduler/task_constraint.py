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
from typing import Optional, Literal, List, Tuple, Union

from z3 import And, Bool, BoolRef, If, Implies, Int, Not, Or, PbEq, PbGe, PbLe, Xor

from processscheduler.constraint import TaskConstraint
from processscheduler.task import Task
from processscheduler.buffer import NonConcurrentBuffer
from processscheduler.util import sort_no_duplicates

from pydantic import Field, PositiveInt


#
# Task groups
#
class TaskGroup(TaskConstraint):
    list_of_tasks: List[Task]
    time_interval: Tuple[int, int] = Field(default=None)
    time_interval_length: int = Field(default=0)

    def __init__(self, **data) -> None:
        super().__init__(**data)

        u_id = uuid.uuid4().int
        self._start = Int(f"task_group_start_{u_id}")
        self._end = Int(f"task_group_end_{u_id}")

        if self.time_interval is not None:
            self._scheduled_assertion = [
                self._start >= self.time_interval[0],
                self._end <= self.time_interval[1],
            ]
        elif self.time_interval_length is not None:
            self._scheduled_assertion = [
                self._end <= self._start + self.time_interval_length
            ]

        for task in self.list_of_tasks:
            self._scheduled_assertion += [
                task._start >= self._start,
                task._end <= self._end,
            ]


class UnorderedTaskGroup(TaskGroup):
    """A set of tasks that can be scheduled in any order, with time bounds."""

    def __init__(self, **data) -> None:
        super().__init__(**data)

        self.set_z3_assertions(And(self._scheduled_assertion))


class OrderedTaskGroup(TaskGroup):
    """A set of tasks that can be scheduled in a specified order, with time bounds."""

    kind: Literal["lax", "strict", "tight"] = Field(default="lax")

    def __init__(self, **data) -> None:
        super().__init__(**data)
        # add a constraint between each task
        for i in range(len(self.list_of_tasks) - 1):
            if self.kind == "lax":
                self._scheduled_assertion += [
                    self.list_of_tasks[i]._end <= self.list_of_tasks[i + 1]._start
                ]
            elif self.kind == "strict":
                self._scheduled_assertion += [
                    self.list_of_tasks[i]._end < self.list_of_tasks[i + 1]._start
                ]
            else:  # kind == 'tight':
                self._scheduled_assertion += [
                    self.list_of_tasks[i]._end == self.list_of_tasks[i + 1]._start
                ]

        self.set_z3_assertions(And(self._scheduled_assertion))


#
# Tasks constraints for two or more classes
#
class TaskPrecedence(TaskConstraint):
    """Task precedence relation"""

    task_before: Union[Task, TaskGroup]
    task_after: Union[Task, TaskGroup]
    offset: int = Field(default=0, ge=0)
    kind: Literal["lax", "strict", "tight"] = Field(default="lax")

    def __init__(self, **data) -> None:
        super().__init__(**data)
        """kind might be either LAX/STRICT/TIGHT
        Semantics : task after will start at least after offset periods
        task_before is finished.
        LAX constraint: task1_before_end + offset <= task_after_start
        STRICT constraint: task1_before_end + offset < task_after_start
        TIGHT constraint: task1_before_end + offset == task_after_start
        """

        lower = (
            self.task_before._end + self.offset
            if self.offset > 0
            else self.task_before._end
        )
        upper = self.task_after._start

        if self.kind == "lax":
            scheduled_assertion = lower <= upper
        elif self.kind == "strict":
            scheduled_assertion = lower < upper
        else:  # kind == 'tight':
            scheduled_assertion = lower == upper

        if self.task_before.optional or self.task_after.optional:
            # both tasks must be scheduled so that the precedence constraint applies
            self.set_z3_assertions(
                Implies(
                    And(self.task_before._scheduled, self.task_after._scheduled),
                    scheduled_assertion,
                )
            )
        else:
            self.set_z3_assertions(scheduled_assertion)


class TasksStartSynced(TaskConstraint):
    """Two tasks that must start at the same time"""

    task_1: Task
    task_2: Task

    def __init__(self, **data) -> None:
        super().__init__(**data)

        scheduled_assertion = self.task_1._start == self.task_2._start

        if self.task_1.optional or self.task_2.optional:
            # both tasks must be scheduled so that the startsynced constraint applies
            self.set_z3_assertions(
                Implies(
                    And(self.task_1._scheduled, self.task_2._scheduled),
                    scheduled_assertion,
                )
            )
        else:
            self.set_z3_assertions(scheduled_assertion)


class TasksEndSynced(TaskConstraint):
    """Two tasks that must complete at the same time"""

    task_1: Task
    task_2: Task

    def __init__(self, **data) -> None:
        super().__init__(**data)

        scheduled_assertion = self.task_1._end == self.task_2._end

        if self.task_1.optional or self.task_2.optional:
            # both tasks must be scheduled so that the endsynced constraint applies
            self.set_z3_assertions(
                Implies(
                    And(self.task_1._scheduled, self.task_2._scheduled),
                    scheduled_assertion,
                )
            )
        else:
            self.set_z3_assertions(scheduled_assertion)


class TasksDontOverlap(TaskConstraint):
    """Two tasks must not overlap, i.e. one needs to be completed before
    the other can be processed"""

    task_1: Task
    task_2: Task

    def __init__(self, **data) -> None:
        super().__init__(**data)

        scheduled_assertion = Xor(
            self.task_2._start >= self.task_1._end,
            self.task_1._start >= self.task_2._end,
        )

        if self.task_1.optional or self.task_2.optional:
            # if one task is not scheduledboth tasks must be scheduled so that the not overlap constraint applies
            self.set_z3_assertions(
                Implies(
                    And(self.task_1._scheduled, self.task_2._scheduled),
                    scheduled_assertion,
                )
            )
        else:
            self.set_z3_assertions(scheduled_assertion)


class TasksContiguous(TaskConstraint):
    """A list of tasks are scheduled contiguously."""

    list_of_tasks: List[Task]

    def __init__(self, **data) -> None:
        super().__init__(**data)

        starts = [t._start for t in self.list_of_tasks]
        ends = [t._end for t in self.list_of_tasks]
        # sort both lists
        sorted_starts, constraints_start = sort_no_duplicates(starts)
        sorted_ends, constraints_end = sort_no_duplicates(ends)
        for all_constraints in constraints_start + constraints_end:
            self.set_z3_assertions(all_constraints)
        # from now, starts and ends are sorted in asc order
        # the space between two consecutive tasks is the sorted_start[i+1]-sorted_end[i]
        # we just have to constraint this variable
        for i in range(1, len(sorted_starts)):
            asst = sorted_starts[i] == sorted_ends[i - 1]
            #  another set of conditions, related to the time periods
            condition_only_scheduled_tasks = And(
                sorted_ends[i - 1] >= 0, sorted_starts[i] >= 0
            )
            # finally create the constraint
            new_cstr = Implies(Or(condition_only_scheduled_tasks), asst)
            self.set_z3_assertions(new_cstr)


#
# Task constraints for one single task
#
class TaskStartAt(TaskConstraint):
    """One task must start at the desired time"""

    task: Task
    value: int

    def __init__(self, **data) -> None:
        super().__init__(**data)

        scheduled_assertion = self.task._start == self.value

        if self.task.optional:
            self.set_z3_assertions(Implies(self.task._scheduled, scheduled_assertion))
        else:
            self.set_z3_assertions(scheduled_assertion)


class TaskStartAfter(TaskConstraint):
    task: Task
    value: int
    kind: Literal["lax", "strict"] = Field(default="lax")

    def __init__(self, **data) -> None:
        super().__init__(**data)

        if self.kind == "strict":
            scheduled_assertion = self.task._start > self.value
        elif self.kind == "lax":
            scheduled_assertion = self.task._start >= self.value

        if self.task.optional:
            self.set_z3_assertions(Implies(self.task._scheduled, scheduled_assertion))
        else:
            self.set_z3_assertions(scheduled_assertion)


class TaskEndAt(TaskConstraint):
    """On task must complete at the desired time"""

    task: Task
    value: int

    def __init__(self, **data) -> None:
        super().__init__(**data)

        scheduled_assertion = self.task._end == self.value

        if self.task.optional:
            self.set_z3_assertions(Implies(self.task._scheduled, scheduled_assertion))
        else:
            self.set_z3_assertions(scheduled_assertion)


class TaskEndBefore(TaskConstraint):
    """task.end < value"""

    task: Task
    value: int
    kind: Literal["lax", "strict"] = Field(default="lax")

    def __init__(self, **data) -> None:
        super().__init__(**data)

        if self.kind == "strict":
            scheduled_assertion = self.task._end < self.value
        elif self.kind == "lax":
            scheduled_assertion = self.task._end <= self.value

        if self.task.optional:
            self.set_z3_assertions(Implies(self.task._scheduled, scheduled_assertion))
        else:
            self.set_z3_assertions(scheduled_assertion)


#
# Optional classes only constraints
#
class OptionalTaskConditionSchedule(TaskConstraint):
    """An optional task that is scheduled only if a condition is fulfilled."""

    task: Task
    condition: BoolRef

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data) -> None:
        super().__init__(**data)

        if not self.task.optional:
            raise TypeError(f"Task {self.task.name} must be optional.")

        self.set_z3_assertions(
            If(
                self.condition,
                self.task._scheduled == True,
                self.task._scheduled == False,
            )
        )


class OptionalTasksDependency(TaskConstraint):
    """task_2 is scheduled if and only if task_1 is scheduled"""

    task_1: Task
    task_2: Task

    def __init__(self, **data) -> None:
        super().__init__(**data)

        if not self.task_2.optional:
            raise TypeError(f"Task {self.task_2.name} must be optional.")

        self.set_z3_assertions(self.task_1._scheduled == self.task_2._scheduled)


class ForceScheduleNOptionalTasks(TaskConstraint):
    """Given a set of m different optional tasks, force the solver to schedule
    at at least/at most/exactly n tasks, with 0 < n <= m."""

    list_of_optional_tasks: List[Task]
    nb_tasks_to_schedule: PositiveInt = Field(default=1)
    kind: Literal["min", "max", "exact"] = Field(default="exact")

    def __init__(self, **data) -> None:
        super().__init__(**data)

        problem_function = {"min": PbGe, "max": PbLe, "exact": PbEq}

        # first check that all tasks from the list_of_optional_tasks are
        # actually optional
        for task in self.list_of_optional_tasks:
            if not task.optional:
                raise TypeError(
                    "The task {task.name} must expilicitly be set as optional."
                )
        # all scheduled variables to take into account
        sched_vars = [task._scheduled for task in self.list_of_optional_tasks]
        asst = problem_function[self.kind](
            [(scheduled, True) for scheduled in sched_vars], self.nb_tasks_to_schedule
        )
        self.set_z3_assertions(asst)


class ScheduleNTasksInTimeIntervals(TaskConstraint):
    """Given a set of m different tasks, and a list of time intervals, schedule N tasks among m
    in this time interval"""

    list_of_tasks: List[Task]
    nb_tasks_to_schedule: int
    list_of_time_intervals: List[Tuple[int, int]]
    kind: Literal["min", "max", "exact"] = Field(default="exact")

    def __init__(self, **data) -> None:
        super().__init__(**data)

        problem_function = {"min": PbGe, "max": PbLe, "exact": PbEq}

        # count the number of tasks that re scheduled in this time interval
        all_bools = []
        for task in self.list_of_tasks:
            # for this task, the logic expression is that any of its start or end must be
            # between two consecutive intervals
            bools_for_this_task = []
            for time_interval in self.list_of_time_intervals:
                task_in_time_interval = Bool(
                    "InTimeIntervalTask_%s_%i" % (task.name, uuid.uuid4().int)
                )
                lower_bound, upper_bound = time_interval
                cstrs = [
                    task._start >= lower_bound,
                    task._end <= upper_bound,
                    Not(
                        And(task._start < lower_bound, task._end > lower_bound)
                    ),  # overlap at start
                    Not(
                        And(task._start < upper_bound, task._end > upper_bound)
                    ),  # overlap at end
                    Not(And(task._start < lower_bound, task._end > upper_bound)),
                ]  # full overlap
                asst = Implies(task_in_time_interval, And(cstrs))
                self.set_z3_assertions(asst)
                bools_for_this_task.append(task_in_time_interval)
            # only one maximum bool to True from the previous possibilities
            asst_tsk = PbLe([(scheduled, True) for scheduled in bools_for_this_task], 1)
            self.set_z3_assertions(asst_tsk)
            all_bools.extend(bools_for_this_task)

        # we also have to exclude all the other cases, where start or end can be between two intervals
        # then set the constraint for the number of tasks to schedule
        asst_pb = problem_function[self.kind](
            [(scheduled, True) for scheduled in all_bools], self.nb_tasks_to_schedule
        )
        self.set_z3_assertions(asst_pb)


#
# Task buffer constraints
#
class TaskUnloadBuffer(TaskConstraint):
    """A tasks that unloads a buffer"""

    task: Task
    buffer: NonConcurrentBuffer
    quantity: int

    def __init__(self, **data) -> None:
        super().__init__(**data)

        self.buffer.add_unloading_task(self.task, self.quantity)


class TaskLoadBuffer(TaskConstraint):
    """A task that loads a buffer"""

    task: Task
    buffer: NonConcurrentBuffer
    quantity: int

    def __init__(self, **data) -> None:
        super().__init__(**data)

        self.buffer.add_loading_task(self.task, self.quantity)
