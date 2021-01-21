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

from z3 import And, BoolRef, Implies, Xor

from processscheduler.base import _Constraint

#
# Task constraints base class
#
class _TaskConstraint(_Constraint):
    """ abstract class for task constraint.

    Task constraints only apply for scheduled tasks. If an optional
    tak is not schedules, then the constraint does not apply.
    """
    def __init__(self):
        super().__init__()

#
# Tasks constraints for two or more classes
#
class TaskPrecedence(_TaskConstraint):
    """ Task precedence relation """
    def __init__(self, task_before, task_after,
                 offset=0, kind='lax'):
        """ kind might be either LAX/STRICT/TIGHT
        Semantics : task after will start at least after offset periods
        task_before is finished.
        LAX constraint: task1_before_end + offset <= task_after_start
        STRICT constraint: task1_before_end + offset < task_after_start
        TIGHT constraint: task1_before_end + offset == task_after_start
        """
        super().__init__()

        if kind not in ['lax', 'strict', 'tight']:
            raise ValueError("kind must either be 'lax', 'strict' or 'tight'")

        if not isinstance(offset, int) or offset < 0:
            raise ValueError('offset must be a positive integer')

        self.offset = offset
        self.kind = kind

        if offset > 0:
            lower = task_before.end + offset
        else:
            lower = task_before.end
        upper = task_after.start

        if kind == 'lax':
            scheduled_assertion = lower <= upper
        elif kind == 'strict':
            scheduled_assertion = lower < upper
        else: # kind == 'tight':
            scheduled_assertion = lower == upper

        if task_before.optional or task_after.optional:
            # both tasks must be scheduled so that the precedence constraint applies
            self.add_assertion(Implies(And(task_before.scheduled, task_after.scheduled) , scheduled_assertion))
        else:
            self.add_assertion(scheduled_assertion)

class TasksStartSynced(_TaskConstraint):
    """ Two tasks that must start at the same time """
    def __init__(self, task_1, task_2) -> None:
        super().__init__()

        scheduled_assertion = task_1.start == task_2.start
        
        if task_1.optional or task_2.optional:
            # both tasks must be scheduled so that the startsynced constraint applies
            self.add_assertion(Implies(And(task_1.scheduled, task_2.scheduled)
                                       , scheduled_assertion))
        else:
            self.add_assertion(scheduled_assertion)

class TasksEndSynced(_TaskConstraint):
    """ Two tasks that must complete at the same time """
    def __init__(self, task_1, task_2) -> None:
        super().__init__()

        scheduled_assertion = task_1.end == task_2.end
        
        if task_1.optional or task_2.optional:
            # both tasks must be scheduled so that the endsynced constraint applies
            self.add_assertion(Implies(And(task_1.scheduled, task_2.scheduled) , scheduled_assertion))
        else:
            self.add_assertion(scheduled_assertion)

class TasksDontOverlap(_TaskConstraint):
    """ two tasks must not overlap, i.e. one needs to be completed before
    the other can be processed """
    def __init__(self, task_1, task_2) -> None:
        super().__init__()

        scheduled_assertion = Xor(task_2.start >= task_1.end,
                                  task_1.start >= task_2.end)
        
        if task_1.optional or task_2.optional:
            # if one task is not scheduledboth tasks must be scheduled so that the not overlap constraint applies
            self.add_assertion(Implies(And(task_1.scheduled, task_2.scheduled) , scheduled_assertion))
        else:
            self.add_assertion(scheduled_assertion)

#
# Task constraints for one single task
#
class TaskStartAt(_TaskConstraint):
    """ One task must start at the desired time """
    def __init__(self, task, value: int) -> None:
        super().__init__()
        self.value = value

        scheduled_assertion = task.start == value

        if task.optional:
            self.add_assertion(Implies(task.scheduled, scheduled_assertion))
        else:
            self.add_assertion(scheduled_assertion)

class TaskStartAfterStrict(_TaskConstraint):
    """ task.start > value """
    def __init__(self, task, value: int) -> None:
        super().__init__()
        self.value = value

        scheduled_assertion = task.start > value

        if task.optional:
            self.add_assertion(Implies(task.scheduled, scheduled_assertion))
        else:
            self.add_assertion(scheduled_assertion)

class TaskStartAfterLax(_TaskConstraint):
    """  task.start >= value  """
    def __init__(self, task, value: int) -> None:
        super().__init__()
        self.value = value

        scheduled_assertion = task.start >= value

        if task.optional:
            self.add_assertion(Implies(task.scheduled, scheduled_assertion))
        else:
            self.add_assertion(scheduled_assertion) 

class TaskEndAt(_TaskConstraint):
    """ On task must complete at the desired time """
    def __init__(self, task, value: int) -> None:
        super().__init__()
        self.value = value

        scheduled_assertion = task.end == value

        if task.optional:
            self.add_assertion(Implies(task.scheduled, scheduled_assertion))
        else:
            self.add_assertion(scheduled_assertion) 

class TaskEndBeforeStrict(_TaskConstraint):
    """ task.end < value """
    def __init__(self, task, value: int) -> None:
        super().__init__()
        self.value = value

        scheduled_assertion = task.end < value

        if task.optional:
            self.add_assertion(Implies(task.scheduled, scheduled_assertion))
        else:
            self.add_assertion(scheduled_assertion)

class TaskEndBeforeLax(_TaskConstraint):
    """ task.end <= value """
    def __init__(self, task, value: int) -> None:
        super().__init__()
        self.value = value

        scheduled_assertion = task.end <= value

        if task.optional:
            self.add_assertion(Implies(task.scheduled, scheduled_assertion))
        else:
            self.add_assertion(scheduled_assertion)
#
# Optional classes only constraints
#
class OptionalTaskConditionSchedule(_TaskConstraint):
    """An optional task that is schedule only a certain condition is fullfilled."""
    def __init__(self, task, condition: BoolRef) -> None:
        super().__init__()

        if not task.optional:
            raise ValueError('Task %s must be optional.' % task.name)

        self.add_assertion(Implies(condition, task.scheduled))

class OptionalTasksDependency(_TaskConstraint):
    """task_2 is scheduled if and only if task_1 is scheduled"""
    def __init__(self, task_1, task_2) -> None:
        super().__init__()

        if not task_2.optional:
            raise ValueError('Task %s must be optional.' % task_2.name)

        self.add_assertion(Implies(task_1.scheduled, task_2.scheduled))
