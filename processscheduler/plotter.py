# Copyright (c) 2020-present Thomas Paviot (tpaviot@gmail.com)
#
# This file is part of ProcessScheduler.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.

from pathlib import Path
import random
from typing import Optional, Tuple, Union
import warnings

try:
    import numpy as np

    HAVE_NUMPY = True
except ImportError:
    HAVE_NUMPY = False

try:
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    HAVE_MATPLOTLIB = True
except ImportError:
    HAVE_MATPLOTLIB = False

try:
    from plotly.figure_factory import create_gantt

    HAVE_PLOTLY = True
except ImportError:
    HAVE_PLOTLY = False

from processscheduler.function import (
    ConstantFunction,
    LinearFunction,
    PolynomialFunction,
)
from processscheduler.solution import SchedulingSolution


def plot_function(
    function: Union[ConstantFunction, LinearFunction, PolynomialFunction],
    interval: Tuple[float, float],
    show_plot=True,
    n_points=100,
    title="Function",
) -> None:
    """Plot the function curve using matplotlib."""
    if not HAVE_MATPLOTLIB:
        raise ModuleNotFoundError("matplotlib is not installed.")

    if not HAVE_NUMPY:
        raise ModuleNotFoundError("numpy is not installed.")

    lower_bound, upper_bound = interval
    x = np.linspace(lower_bound, upper_bound, n_points)
    y = [function(x_) for x_ in x]
    if isinstance(function, ConstantFunction):
        label_function = f"$f(t)={function.value}$"
    elif isinstance(function, LinearFunction):
        label_function = f"$f(t)={function.slope} t + {function.intercept}$"
    elif isinstance(function, PolynomialFunction):
        degree = len(function.coefficients) - 1
        label_function = "$"
        first_coeff = function.coefficients[0]
        if first_coeff != 0:
            label_function += f"{first_coeff}t^{degree}"
        for i, coefficient in enumerate(function.coefficients[1:-1]):
            if coefficient != 0:
                label_function += f"+{coefficient}t^{degree-i}"
        last_coeff = function.coefficients[-1]
        if last_coeff != 0:
            label_function += f"+{last_coeff}"
        label_function += "$"
    plt.plot(x, y, label=label_function)
    plt.legend()
    plt.title(title)
    plt.grid(True)
    plt.xlabel("x")
    plt.ylabel("F(x)")

    if show_plot:
        plt.show()


#
# Gantt graphical rendering using plotly and matplotlib
#
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
    """Use plotly.create_gantt method, see
    https://plotly.github.io/plotly.py-docs/generated/plotly.figure_factory.create_gantt.html
    """
    if not solution:
        raise AssertionError("no solution.")

    if not HAVE_PLOTLY:
        raise AssertionError("plotly is not installed.")

    if render_mode not in ["Task", "Resource"]:
        raise ValueError("data_type must be either Task or Resource")

    # tasks to render
    if render_mode == "Task":
        tasks_to_render = solution.get_scheduled_tasks()
    else:
        tasks_to_render = solution.tasks

    df = []
    for task_name in tasks_to_render:
        task_solution = solution.tasks[task_name]
        if task_solution.assigned_resources:
            resource_text = ",".join(task_solution.assigned_resources)
        else:
            resource_text = r"($\emptyset$)"
        df.append(
            dict(
                Task=task_name,
                Start=task_solution.start_time,
                Finish=task_solution.end_time,
                Resource=resource_text,
            )
        )

    gantt_title = f"{solution.problem.name} Gantt chart"
    # add indicators value to title
    if solution.indicators and show_indicators:
        for indicator_name in solution.indicators:
            gantt_title += f" - {indicator_name}: {solution.indicators[indicator_name]}"

    def r():
        return random.randint(0, 255)

    colors = ["#%02X%02X%02X" % (r(), r(), r()) for _ in df]
    if sort is not None:
        if sort in ["Task", "Resource"]:
            df = sorted(df, key=lambda i: i[sort], reverse=False)
        elif sort in ["Start", "Finish"]:
            df = sorted(df, key=lambda i: i[sort], reverse=True)
        else:
            raise ValueError(
                'sort must be either "Task", "Resource", "Start", or "Finish"'
            )

    if fig_size is None:
        fig = create_gantt(
            df,
            colors=colors,
            index_col=render_mode,
            show_colorbar=True,
            showgrid_x=True,
            showgrid_y=True,
            show_hover_fill=True,
            title=gantt_title,
            bar_width=0.5,
        )
    else:
        fig = create_gantt(
            df,
            colors=colors,
            index_col=render_mode,
            show_colorbar=True,
            showgrid_x=True,
            showgrid_y=True,
            show_hover_fill=True,
            title=gantt_title,
            bar_width=0.5,
            width=fig_size[0],
            height=fig_size[1],
        )

    # buffers, show an histogram
    if solution.buffers:
        warnings.warn("Not implemented. TODO: render buffers")

    if fig_filename is not None:
        fig.write_image(fig_filename)

    if html_filename is not None:
        file = Path(html_filename)
        file.write_text(fig.to_html(include_plotlyjs="cdn"), encoding="utf-8")

    if show_plot:
        fig.show()


