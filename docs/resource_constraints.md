# Resource Constraints

ProcessScheduler provides a set of ready-to-use resource constraints. They allow expressing common rules such as "the resource A is available only from 8 am to 12" etc. There are a set of builtin ready-to-use constraints, listed below.

``` mermaid
classDiagram
  Constraint <|-- ResourceConstraint
  ResourceConstraint <|-- WorkLoad
  ResourceConstraint <|-- ResourceUnavailable
  ResourceConstraint <|-- ResourceNonDelay
  ResourceConstraint <|-- ResourceTasksDistance
  ResourceConstraint <|-- SameWorkers
  ResourceConstraint <|-- DistinctWorkers
```

## WorkLoad

The `WorkLoad` constraint can be used to restrict the number of tasks which are executed during  certain time periods.

This constraint applies to one resource, whether it is a single worker or a cumulative worker. It takes the time periods as a python dictionary composed of time intervals (the keys) and an integer number (the capacity). The `kind` parameter allows to define which kind of restriction applies to the resource: `'exact'`, `'max'` (default value) or `'min'`.

``` py
 c1 = ps.WorkLoad(resource=worker_1,
                  dict_time_intervals_and_bound={(0, 6): 2})
```

In the previous example, the resource `worker_1` cannot be scheduled into more than 2 timeslots between instants 0 and 6.

Any number of time intervals can be passed to this class, just extend the timeslots dictionary, e.g.:

``` py
c1 = ps.WorkLoad(resource=worker_1,
                 dict_time_intervals_and_bound={(0, 6): 2, (19, 21): 6})
```

The `WorkLoad` is not necessarily a *limitation*. Indeed you can specify that the integer number is actually an exact of minimal value to target. For example, if we need the resource `worker_1` to be scheduled **at least** into three time slots between instants 0 and 10, then:

``` py
c1 = ps.WorkLoad(resource=worker_1,
                 dict_time_intervals_and_bound={(0, 10): 3},
                 kind='min')
```

## ResourceUnavailable

A `ResourceUnavailable` applies to a resource and prevent the solver to schedule this resource during certain time periods. This class takes a list of intervals:

``` py
worker_1 = ps.Worker('Sylvia')
ca = ps.ResourceUnavailable(resource=worker_1,
                            list_of_time_intervals=[(1,2), (6,8)])
```

The `ca` instance constraints the resource to be unavailable for 1 period between 1 and 2 instants, and for 2 periods between instants 6 and 8.

!!! note

    This constraint is a special case for the `WorkLoad` where the `number_of_time_slots` is set to `0`.


## ResourceTasksDistance

This constraint enforces a specific number of time unitary periods between tasks for a single resource. It can be applied within specified time intervals.

| attribute | type | default | description |
| --------- | ---- | ------- | ----------- |
| resource  | Union[Worker, CumulativeWorker] | x | The resource to which the constraint applies.|
| distance  | int  |   X     | The desired number of time unitary periods between tasks.|
| list_of_time_intervals | list | None | A list of time intervals within which the constraint is restricted.|
| mode | Literal["min", "max", "exact"] | "exact" | The mode for enforcing the constraint |

``` py
worker_1 = ps.Worker(name="Worker1")

ps.ResourceTasksDistance(
    resource=worker_1,
    distance=4,
    mode="exact",
    list_of_time_intervals=[[10, 20], [30, 40]])
```

## ResourceNonDelay

A non-delay schedule is a type of feasible schedule where no machine is kept idle while there is an operation waiting for processing. Essentially, this approach prohibits unforced idleness.

`ResourceNonDelay` class is designed to prevent idle time for a resource when a task is ready for processing bu forcing idle time to 0. That means that all tasks processed by this resource will be contiguous in the schedule, if ever a solution exists.

``` py
machine_1 = ps.Worker('Machine1')
ps.ResourceNonDelay(resource=worker_1)
```

## DistinctWorkers

A `AllDifferentWorkers` constraint applies to two `SelectWorkers` instances, used to assign alternative resources to a task. It constraints the solver to select different workers for each `SelectWorkers`. For instance:

``` py
s1 = ps.SelectWorkers(list_of_workers=[worker_1, worker_2])
s2 = ps.SelectWorkers(list_of_workers=[worker_1, worker_2])
```

could lead the solver to select worker_1 in both cases. Adding the following line:

``` py
cs = ps.DistinctWorkers(select_workers_1=s1,
                        select_workers_2=s2)
```

let the solver selects the worker_1 for s1 and worker_2 for s2 or the opposite, worker_2 for s1 and worker_1 for s2. The cases where worker_1 is selected by both s1 and s2 or worker_2 by selected by both s1 and s2 are impossible.

## SameWorkers

A `AllSameWorkers` constraint applies to two `SelectWorkers` instances. It constraints the solver to ensure both different `SelectWorkers` instances select the same worker. For example:

``` py
s1 = ps.SelectWorkers(list_of_workers=[worker_1, worker_2])
s2 = ps.SelectWorkers(list_of_workers=[worker_1, worker_2])
```

could lead the solver to select worker_1 for s1 and worker_2 for s2. Adding the following line:

``` py
cs = ps.SameWorkers(select_workers_1=s1,
                    select_workers_2=s2)
```

ensures either worker_1 is selected by both s1 and s2, or worker_2 is selected by both s1 and s2.
