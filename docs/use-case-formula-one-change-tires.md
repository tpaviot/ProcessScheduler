# Use case: formula one pitstop

This example is based on the DailyMail blog entry https://www.dailymail.co.uk/sport/formulaone/article-4401632/Formula-One-pit-stop-does-crew-work.html where a nice image shows 21 people changing the 4 tires of a Formula 1 Ferrari. In this example, only 16 out 21 people are represented. This notebook can be tested online at mybinder.org
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/tpaviot/ProcessScheduler/HEAD?filepath=doc/use-case-formula-one-change-tires.ipynb)


```python
from IPython.display import YouTubeVideo

YouTubeVideo("aHSUp7msCIE", width=800, height=300)
```

### Imports


```python
import processscheduler as ps

%config InlineBackend.figure_formats = ['svg']
```

### Create the scheduling problem
The total horizon is not knwown, leave it empty and only set the problem name.


```python
change_tires_problem = ps.SchedulingProblem("ChangeTires")
```

### Create the 16 available resources
Each people in and around the car is represented as a worker.


```python
nb_lifters = 2
nb_gunners = 4
nb_tyre_handlers = 8
nb_stabilizers = 2
```


```python
# Lift tasks
lifters = [ps.Worker("JackOperator%i" % (i + 1)) for i in range(nb_lifters)]
gunners = [ps.Worker("Gunner%i" % (i + 1)) for i in range(nb_gunners)]
tyre_handlers = [ps.Worker("Handler%i" % (i + 1)) for i in range(nb_tyre_handlers)]
stabilizers = [ps.Worker("Stabilizer%i" % (i + 1)) for i in range(nb_stabilizers)]
```

### Create tasks and assign resources
One period is mapped to one second. For example, if lifting the rear take 2sec then the duration will be set to 2.


```python
# lift tasks and lifters
# both lift tasks can be processed by any one of the lifters
lift_rear_up = ps.FixedDurationTask("LiftRearUp", duration=2)
lift_front_up = ps.FixedDurationTask("LiftFrontUp", duration=2)
lift_rear_up.add_required_resource(lifters[0])
lift_front_up.add_required_resource(lifters[1])

lift_rear_down = ps.FixedDurationTask("LiftRearDown", duration=2)
lift_front_down = ps.FixedDurationTask("LiftFrontDown", duration=2)
lift_rear_down.add_required_resource(lifters[0])
lift_front_down.add_required_resource(lifters[1])

# unscrew tasks
unscrew_front_left_tyre = ps.FixedDurationTask("UnScrewFrontLeftTyre", duration=2)
unscrew_front_right_tyre = ps.FixedDurationTask("UnScrewFrontRightTyre", duration=2)
unscrew_rear_left_tyre = ps.FixedDurationTask("UnScrewRearLeftTyre", duration=2)
unscrew_rear_right_tyre = ps.FixedDurationTask("UnScrewRearRightTyre", duration=2)

gunner_unscrew_front_left_tyre = ps.SelectWorkers(gunners, 1)
unscrew_front_left_tyre.add_required_resource(gunner_unscrew_front_left_tyre)

gunner_unscrew_front_right_tyre = ps.SelectWorkers(gunners, 1)
unscrew_front_right_tyre.add_required_resource(gunner_unscrew_front_right_tyre)

gunner_unscrew_rear_left_tyre = ps.SelectWorkers(gunners, 1)
unscrew_rear_left_tyre.add_required_resource(gunner_unscrew_rear_left_tyre)

gunner_unscrew_rear_right_tyre = ps.SelectWorkers(gunners, 1)
unscrew_rear_right_tyre.add_required_resource(gunner_unscrew_rear_right_tyre)

# screw tasks and gunners
screw_front_left_tyre = ps.FixedDurationTask("ScrewFrontLeftTyre", duration=2)
screw_front_right_tyre = ps.FixedDurationTask("ScrewFrontRightTyre", duration=2)
screw_rear_left_tyre = ps.FixedDurationTask("ScrewRearLeftTyre", duration=2)
screw_rear_right_tyre = ps.FixedDurationTask("ScrewRearRightTyre", duration=2)

gunner_screw_front_left_tyre = ps.SelectWorkers(gunners)
screw_front_left_tyre.add_required_resource(gunner_screw_front_left_tyre)

gunner_screw_front_right_tyre = ps.SelectWorkers(gunners)
screw_front_right_tyre.add_required_resource(gunner_screw_front_right_tyre)

gunner_screw_rear_left_tyre = ps.SelectWorkers(gunners)
screw_rear_left_tyre.add_required_resource(gunner_screw_rear_left_tyre)

gunner_screw_rear_right_tyre = ps.SelectWorkers(gunners)
screw_rear_right_tyre.add_required_resource(gunner_screw_rear_right_tyre)
```


