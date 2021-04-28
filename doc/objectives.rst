Indicator and Objective
=======================

Indicator
---------

The :class:`Indicator` class allows to define a criterion that quantifies the schedule so that it can be compared with other schedules. An :class:`Indicator` instance results in a conclusion such a 'this schedule A is better than schedule B because the indicator XXX is greater/lower'.

An :class:`Indicator` instance is created by passing the indicator name as well as the mathematical expression to compute. For example:

.. code-block:: python

    flow_time = Indicator('FlowTime', task1.end + task2.end)
    duration_square = Indicator('MinTaskDuration', task1.duration ** 2 + task2.duration ** 2)

Indicator values are computed by the solver, and are available after a solution is actually found. If the solution rendered as a matplotlib Gantt chart, then the indicator values are displayed on the upper right corner of the chart.

.. note::

    You can add any number of Indicators. The mathematical expression must be expressed in a polynomial formalism, i.e. you can't use advanced mathematical functions such as :func:`sqrt`, :func:`sin` or whatever.

Builtin indicators
------------------

Resource Cost indicator
^^^^^^^^^^^^^^^^^^^^^^^
Use the :func:`add_indicator_resource_cost` method to insert a cost computation to your schedule. This method takes a list of resources and compute the total cost (sum of productivity * duration for all resources).

Objective
---------

An objective is a target value for an :class:`Indicator` or any of the variables defined in the problem:

- if the target value is known, then the objective can either be :class:`EqualObjective`, :class:`AtLeastObjective` or :class:`AtMostObjective`,

- it the target value is unknown but you want to find a minimal or maximal value, the the objective can be the result from an optimization resolution, :class:`MaximizeObjective` or :class:`MinimizeObjective`.

.. warning::

    Using :class:`MaximizeObjective` or :class:`MinimizeObjective` classes turn the problem into an optimization problem. This will result in heavier computations and, thus, a longer time for the solution to get known.

Builtin optimization objectives
-------------------------------

The following builtin objectives are available:

- :func:`add_objective_makespan`: minimize the schedule horizon,

- :func:`add_objective_resource_cost`: minimize the total cost for selected resource(s),

- :func:`add_objective_priorities`: minimize total priority indicator (tasks with high priorities will be scheduled before tasks with lower priorities, under the condition however that all constraints are satisfied),

- :func:`add_objective_start_earliest`: minimize the start time of the last task to be scheduled,

- :func:`add_objective_start_latest`: maximize the start time of the first task t obe scheduled,

- :func:`add_objective_flowtime`: minimize flowtime.

Single objective optimization
-----------------------------
Imagine you need to schedule one specific task :attr:`task_1` the later. After you defined the task as usual, then create the objective and set the optimization target:

.. code-block:: python

    pb = ps.SchedulingProblem('MultiObjective2', horizon=20)
    task_1 = ps.FixedDurationTask('task1', duration = 3)
    indicator_1 = ps.Indicator('Task1End', task_1.end)
    ps.MaximizeObjective('MaximizeTask1End', indicator_1)
    ps.SchedulingSolver(pb).solve()

After running the script, you may get the following output:

.. code-block:: bash

    Optimization results:
    =====================
        ->Objective priority specification: lex
        ->Objective values:
            ->Indicator_Task1End(max objective): 20

The solver gives the expected result.

Multiple objective optimization
-------------------------------
ProcessScheduler can deal with multiple objectives optimization, but you have to know wether or not the objectives are **independent** from each other.


Independent objectives
^^^^^^^^^^^^^^^^^^^^^^
Imagine you need to schedule two tasks :attr:`task_1` and :attr:`task_2` the later. After you defined the task as usual, then create the objective and set the optimization target:

.. code-block:: python

    pb = ps.SchedulingProblem('MultiObjective2', horizon=20)
    task_1 = ps.FixedDurationTask('task1', duration = 3)
    task_2 = ps.FixedDurationTask('task2', duration = 3)
    indicator_1 = ps.Indicator('Task1End', task_1.end)
    indicator_2 = ps.Indicator('Task2End', task_2.end)
    ps.MaximizeObjective('MaximizeTask1End', indicator_1)
    ps.MaximizeObjective('MaximizeTask2End', indicator_2)
    ps.SchedulingSolver(pb).solve()

After running the script, you may get the following output:

.. code-block:: bash

    Optimization results:
    =====================
        ->Objective priority specification: lex
        ->Objective values:
            ->Indicator_Task1End(max objective): 20
            ->Indicator_Task2End(max objective): 20

