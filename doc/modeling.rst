Scheduling problem modeling
===========================

There are a variety of command line tools provided by the cxxheaderparser
project.

SchedulingProblem
-----------------

The :class:`SchedulingProblem` class is the container for all modeling objects, such as tasks, resources and constraints.

A :class:`SchedulingProblem` instance holds a *time* interval: the lower bound of this interval (the *initial time*) is always 0, the upper bound (the *final time*) can be set by passing the :attr:`horizon` attribute to the
:func:`__init__` method:

.. code-block:: python

    problem_modeling = SchedulingProblem('MySchedulingProblem', horizon=20)
 
The time interval is divided into a finite number of *periods*. Each period has a duration of 1. Let :math:`horizon` be the horizon, then the number of periods is :math:`horizon` as well, and the number of points in the interval (the *instants*) is :math:`horizon+1`.

A period is the finest granularity that describes the time line, the task durations, and the schedule itself. The time line is dimensionless. It is up to you to map one period to the desired duration, in seconds/minutes/hours. For example:

- you need to schedule a set of tasks in a single day, let's say from 8 am to 6pm (office hours). The time interval is 10 hours length. If you plan to schedule tasks with a granularity of 1 hour, then the horizon value will be 10:

.. math:: horizon = \frac{18-8}{1}=10

- you need to schedule a set of tasks in the morning, from 8 am to 12. The time interval is 4 hours. If you plan to schedule tasks with a granularity of 1 minute, then the horizon must be 240:

.. math:: horizon = \frac{12-8}{1/60}=240

.. note::
   The :attr:`horizon` attribute is optional. If its not passed to the :class:`SchedulingProblem` instantiation, the solver will later find an horizon value compliant with the set of constraints. In the case where your scheduling problem aims at optimizing the horizon (e.g. a makespan objective), then don't set the horizon at startup.

Tasks
-----
A :class:`Task` is defined by the three parameters:

- :attr:`start`: a point in the :math:`[0, horizon]` integer interval. If the task is scheduled, then :math:`start>=0`

- :attr:`end`: a point in the :math:`[0, horizon]` integer interval. If the task is scheduled, then :math:`end>=start`

- :attr:`duration`: a integer number of periods. Of course :math:`start+duration=end`


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

.. note::
  A :class:`VariableDurationTask` duration can be bounded by lower and upper values (a number of periods).

.. code-block:: python

    # The duration of this task will depend on the number of workers that hold boxes
    move_boxes = VariableDurationTask('MoveBoxesFromMachineAToInventory')

Task Constraints
----------------
Task constraints are temporal first-order logic assertions between task variables. They allow expressing rules such as "the task A must start exactly at the instant 4", "the task B must end at the same time than the task C ends", "the task C must be scheduled exactly 3 periods after the task D is completed" etc.

There are a set of builtin ready-to-use constraints, listed below. In the :ref:`advanced-constraints` section you will see how to build your own constraints.

Builtin constraints: if the class name starts with *Task* then the constraint applies to one single task, if the class name starts with *Tasks* it applies to 2 task instances.

- :class:`TaskPrecedence`

- :class:`TasksStartSynced`: takes two parameters :attr:`task_1` and :attr:`task_2` such as the schedule must satisfy the constraint :math:`task_1.start = task_2.start`

- :class:`TasksEndSynced`: takes two parameters :attr:`task_1` and :attr:`task_2` such as the schedule must satisfy the constraint :math:`task_1.end = task_2.end`

- :class:`TasksDontOverlap`: takes two parameters :attr:`task_1` and :attr:`task_2` such as the task_1 ends before the task_2 istarted or the opposite (task_2 ends before task_1 is started)

- :class:`TaskStartAt`: takes two parameters :attr:`task` and :attr:`value` such as the task starts exactly at the instant *value* :math:`task.start = value`

- :class:`TaskStartAfterStrict`: takes two parameters :attr:`task` and :attr:`value` such as the task starts strictly after the instant *value* :math:`task.start > value`

- :class:`TaskStartAfterLax`: takes two parameters :attr:`task` and :attr:`value` such as the task starts after the instant *value* :math:`task.start >= value`

- :class:`TaskEndAt`: takes two parameters :attr:`task` and :attr:`value` such as the task ends exactly at the instant *value* :math:`task.end = value`

- :class:`TaskEndBeforeStrict`: takes two parameters :attr:`task` and :attr:`value` such as the task ends strictly before the instant *value* :math:`task.end < value`

- :class:`TaskEndBeforeLax`: takes two parameters :attr:`task` and :attr:`value` such as the task ends before the instant *value* :math:`task.end <= value`

Workers
-------
The Worker class.
