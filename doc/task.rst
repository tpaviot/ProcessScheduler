Task
====

According to the `APICS dictionary <http://www.apics.org/>`_, a task may either be:

1. In project management, the lowest level to which work can be divided on a project

2. In activity-based cost accounting, a task, a subdivision of an activity, is the least amount of work. Tasks are used to describe activities.

In the context of the this software library, the concept of task reflects the first point. The purpose of ProcessScheduler is to provide a sequence (a temporal ordering) of a collection of tasks.

The Task class
--------------

A :class:`Task` is defined by the three parameters:

- :attr:`start`: a point in the :math:`[0, horizon]` integer interval. If the task is scheduled, then :math:`start>=0`

- :attr:`end`: a point in the :math:`[0, horizon]` integer interval. If the task is scheduled, then :math:`end>=start`

- :attr:`duration`: a integer number of periods, such as :math:`duration=end-start`

.. image:: img/Task.svg
    :align: center
    :width: 90%

.. note::
  :attr:`start` and :attr:`end` attributes can be constrained, but not set at the Task class instantiation.

Three base Task objects can be used to represent a task:

- a :class:`ZeroDurationTask`: a task with :math:`duration=0`, that is to say :math:`start=end` when scheduled. Useful to represent project milestones, or other important points in time for the schedule

.. code-block:: python

    project_kickup = ZeroDurationTask('KickUp')

- a :class:`FixedDurationTask`: you know a priori the task duration, it will not be changed by the solver. In that case, you must pass the :attr:`duration` parameter when creating the instance:

.. code-block:: python

    # I assume one period to be mapped to 15min, cooking will be 1.5 hour
    cook_chicken = FixedDurationTask('CookChicken', duration=6)

- a :class:`VariableDurationTask`: a task for which you do not know the duration or for which you want to leave the solver suggest a value.

.. code-block:: python

    # The duration of this task will depend on the number of workers that hold boxes
    move_boxes = VariableDurationTask('MoveBoxesFromMachineAToInventory')

.. note::
  A :class:`VariableDurationTask` duration can be bounded by lower and upper values (a number of periods).


Task Constraints
----------------
Task constraints are temporal first-order logic assertions between task variables. They allow expressing rules such as "the task A must start exactly at the instant 4", "the task B must end at the same time than the task C ends", "the task C must be scheduled exactly 3 periods after the task D is completed" etc.

There are a set of builtin ready-to-use constraints, listed below. In the :ref:`advanced-constraints` section you will see how to build your own constraints.

Builtin constraints: if the class name starts with *Task* then the constraint applies to one single task, if the class name starts with *Tasks* it applies to 2 task instances.

- :class:`TaskPrecedence`

- :class:`TasksStartSynced`: takes two parameters :attr:`task_1` and :attr:`task_2` such as the schedule must satisfy the constraint :math:`task_1.start = task_2.start`

.. image:: img/TasksStartSynced.svg
    :align: center
    :width: 90%

- :class:`TasksEndSynced`: takes two parameters :attr:`task_1` and :attr:`task_2` such as the schedule must satisfy the constraint :math:`task_1.end = task_2.end`

.. image:: img/TasksEndSynced.svg
    :align: center
    :width: 90%

- :class:`TasksDontOverlap`: takes two parameters :attr:`task_1` and :attr:`task_2` such as the task_1 ends before the task_2 istarted or the opposite (task_2 ends before task_1 is started)

.. image:: img/TasksDontOverlap.svg
    :align: center
    :width: 90%

- :class:`TaskStartAt`: takes two parameters :attr:`task` and :attr:`value` such as the task starts exactly at the instant *value* :math:`task.start = value`

- :class:`TaskStartAfterStrict`: takes two parameters :attr:`task` and :attr:`value` such as the task starts strictly after the instant *value* :math:`task.start > value`

- :class:`TaskStartAfterLax`: takes two parameters :attr:`task` and :attr:`value` such as the task starts after the instant *value* :math:`task.start >= value`

- :class:`TaskEndAt`: takes two parameters :attr:`task` and :attr:`value` such as the task ends exactly at the instant *value* :math:`task.end = value`

- :class:`TaskEndBeforeStrict`: takes two parameters :attr:`task` and :attr:`value` such as the task ends strictly before the instant *value* :math:`task.end < value`

- :class:`TaskEndBeforeLax`: takes two parameters :attr:`task` and :attr:`value` such as the task ends before the instant *value* :math:`task.end <= value`
