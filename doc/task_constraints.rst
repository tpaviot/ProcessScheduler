****************
Task Constraints
****************
ProcessScheduler offers a comprehensive set of predefined temporal task constraints to help you express common scheduling rules efficiently. These constraints allow you to define task-related rules such as "Task A must start exactly at time 4," "Task B must end simultaneously with Task C," "Task C should be scheduled precisely 3 periods after Task D," and more.

.. note::

    Constraints that start with ``Task*`` apply to a single task, while those starting with ``Task**s***`` apply to two or more task instances.

.. note::

    All Task constraints can be defined as either mandatory or optional. By default, constraints are mandatory (parameter optional=False). If you set the optional attribute to True, the constraint becomes optional and may or may not apply based on the solver's discretion. You can force the schedule to adhere to an optional constraint using the task.applied attribute:

    .. code:: python

        pb.add_constraint([task.applied == True])


Single task temporal constraints
================================
These constraints apply to individual tasks.

TaskStartAt
-----------
Ensures that a tasks starts precisely at a specified time instant.

:class:`TaskStartAt`: takes two parameters :attr:`task` and :attr:`value` such as the task starts exactly at the instant :math:`task.start = value`

TaskStartAfter
--------------
Enforces that a task must start after a given time instant.

:class:`TaskStartAfterStrict`: the constraint  :math:`task.start > value`
can be strict lor lax.

TaskEndAt
---------
Ensures that a task ends precisely at a specified time instant.

- :class:`TaskEndAt`: takes two parameters :attr:`task` and :attr:`value` such as the task ends exactly at the instant *value* :math:`task.end = value`

TaskEndBefore
-------------
Requires that a task ends before or at a given time instant.

- :class:`TaskEndBeforeStrict`: the constraint :math:`task.end < value`
can be strict or lax.

Two tasks temporal constraints
==============================
These constraints apply to sets of two tasks.

TaskPrecedence
--------------
Ensures that one task is scheduled before another. The precedence can be either 'lax,' 'strict,' or 'tight,' and an optional offset can be applied.

The :class:`TaskPrecedence` class takes two parameters :attr:`task_1` and :attr:`task_2` and constraints :attr:`task_2` to be scheduled after :attr:`task_1` is completed. The precedence type can either be :const:`'lax'` (default, :attr:`task_2.start` >= :attr:`task_1.end`)), :const:`'strict'` (:attr:`task_2.start` >= :attr:`task_1.end`)) or :const:`'tight'` (:attr:`task_2.start` >= :attr:`task_1.end`, task_2 starts immediately after task_1 is completed). An optional parameter :attr:`offset` can be additionally set.

.. code-block:: python

    task_1 = ps.FixedDurationTask('Task1', duration=3)
    task_2 = ps.FixedVariableTask('Task2')
    pc = TaskPrecedence(task1, task2, kind='tight', offset=2)

constraints the solver to schedule task_2 start exactly 2 periods after task_1 is completed.

TasksStartSynced
----------------
Specify that two tasks must start at the same time.

:class:`TasksStartSynced` takes two parameters :attr:`task_1` and :attr:`task_2` such as the schedule must satisfy the constraint :math:`task_1.start = task_2.start`

.. image:: img/TasksStartSynced.svg
    :align: center
    :width: 90%

TasksEndSynced
--------------
Specify that two tasks must end at the same time.

:class:`TasksEndSynced` takes two parameters :attr:`task_1` and :attr:`task_2` such as the schedule must satisfy the constraint :math:`task_1.end = task_2.end`

.. image:: img/TasksEndSynced.svg
    :align: center
    :width: 90%

TasksDontOverlap
----------------
Ensures that two tasks should not overlap in time.

:class:`TasksDontOverlap` takes two parameters :attr:`task_1` and :attr:`task_2` such as the task_1 ends before the task_2 is started or the opposite (task_2 ends before task_1 is started)

.. image:: img/TasksDontOverlap.svg
    :align: center
    :width: 90%

$n$ tasks temporal constraints
==============================

TasksContiguous
---------------
Forces a set of tasks to be scheduled contiguously.

:class:`TasksContiguous` takes a liste of tasks, force the schedule so that tasks are contiguous.

UnorderedTaskGroup
------------------
An UnorderedTaskGroup represents a collection of tasks that can be scheduled in any order. This means that the tasks within this group do not have a strict temporal sequence.

OrderedTaskGroup
------------------
A set of tasks that can be scheduled in any order, with time bounds

Advanced tasks constraints
==========================

ScheduleNTasksInTimeIntervals
-----------------------------
Schedules a specific number of tasks within defined time intervals.

Given a list of :math:`m` tasks, and a list of time intervals, :class:`ScheduleNTasksInTimeIntervals` schedule :math:`N` tasks among :math:`m` in this time interval.

ResourceTasksDistance
---------------------
Defines constraints on the temporal distance between tasks using a shared resource.

:class:`ResourceTasksDistance` takes a mandatory attribute :attr:`distance` (integer), an optional :attr:`time_periods` (list of couples of integers e.g. [[0, 1], [5, 19]]). All tasks, that use the given resource, scheduled within the :attr:`time_periods` must have a maximal distance of :attr:`distance` (distance being considered as the time between two consecutive tasks).

.. note::

    If the task(s) is (are) optional(s), all these constraints apply only if the task is scheduled. If the solver does not schedule the task, these constraints does not apply.

Logical task constraints
========================

OptionalTaskConditionSchedule
-----------------------------
Creates a constraint that schedules a task based on a specified Boolean condition.

:class:`OptionalTaskConditionSchedule` creates a constraint that adds a condition for the task to be scheduled. The condition is a z3 BoolRef

OptionalTasksDependency
-----------------------
:class:`OptionalTasksDependency` takes two optional tasks :attr:`task_1` and :attr:`task_2`, and ensures that if task_1 is scheduled then that task_2 is forced to be scheduled as well.

ForceScheduleNOptionalTasks
---------------------------
Forces the scheduling of a specified number of optional tasks out of a larger set of optional tasks.

:class:`ForceScheduleNOptionalTasks` forces :math:`m` optional tasks among :math:`n` to be scheduled, with :math:`m \leq n`.
