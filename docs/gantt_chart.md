## Render to a Gantt chart

### matplotlib

Call the :func:`render_gantt_matplotlib` to render the solution as a Gantt chart. The time line is from 0 to `horizon` value, you can choose to render either `Task` or `Resource` (default).

``` py
def render_gantt_matplotlib(
    solution: SchedulingSolution,
    fig_size: Optional[Tuple[int, int]] = (9, 6),
    show_plot: Optional[bool] = True,
    show_indicators: Optional[bool] = True,
    render_mode: Optional[str] = "Resource",
    fig_filename: Optional[str] = None,
)
```

``` py
solution = solver.solve()
if solution is not None:
    solution.render_gantt_matplotlib()  # default render_mode is 'Resource'
    # a second gantt chart, in 'Task' mode
    solution.render_gantt_matplotlib(render_mode='Task')
```

### plotly

!!! note

    Be sure plotly is installed.

``` py
def render_gantt_plotly(
    solution: SchedulingSolution,
    fig_size: Optional[Tuple[int, int]] = None,
    show_plot: Optional[bool] = True,
    show_indicators: Optional[bool] = True,
    render_mode: Optional[str] = "Resource",
    sort: Optional[str] = None,
    fig_filename: Optional[str] = None,
    html_filename: Optional[str] = None,
) -> None:
```

Call the `ps.render_gantt_plotly` to render the solution as a Gantt chart using **plotly**.

!!! warning

    Take care that plotly rendering needs **real timepoints** (set at least `delta_time` at the problem creation).

``` py
sol = solver.solve()
if sol is not None:
    # default render_mode is 'Resource'
    ps.render_gantt_plotly(solution=sol, sort="Start", html_filename="index.html")
    # a second gantt chart, in 'Task' mode
    ps.render_gantt_plotly(solution=sol, render_mode='Task')
```
