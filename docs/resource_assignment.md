# Resource assignment

In the context of scheduling, resource assignment is the process of determining which resource or resources should be assigned to a task for its successful processing. ProcessScheduler provides flexible ways to specify resource assignments for tasks, depending on your scheduling needs. A `Worker` instance can process only one task per time period whereas a `CumulativeWorker` can process multiple tasks at the same time.

!!! note

    To assign a resource to a task, use the **add_required_resources** method of the `Task` class.

The semantics of the resource assignment is the creation of the relationship between any instance of the `Task` class and a `Resource`.

``` mermaid
classDiagram
    Task "0..n" -- "1..n" Resource
```

The most common case is that a finite number $n$ of workers are required to perform a set of $m$ tasks.

There are three ways to assign resource(s) to perform a task : single resource assignment, multiple resource assignement and alternative resource assignement.


## Single resource assignment

For assigning a single resource to a task, you can use the following syntax:

``` py
assemble_engine = FixedDurationTask(name='AssembleCarEngine',
                                    duration=10)
john = Worker(name='JohnBenis')

# the AssembleCarEngine can be processed by JohnBenis ONLY
assemble_engine.add_required_resource(john)
```

## Multiple resources assignment

To assign multiple resources to a single task, you can use the following approach:

``` py
paint_car = FixedDurationTask(name='PaintCar',
                              duration=13)

john = Worker(name='JohnBenis')
alice = Worker(name='AliceParker')

# the PaintCar task requires JohnBenis AND AliceParker
paint_engine.add_required_resources([john, alice])
```

All of the workers in the list are mandatory to perform the task. If ever one of the worker is not available, then the task cannot be scheduled.

## Alternative resource assignment

ProcessScheduler introduces the `SelectWorkers` class, which allows the solver to decide which resource(s) to assign to a task from a collection of capable workers. You can specify whether the solver should assign exactly $n$ resources, at most $n$ resources, or at least $n$ resources.

``` mermaid
classDiagram
  SelectWorkers
class SelectWorkers{
    +List[Resource] list_of_workers
    +int nb_workers_to_select
    +str kind
  }
```
Let's consider the following example: 3 drillers are available, a drilling task can be processed by any of one of these 3 drillers. This can be represented as:

``` py
drilling_hole = FixedDurationTask(name='DrillHolePhi10mm',
                                  duration=10)
driller_1 = Worker(name='Driller1')
driller_2 = Worker(name='Driller2')
driller_3 = Worker(name='Driller3')

# the DrillHolePhi10mm task can be processed by the Driller1 OR
# the Driller2 OR the Driller 3
sw = SelectWorkers(list_of_workers=[driller_1, driller_2, driller_3],
                   nb_workers_to_select=1,
                   kind='exact')

drilling_hole.add_required_resource(sw)
```

In this case, the solver is instructed to assign exactly one resource from the list of three workers capable of performing the task. The `kind` parameter can be set to `'exact'` (default), `'min'`, or `'max'`, depending on your requirements. Additionally, you can specify the number of workers to select with `nb_workers_to_select`, which can be any integer between 1 (default value) and the total number of eligible workers in the list.

These resource assignment options provide flexibility and control over how tasks are allocated to available resources, ensuring efficient scheduling in various use cases.
