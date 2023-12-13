# Use case: flowshop scheduling

This example is based on the paper from Tao et al. (2015), where authors present an introduction example. In a flow shop problem, a set of $n$ jobs has to be processed on $m$ different machines in the same order. Job $j$, $j=1,2,...,n$ is processed on machines $i$, $i=1,2,..,m$, with a nonnegative processing time $p(i,j)$ and a release date $r_j$, which is the earliest time when the job is permitted to process. Each machine can process at most one job and each job can be handled by at most one machine at any given time. The machine processes the jobs in a first come, first served manner. The goal is to determine a job sequence that minimizes the makespan.

The problem statement is:
<img src="img/flow_shop_problem.png" alt="problem definition" width="160"/>

The following solution is reported by the authors (order J1, J3, J4, J2, scheduled horizon: 29):
<img src="img/flow_shop_solution.png" alt="gantt solution" width="500"/>

In this notebook, we try to reproduce the results reported by the authors.

**Reference**

Tao Ren, Meiting Guo, Lin Lin, Yunhui Miao, "A Local Search Algorithm for the Flow Shop Scheduling Problem with Release Dates", Discrete Dynamics in Nature and Society, vol. 2015, Article ID 320140, 8 pages, 2015. https://doi.org/10.1155/2015/320140

### Imports


```python
import processscheduler as ps

%config InlineBackend.figure_formats = ['svg']
```

### Create the scheduling problem
The total horizon is unknwown, leave it empty and only set the problem name.


```python
flow_shop_problem = ps.SchedulingProblem("FlowShop")
```

### Create the 3 machines M1, M2 and M3


```python
M3 = ps.Worker("M3")
M2 = ps.Worker("M2")
M1 = ps.Worker("M1")
```

### Create jobs J1, J2, J3 and J4 - related tasks


```python
# J1
J11 = ps.FixedDurationTask("J11", duration=2)
J12 = ps.FixedDurationTask("J12", duration=5)
J13 = ps.FixedDurationTask("J13", duration=6)

# J2
J21 = ps.FixedDurationTask("J21", duration=1)
J22 = ps.FixedDurationTask("J22", duration=5)
J23 = ps.FixedDurationTask("J23", duration=7)

# J3
J31 = ps.FixedDurationTask("J31", duration=1)
J32 = ps.FixedDurationTask("J32", duration=4)
J33 = ps.FixedDurationTask("J33", duration=1)

# J4
J41 = ps.FixedDurationTask("J41", duration=3)
J42 = ps.FixedDurationTask("J42", duration=4)
J43 = ps.FixedDurationTask("J43", duration=7)
```

### Assign resources
One machine per task.


```python
J11.add_required_resource(M1)
J12.add_required_resource(M2)
J13.add_required_resource(M3)

J21.add_required_resource(M1)
J22.add_required_resource(M2)
J23.add_required_resource(M3)

J31.add_required_resource(M1)
J32.add_required_resource(M2)
J33.add_required_resource(M3)

J41.add_required_resource(M1)
J42.add_required_resource(M2)
J43.add_required_resource(M3)
```

### Constraint: release dates


```python
r1 = 0
r2 = 9
r3 = 2
r4 = 7

ps.TaskStartAfter(J11, r1)
ps.TaskStartAfter(J12, r1)
ps.TaskStartAfter(J13, r1)

ps.TaskStartAfter(J21, r2)
ps.TaskStartAfter(J22, r2)
ps.TaskStartAfter(J23, r2)

ps.TaskStartAfter(J31, r3)
ps.TaskStartAfter(J32, r3)
ps.TaskStartAfter(J33, r3)

ps.TaskStartAfter(J41, r4)
ps.TaskStartAfter(J42, r4)
ps.TaskStartAfter(J43, r4)
```

### Constraints: precedences
All jobs should be scheduled in the same ordre on each machine. The constraint is expressed as following: all J2 tasks must be scheduled before Or after J2 tasks, AND all J3 tasks must be scheduled before OR oafter J1 tasks etc.


```python
J1 = [J11, J12, J13]
J2 = [J21, J22, J23]
J3 = [J31, J32, J33]
J4 = [J41, J42, J43]

# we need to combinations function of the itertools module,
# to compute all pairs from the list of jobs.
from itertools import combinations

for Ja, Jb in combinations([J1, J2, J3, J4], 2):
    befores = []
    afters = []
    for i in range(3):
        Ja_before_Jb = ps.TaskPrecedence(Ja[i], Jb[i])
        Ja_after_Jb = ps.TaskPrecedence(Jb[i], Ja[i])
        befores.append(Ja_before_Jb)
        afters.append(Ja_after_Jb)
    xor_operation = ps.xor_([ps.and_(befores), ps.and_(afters)])
    flow_shop_problem.add_constraint(xor_operation)
```

### Add  a makespan objective


```python
makespan_obj = flow_shop_problem.add_objective_makespan()
```

### Solution, plot the schedule


```python
solver = ps.SchedulingSolver(flow_shop_problem)
solution = solver.solve()
solution.render_gantt_matplotlib(fig_size=(10, 5), render_mode="Resource")
```

We confirm the job sort from Tao et al. (2015) (J1 then J3, J4 and finally J2). The horizon is here only 21.