```python
# tires OFF and handlers
front_left_tyre_off = ps.FixedDurationTask("FrontLeftTyreOff", duration=2)
front_right_tyre_off = ps.FixedDurationTask("FrontRightTyreOff", duration=2)
rear_left_tyre_off = ps.FixedDurationTask("RearLeftTyreOff", duration=2)
rear_right_tyre_off = ps.FixedDurationTask("RearRightTyreOff", duration=2)

for tyre_off_task in [
    front_left_tyre_off,
    front_right_tyre_off,
    rear_left_tyre_off,
    rear_right_tyre_off,
]:
    tyre_off_task.add_required_resource(ps.SelectWorkers(tyre_handlers))

# tires ON and handlers, same as above
front_left_tyre_on = ps.FixedDurationTask("FrontLeftTyreOn", duration=2)
front_right_tyre_on = ps.FixedDurationTask("FrontRightTyreOn", duration=2)
rear_left_tyre_on = ps.FixedDurationTask("RearLeftTyreOn", duration=2)
rear_right_tyre_on = ps.FixedDurationTask("RearRightTyreOn", duration=2)

for tyre_on_task in [
    front_left_tyre_on,
    front_right_tyre_on,
    rear_left_tyre_on,
    rear_right_tyre_on,
]:
    tyre_on_task.add_required_resource(ps.SelectWorkers(tyre_handlers))
```

**Stabilizers** start their job as soon as the car is stopped until the end of the whole activity.


```python
stabilize_left = ps.VariableDurationTask("StabilizeLeft")
stabilize_right = ps.VariableDurationTask("StabilizeRight")

stabilize_left.add_required_resource(stabilizers[0])
stabilize_right.add_required_resource(stabilizers[1])

ps.TaskStartAt(stabilize_left, 0)
ps.TaskStartAt(stabilize_right, 0)

ps.TaskEndAt(stabilize_left, change_tires_problem.horizon)
ps.TaskEndAt(stabilize_right, change_tires_problem.horizon)
```

### Task precedences


```python
# front left tyre operations
fr_left = [
    unscrew_front_left_tyre,
    front_left_tyre_off,
    front_left_tyre_on,
    screw_front_left_tyre,
]
for i in range(len(fr_left) - 1):
    ps.TaskPrecedence(fr_left[i], fr_left[i + 1])
# front right tyre operations
fr_right = [
    unscrew_front_right_tyre,
    front_right_tyre_off,
    front_right_tyre_on,
    screw_front_right_tyre,
]
for i in range(len(fr_right) - 1):
    ps.TaskPrecedence(fr_right[i], fr_right[i + 1])
# rear left tyre operations
re_left = [
    unscrew_rear_left_tyre,
    rear_left_tyre_off,
    rear_left_tyre_on,
    screw_rear_left_tyre,
]
for i in range(len(re_left) - 1):
    ps.TaskPrecedence(re_left[i], re_left[i + 1])
# front left tyre operations
re_right = [
    unscrew_rear_right_tyre,
    rear_right_tyre_off,
    rear_right_tyre_on,
    screw_rear_right_tyre,
]
for i in range(len(re_right) - 1):
    ps.TaskPrecedence(re_right[i], re_right[i + 1])

# all un screw operations must start after the car is lift by both front and rear jacks
for unscrew_tasks in [
    unscrew_front_left_tyre,
    unscrew_front_right_tyre,
    unscrew_rear_left_tyre,
    unscrew_rear_right_tyre,
]:
    ps.TaskPrecedence(lift_rear_up, unscrew_tasks)
    ps.TaskPrecedence(lift_front_up, unscrew_tasks)

# lift down operations must occur after each screw task is completed
for screw_task in [
    screw_front_left_tyre,
    screw_front_right_tyre,
    screw_rear_left_tyre,
    screw_rear_right_tyre,
]:
    ps.TaskPrecedence(screw_task, lift_rear_down)
    ps.TaskPrecedence(screw_task, lift_front_down)
```

### First solution, plot the schedule


```python
solver = ps.SchedulingSolver(change_tires_problem)
solution_1 = solver.solve()
solution_1.render_gantt_matplotlib(fig_size=(10, 5), render_mode="Resource")
```

### Second solution: add a makespan objective
Obviously, the former solution is not the *best* solution, not sure Ferrari will win this race ! The whole "change tires" activity must be as short as possible, so let's add a *makespan* objective, i.e. a constraint that minimizes the schedule horizon.


```python
# add makespan objective
change_tires_problem.add_objective_makespan()

solver_2 = ps.SchedulingSolver(change_tires_problem)
solution_2 = solver_2.solve()
solution_2.render_gantt_matplotlib(fig_size=(9, 5), render_mode="Task")
```

### Third solution: constraint workers
This is not the best possible solution. Indeed, we can notice that the Gunner2 unscrews the RearRightTyre and screw the RearLeft tyre. We cannot imagine that a solution where gunners turn around the car is acceptable. There are two solutions to fix the schedule:
-   let the gunner be able to turn around the car, and add a "Move" task with a duration that represent the time necessary to move from one tyre to the other,
-   constraint the worker to screw the same tyre he unscrewed. Let's go this way


```python
ps.SameWorkers(gunner_unscrew_front_left_tyre, gunner_screw_front_left_tyre)
ps.SameWorkers(gunner_unscrew_front_right_tyre, gunner_screw_front_right_tyre)
ps.SameWorkers(gunner_unscrew_rear_left_tyre, gunner_screw_rear_left_tyre)
ps.SameWorkers(gunner_unscrew_rear_right_tyre, gunner_screw_rear_right_tyre)

solver_3 = ps.SchedulingSolver(change_tires_problem)
solution_3 = solver_3.solve()
solution_3.render_gantt_matplotlib(fig_size=(9, 5), render_mode="Task")
```

This is much better !
