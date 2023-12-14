# Objective

ProcessScheduler is able to compute optimized schedules according to one (single optimization) or any number (multi-objectives) of **objectives**.

An objective is a target value for an `Indicator` or any of the variables defined in the scheduling problem:

* if the target value is known, then the objective can either be `ExactObjective`,

* it the target value is unknown but you want to find a minimal or maximal value, the the objective can be the result from an optimization resolution, `MaximizeObjective` or `MinimizeObjective`.

!!! warning

    Setting any kind of objectives turns the scheduling problem into an optimization problem. This will result in heavier computations and, thus, a longer time for the problem to be solved.

## Builtin optimization objectives

Available builtin objectives are listed below:


| Type      | Kind | Description                          |
| ----------- | -----| ------------------------------------ |
| ObjectiveMinimizeMakespan | Minimize | Minimize the schedule horizon |
| ObjectiveMaximizeResourceUtilization | Maximize | Number of tardy tasks from the selected tasks |
| ObjectiveMinimizeResourceCost | Maximize | Maximum lateness of selected tasks |
| ObjectivePriorities  | Minimize | Resource utilization, from 0% to 100% of the schedule horizon, of the selected resource |
| ObjectiveTasksStartLatest  | Single resource | Number of tasks assigned to the selected resource |
| ObjectiveTasksStartEarliest  | List of resources| Total cost of selected resources |
| ObjectiveMinimizeFlowtime  |Buffer | Maximum level of the selected buffer |
| ObjectiveMinimizeFlowtimeSingleResource  | Buffer | Minimum level of the selected buffer |
| ObjectiveMaximizeMaxBufferLevel  | Buffer | Minimum level of the selected buffer |
| ObjectiveMinimizeMaxBufferLevel  | Buffer | Minimum level of the selected buffer |

## Custommized objectives

You can create your own objective using the `ObjectiveMaximizeIndicator` and `ObjectiveMinimizeIndicator` classes.

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

## Multiple objective optimization, weighted objective

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
