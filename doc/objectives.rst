Indicator and Objective
=======================

Indicator
---------

The :class:`Indicator` class allows to define a criterion that quantifies the schedule so that it can be compared with other schedules. An :class:`Indicator` instance results in a conclusion such a 'this schedule A is better than schedule B because the indicator XXX is greater/lower'.

An :class:`Indicator` instance is created by passing the indicator name as well as the mathematical expression to compute. For example:

.. code-block:: python

	flow_time = Indicator('FlowTime', task1.end + task2.end)
	duration_square = Indicator('MinTaskDuration', task1.duration ** 2 + task2.duration ** 2)

Indicator values are computed by the solver, and are available after a solution is actually found. If the solution rendered as a matplotlib Gantt chart, then the indicator values are displayed on the chart.

.. note::

	You can add any number of Indicators. The mathematical expression must be expressed in a polynomial formalism, i.e. you can't use advanced mathematical functions such as :func:`sqrt`, :func:`sin` or whatever.

Builtin objectives
------------------

Objective
---------

An objective is a target value for an :class:`Indicator` or any of the variables defined in the problem:

- if the target value is known, then the objective can either be :class:`EqualObjective`, :class:`AtLeastObjective` or :class:`AtMostObjective`

- it the target value is unknown but you want to find a minimal or maximal value, the the objective can be a :class:`MaximizeObjective` or :class:`MinimizeObjective`. This turns the scheduling problem into an optimization problem: the solver finds the best possible solution among many.
