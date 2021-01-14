[![Codacy Badge](https://app.codacy.com/project/badge/Grade/7221205f866145bfa4f18c08bd96e71f)](https://www.codacy.com/gh/tpaviot/ProcessScheduler/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=tpaviot/ProcessScheduler&amp;utm_campaign=Badge_Grade)
[![codecov](https://codecov.io/gh/tpaviot/ProcessScheduler/branch/master/graph/badge.svg?token=9HI1FPJUDL)](https://codecov.io/gh/tpaviot/ProcessScheduler)
[![Azure Build Status](https://dev.azure.com/tpaviot/ProcessScheduler/_apis/build/status/tpaviot.ProcessScheduler?branchName=master)](https://dev.azure.com/tpaviot/ProcessScheduler/_build?definitionId=9)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/tpaviot/ProcessScheduler/HEAD?filepath=examples-notebooks)
[![Documentation Status](https://readthedocs.org/projects/processscheduler/badge/?version=latest)](https://processscheduler.readthedocs.io/en/latest/?badge=latest)

# ProcessScheduler
A python library to compute resource-constrained task schedules.

## About
The computation is based on a set of constraints expressed under the form of first-order logic assertions. Problem solving is performed by the [Z3Prover](https://github.com/Z3Prover/z3).

## Helloworld

```python
import processscheduler as ps
# a simple problem, without horizon (solver will find it)
pb = ps.SchedulingProblem('HelloWorldProcessScheduler')

# add two tasks
task_hello = ps.FixedDurationTask('Process', duration=2)
task_world = ps.FixedDurationTask('Scheduler', duration=2)
pb.add_tasks([task_hello, task_world])

# precedence constraint: task_world must be scheduled
# after task_hello
c1 = ps.TaskPrecedence(task_hello, task_world, offset=0)
pb.add_constraint(c1)

# solve
solver = ps.SchedulingSolver(pb)
solver.solve()

# displays solution, ascii or matplotlib gantt diagram
pb.render_gantt_matplotlib()
```

![png](examples-notebooks/pics/hello_world_gantt.svg)

## Features

*   tasks: ZeroDurationTask, FixedDurationTask, VariableDurationTask
*   resources: Worker, AlternativeWorkers
*   task constraints: TasksPrecedence, TasksStartSynced, TasksEndSynced, TaskStartAt, TaskEndAt, TaskStartAfterStrict, TaskStartAfterLax, TaskEndBeforeStrict, TaskEndBeforeLax
*   nested boolean operators between task constraints: not, or, xor, and
*   objectives: makespan, flowtime, earliest, latest

## Installation

ProcessScheduler has not any release yet. You have to download/test the development version from the git repository.

Fist create a local copy of this repository:
```bash
git clone https://github.com/tpaviot/ProcessScheduler
```
then install the development version:

```bash
cd ProcessScheduler
pip install ./src
```

## Documentation

Documentation can be found at https://processscheduler.readthedocs.io/

## Jypter notebooks

There are some [Jupypter notebooks](https://github.com/tpaviot/ProcessScheduler/tree/master/example-notebooks). They can be executed online at [myBinder.org](https://mybinder.org/v2/gh/tpaviot/ProcessScheduler/HEAD?filepath=example-notebooks)

## Code quality

ProcessScheduler code is unittested, covered (coverage.py, codecov.io), continuously-integrated at MS azure, analyzed (codacy).

## License/Author

ProcessScheduler is distributed under the terms of the GNU General Public License v3 or (at your option) any later version. 
