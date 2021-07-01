SchedulingProblem
=================

The :class:`SchedulingProblem` class is the container for all modeling objects, such as tasks, resources and constraints.

Time slots as integers
----------------------

A :class:`SchedulingProblem` instance holds a *time* interval: the lower bound of this interval (the *initial time*) is always 0, the upper bound (the *final time*) can be set by passing the :attr:`horizon` attribute to the
:func:`__init__` method:

.. code-block:: python

    my_problem = SchedulingProblem('MySchedulingProblem', horizon=20)
 
The time interval is divided into a finite number of *periods*. Each period has a duration of 1. If :math:`horizon` is the horizon, then the number of periods is :math:`horizon` as well, and the number of points in the interval :math:`[0;horizon]` is :math:`horizon+1`.

.. image:: img/TimeLineHorizon.svg
    :align: center
    :width: 90%

.. warning::

    ProcessScheduler handles variables represented by **integer** values.

A period is the finest granularity level that describes the time line, the task durations, and the schedule itself. The time line is dimensionless. It is up to you to map one period to the desired duration, in seconds/minutes/hours. For example:

- you need to schedule a set of tasks in a single day, let's say from 8 am to 6pm (office hours). The time interval is then 10 hours length. If you plan to schedule tasks with a granularity of 1 hour, then the horizon value will be 10 in order to get the desired number of periods:

.. math:: horizon = \frac{18-8}{1}=10

- you need to schedule a set of tasks in the morning, from 8 am to 12. The time interval is 4 hours. If you plan to schedule tasks with a granularity of 1 minute, then the horizon must be 240:

.. math:: horizon = \frac{12-8}{1/60}=240

.. note::
   The :attr:`horizon` attribute is optional. If it is not passed to the :meth:`__init__` method, the solver will search an horizon value compliant with the set of constraints. In the case where the scheduling problem aims at optimizing the horizon (e.g. a makespan objective), the horizon should not be set manually.

Mapping integers to datetime objects
------------------------------------

Because a Gantt chart if much more readable if real dates are represented instead of integers, it is possible to explicitly set the values in second, minutes, hours etc. The integer ``1``, i.e. the smallest time duration for a task, can be mapped to a ``timedelta`` python object. Any instant can be mapped to a ``datetime`` python object.

Python ``timedelta`` objects are created with python:

.. code:: python

    from datetime import timedelta
    delta = timedelta(days=50,
                      seconds=27,
                      microseconds=10,
                      milliseconds=29000,
                      minutes=5,
                      hours=8,
                      weeks=2)

For ``datetime`` objects:

.. code:: python

    from datetime import datetime
    now = datetime.now()

These attribute values can be passed to the SchedulingProblem initialization method:

.. code:: python

    problem = ps.SchedulingProblem('DateTimeBase',
                                    horizon=7,
                                    delta_time=timedelta(minutes=15),
                                    start_time=datetime.now())

After the solver has completed the solution, the end times, start times and durations are exported either to the Gantt chart or any other output type.

.. note::

    Users should refer to the `datetime python package documentation <https://docs.python.org/3/library/datetime.html>`_.
