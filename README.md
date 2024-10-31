# ProcessScheduler

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/7221205f866145bfa4f18c08bd96e71f)](https://www.codacy.com/gh/tpaviot/ProcessScheduler/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=tpaviot/ProcessScheduler&amp;utm_campaign=Badge_Grade)
[![codecov](https://codecov.io/gh/tpaviot/ProcessScheduler/branch/master/graph/badge.svg?token=9HI1FPJUDL)](https://codecov.io/gh/tpaviot/ProcessScheduler)
[![Azure Build Status](https://dev.azure.com/tpaviot/ProcessScheduler/_apis/build/status/tpaviot.ProcessScheduler?branchName=master)](https://dev.azure.com/tpaviot/ProcessScheduler/_build?definitionId=9)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/tpaviot/ProcessScheduler/HEAD?filepath=examples-notebooks)
[![PyPI version](https://badge.fury.io/py/ProcessScheduler.svg)](https://badge.fury.io/py/ProcessScheduler)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4480745.svg)](https://doi.org/10.5281/zenodo.4480745)

ProcessScheduler is a Python package for optimizing scheduling problems using advanced constraint satisfaction techniques. It provides an intuitive API for modeling complex scheduling scenarios while handling the underlying mathematical computations transparently.

## Updates

-   2024/01/31: Release 2.0.0
-   2024/01/30: Release 2.0.0a
-   2023/12/13: Huge on-going refactoring [#133](https://github.com/tpaviot/ProcessScheduler/issues/133)
-   2023/12/12: Release 0.9.4

## Key Features

- **Task Management**
  - Define tasks with duration, priority, and work requirements
  - Support for fixed, variable, and zero-duration tasks
  - Optional tasks and task dependencies

- **Resource Handling**
  - Individual workers with productivity and cost parameters
  - Resource pools with shared skills
  - Resource availability and unavailability periods

- **Constraint Modeling**
  - Rich set of task and resource constraints
  - First-order logic operations (NOT, OR, XOR, AND, IMPLIES, IF/THEN/ELSE)
  - Buffer management for material consumption/production

- **Optimization & Analysis**
  - Multi-objective optimization (makespan, flowtime, cost)
  - Custom performance indicators
  - Gantt chart visualization
  - Export to JSON, SMT-LIB 2.0, Excel formats

## Installation

### Basic Installation
```bash
pip install ProcessScheduler==2.0.0
```

### Full Installation (with optional dependencies)
```bash
pip install ProcessScheduler[full]==2.0.0
# Or install optional dependencies separately:
pip install matplotlib plotly kaleido ipywidgets isodate ipympl psutil XlsxWriter
```

## Documentation & Examples

- [Documentation](https://processscheduler.github.io/)
- [Interactive Examples](https://mybinder.org/v2/gh/tpaviot/ProcessScheduler/HEAD?filepath=examples-notebooks) (via Binder)


## Quick Start

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

-   unittests,
-   code coverage (coverage.py, codecov.io),
-   continuous-integration at MS azure,
-   static code analysis (codacy),
-   spelling mistakes tracking (codespell),
-   code formatting using the black python formatter

## License/Author

ProcessScheduler is distributed under the terms of the GNU General Public License v3 or (at your option) any later version. It is currently developed and maintained by Thomas Paviot (tpaviot@gmail.com).
