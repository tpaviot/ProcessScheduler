# Indicator

The `Indicator` class allows to define a criterion that quantifies the schedule so that it can be compared with other schedules. An `Indicator` measures a specific behaviour you need to trace, evaluate or optimize.

All builtin indicators inherit from the base class `Indicator`:
``` mermaid
classDiagram
  Indicator
class Indicator{
    +List[int, int] bounds
  }
```

Indicator values are computed by the solver, and are part of the solution. If the solution is rendered as a matplotlib Gantt chart, the indicator value is displayed on the upper right corner of the chart.

!!! note

    There is no limit to the number of Indicators defined in the problem. The mathematical expression must be expressed in a polynomial form and using the `Sqrt` function. Any other advanced mathematical functions such as `exp`, `sin`, etc. is not allowed because not supported by the solver.

## Builtin indicators

Available builtin indicators are listed below:


| Type      | Apply to | Description                          |
| ----------- | -----| ------------------------------------ |
| IndicatorTardiness | List of tasks | Unweighted total tardiness of the selected tasks |
| IndicatorNumberOfTardyTasks | List of tasks | Number of tardy tasks from the selected tasks |
| IndicatorMaximumLateness | List of tasks | Maximum lateness of selected tasks |
| IndicatorResourceUtilization  | Single resource | Resource utilization, from 0% to 100% of the schedule horizon, of the selected resource |
| IndicatorNumberTasksAssigned  | Single resource | Number of tasks assigned to the selected resource |
| IndicatorResourceCost  | List of resources| Total cost of selected resources |
| IndicatorMaxBufferLevel  |Buffer | Maximum level of the selected buffer |
| IndicatorMinBufferLevel  | Buffer | Minimum level of the selected buffer |

## Customized indicators

Use the `IndicatorFromMathExpression` class to define an indicator that may not be available from the previous list.

``` py
ind = ps.IndicatorFromMathExpression(name="Task1End",
                                     expression=task_1._end)
```

or

``` py
ind = ps.IndicatorFromMathExpression(name="SquareDistanceBetweenTasks",
                                     expression=(task_1._start - task_2._end) ** 2)
```

Customized indicators can also be bounded, although it is an optional feature. Bounds are constraints over an indicator value. It is useful if the indicator is further be maximized (or minimized) by an optimization solver, in order to reduce the computation time. For example,

``` py
indicator1 = Indicator(name='Example1',
                       expression=task2.start - task1.end,
                       bounds = (0,100)) # If lower and upper bounded
indicator2 = Indicator(name='Example2',
                       expression=task3.start - task2.end,
                       bounds = (None,100)) # If only upper bounded
indicator3 = Indicator(name='Example3',
                       expression=task4.start - task3.end,
                       bounds = (0,None)) # If only lower bounded
```

Bounds are set to `None` by default.
