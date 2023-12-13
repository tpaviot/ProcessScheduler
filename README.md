[![Codacy Badge](https://app.codacy.com/project/badge/Grade/7221205f866145bfa4f18c08bd96e71f)](https://www.codacy.com/gh/tpaviot/ProcessScheduler/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=tpaviot/ProcessScheduler&amp;utm_campaign=Badge_Grade)
[![codecov](https://codecov.io/gh/tpaviot/ProcessScheduler/branch/master/graph/badge.svg?token=9HI1FPJUDL)](https://codecov.io/gh/tpaviot/ProcessScheduler)
[![Azure Build Status](https://dev.azure.com/tpaviot/ProcessScheduler/_apis/build/status/tpaviot.ProcessScheduler?branchName=master)](https://dev.azure.com/tpaviot/ProcessScheduler/_build?definitionId=9)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/tpaviot/ProcessScheduler/HEAD?filepath=examples-notebooks)
[![Documentation Status](https://readthedocs.org/projects/processscheduler/badge/?version=latest)](https://processscheduler.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/ProcessScheduler.svg)](https://badge.fury.io/py/ProcessScheduler)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4480745.svg)](https://doi.org/10.5281/zenodo.4480745)

# ProcessScheduler
ProcessScheduler is a Python package for creating optimized scheduling based on identified resources and tasks to be carried out. It offers a set of classes and methods for finely modeling a wide range of use cases with rich semantics. Complex mathematical calculations necessary for problem resolution are transparently handled for the user, allowing them to focus on problem modeling. ProcessScheduler is aimed at project managers, business organization consultants, or industrial logistics experts looking to optimize the achievement of time or cost objectives.

## Updates

- [2023/12/13]: Huge on-going refactoring [#133](https://github.com/tpaviot/ProcessScheduler/issues/133)
- [2023/12/12]: Release 0.9.4

## Features

* Tasks: Creation of tasks defined by their duration, priority, and required effort.

* Resources: Individual workers defined by their productivity, cost, and availability.

* Resource Allocation: Allocation from a set of workers sharing common skills.

* Buffers: Support for tasks that consume raw materials.

* Indicators: Including cost, resource effort, or any customized indicator.

* Task and resource constraints that can be combined using first-order logic operations (NOT, OR, XOR, AND, IMPLIES, IF/THEN ELSE) for rich representations.

* Multi-optimized schedule computation, including makespan, flowtime, earliest start, latest start, resource cost, or any customized indicator you have defined.

* Gantt diagram generation and rendering.

* Results export to JSON, SMT-LIB 2.0, Excel, or other formats for further analysis.

## Install latest version with pip

Install with pip.

```bash
pip install ProcessScheduler==0.9.4
```

This comes with the only required dependency: the Microsoft free and open source licenses [S3 solver](https://github.com/Z3Prover/z3). If you want to take advantage of all the features, you can install optional dependencies:

```bash
pip install matplotlib plotly kaleido ipywidgets isodate ipympl psutil XlsxWriter
```

## Run online

There are some Jupypter notebooks that can be executed online at [myBinder.org](https://mybinder.org/v2/gh/tpaviot/ProcessScheduler/HEAD?filepath=examples-notebooks)

## Documentation

User-end documentation available at https://processscheduler.readthedocs.io/

## Helloworld

```python
import processscheduler as ps
# a simple problem, without horizon (solver will find it)
pb = ps.SchedulingProblem('HelloWorldProcessScheduler')

# add two tasks
task_hello = ps.FixedDurationTask('Process', duration=2)
task_world = ps.FixedDurationTask('Scheduler', duration=2)

# precedence constraint: task_world must be scheduled
# after task_hello
ps.TaskPrecedence(task_hello, task_world)

# solve
solver = ps.SchedulingSolver(pb)
solution = solver.solve()

# display solution, ascii or matplotlib gantt diagram
solution.render_gantt_matplotlib()
```

![png](examples-notebooks/pics/hello_world_gantt.svg)

## Code quality

ProcessScheduler uses the following tools to ensure code quality:

* unittests,

* code coverage (coverage.py, codecov.io),

* continuous-integration at MS azure,

* static code analysis (codacy),

* spelling mistakes tracking (codespell),

* code formatting using the black python formatter

## License/Author

ProcessScheduler is distributed under the terms of the GNU General Public License v3 or (at your option) any later version. It is currently developed and maintained by Thomas Paviot (tpaviot@gmail.com).
