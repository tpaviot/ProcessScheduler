Indicator
=========

`Indicator` class
------------------------

The `Indicator` class allows to define a criterion that quantifies the schedule so that it can be compared with other schedules. An `Indicator` instance results in a conclusion such a 'the schedule A is better than schedule B because the indicator XXX is greater/lower'.

An `Indicator` instance is created by passing the indicator name as well as the mathematical expression to compute. For example:

.. code-block:: python

    flow_time = Indicator('FlowTime', task1.end + task2.end)
    duration_square = Indicator('MinTaskDuration', task1.duration ** 2 + task2.duration ** 2)

Indicator values are computed by the solver, and are part of the solution. If the solution is rendered as a matplotlib Gantt chart, the indicator values are displayed on the upper right corner of the chart.

Indicators can also be bounded, although it is an optional feature. It is useful if the indicator is further be maximized (or minimized) by an optimization solver, in order to reduce the computation time. For example,

.. code-block:: python

    indicator1 = Indicator('Example1', task2.start - task1.end, bounds = (0,100)) # If lower and upper bounded
    indicator2 = Indicator('Example2', task3.start - task2.end, bounds = (None,100)) # If only upper bounded
    indicator3 = Indicator('Example3', task4.start - task3.end, bounds = (0,None)) # If only lower bounded

.. note::

    There is no limit to the number of Indicators defined in the problem. The mathematical expression must be expressed in a polynomial form and using the :func:`Sqrt` function. Any other advanced mathematical functions such as :func:`exp`, :func:`sin`, etc. is not allowed because not supported by the solver.

Builtin indicators : Resource cost, utilization, number of tasks assigned
-------------------------------------------------------------------------
Two usual indicators are available : the utilization and cost of a resource (or a list of resources).

Use the :func:`add_indicator_resource_utilization` method to insert a cost computation to your schedule. This method takes a list of resources and compute the total cost (sum of productivity * duration for all resources). The result is a percentage: an utilization of 100% means that the resource is assigned 100% of the schedule timeline. In the following example, the indicator reports the utilization percentage of the :func:`worker_1`.

.. code-block:: python

    utilization_res_1 = problem.add_indicator_resource_utilization(worker_1)

The :func:`add_indicator_resource_cost` method returns the total cost of a resource (or a list of resource). It is computed using each cost function defined for each resource. In the following example, the indicator :func:`cost_ind` is the total cost for both ressources :func:`worker_1` and :func:`worker_2`.

.. code-block:: python

    cost_ind = problem.add_indicator_resource_cost([worker_1, worker_2])

At last, the :func:`add_indicator_number_tasks_assigned` method returns the number of tasks assigned to a resource after the schedule is completed.

.. code-block:: python

    problem.add_indicator_number_tasks_assigned(worker)
