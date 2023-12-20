# ProcessScheduler

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/7221205f866145bfa4f18c08bd96e71f)](https://www.codacy.com/gh/tpaviot/ProcessScheduler/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=tpaviot/ProcessScheduler&amp;utm_campaign=Badge_Grade)
[![codecov](https://codecov.io/gh/tpaviot/ProcessScheduler/branch/master/graph/badge.svg?token=9HI1FPJUDL)](https://codecov.io/gh/tpaviot/ProcessScheduler)
[![Azure Build Status](https://dev.azure.com/tpaviot/ProcessScheduler/_apis/build/status/tpaviot.ProcessScheduler?branchName=master)](https://dev.azure.com/tpaviot/ProcessScheduler/_build?definitionId=9)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/tpaviot/ProcessScheduler/HEAD?filepath=examples-notebooks)
[![PyPI version](https://badge.fury.io/py/ProcessScheduler.svg)](https://badge.fury.io/py/ProcessScheduler)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4480745.svg)](https://doi.org/10.5281/zenodo.4480745)

ProcessScheduler is a versatile Python package designed for creating optimized scheduling in various industrial domains, including manufacturing, construction, healthcare, and more. This tool, aimed at project managers, business organization consultants, or industrial logistics experts, focuses on optimizing time or cost objectives. It offers a robust set of classes and methods to model a wide range of use cases with rich semantics, making it ideal for tackling intricate scheduling challenges. The package simplifies complex mathematical calculations necessary for problem resolution, thereby allowing users to concentrate on problem modeling rather than the computational intricacies, streamlining operations and offering solutions for scenarios that defy straightforward resolutions.

Within this toolkit, you'll find a rich array of features, including:

- **Task Definition**: Define tasks with zero, fixed, or variable durations, along with work_amount specifications.

- **Resource Management**: Create and manage resources, complete with productivity and cost attributes. Efficiently assign resources to tasks.

- **Temporal Task Constraints**: Handle task temporal constraints such as precedence, fixed start times, and fixed end times.

- **Resource Constraints**: Manage resource availability and allocation.

- **Logical Operations**: Employ first-order logic operations to define relationships between tasks and resource constraints, including and/or/xor/not boolean operators, implications, if/then/else conditions.

- **Multi-Objective Optimization**: Optimize schedules across multiple objectives.

- **Gantt Chart Visualization**: Visualize schedules effortlessly with Gantt chart rendering, compatible with both matplotlib and plotly libraries.

- **Export Capabilities**: Seamlessly export solutions to JSON format and SMT problems to SMTLIB format.

This comprehensive guide will walk you through the process of model creation, solver execution, and solution analysis, making it a valuable resource for harnessing the full potential of ProcessScheduler.
