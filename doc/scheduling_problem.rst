SchedulingProblem
=================

The :class:`SchedulingProblem` class is the container for all modeling objects, such as tasks, resources and constraints.

.. warning::

    ProcessScheduler handles variables represented by **integer** values.

A :class:`SchedulingProblem` instance holds a *time* interval: the lower bound of this interval (the *initial time*) is always 0, the upper bound (the *final time*) can be set by passing the :attr:`horizon` attribute to the
:func:`__init__` method:

.. code-block:: python

    problem_modeling = SchedulingProblem('MySchedulingProblem', horizon=20)
 
The time interval is divided into a finite number of *periods*. Each period has a duration of 1. If :math:`horizon` is the horizon, then the number of periods is :math:`horizon` as well, and the number of points in the interval :math:`[0;horizon]` is :math:`horizon+1`.

.. image:: img/TimeLineHorizon.svg
    :align: center
    :width: 90%

A period is the finest granularity level that describes the time line, the task durations, and the schedule itself. The time line is dimensionless. It is up to you to map one period to the desired duration, in seconds/minutes/hours. For example:

- you need to schedule a set of tasks in a single day, let's say from 8 am to 6pm (office hours). The time interval is then 10 hours length. If you plan to schedule tasks with a granularity of 1 hour, then the horizon value will be 10 in order to get the desired number of periods:

.. math:: horizon = \frac{18-8}{1}=10

- you need to schedule a set of tasks in the morning, from 8 am to 12. The time interval is 4 hours. If you plan to schedule tasks with a granularity of 1 minute, then the horizon must be 240:

.. math:: horizon = \frac{12-8}{1/60}=240

.. note::
   The :attr:`horizon` attribute is optional. If it is not passed to the :meth:`__init__` method, the solver will search an horizon value compliant with the set of constraints. In the case where the scheduling problem aims at optimizing the horizon (e.g. a makespan objective), the horizon should not be set manually.
