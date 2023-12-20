# Workflow

The structure of the present documentation follows the workflow that mimics the template of a ProcessScheduler python script:

``` mermaid
graph TD
  A[Create a SchedulingProblem] --> B[Create objects that represent your problem];
  B --> C[Create constraints];
  C --> D[Create objectives];
  D --> E[Solve];
  E --> F[Analye];
  F --> B;
```
