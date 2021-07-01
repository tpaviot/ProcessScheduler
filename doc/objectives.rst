Optimization
============

An objective is a target value for an :class:`Indicator` or any of the variables defined in the scheduling problem:

- if the target value is known, then the objective can either be :class:`ExactObjective`, :class:`MinimumObjective` or :class:`MaximumObjective`,

- it the target value is unknown but you want to find a minimal or maximal value, the the objective can be the result from an optimization resolution, :class:`MaximizeObjective` or :class:`MinimizeObjective`.

.. warning::

    Using :class:`MaximizeObjective` or :class:`MinimizeObjective` classes turn the problem into an optimization problem. This will result in heavier computations and, thus, a longer time for the solution to get known.

Builtin optimization objectives
-------------------------------

The following builtin objectives are available:

- :func:`add_objective_makespan`: minimize the schedule horizon,

- :func:`add_objective_resource_utilization`: maximize resource occupation,

- :func:`add_objective_resource_cost`: minimize the total cost for selected resource(s),

- :func:`add_objective_priorities`: minimize total priority indicator (tasks with high priorities will be scheduled before tasks with lower priorities, under the condition however that all constraints are satisfied),

- :func:`add_objective_start_earliest`: minimize the start time of the last task to be scheduled,

- :func:`add_objective_start_latest`: maximize the start time of the first task to be scheduled,

- :func:`add_objective_flowtime`: minimize flowtime.

- :func:`add_objective_flowtime_single_resource`: minimize flowtime of a single resource on a specific time interval

Single objective optimization
-----------------------------
Imagine you need to schedule one specific task :attr:`task_1` the later. After you defined the task as usual, then create the objective and set the optimization target:

.. code-block:: python

    pb = ps.SchedulingProblem('SingleObjective1', horizon=20)
    task_1 = ps.FixedDurationTask('task1', duration = 3)
    indicator_1 = ps.Indicator('Task1End', task_1.end)
    ps.MaximizeObjective('MaximizeTask1End', indicator_1)
    ps.SchedulingSolver(pb).solve()

The expected value for the indicator_1 maximization is 20. After running the script, you may get the following output:

.. code-block:: bash

    Solver type:
    ===========
    -> Standard SAT/SMT solver
    Incremental optimizer:
    ======================
    Found better value: 3 elapsed time:0.000s
    Checking better value >3
    Found better value: 4 elapsed time:0.071s
    Checking better value >4
    [...]
    Checking better value >18
    Found better value: 19 elapsed time:0.074s
    Checking better value >19
    Found better value: 20 elapsed time:0.074s
    Checking better value >20
    No solution can be found for problem MultiObjective2.
    Reason: Unsatisfiable problem: no solution exists
    Found optimum 20. Stopping iteration.
    total number of iterations: 19
    value: 20
    MultiObjective2 satisfiability checked in 0.07s

The solver returns the expected result.

Multiple objective optimization
-------------------------------
ProcessScheduler can deal with multiple objectives optimization. There is no limitation regarding the number of objectives.

Imagine you need to schedule two tasks :attr:`task_1` and :attr:`task_2` the later. After you defined the task as usual, then create the objective and set the optimization target:

.. code-block:: python

    pb = ps.SchedulingProblem('MultiObjective1', horizon=20)
    task_1 = ps.FixedDurationTask('task1', duration = 3)
    task_2 = ps.FixedDurationTask('task2', duration = 3)
    indicator_1 = ps.Indicator('Task1End', task_1.end)
    indicator_2 = ps.Indicator('Task2End', task_2.end)
    ps.MaximizeObjective('MaximizeTask1End', indicator_1)
    ps.MaximizeObjective('MaximizeTask2End', indicator_2)
    solution = ps.SchedulingSolver(pb).solve()
    print(solution)

After running the script, you may get the following output:

.. code-block:: bash

    [...]
    {
    "horizon": 20,
    "indicators": {
        "EquivalentIndicator": -40,
        "Task1End": 20,
        "Task2End": 20
    },
    [...]


The solver gives the expected result. Note that an EquivalentIndicator is built from both indicators. A maximization problem is always turned into a minimization problem (the equivalent indicator is negative).

Weighted objectives
-------------------
In the previous example, if we add a constraint between tasks :attr:`task_1` and :attr:`task_2`, then both tasks end may not be independent from each other. For example, let's add the following constraint:

.. code-block:: python

    pb.add_constraint(task_1.end == 20 - task_2.start)

This looks like a kind of balance: the later :attr:`task_1` is scheduled, the sooner :attr:`task_2` is scheduled. We can leave both optimizations enabled, but the solver has to know what to do with these conflicting objectives, and especially what is there relative **weight**.

.. note::

    MaimizeObjective and MinimizeObjective have an optional :attr:`weight` parameter set by default to :attr:`1.0`. The higher this value, the more important the objective.

The python script will look like

.. code-block:: python

    import processscheduler as ps
    pb = ps.SchedulingProblem('MultiObjective2', horizon=20)
    task_1 = ps.FixedDurationTask('task1', duration = 3)
    task_2 = ps.FixedDurationTask('task2', duration = 3)
    pb.add_constraint(task_1.end == 20 - task_2.start)
    indicator_1 = ps.Indicator('Task1End', task_1.end)
    indicator_2 = ps.Indicator('Task2End', task_2.end)

    ps.MaximizeObjective('MaximizeTask1End', indicator_1, weight=1.)
    ps.MaximizeObjective('MaximizeTask2End', indicator_2, weight=1.)
    solution = ps.SchedulingSolver(pb).solve()
    print(solution)

.. code-block:: bash

    "indicators": {
        "EquivalentIndicator": -23,
        "Task1End": 20,
        "Task2End": 3
    },


The solver decides to schedule the Task1 at the end of the timeline. Let's change the relative weights so that the second objective is considered as more important:

.. code-block:: python

    ps.MaximizeObjective('MaximizeTask1End', indicator_1, weight=1.)
    # the second one is ten times more important
    ps.MaximizeObjective('MaximizeTask2End', indicator_2, weight=10.)

This lead the solver to another solution:

.. code-block:: bash

    "indicators": {
        "EquivalentIndicator": -203,
        "Task1End": 3,
        "Task2End": 20
    },

..
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

    In the previous example, the maximum of task_1end can be 20, and the maximum of task_2.end can also be 20, but not at the same time. The :attr:`box` priority then gives an information about the values that can be reached.

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
