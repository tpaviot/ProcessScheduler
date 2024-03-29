# Problem solving

Solving a scheduling problem involves the `SchedulingSolver` class.

## Solver definition

A `SchedulingSolver` instance takes a `SchedulingProblem` instance:

``` py
solver = SchedulingSolver(problem=scheduling_problem_instance)
```

It takes the following optional arguments:

* `debug`: False by default, if set to True will output many useful information.

* `max_time`: in seconds, the maximal time allowed to find a solution. Default is 10s.

* `parallel`: boolean False by default, if True force the solver to be executed in multithreaded mode. It *might* be quicker. Or not.

* `random_values`: a boolean, default to `False`. If set to `True`, enable a builtin generator to set random initial values. By setting this attribute to `True`, one expects the solver to give a different solution each time it is called.

* `logics`: a string, None by default. Can be set to any of the supported z3 logics, "QF_IDL", "QF_LIA", etc. see https://smtlib.cs.uiowa.edu/logics.shtml. By default (logics set to None), the solver tries to find the best logics, but there can be significant improvements by setting a specific logics ("QF_IDL" or "QF_UFIDL" seems to give the best performances).

* `verbosity`: an integer, 0 by default. 1 or 2 increases the solver verbosity. TO be used in a debugging or inspection purpose.

* `optimizer`: a string, "incremental" by default, can be also set to "optimize". 1 or 2 increases the solver verbosity. TO be used in a debugging or inspection purpose.

* `optimize_priority`: a string among "pareto", "lex", "box", "weight".

## Solve

Just call the `solve` method. This method returns a `Solution` instance.

``` py
solution = solver.solve()
```

Running the `solve` method returns can either fail or succeed, according to the 4 following cases:

1. The problem cannot be solved because some constraints are contradictory. It is called "Unsatisfiable". The `solve` method returns False. For example:

``` py
TaskStartAt(task=cook_the_chicken, value=2)
TaskStartAt(task=cook_the_chicken, value=3)
```

It is obvious that these constraints cannot be both satisfied.

2. The problem cannot be solved for an unknown reason (the satisfiability of the set of constraints cannot be computed). The `solve` method returns False.

3. The solver takes too long to complete and exceeds the allowed `max_time`. The `solve` method returns False.

4. The solver successes in finding a schedule that satisfies all the constraints. The `solve` method returns the solution, which can be rendered as a Gantt chart or a JSON string.

!!! note

    If the solver fails to give a solution, increase the `max_time` (case 2) or remove some constraints (case 1).

## Find another solution

The solver may schedule:

* one solution among many, in the case where there is no optimization,

* the best possible schedule in case of an optimization issue.

In both cases, you may need to check a different schedule that fits all the constraints. Use the `find_another_solution` method and pass the variable you would want the solver to look for another solution.

!!! note

    Before requesting another solution, the `solve` method has first to be executed, i.e. there should already be a current solution.

You can pass any variable to the `find_another_solution` method: a task start, a task end, a task duration, a resource productivity etc.

For example, there are 5 different ways to schedule a FixedDurationTask with a duration=2 in an horizon of 6. The default solution returned by the solver is:

``` py
problem = ps.SchedulingProblem(name='FindAnotherSolution', horizon=6)
task_1 = ps.FixedDurationTask(name='task1', duration=2)
problem.add_task(task_1)
solver = ps.SchedulingSolver(problem=problem)
solution = solver.solve()
print("Solution for task_1.start:", solution.tasks['task1'])
```

``` bash
Solution for task_1.start: 0
```

Then, we can request for another solution:

``` py
solution = solver.find_another_solution(task_1.start)
if solution is not None:
    print("New solution for task_1.start:", solution.tasks['task1'])
```

``` bash
Solution for task_1.start: 1
```

You can recursively call `find_another_solution` to find all possible solutions, until the solver fails to return a new one.

## Run in debug mode

If the `debug` attribute is set to True, the z3 solver is run with the unsat_core option. This will result in a much longer computation time, but this will help identifying the constraints that conflict. Because of this higher consumption of resources, the `debug` flag should be used only if the solver fails to find a solution.

## Optimization

Please refer to the [Objectives](objectives.md) page for further details.

## Gantt chart

Please refer to the [Gantt chart](gantt_chart.md) page for further details.

## Logics

| logics | computing_time(s) | flowtime | priority | obj value |
| - | - | - | - | - |
|QF_LRA|2.84|147|289|436|
|QF_LIA|4.25|165|320|485|
|QF_RDL|0.48|None|None|None|
|QF_IDL|3.45|174|339|513|
|QF_AUFLIA|6.01|129|270|399|
|QF_ALIA|3.69|139|280|419|
|QF_AUFLIRA|4.30|145|266|411|
|QF_AUFNIA|4.41|159|337|496|
|QF_AUFNIRA|5.35|168|310|478|
|QF_ANIA|6.12|168|320|488|
|QF_LIRA|5.41|151|302|453|
|QF_UFLIA|6.18|143|296|439|
|QF_UFLRA|9.19|143|305|448|
|QF_UFIDL|4.98|132|263|395|
|QF_UFRDL|5.69|171|352|523|
|QF_NIRA|6.72|142|268|410|
|QF_UFNRA|8.51|160|300|460|
|QF_UFNIA|18.89|130|261|391|
|QF_UFNIRA|6.36|171|320|491|
|QF_S|5.28|152|289|441|
|QF_SLIA|4.33|174|361|535|
|UFIDL|6.70|126|246|372|
|HORN|0.49|None|None|None|
|QF_FPLRA|6.21|129|253|382|
