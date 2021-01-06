SchedulingProblem
=================

The :class:`SchedulingProblem` class is the container for all modeling objects, such as tasks, resources and constraints.

A :class:`SchedulingProblem` instance holds a *time* interval: the lower bound of this interval (the *initial time*) is always 0, the upper bound (the *final time*) can be set by passing the :attr:`horizon` attribute to the
:func:`__init__` method:

.. code-block:: python

    problem_modeling = SchedulingProblem('MySchedulingProblem', horizon=20)
 
The time interval is divided into a finite number of *periods*. Each period has a duration of 1. Let :math:`horizon` be the horizon, then the number of periods is :math:`horizon` as well, and the number of points in the interval :math:`[0;horizon]` is :math:`horizon+1`.

.. image:: img/TimeLineHorizon.svg
    :align: center
    :width: 90%

A period is the finest granularity that describes the time line, the task durations, and the schedule itself. The time line is dimensionless. It is up to you to map one period to the desired duration, in seconds/minutes/hours. For example:

- you need to schedule a set of tasks in a single day, let's say from 8 am to 6pm (office hours). The time interval is 10 hours length. If you plan to schedule tasks with a granularity of 1 hour, then the horizon value will be 10:

.. math:: horizon = \frac{18-8}{1}=10

- you need to schedule a set of tasks in the morning, from 8 am to 12. The time interval is 4 hours. If you plan to schedule tasks with a granularity of 1 minute, then the horizon must be 240:

.. math:: horizon = \frac{12-8}{1/60}=240

.. note::
   The :attr:`horizon` attribute is optional. If its not passed to the :class:`SchedulingProblem` instantiation, the solver will later find an horizon value compliant with the set of constraints. In the case where your scheduling problem aims at optimizing the horizon (e.g. a makespan objective), then don't set the horizon at startup.
