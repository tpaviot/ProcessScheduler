# Optimization

ProcessScheduler is able to compute optimized schedules according to one (single optimization) or any number (multi-objectives) of objectives.

## Objective

An objective is a target value for an `Indicator` or any of the variables defined in the scheduling problem:

* if the target value is known, then the objective can either be `ExactObjective`, `MinimumObjective` or `MaximumObjective`,

* it the target value is unknown but you want to find a minimal or maximal value, the the objective can be the result from an optimization resolution, `MaximizeObjective` or `MinimizeObjective`.

!!! warning

    Using `MaximizeObjective` or `MinimizeObjective` classes turn the problem into an optimization problem. This will result in heavier computations and, thus, a longer time for the problem to be solved.

For example, if you need to optimize the utilization of a resource (bounded up to 100% within the problem horizon),

``` py
# first create the indicator
utilization_res_1 = problem.add_indicator_resource_utilization(worker_1)
# the tell the solver to optimize this value
ps.MaximizeObjective("MaximizeResource1Utilization", utilization_res_1)
```

## Builtin optimization objectives

For any problem, the following builtin objectives are available:

* `add_objective_makespan`: minimize the schedule horizon,

* `add_objective_resource_utilization`: maximize resource occupation,

* `add_objective_resource_cost`: minimize the total cost for selected resource(s),

* `add_objective_priorities`: minimize total priority indicator (tasks with high priorities will be scheduled before tasks with lower priorities, under the condition however that all constraints are satisfied),

* `add_objective_start_earliest`: minimize the start time of the last task to be scheduled,

* `add_objective_start_latest`: maximize the start time of the first task to be scheduled,

* `add_objective_flowtime`: minimize flowtime.

* `add_objective_flowtime_single_resource`: minimize flowtime of a single resource on a specific time interval

## Available solvers : incremental and optimize

The default optimization solver is `incremental`. After a solution is found, the solver will run again and again to find a better solution untill the maximum allowed time is reached. If you provide a small max_time value, the solver will exit to the last found value, but there may be a better value. In that case, just increase the max_time and run again the solver.

``` py
solver = ps.SchedulingSolver(problem=pb,
                             max_time=300)  # 300s is 5 minutes
solution = solver.solve()
```

The other available solver is called `optimize`, which use the builtin optsmt z3-solver. The computation cannot be interrupted, so be careful if the problem to solve involves many tasks/resources. However, the :func`optimize` is guaranteed to return the optimal value.

``` py
solver = ps.SchedulingSolver(problem=pb,
                             optimizer="optimize")  # 300s is 5 minutes
solution = solver.solve()
```

## Single objective optimization

Imagine you need to schedule one specific task `task_1` the later. After you defined the task as usual, then create the objective and set the optimization target:

``` py
pb = ps.SchedulingProblem(name='SingleObjective1', horizon=20)
task_1 = ps.FixedDurationTask(name='task1', duration = 3)
indicator_1 = ps.Indicator(name='Task1End', task_1.end)
ps.MaximizeObjective(name='MaximizeTask1End', indicator_1)
ps.SchedulingSolver(pb).solve()
```

The expected value for the indicator_1 maximization is 20. After running the script, you may get the following output:
``` bash
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
```

The solver returns the expected result.

## Multiple objective optimization using the incremental solver (default)

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

# Weighted objectives

In the previous example, if we add a constraint between tasks `task_1` and `task_2`, then both tasks end may not be independent from each other. For example, let's add the following constraint:

``` py
pb.add_constraint(task_1.end == 20 - task_2.start)
```

This looks like a kind of balance: the later `task_1` is scheduled, the sooner `task_2` is scheduled. We can leave both optimizations enabled, but the solver has to know what to do with these conflicting objectives, and especially what is there relative **weight**.

!!! note

    MaimizeObjective and MinimizeObjective have an optional `weight` parameter set by default to `1.0`. The higher this value, the more important the objective.

The python script will look like

``` py
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
```

``` bash
"indicators": {
    "EquivalentIndicator": -23,
    "Task1End": 20,
    "Task2End": 3
},
```

The solver decides to schedule the Task1 at the end of the timeline. Let's change the relative weights so that the second objective is considered as more important:

``` py
ps.MaximizeObjective('MaximizeTask1End', indicator_1, weight=1.)
# the second one is ten times more important
ps.MaximizeObjective('MaximizeTask2End', indicator_2, weight=10.)
```

This lead the solver to another solution:

``` bash
"indicators": {
    "EquivalentIndicator": -203,
    "Task1End": 3,
    "Task2End": 20
},
```

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
