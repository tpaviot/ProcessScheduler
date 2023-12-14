# Problem solving

Solving a scheduling problem involves the `SchedulingSolver` class.

## Solver definition

A `SchedulingSolver` instance takes a `SchedulingProblem` instance:

``` py
solver = SchedulingSolver(problem=scheduling_problem_instance)
```

It takes the following optional arguments:

* `debug`: False by default, if set to True will output many useful information.

* `max_time`: in seconds, the maximal time allowed to find a solution. Default is 60s.

* `parallel`: boolean False by default, if True force the solver to be executed in multithreaded mode. It *might* be quicker. It might not.

* `random_values`: a boolean, default to :const:`False`. If set to :const:`True`, enable a builtin generator to set random initial values. By setting this attribute to :const:`True`, one expects the solver to give a different solution each time it is called.

* `logics`: a string, None by default. Can be set to any of the supported z3 logics, "QF_IDL", "QF_LIA", etc. see https://smtlib.cs.uiowa.edu/logics.shtml. By default (logics set to None), the solver tries to find the best logics, but there can be significant improvements by setting a specific logics ("QF_IDL" or "QF_UFIDL" seems to give the best performances).

* `verbosity`: an integer, 0 by default. 1 or 2 increases the solver verbosity. TO be used in a debugging or inspection purpose.

## Solve

Just call the :func:`solve` method. This method returns a `Solution` instance.

``` py
solution = solver.solve()
```

Running the `solve` method returns can either fail or succeed, according to the 4 following cases:

1. The problem cannot be solved because some constraints are contradictory. It is called "Unsatisfiable". The :func:`solve` method returns False. For example:

``` py
TaskStartAt(task=cook_the_chicken, value=2)
TaskStartAt(task=cook_the_chicken, value=3)
```

It is obvious that these constraints cannot be both satisfied.

2. The problem cannot be solved for an unknown reason (the satisfiability of the set of constraints cannot be computed). The `solve` method returns False.

3. The solver takes too long to complete and exceeds the allowed `max_time`. The `solve` method returns False.

4. The solver successes in finding a schedule that satisfies all the constraints. The `solve` method returns the solution as a JSON dictionary.

!!! note

   If the solver fails to give a solution, increase the `max_time` (case 3) or remove some constraints (cases 1 and 2).

## Find another solution

The solver may schedule:

* one solution among many, in the case where there is no optimization,

* the best possible schedule in case of an optimization issue.

In both cases, you may need to check a different schedule that fits all the constraints. Use the :func:`find_another_solution` method and pass the variable you would want the solver to look for another solution.

!!! note

    Before requesting another solution, the `solve` method has first to be executed, i.e. there should already be a current solution.

You can pass any variable to the `find_another_solution` method: a task start, a task end, a task duration, a resource productivity etc.

For example, there are 5 different ways to schedule a FixedDurationTask with a duration=2 in an horizon of 6. The default solution returned by the solver is:

``` py
problem = ps.SchedulingProblem('FindAnotherSolution', horizon=6)
solutions =[]
task_1 = ps.FixedDurationTask('task1', duration=2)
problem.add_task(task_1)
solver = ps.SchedulingSolver(problem)
solution = solver.solve()
print("Solution for task_1.start:", task_1.scheduled_start)
```

``` console
Solution for task_1.start: 0
```

Then, we can request for another solution:

``` py
solution = solver.find_another_solution(task_1.start)
if solution is not None:
    print("New solution for task_1.start:", solution.tasks[task_1.name].start)
```

``` bash
Solution for task_1.start: 1
```

You can recursively call `find_another_solution` to find all possible solutions, until the solver fails to return a new one.

## Optimization solver, incremental solver

ProcessScheduler can deal with multiple objectives optimization. There is no limitation regarding the number of objectives.

Imagine you need to schedule two tasks `task_1` and `task_2` the later. After you defined the task as usual, then create the objective and set the optimization target:

``` py
pb = ps.SchedulingProblem('MultiObjective1', horizon=20)
task_1 = ps.FixedDurationTask('task1', duration = 3)
task_2 = ps.FixedDurationTask('task2', duration = 3)
indicator_1 = ps.Indicator('Task1End', task_1.end)
indicator_2 = ps.Indicator('Task2End', task_2.end)
ps.MaximizeObjective('MaximizeTask1End', indicator_1)
ps.MaximizeObjective('MaximizeTask2End', indicator_2)
solution = ps.SchedulingSolver(pb).solve()
print(solution)
```

After running the script, you may get the following output:

``` bash
[...]
{
"horizon": 20,
"indicators": {
    "EquivalentIndicator": -40,
    "Task1End": 20,
    "Task2End": 20
},
[...]
```

The solver gives the expected result. Note that an EquivalentIndicator is built from both indicators. A maximization problem is always turned into a minimization problem (the equivalent indicator is negative).

## Multiple objective optimization using the optimize solver (default)

### Lexicon priority (`'lex'`, default)

The solver optimizes the first objective, then the second one while keeping the first value, then the third one keeping both previous values etc.

In the previous example, the first objective to be optimized will be the end of task_1, obviously 20. Then, this value being fixed, there's no other solution than start of the second task is 0, then task_2 end will be 3.

``` py
ps.SchedulingSolver(pb, optimizer=optimize, optimize_priority='lex').solve()
```

And the output

``` bash
Optimization results:
=====================
    ->Objective priority specification: lex
    ->Objective values:
        ->Indicator_Task1End(max objective): 20
        ->Indicator_Task2End(max objective): 3
```

### Box priority (`'box'`)

The optimization solver breaks the dependency between objectives and look for the maximum (resp. minimum) value that can be achieved for each objective.

In the previous example, the maximum of task_1end can be 20, and the maximum of task_2.end can also be 20, but not at the same time. The `box` priority then gives an information about the values that can be reached.

``` py
ps.SchedulingSolver(pb, optimizer=optimize, optimize_priority='box').solve()
```

And the output

``` bash
Optimization results:
=====================
    ->Objective priority specification: lex
    ->Objective values:
        ->Indicator_Task1End(max objective): 20
        ->Indicator_Task2End(max objective): 20
```

!!! note

    In `box` mode, both objectives may not be reached simultaneously, the solver will give anyway a solution that satisfies **all** constraints (by default the solution obtained from the lexicon mode).

### Pareto priority (`'pareto'`)

The optimization solver suggests a new solution each time the `solve()` method is called. This allows traversing all solutions. Indeed we can have the task_1 end to 20 and task_2 end 3, but also the task_1 end to 19 and task_2 end to 4 etc. These all are solutions for the optimization problem.

The python code has to be slightly modified:

``` py
solver = ps.SchedulingSolver(pb, optimizer=optimize, optimize_priority='pareto')
while solver.solve():
    pass
```

And the output will be:

``` bash
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
```

Here you have 18 different solutions. You can add a test to the loop to stop the iteration as soon as you're ok with the solution.

## Run in debug mode

If the `debug` attribute is set to True, the z3 solver is run with the unsat_core option. This will result in a much longer computation time, but this will help identifying the constraints that conflict. Because of this higher consumption of resources, the `debug` flag should be used only if the solver fails to find a solution.
