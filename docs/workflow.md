# Workflow

The structure of this documentation is designed to mirror the typical workflow of a ProcessScheduler Python script, guiding you through each step of the scheduling process:

``` mermaid
graph TD
  A[1. Create a SchedulingProblem] --> B[2. Create objects that represent the problem];
  B --> C[3. Constraint the schedule];
  C --> D[4. Add indicators];
  D --> E[5. Add objectives];
  E --> F[6. Solve];
  F --> G[7. Analyse];
  G --> B;
```

1. Create a **[SchedulingProblem](scheduling_problem.md)**: This is the foundational step where you establish the SchedulingProblem, serving as the primary container for all components of your scheduling scenario.

2. Create **Objects Representing The Problem**: Select appropriate **Task** and **Resource** objects to accurately represent the elements of your use case. This step involves defining the tasks to be scheduled and the resources available for these tasks.

3. Apply **Constraints** to the Schedule: Introduce temporal or logical constraints to define how tasks should be ordered or how resources are to be utilized. Constraints are critical for reflecting real-world limitations and requirements in your schedule.

4. Add **Indicators** (optional): indicators or metrics are added to the scheduling problem. These indicators might include key performance metrics, resource utilization rates, or other measurable factors that are crucial for analyzing the effectiveness of the schedule. By adding this step, the schedule can be more effectively monitored and evaluated.

5. Define **Objectives** (optional): you can specify one or more objectives. Objectives, built on Indicators, are used to determine what constitutes an 'optimal' schedule within the confines of your constraints. This could include minimizing total time, cost, or other metrics relevant to your scenario.

5. **Execute the Solver**: Run the solver to find a feasible (and possibly optimal, depending on defined objectives) schedule based on your tasks, resources, constraints, and objectives.

6. **Analyze** the Results: Once the solver has found a solution, you can render the schedule in various formats such as a Gantt chart or export it to Excel. This step is crucial for evaluating the effectiveness of the proposed schedule. Based on the analysis, you might revisit the representation stage to adjust your problem model, refine constraints, or alter objectives.

This workflow provides a structured approach to building and solving scheduling problems, ensuring that all essential aspects of your scheduling scenario are methodically addressed.