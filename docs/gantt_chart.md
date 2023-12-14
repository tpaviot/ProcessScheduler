## Render to a Gantt chart

Call the :func:`render_gantt_matplotlib` to render the solution as a Gantt chart. The time line is from 0 to `horizon` value, you can choose to render either `Task` or `Resource` (default).

``` py
solution = solver.solve()
if solution is not None:
    solution.render_gantt_matplotlib()  # default render_mode is 'Resource'
    # a second gantt chart, in 'Task' mode
    solution.render_gantt_matplotlib(render_mode='Task')
```

Call the `ps.render_gantt_plotly` to render the solution as a Gantt chart using **plotly**.
Take care that plotly rendering needs **real timepoints** (set at least `delta_time` at the problem creation).

``` py
solution = solver.solve()
if solution is not None:
    # default render_mode is 'Resource'
    solution.render_gantt_plotly(sort="Start", html_filename="index.html")
    # a second gantt chart, in 'Task' mode
    solution.render_gantt_plotly(render_mode='Task')
```
