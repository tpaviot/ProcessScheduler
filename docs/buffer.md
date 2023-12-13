A `Buffer` is an object where tasks can load or unload a finite number of items. A ``Buffer`` can be used to represent a tank, or a temporary buffer of a workshop where manufactured parts are temporarily stored.

A `NonConcurrentBuffer` is a specific buffers where tasks cannot load and/or unload at the same time. In other words, only one task can access the buffer at a given time.
A `NonConcurrentBuffer`` has three main attributes:

1. the `initial_level`, i.e. the number of items in the buffer for time t=0,
2. the `lower_bound`, an optional parameter that sets the minimum number of items in the buffer during the schedule. If ever the solver cannot find a solution where the buffer level is always greater than the `lower_bound`, it will report an *unsatisfiable* problem,
3. the `upper_bound`, an optional parameter that sets the maximum number of items in the buffer during the schedule (in other words, the buffer capacity). If ever the solver cannot find a solution where the buffer level is always lower than the `upper_bound`, it will report an *unsatisfiable* problem.

Both `initial_level`, `lower_bound` and `upper_bound` are optional parameters. A `NonConcurrentBuffer` can be created as follows:

``` py
buff1 = ps.NonConcurrentBuffer("Buffer1")
buff2 = ps.NonConcurrentBuffer("Buffer2", initial_state=10)
buff3 = ps.NonConcurrentBuffer("Buffer3", lower_bound=0)
buff4 = ps.NonConcurrentBuffer("Buffer4", upper_bound=20)
buff5 = ps.NonConcurrentBuffer("Buffer5",
                               initial_state=3,
                               lower_bound=0, 
                               upper_bound=10)
```

## Buffer constraints

Buffers are loaded/unloaded by tasks. As a consequence, special tasks constraints are used to connect tasks to buffers: `TaskUnloadBuffer` and `TaskLoadBuffer`. Both classes take the task instance, the target buffer, and a `quantity`. Load/Unload constraints can be created as follows:

``` py
c1 = ps.TaskUnloadBuffer(task_1, buffer, quantity=3)
c2 = ps.TaskUnloadBuffer(task_2, buffer, quantity=6)
# etc.
```

!!! note

    There is no limitation on the number of buffers and/or buffer constraints.

### Example

Let's take an example where a task :const:`T1` uses a machine :const:`M1` to manufacture a part (duration time for this task is 4). It takes one part in a :const:`Buffer1` and loads the :const:`Buffer2`.

``` py
machine_1 = ps.Worker('M1')
task_1 = ps.FixedDurationTask('T1', duration=4)
task_1.add_required_resource(machine_1)
# the create buffers
buffer_1 = ps.NonConcurrentBuffer("Buffer1", initial_state=5)
buffer_2 = ps.NonConcurrentBuffer("Buffer2", initial_state=0)
# buffer constraints
c1 = ps.TaskUnloadBuffer(task_1, buffer_1, quantity=1)
c2 = ps.TaskLoadBuffer(task_1, buffer_2, quantity=1)
```

The graphical output shows the Gantt chart and the evolution of the buffer states along the time line.

![Buffer example](img/BufferExample.svg){ width="100%" }
