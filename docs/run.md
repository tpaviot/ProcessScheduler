# Run

In order to check that the installation is successful and ProcessScheduler ready to run on your machine, edit/run the following example:

```python
import processscheduler as ps 

pb = ps.SchedulingProblem(name="Test", horizon=10)

T1 = ps.FixedDurationTask(name="T1", duration=6)
T2 = ps.FixedDurationTask(name="T2", duration=4)

W1 = ps.Worker(name="W1")

T1.add_required_resource(W1)
T2.add_required_resource(W1)

solver = ps.SchedulingSolver(problem=pb)

solution = solver.solve()
print(solution)
```

If pandas is installed, you should get the following output:

```bash
Solver type:
===========
        -> Standard SAT/SMT solver
Total computation time:
=====================
        Test satisfiability checked in 0.00s
  Task name Allocated Resources  Start  End  Duration  Scheduled  Tardy
0        T1                [W1]      0    6         6       True  False
1        T2                [W1]      6   10         4       True  False
```
