# Use case: software development

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/tpaviot/ProcessScheduler/HEAD?filepath=doc/use-case-software-development.ipynb)

To illustrate the way to use ProcessScheduler, let's imagine the simple following use case: the developmenent of a scheduling software intended for end-user. The software is developed using Python, and provides a modern Qt GUI. Three junior developers are in charge (Elias, Louis, Elise), under the supervision of their project manager Justine. The objective of this document is to generate a schedule of the different developmenent tasks to go rom the early design stages to the first software release. This notebook can tested online at mybinder.org


### Step 1. Import the module
The best way to import the processscheduler module is to choose an alias import. Indeed, a global import should generate name conflicts. Here, the *ps* alias is used.


``` py
import processscheduler as ps
from datetime import timedelta, datetime

%config InlineBackend.figure_formats = ['svg']
```

### Step 2. Create the scheduling problem
The SchedulingProblem has to be defined. The problem must have a name (it is a mandatory argument). Of course you can create as many problems (i.e; SchedulingProblem instances), for example if you need to compare two or more different schedules.

``` py
problem = ps.SchedulingProblem(
    name="SoftwareDevelopment", delta_time=timedelta(days=1), start_time=datetime.now()
)
```

### Step 3. Create tasks instances
The SchedulingProblem has to be defined. The problem must have a name (it is a mandatory argument). Of course you can create as many problems (i.e SchedulingProblem instances) as needed, for example if you need to compare two or more different schedules. In this example, one period is one day.

``` py
preliminary_design = ps.FixedDurationTask(name="PreliminaryDesign", duration=1)  # 1 day
core_development = ps.VariableDurationTask(name="CoreDevelopmenent", work_amount=10)
gui_development = ps.VariableDurationTask(name="GUIDevelopment", work_amount=15)
integration = ps.VariableDurationTask(name="Integration", work_amount=3)
tests_development = ps.VariableDurationTask(name="TestDevelopment", work_amount=8)
release = ps.ZeroDurationTask(name="ReleaseMilestone")
```

### Step 4. Create tasks time constraints
Define precedences or set start and end times

``` py
ps.TaskStartAt(task=preliminary_design, value=0)
ps.TaskPrecedence(task_before=preliminary_design, task_after=core_development)
ps.TaskPrecedence(task_before=preliminary_design, task_after=gui_development)
ps.TaskPrecedence(task_before=gui_development, task_after=tests_development)
ps.TaskPrecedence(task_before=core_development, task_after=tests_development)
ps.TaskPrecedence(task_before=tests_development, task_after=integration)
ps.TaskPrecedence(task_before=integration, task_after=release)
```

``` bash
    TaskPrecedence_30566790(<class 'processscheduler.task_constraint.TaskPrecedence'>)
    1 assertion(s):
    Integration_end <= ReleaseMilestone_start
```

### Step 5. Create resources
Define all resources required for all tasks to be processed, including productivity and cost_per_period.

``` py
elias = ps.Worker(
    name="Elias", productivity=2, cost=ps.ConstantCostFunction(value=600)
)  # cost in $/day
louis = ps.Worker(
    name="Louis", productivity=2, cost=ps.ConstantCostFunction(value=600)
)
elise = ps.Worker(
    name="Elise", productivity=3, cost=ps.ConstantCostFunction(value=800)
)
justine = ps.Worker(
    name="Justine", productivity=2, cost=ps.ConstantCostFunction(value=1200)
)
```

### Step 6. Assign resources to tasks

``` py
preliminary_design.add_required_resources([elias, louis, elise, justine])
core_development.add_required_resources([louis, elise])
gui_development.add_required_resources([elise])
tests_development.add_required_resources([elias, louis])
integration.add_required_resources([justine])
release.add_required_resources([justine])
```
### Step 7. Add a total cost indicator
This resource cost indicator computes the total cost of selected resources.

``` py
cost_ind = ps.IndicatorResourceCost(list_of_resources=[elias, louis, elise, justine])
```

### Step 8. Solve and plot using plotly

``` py
# solve
solver = ps.SchedulingSolver(problem=problem)
solution = solver.solve()
```
``` bash
    Solver type:
    ===========
    	-> Standard SAT/SMT solver
    Total computation time:
    =====================
    	SoftwareDevelopment satisfiability checked in 0.01s
```

``` py
if solution:
    ps.render_gantt_plotly(solution)
```

![Gantt](img/software-development-gantt.png)
