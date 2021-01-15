Task
====

According to the `APICS dictionary <http://www.apics.org/>`_, a task may either be:

1. In project management, the lowest level to which work can be divided on a project

2. In activity-based cost accounting, a task, a subdivision of an activity, is the least amount of work. Tasks are used to describe activities.

In the context of this software library, the concept of task reflects the first point. The purpose of ProcessScheduler is to compute a sequence (a temporal ordering) of a collection of tasks that satisfy a set of constraints.

Start/end/duration
------------------

The :class:`Task` class and its derivatives represent any task. A :class:`Task` instance is defined by the three following parameters:

- :attr:`start`: a point in the :math:`[0, horizon]` integer interval. If the task is scheduled, then :math:`start>=0`

- :attr:`end`: a point in the :math:`[0, horizon]` integer interval. If the task is scheduled, then :math:`end>=start`

- :attr:`duration`: a integer number of periods, such as :math:`duration=end-start`

.. image:: img/Task.svg
    :align: center
    :width: 90%

.. note::
  :attr:`start` and :attr:`end` attributes can be constrained, but not set at the Task class instantiation.

Three :class:`Task` derivative classes can be used to represent a task:

- a :class:`ZeroDurationTask`: a task with :math:`duration=0`, that is to say :math:`start=end` when scheduled. Useful to represent project milestones, or other important points in time for the schedule

.. code-block:: python

    project_kickup = ZeroDurationTask('KickUp')

.. warning::

	Each :class:`Task` instance must have a unique name in the scheduling problem. To prevent that two tasks have the same name, ProcessScheduler raises an exception if ever a task with an existing name is created.

- a :class:`FixedDurationTask`: the task duration is known *a priori*, it will not be changed by the solver. In that case, you must pass the :attr:`duration` parameter when creating the instance:

.. code-block:: python

    # I assume one period to be mapped to 15min, cooking will be 1.5 hour
    cook_chicken = FixedDurationTask('CookChicken', duration=6)

- a :class:`VariableDurationTask`: a task for which the duration is not known and for which the solver is expected to find a value.

.. code-block:: python

    # The duration of this task will depend on the number of workers that hold boxes
    move_boxes = VariableDurationTask('MoveBoxesFromMachineAToInventory')

.. note::
  A :class:`VariableDurationTask` duration can be bounded by lower and upper values (a number of periods).

Work amount
-----------
The :attr:`work_amount` is the total amount of work that must be produced by the :class:`Task`. It is set to :const:`0` by default.

In a Formula 1 race, the 