def render_gantt_matplotlib(
    solution: SchedulingSolution,
    fig_size: Optional[Tuple[int, int]] = (9, 6),
    show_plot: Optional[bool] = True,
    show_indicators: Optional[bool] = True,
    render_mode: Optional[str] = "Resource",
    fig_filename: Optional[str] = None,
) -> None:
    """generate a gantt diagram using matplotlib.
    Inspired by
    https://www.geeksforgeeks.org/python-basic-gantt-chart-using-matplotlib/
    """
    if not solution:
        raise AssertionError("no solution.")

    if not solution.resources:
        render_mode = "Task"

    if render_mode not in ["Resource", "Task"]:
        raise ValueError("render_mode must either be 'Resource' or 'Task'")

    # tasks to render
    if render_mode == "Task":
        tasks_to_render = (
            solution.get_scheduled_tasks()
        )  # get_all_tasks_but_unavailable()
    else:
        tasks_to_render = solution.tasks

    # render mode is Resource by default, can be set to 'Task'
    if render_mode == "Resource":
        plot_title = f"Resources schedule - {solution.problem.name}"
        plot_ylabel = "Resources"
        plot_ticklabels = list(solution.resources.keys())
        nbr_y_values = len(solution.resources)
    elif render_mode == "Task":
        plot_title = f"Task schedule - {solution.problem.name}"
        plot_ylabel = "Tasks"
        plot_ticklabels = list(tasks_to_render.keys())
        nbr_y_values = len(tasks_to_render)

    if solution.buffers:
        gantt_chart, buffer_chart = plt.subplots(2, 1, figsize=fig_size)[1]
    else:
        gantt_chart = plt.subplots(1, 1, figsize=fig_size)[1]
    gantt_chart.set_title(plot_title)

    # x axis, use real date and times if possible
    if solution.problem.delta_time is not None:
        if solution.problem.start_time is not None:
            # get all days
            times = [
                solution.problem.start_time + i * solution.problem.delta_time
                for i in range(solution.horizon + 1)
            ]
            times_str = []
            for t in times:
                times_str.append(t.strftime("%H:%M"))
        else:
            times_str = [
                f"{i * solution.problem.delta_time}"
                for i in range(solution.horizon + 1)
            ]
        gantt_chart.set_xlim(0, solution.horizon)
        plt.xticks(range(solution.horizon + 1), times_str, rotation=60)
        plt.subplots_adjust(bottom=0.15)
        gantt_chart.set_xlabel("Time", fontsize=12)
    else:
        # otherwise use integers
        gantt_chart.set_xlim(0, solution.horizon)
        gantt_chart.set_xticks(range(solution.horizon + 1))
        # Setting label
        gantt_chart.set_xlabel(f"Time ({solution.horizon} periods)", fontsize=12)

    gantt_chart.set_ylabel(plot_ylabel, fontsize=12)

    # colormap definition
    cmap = LinearSegmentedColormap.from_list(
        "custom blue", ["#bbccdd", "#ee3300"], N=len(solution.tasks)
    )  # nbr of colors
    # defined a mapping between the tasks and the colors, so that
    # each task has the same color on both graphs
    task_colors = {}
    for i, task_name in enumerate(tasks_to_render):
        task_colors[task_name] = cmap(i)
    # the task color is defined from the task name, this way the task has
    # already the same color, even if it is defined after
    gantt_chart.set_ylim(0, 2 * nbr_y_values)
    gantt_chart.set_yticks(range(1, 2 * nbr_y_values, 2))
    gantt_chart.set_yticklabels(plot_ticklabels)
    # in Resources mode, create one line per resource on the y axis
    gantt_chart.grid(axis="x", linestyle="dashed")

    def draw_broken_barh_with_text(start, length, bar_color, text, hatch=None):
        # first compute the bar dimension
        bar_dimension = (start - 0.05, 0.1) if length == 0 else (start, length)
        gantt_chart.broken_barh(
            [bar_dimension],
            (i * 2, 2),
            edgecolor="black",
            linewidth=2,
            facecolors=bar_color,
            hatch=hatch,
            alpha=0.5,
        )
        gantt_chart.text(
            x=start + length / 2,
            y=i * 2 + 1,
            s=text,
            ha="center",
            va="center",
            color="black",
        )

    # in Tasks mode, create one line per task on the y axis
    if render_mode == "Task":
        for i, task_name in enumerate(tasks_to_render):
            # build the bar text string
            task_solution = solution.tasks[task_name]
            if task_solution.assigned_resources:
                text = ",".join(task_solution.assigned_resources)
            else:
                text = r"($\emptyset$)"
            draw_broken_barh_with_text(
                task_solution.start,
                task_solution.duration,
                task_colors[task_name],
                text,
            )
    elif render_mode == "Resource":
        for i, resource_name in enumerate(solution.resources):
            ress = solution.resources[resource_name]
            # each interval from the busy_intervals list is rendered as a bar
            for task_name, start, end in ress.assignments:
                hatch = None
                bar_color = task_colors[task_name]
                text_to_display = task_name
                draw_broken_barh_with_text(
                    start, end - start, bar_color, text_to_display, hatch
                )
    # display indicator values in the legend area
    if solution.indicators and show_indicators:
        for indicator_name in solution.indicators:
            gantt_chart.plot(
                [],
                [],
                " ",
                label=f"{indicator_name}: {solution.indicators[indicator_name]}",
            )
        gantt_chart.legend(title="Indicators", title_fontsize="large", framealpha=0.5)

    # buffers, show a plot for all buffers
    if solution.buffers:
        buffer_chart.set_title("Buffers")
        buffer_chart.set_xlim(0, solution.horizon)
        buffer_chart.set_xticks(range(solution.horizon + 1))
        buffer_chart.grid(True)
        buffer_chart.set_xlabel("Timeline")
        buffer_chart.set_ylabel("Buffer level")

        for buffer in solution.buffers.values():
            all_x = [0] + buffer.level_change_times + [solution.horizon]
            # build data from the level and level_change_times
            i = 0
            X = []
            Y = []
            for y in buffer.level:
                X += [all_x[i], all_x[i + 1], np.nan]
                Y += [y, y, np.nan]
                i += 1

            plt.plot(X, Y, linewidth=2, label=f"{buffer.name}")
        buffer_chart.legend()
    if fig_filename is not None:
        plt.savefig(fig_filename)

    if show_plot:
        plt.show()
