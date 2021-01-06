Scheduling problem solving
==========================

Solving a scheduling problem involves the :class:`SchedulingSolver` class.

Defining the solver
-------------------
A :class:`SchedulingSolver` instance takes a :class:`SchedulingProblem` instance:

.. code-block:: python

    solver = SchedulingSolver(scheduling_problem_instance)

It takes three optional arguments:

- :attr:`verbosity`: False by default, if set to True will output many useful information

- :attr:`max_time`: in seconds, the maximal time allowed to find a solution. Default is 60s.

- :attr:`parallel`: boolean False by default, if True the solver will be executed in multithreaded mode. It *might* be quicker. It might not.

Solving
-------
Just call the :func:`solve` method.

.. code-block:: python

    solver.solve()

The :func:`solve` method returns a boolean, True if a solution was found, False otherwise. There are four cases:

1. The problem cannot be solved because some constraints are contradictory. It is called "Unsatisfiable". The :func:`solve` method returns False. For example:

.. code-block:: python

	TaskStartAt(cook_the_chicken, 2)
	TaskStartAt(cook_the_chicken, 3)

It is obvious that these constraints cannot be both satisfied.

2. The problem cannot be solved for an unknown reason (the satisfiability of the set of constraints cannot be computed). The :func:`solve` method returns False.

3. The solver takes too long to complete and exceeds the allowed :attr:`max_time`. The :func:`solve` method returns False.

4. The solver successes in finding a schedule that satisfies all the constraints. The :func:`solve` method returns True.

.. note::
   If the solver fails to give a solution: increase the :attr:`max_time` (case 3), remove some contraints (cases 1 and 2). In most cases, the solver does find a solution.
