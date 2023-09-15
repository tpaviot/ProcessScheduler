******************
Scheduling problem
******************

The :class:`SchedulingProblem` class is the container for all modeling objects, such as tasks, resources and constraints.

Time slots as integers
======================
A :class:`SchedulingProblem` instance holds a *time* interval: the lower bound of this interval (the *initial time*) is always 0, the upper bound (the *final time*) can be set by passing the :attr:`horizon` attribute to the :func:`__init__` method:

.. code-block:: python

    my_problem = SchedulingProblem('MySchedulingProblem', horizon=20)

The interval's duration is subdivided into discrete units called *periods*, each with a fixed duration of 1. If :math:`horizon` is set to a value, then the number of periods is equal to :math:`horizon`, and the number of points within the interval :math:`[0;horizon]` is :math:`horizon+1`.

.. image:: img/TimeLineHorizon.svg
    :align: center
    :width: 90%

.. warning::

    ProcessScheduler handles variables using **integer** values.

A period represents the finest granularity level for defining the timeline, task durations, and the schedule itself. This timeline is dimensionless, allowing you to map a period to your desired duration, be it in seconds, minutes, hours, or any other unit. For instance:

- If you aim to schedule tasks within a single day, say from 8 am to 6 pm (office hours), resulting in a 10-hour time interval, and you plan to schedule tasks in 1-hour intervals, then the horizon value should be set to 10 to achieve the desired number of periods:

.. math:: horizon = \frac{18-8}{1}=10

- If your task scheduling occurs in the morning, from 8 am to 12 pm, resulting in a 4-hour time interval, and you intend to schedule tasks in 1-minute intervals, then the horizon value must be 240:

.. math:: horizon = \frac{12-8}{1/60}=240

.. note::
    The :attr:`horizon` attribute is optional. If it's not explicitly provided during the :meth:`__init__` method, the solver will determine an appropriate horizon value that complies with the defined constraints. In cases where the scheduling problem aims to optimize the horizon, such as achieving a specific makespan objective, manual setting of the horizon is not necessary.


Mapping integers to datetime objects
====================================
To enhance the readability of Gantt charts and make schedules more intuitive, ProcessScheduler allows you to represent time intervals in real dates and times rather than integers. You can explicitly set time values in seconds, minutes, hours, and more. The smallest time duration for a task, represented by the integer `1`, can be mapped to a Python `timedelta` object. Similarly, any point in time can be mapped to a Python `datetime` object.

Creating Python timedelta objects can be achieved as follows:

.. code:: python

    from datetime import timedelta
    delta = timedelta(days=50,
                      seconds=27,
                      microseconds=10,
                      milliseconds=29000,
                      minutes=5,
                      hours=8,
                      weeks=2)

For Python `datetime` objects, you can create them like this:

.. code:: python

    from datetime import datetime
    now = datetime.now()

These attribute values can be provided to the SchedulingProblem initialization method as follows:

.. code:: python

    problem = ps.SchedulingProblem('DateTimeBase',
                                    horizon=7,
                                    delta_time=timedelta(minutes=15),
                                    start_time=datetime.now())

Once the solver has completed its work and generated a solution, you can export the end times, start times, and durations to the Gantt chart or any other output format.

.. note::

    For more detailed information on Python's `datetime package documentation <https://docs.python.org/3/library/datetime.html>`_ and its capabilities, please refer to the datetime Python package documentation. This documentation provides comprehensive guidance on working with date and time objects in Python.
