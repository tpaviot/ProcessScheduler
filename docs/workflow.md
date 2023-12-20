# Workflow

The structure of the present documentation follows the workflow that mimics the template of a ProcessScheduler python script:

``` mermaid
graph TD
  A[Create a SchedulingProblem] --> B[Create objects that represent your problem];
  B --> C[Constraint the schedule];
  C --> D[Add objectives];
  D --> E[Solve];
  E --> F[Analye];
  F --> B;
```

* the **[SchedulingProblem](scheduling_problem.md)** is the core container of all. 

* choose among `Task` or `Resource` objects to represent the use case

* add temporal or logical constraints

* optiannly, add objectives if you need to find an optimal schedule according to the constraints

* solve

* render to a Gantt chart, to Excel, whatever, and eventually return back to the representation stage.