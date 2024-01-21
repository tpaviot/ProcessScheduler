# Scheduling problem

The `SchedulingProblem` class is the container for all modeling objects, such as tasks, resources and constraints.

!!! note

    Creating a `SchedulingProblem` is the first step of the Python script. 

## Time slots as integers

A `SchedulingProblem` instance holds a *time* interval: the lower bound of this interval (the *initial time*) is always 0, the upper bound (the *final time*) can be set by passing the `horizon` attribute, for example:

``` py
my_problem = SchedulingProblem(name='MySchedulingProblem',
                               horizon=20)
```

The interval's duration is subdivided into discrete units called *periods*, each with a fixed duration of 1. The number of periods is equal to $horizon$, and the number of points within the interval $[0;horizon]$ is $horizon+1$.

![TimeLineHorizon](img/TimeLineHorizon.svg){ width="90%" }

!!! warning

    ProcessScheduler handles only variables using **dimensionless integer values**.

A period represents the finest granularity level for defining the timeline, task durations, and the schedule itself. This timeline is dimensionless, allowing you to map a period to your desired duration, be it in seconds, minutes, hours, or any other unit. For instance:

* If your goal is to plan tasks within a single day, such as from 8 am to 6 pm (office hours), resulting in a 10-hour time span, and you intend to schedule tasks in 1-hour increments, then the horizon value should be set to 10 to achieve the desired number of periods:

$$horizon = \frac{18-8}{1}=10$$

This implies that you can schedule tasks with durations measured in whole hours, making it impractical to schedule tasks with durations of half an hour or 45 minutes.

* If your task scheduling occurs in the morning, from 8 am to 12 pm, resulting in a 4-hour time interval, and you intend to schedule tasks in 1-minute intervals, then the horizon value must be 240:

$$horizon = \frac{12-8}{1/60}=240$$

!!! note

    The `horizon` attribute is optional. If it's not explicitly provided during the `__init__` method, the solver will determine an appropriate horizon value that complies with the defined constraints. In cases where the scheduling problem aims to optimize the horizon, such as achieving a specific makespan objective, manual setting of the horizon is not necessary.

## SchedulingProblem class implementation

| Parameter name | Type | Mandatory/Optional | Default Value |Description |
| -------------- | -----| -------------------| --------------|----------- |
| name           | str  | Mandatory          |               | Problem name |
| horizon        | int  | Optional           |     None      | Problem horizon |
| delta_time     | timedelta | Optional     | None | Value, in minutes, of one time unit |
| start_time     | datetime.datetime | Optional | None | The start date |
| end_time       | datetime.time | Optional | None | The end date |

The only mandatory parameter is the problem `name`.

If `horizon` is specified as an integer, the solver schedules tasks within the defined range, starting from $t=0$ to $t=\text{horizon}$. If unspecified, the solver autonomously determines an appropriate horizon.
The `horizon` parameter does not need to be provided. If an integer is passed, the solver will schedule all tasks between the initial time ($t=0$) and the horizon ($t=horizon$). If not, the solver will decide about a possible horizon.

!!! note

    It is advisable to set the `horizon` parameter when the scheduling involves a predetermined period (e.g., a day, week, or month). This is particularly useful in scenarios aiming to minimize the scheduling horizon, such as in manufacturing scheduling where the goal is to reduce the time needed for processing jobs. In such cases, omitting the horizon allows the solver to optimize it based on problem requirements.

## SchedulingProblem instantiation

Here is the simpliest way to create `SchedulingProblem`.

``` py
import processscheduler as ps
my_problem = ps.SchedulingProblem(name="MyFirstSchedulingProblem", horizon=100)
```

## Mapping integers to datetime objects

To enhance the readability of Gantt charts and make schedules more intuitive, ProcessScheduler allows you to represent time intervals in real dates and times rather than integers. You can explicitly set time values in seconds, minutes, hours, and more. The smallest time duration for a task, represented by the integer `1`, can be mapped to a Python `timedelta` object. Similarly, any point in time can be mapped to a Python `datetime` object.

Creating Python timedelta objects can be achieved as follows:

``` py
from datetime import timedelta
delta = timedelta(days=50,
                  seconds=27,
                  microseconds=10,
                  milliseconds=29000,
                  minutes=5,
                  hours=8,
                  weeks=2)
```

For Python `datetime` objects, you can create them like this:

``` py
from datetime import datetime
now = datetime.now()
```

These attribute values can be provided to the SchedulingProblem initialization method as follows:

``` py
problem = ps.SchedulingProblem(name='DateTimeBase',
                               horizon=7,
                               delta_time=timedelta(minutes=15),
                               start_time=datetime.now())
```

Once the solver has completed its work and generated a solution, you can export the end times, start times, and durations to the Gantt chart or any other output format.

!!! note

    For more detailed information on Python's [datetime package documentation](https://docs.python.org/3/library/datetime.html) and its capabilities, please refer to the datetime Python package documentation. This documentation provides comprehensive guidance on working with date and time objects in Python.
