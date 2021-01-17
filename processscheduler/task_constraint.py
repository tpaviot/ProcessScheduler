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

from z3 import Xor

from processscheduler.base import _Constraint

#
# Task constraints base class
#
class _TaskConstraint(_Constraint):
    """ abstract class for task constraint """
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

        self.task_before = task_before
        self.task_after = task_after
        self.offset = offset
        self.kind = kind

        if offset > 0:
            lower = task_before.end + offset
        else:
            lower = task_before.end
        upper = task_after.start

        if kind == 'lax':
            self.add_assertion(lower <= upper)
        elif kind == 'strict':
            self.add_assertion(lower < upper)
        elif kind == 'tight':
            self.add_assertion(lower == upper)
        else:
            raise ValueError("Unknown precedence type")

        task_after.lower_bounded = True
        task_before.upper_bounded = True

    def __repr__(self):
        comp_chars = {'lax':'<=',
                      'strict':'<',
                      'tight': '==',
                     }
        return "Prcedence constraint: %s %s %s" % (self.task_before,
                                                   comp_chars[self.kind],
                                                   self.task_after)

class TasksStartSynced(_TaskConstraint):
    """ Two tasks that must start at the same time """
    def __init__(self, task_1, task_2) -> None:
        super().__init__()
        self.task_1 = task_1
        self.task_2 = task_2

        self.add_assertion(task_1.start == task_2.start)

class TasksEndSynced(_TaskConstraint):
    """ Two tasks that must complete at the same time """
    def __init__(self, task_1, task_2) -> None:
        super().__init__()
        self.task_1 = task_1
        self.task_2 = task_2

        self.add_assertion(task_1.end == task_2.end)


class TasksDontOverlap(_TaskConstraint):
    """ two tasks must not overlap, i.e. one needs to be completed before
    the other can be processed """
    def __init__(self, task_1, task_2) -> None:
        super().__init__()
        self.task_1 = task_1
        self.task_2 = task_2

        self.add_assertion(Xor(task_2.start >= task_1.end,
                               task_1.start >= task_2.end))

#
# Task constraints for one single task
#
class TaskStartAt(_TaskConstraint):
    """ One task must start at the desired time """
    def __init__(self, task, value: int) -> None:
        super().__init__()
        self.task = task
        self.value = value

        self.add_assertion(task.start == value)

class TaskStartAfterStrict(_TaskConstraint):
    """ task.start > value """
    def __init__(self, task, value: int) -> None:
        super().__init__()
        self.task = task
        self.value = value

        self.add_assertion(task.start > value)

        task.lower_bounded = True

class TaskStartAfterLax(_TaskConstraint):
    """  task.start >= value  """
    def __init__(self, task, value: int) -> None:
        super().__init__()
        self.task = task
        self.value = value

        self.add_assertion(task.start >= value)

        task.lower_bounded = True

class TaskEndAt(_TaskConstraint):
    """ On task must complete at the desired time """
    def __init__(self, task, value: int) -> None:
        super().__init__()
        self.task = task
        self.value = value

        self.add_assertion(task.end == value)

class TaskEndBeforeStrict(_TaskConstraint):
    """ task.end < value """
    def __init__(self, task, value: int) -> None:
        super().__init__()
        self.task = task
        self.value = value

        self.add_assertion(task.end < value)

        task.upper_bounded = True

class TaskEndBeforeLax(_TaskConstraint):
    """ task.end <= value """
    def __init__(self, task, value: int) -> None:
        super().__init__()
        self.task = task
        self.value = value

        self.add_assertion(task.end <= value)

        task.upper_bounded = True
