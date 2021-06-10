Problem solving
===============

Solving a scheduling problem involves the :class:`SchedulingSolver` class.

Define the solver
-----------------
A :class:`SchedulingSolver` instance takes a :class:`SchedulingProblem` instance:

.. code-block:: python

    solver = SchedulingSolver(scheduling_problem_instance)

It takes three optional arguments:

- :attr:`debug`: False by default, if set to True will output many useful information.

- :attr:`max_time`: in seconds, the maximal time allowed to find a solution. Default is 60s.

- :attr:`parallel`: boolean False by default, if True the solver will be executed in multithreaded mode. It *might* be quicker. It might not.

Solve
-----
Just call the :func:`solve` method. This method returns a :class:`Solution` instance.

.. code-block:: python

    solution = solver.solve()

Running the :func:`solve` method returns can either fail or succeed, according to the 4 following cases:

1. The problem cannot be solved because some constraints are contradictory. It is called "Unsatisfiable". The :func:`solve` method returns False. For example:

.. code-block:: python

    TaskStartAt(cook_the_chicken, 2)
    TaskStartAt(cook_the_chicken, 3)

It is obvious that these constraints cannot be both satisfied.

2. The problem cannot be solved for an unknown reason (the satisfiability of the set of constraints cannot be computed). The :func:`solve` method returns False.

3. The solver takes too long to complete and exceeds the allowed :attr:`max_time`. The :func:`solve` method returns False.

4. The solver successes in finding a schedule that satisfies all the constraints. The :func:`solve` method returns True.

.. note::
   If the solver fails to give a solution, increase the :attr:`max_time` (case 3) or remove some constraints (cases 1 and 2).

Find another solution
---------------------
The solver may schedule:

- one solution among many, in the case where there is no optimization,

- the best possible schedule in case of an optimization issue.

In both cases, you may need to check a different schedule that fits all the constraints. Use the :func:`find_another_solution` method and pass the variable you would want the solver to look for another solution.

.. note::
    Before requesting another solution, the :func:`solve` method has first to be executed, i.e. there should already be a current solution.

You can pass any variable to the :func:`find_another_solution` method: a task start, a task end, a task duration, a resource productivity etc.

For example, there are 5 different ways to schedule a FixedDurationTask with a duration=2 in an horizon of 6. The default solution returned by the solver is:

.. code-block:: python

    problem = ps.SchedulingProblem('FindAnotherSolution', horizon=6)
    solutions =[]
    task_1 = ps.FixedDurationTask('task1', duration=2)
    problem.add_task(task_1)
    solver = ps.SchedulingSolver(problem)
    solution = solver.solve()
    print("Solution for task_1.start:", task_1.scheduled_start)

.. code-block:: console

   Solution for task_1.start: 0

Then, we can request for another solution:

.. code-block:: python

    solution = solver.find_another_solution(task_1.start)
    if solution is not None:
        print("New solution for task_1.start:", solution.tasks[task_1.name].start)

.. code-block:: console

   Solution for task_1.start: 1

You can recursively call :func:`find_another_solution` to find all possible solutions, until the solver fails to return a new one.

Run in debug mode
-----------------
If the :attr:`debug` attribute is set to True, the z3 solver is run with the unsat_core option. This will result in a much longer computation time, but this will help identifying the constraints which conflict. Because of this higher consumption of resources, the debug flag should be used only if the solver did not fin any solution, after a first resolution gave no answer. 

Render to a Gantt chart
-----------------------

Call the :func:`render_gantt_matplotlib` to render the solution as a Gantt chart. The time line is from 0 to :attr:`horizon` value, you can choose to render either :attr:`Task` or :attr:`Resource` (default).

.. code-block:: python

    solution = solver.solve()
    if solution is not None:
        solution.render_gantt_matplotlib()  # default render_mode is 'Resource'
        # a second gantt chart, in 'Task' mode
        solution.render_gantt_matplotlib(render_mode='Task')

Call the :func:`render_gantt_plotly` to render the solution as a Gantt chart using **plotly**.
Take care that plotly rendering needs **real timepoints** (set at least :attr:`delta_time` at the problem creation).

.. code-block:: python

    solution = solver.solve()
    if solution is not None:
        solution.render_gantt_plotly(sort="Start", html_filename="index.html")  # default render_mode is 'Resource'
        # a second gantt chart, in 'Task' mode
        solution.render_gantt_plotly(render_mode='Task')