The solver gives the expected result.

Non independent objectives
^^^^^^^^^^^^^^^^^^^^^^^^^^
In the previous example, if we add a constraint between tasks :attr:`task_1` and :attr:`task_2`, then both tasks end may not be independant from each other. For example, let's add the following constraint:

.. code-block:: python

    pb.add_constraint(task_1.end == 20 - task_2.start)

This looks like a kind of balance: the later :attr:`task_1` is scheduled, the sooner :attr:`task_2` is scheduled. We can leave both optimizations enabled, but the solver has to know what to do with these conflicting objectives, and especially what is there relative **priority**.

.. note::

    In case of a multiobjectve optimization problem, you have to set the :attr:`optimize_property` of the scheduling problem. It can be either :attr:`'lex'` (default value), :attr:`'box'` or :attr:`'pareto`'.

The python script will look like

.. code-block:: python

    import processscheduler as ps
    pb = ps.SchedulingProblem('MultiObjective2', horizon=20)
    task_1 = ps.FixedDurationTask('task1', duration = 3)
    task_2 = ps.FixedDurationTask('task2', duration = 3)
    pb.add_constraint(task_1.end == 20 - task_2.start)
    indicator_1 = ps.Indicator('Task1End', task_1.end)
    indicator_2 = ps.Indicator('Task2End', task_2.end)

    ps.MaximizeObjective('MaximizeTask1End', indicator_1)
    ps.MaximizeObjective('MaximizeTask2End', indicator_2)
    ps.SchedulingSolver(pb, optimize_property='speficy the right priority here').solve()

Lexicon priority (:attr:`'lex'`, default)
-----------------------------------------
The solver optimizes the first objective, then the second one while keeping the first value, then the third one keeping both previous values etc.

In the previous example, the first objective to be optimized will be the end of task_1, obviously 20. Then, this value being fixed, there's no other solution than start of the second task is 0, then task_2 end will be 3.

.. code-block:: python

    ps.SchedulingSolver(pb, optimize_priority='lex').solve()

And the output

.. code-block:: bash

    Optimization results:
    =====================
        ->Objective priority specification: lex
        ->Objective values:
            ->Indicator_Task1End(max objective): 20
            ->Indicator_Task2End(max objective): 3

Lexicon priority (:attr:`'box'`)
--------------------------------
The optimization solver breaks the dependency between objectives and look for the maximum (resp. minimum) value that can be achieved for each objective.

In the previous example, the maximum of task_1end can be 20, and the maximum of task_2.end can alos be 20, but not at the same time. The :attr:`box` priority then gives an information about the values that can be reached.

.. code-block:: python

    ps.SchedulingSolver(pb, optimize_priority='lex').solve()


And the output

.. code-block:: bash

    Optimization results:
    =====================
        ->Objective priority specification: lex
        ->Objective values:
            ->Indicator_Task1End(max objective): 20
            ->Indicator_Task2End(max objective): 20

.. note::

    In the :attr:`box` mode, both objectives may not be reached simultaneously, the solver will give anyway a solution that satisfies **all** constraints (by default the solution obtained from the lexicon mode).

Pareto priority (:attr:`'pareto'`)
----------------------------------
The optimization solver suggests a new solution each time the :func:`solve()` method is called. This allows traversing all solutions. Indeed we can have the task_1 end to 20 and task_2 end 3, but also the task_1 end to 19 and task_2 end to 4 etc. These all are solutions for the optimization problem.

The python code has to be slightly modified:

.. code-block:: python

    solver = ps.SchedulingSolver(pb, optimize_priority='pareto')
    while solver.solve():
        pass

And the output will be:

.. code-block:: bash

    Optimization results:
    =====================
        ->Objective priority specification: pareto
        ->Objective values:
            ->Indicator_Task1End(max objective): 20
            ->Indicator_Task2End(max objective): 3
    SAT computation time:
    =====================
        MultiObjective2 satisfiability checked in 0.00s
    Optimization results:
    =====================
        ->Objective priority specification: pareto
        ->Objective values:
            ->Indicator_Task1End(max objective): 19
            ->Indicator_Task2End(max objective): 4
    SAT computation time:
    =====================
        MultiObjective2 satisfiability checked in 0.00s
    Optimization results:
    =====================
        ->Objective priority specification: pareto
        ->Objective values:
            ->Indicator_Task1End(max objective): 18
            ->Indicator_Task2End(max objective): 5
    [...]

Here you have 18 different solutions. You can add a test to the loop to stop the iteration as soon as you're ok with the solution.
