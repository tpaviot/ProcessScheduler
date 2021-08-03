Indicator
=========

:class:`Indicator` class
------------------------

The :class:`Indicator` class allows to define a criterion that quantifies the schedule so that it can be compared with other schedules. An :class:`Indicator` instance results in a conclusion such a 'this schedule A is better than schedule B because the indicator XXX is greater/lower'.

An :class:`Indicator` instance is created by passing the indicator name as well as the mathematical expression to compute. For example:

.. code-block:: python

    flow_time = Indicator('FlowTime', task1.end + task2.end)
    duration_square = Indicator('MinTaskDuration', task1.duration ** 2 + task2.duration ** 2)

Indicator values are computed by the solver, and are part of the solution. If the solution rendered as a matplotlib Gantt chart, the indicator values are displayed on the upper right corner of the chart.

Indicators can also be bounded, although it is optional to do so. Imagine, for instance, an indicator that can only assume values from 0 to 100. Then, if we are maximizing (or minimizing) this indicator in our problem, we want the solver to know that 100 (or 0) is the best value it can achieve. Therefore, we would write:

.. code-block:: python

    indicator1 = Indicator('Example1', task2.start - task1.end, bounds = (0,100)) # If lower and upper bounded
    indicator2 = Indicator('Example2', task3.start - task2.end, bounds = (None,100)) # If only upper bounded
    indicator3 = Indicator('Example3', task4.start - task3.end, bounds = (0,None)) # If only lower bounded

.. note::

    You can add any number of Indicators. The mathematical expression must be expressed in a polynomial formalism, i.e. you can't use advanced mathematical functions such as :func:`sqrt`, :func:`sin` or whatever.

Resource cost and utilization
-----------------------------
Two usual indicators are available : the utilization and cost of a resource (or a list of resources).

Use the :func:`add_indicator_resource_utilization` method to insert a cost computation to your schedule. This method takes a list of resources and compute the total cost (sum of productivity * duration for all resources). The result is a percentage: an utilization of 100% means that the resource is assigned 100% of the schedule timeline.

The :func:`add_indicator_resource_cost` method returns the total cost of a resource (or a list of resource). It is computed using each cost function defined for each resource.
