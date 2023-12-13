# Use case: software development
To illustrate the way to use ProcessScheduler, let's imagine the simple following use case: the developmenent of a scheduling software intended for end-user. The software is developed using Python, and provides a modern Qt GUI. Three junior developers are in charge (Elias, Louis, Elise), under the supervision of their project manager Justine. The objective of this document is to generate a schedule of the different developmenent tasks to go rom the early design stages to the first software release. This notebook can tested online at mybinder.org
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/tpaviot/ProcessScheduler/HEAD?filepath=doc/use-case-software-development.ipynb)

### Step 1. Import the module
The best way to import the processscheduler module is to choose an alias import. Indeed, a global import should generate name conflicts. Here, the *ps* alias is used.


```python
import processscheduler as ps
from datetime import timedelta, datetime

%config InlineBackend.figure_formats = ['svg']
```

### Step 2. Create the scheduling problem
The SchedulingProblem has to be defined. The problem must have a name (it is a mandatory argument). Of course you can create as many problems (i.e; SchedulingProblem instances), for example if you need to compare two or more different schedules.


```python
problem = ps.SchedulingProblem(
    "SoftwareDevelopment", delta_time=timedelta(days=1), start_time=datetime.now()
)
```

### Step 3. Create tasks instances
The SchedulingProblem has to be defined. The problem must have a name (it is a mandatory argument). Of course you can create as many problems (i.e SchedulingProblem instances) as needed, for example if you need to compare two or more different schedules. In this example, one period is one day.


```python
preliminary_design = ps.FixedDurationTask("PreliminaryDesign", duration=1)  # 1 day
core_development = ps.VariableDurationTask("CoreDevelopmenent", work_amount=10)
gui_development = ps.VariableDurationTask("GUIDevelopment", work_amount=15)
integration = ps.VariableDurationTask("Integration", work_amount=3)
tests_development = ps.VariableDurationTask("TestDevelopment", work_amount=8)
release = ps.ZeroDurationTask("ReleaseMilestone")
```

### Step 4. Create tasks time constraints
Define precedences or set start and end times


```python
ps.TaskStartAt(preliminary_design, 0)
ps.TaskPrecedence(preliminary_design, core_development)
ps.TaskPrecedence(preliminary_design, gui_development)
ps.TaskPrecedence(gui_development, tests_development)
ps.TaskPrecedence(core_development, tests_development)
ps.TaskPrecedence(tests_development, integration)
ps.TaskPrecedence(integration, release)
```

### Step 5. Create resources
Define all resources required for all tasks to be processed, including productivity and cost_per_period.


```python
elias = ps.Worker(
    "Elias", productivity=2, cost=ps.ConstantCostPerPeriod(600)
)  # cost in $/day
louis = ps.Worker("Louis", productivity=2, cost=ps.ConstantCostPerPeriod(600))
elise = ps.Worker("Elise", productivity=3, cost=ps.ConstantCostPerPeriod(800))
justine = ps.Worker("Justine", productivity=2, cost=ps.ConstantCostPerPeriod(1200))
```

### Step 6. Assign resources to tasks


```python
preliminary_design.add_required_resources([elias, louis, elise, justine])
core_development.add_required_resources([louis, elise])
gui_development.add_required_resources([elise])
tests_development.add_required_resources([elias, louis])
integration.add_required_resources([justine])
release.add_required_resources([justine])
```

### Step 7. Add a total cost indicator
This resource cost indicator computes the total cost of selected resources.


```python
cost_ind = problem.add_indicator_resource_cost([elias, louis, elise, justine])
```

### Step 8. Solve and plot using plotly


```python
# solve
solver = ps.SchedulingSolver(problem)
solution = solver.solve()
```


```python
if solution:
    solution.render_gantt_plotly()
```
