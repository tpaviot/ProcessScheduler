"""Solution definition and Gantt export."""

# Copyright (c) 2020-2021 Thomas Paviot (tpaviot@gmail.com)
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

from datetime import timedelta, datetime
from pathlib import Path
from typing import List, Optional, Tuple, Dict
import random

from pydantic import BaseModel, Field

from processscheduler.base import BaseModelWithJson
from processscheduler.problem import SchedulingProblem
from processscheduler.excel_io import export_solution_to_excel_file


class TaskSolution(BaseModelWithJson):
    """Class to represent the solution for a scheduled Task."""

    name: str
    type: str = Field(default="")
    start: int = Field(default=0)
    end: int = Field(default=0)
    duration: int = Field(default=0)

    start_time: datetime = Field(default=None)
    end_time: datetime = Field(default=None)
    duration_time: timedelta = Field(default=None)

    optional: bool = Field(default=False)
    scheduled: bool = Field(default=False)

    # the name of assigned resources
    assigned_resources: List[str] = Field(default=[])


class ResourceSolution(BaseModelWithJson):
    """Class to represent the solution for the resource assignments."""

    name: str
    type: str = Field(default="")
    # an assignment is a list of tuples : [(Task_name, start, end), (task_2name, start2, end2) etc.]
    assignments: List[Tuple[str, int, int]] = Field(default=[])


class BufferSolution(BaseModelWithJson):
    """Class to represent the solution for a Buffer."""

    name: str
    # a collection of instants where the buffer state changes
    state_change_times: List[int] = Field(default=[])
    # a collection that represents the buffer state along the
    # whole schedule. Represented a integer values
    state: List[int] = Field(default=[])


class SchedulingSolution(BaseModelWithJson):
    """A class that represent the solution of a scheduling problem. Can be rendered
    to a matplotlib Gantt chart, or exported to json
    """

    problem: SchedulingProblem
    horizon: int = Field(default=0)
    tasks: Dict[str, TaskSolution] = Field(default={})
    resources: Dict[str, ResourceSolution] = Field(default={})
    buffers: Dict[str, BufferSolution] = Field(default={})
    indicators: Dict[str, int] = Field(default={})

    def get_all_tasks_but_unavailable(self):
        """Return all tasks except those of the type UnavailabilityTask
        used to represent a ResourceUnavailable constraint."""
        return {
            task: self.tasks[task] for task in self.tasks if "NotAvailable" not in task
        }

    def get_scheduled_tasks(self):
        """Return scheduled tasks."""
        tasks_not_unavailable = self.get_all_tasks_but_unavailable()
        return {
            task: tasks_not_unavailable[task]
            for task in tasks_not_unavailable
            if tasks_not_unavailable[task].scheduled
        }

    def add_indicator_solution(self, indicator_name: str, indicator_value: int) -> None:
        """Add indicator solution."""
        self.indicators[indicator_name] = indicator_value

    def add_task_solution(self, task_solution: TaskSolution) -> None:
        """Add task solution."""
        self.tasks[task_solution.name] = task_solution

    def add_resource_solution(self, resource_solution: ResourceSolution) -> None:
        """Add resource solution."""
        self.resources[resource_solution.name] = resource_solution

    def add_buffer_solution(self, buffer_solution: BufferSolution) -> None:
        self.buffers[buffer_solution.name] = buffer_solution

    #
    # Gantt graphical rendering using plotly and matplotlib
    #
    def render_gantt_plotly(
        self,
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
        try:
            from plotly.figure_factory import create_gantt
        except ImportError as exc:
            raise ModuleNotFoundError("plotly is not installed.") from exc

        if render_mode not in ["Task", "Resource"]:
            raise ValueError("data_type must be either Task or Resource")

        # tasks to render
        if render_mode == "Task":
            tasks_to_render = self.get_all_tasks_but_unavailable()
        else:
            tasks_to_render = self.tasks

        df = []
        for task_name in tasks_to_render:
            task_solution = self.tasks[task_name]
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

        gantt_title = f"{self.problem.name} Gantt chart"
        # add indicators value to title
        if self.indicators and show_indicators:
            for indicator_name in self.indicators:
                gantt_title += f" - {indicator_name}: {self.indicators[indicator_name]}"

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
        if self.buffers:
            print("POPO il y a des buffers!!")

        if fig_filename is not None:
            fig.write_image(fig_filename)

        if html_filename is not None:
            file = Path(html_filename)
            file.write_text(fig.to_html(include_plotlyjs="cdn"), encoding="utf-8")

        if show_plot:
            fig.show()

    def render_gantt_matplotlib(
        self,
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
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            from matplotlib.colors import LinearSegmentedColormap
        except ImportError as exc:
            raise ModuleNotFoundError("matplotlib is not installed.") from exc

        if not self.resources:
            render_mode = "Task"

        if render_mode not in ["Resource", "Task"]:
            raise ValueError("render_mode must either be 'Resource' or 'Task'")

        # tasks to render
        if render_mode == "Task":
            tasks_to_render = self.get_all_tasks_but_unavailable()
        else:
            tasks_to_render = self.tasks

        # render mode is Resource by default, can be set to 'Task'
        if render_mode == "Resource":
            plot_title = f"Resources schedule - {self.problem.name}"
            plot_ylabel = "Resources"
            plot_ticklabels = list(self.resources.keys())
            nbr_y_values = len(self.resources)
        elif render_mode == "Task":
            plot_title = f"Task schedule - {self.problem.name}"
            plot_ylabel = "Tasks"
            plot_ticklabels = list(tasks_to_render.keys())
            nbr_y_values = len(tasks_to_render)

        if self.buffers:
            gantt_chart, buffer_chart = plt.subplots(2, 1, figsize=fig_size)[1]
        else:
            gantt_chart = plt.subplots(1, 1, figsize=fig_size)[1]
        gantt_chart.set_title(plot_title)

        # x axis, use real date and times if possible
        if self.problem.delta_time is not None:
            if self.problem.start_time is not None:
                # get all days
                times = [
                    self.problem.start_time + i * self.problem.delta_time
                    for i in range(self.horizon + 1)
                ]
                times_str = []
                for t in times:
                    times_str.append(t.strftime("%H:%M"))
            else:
                times_str = [
                    f"{i * self.problem.delta_time}" for i in range(self.horizon + 1)
                ]
            gantt_chart.set_xlim(0, self.horizon)
            plt.xticks(range(self.horizon + 1), times_str, rotation=60)
            plt.subplots_adjust(bottom=0.15)
            gantt_chart.set_xlabel("Time", fontsize=12)
        else:
            # otherwise use integers
            gantt_chart.set_xlim(0, self.horizon)
            gantt_chart.set_xticks(range(self.horizon + 1))
            # Setting label
            gantt_chart.set_xlabel(f"Time ({self.horizon} periods)", fontsize=12)

        gantt_chart.set_ylabel(plot_ylabel, fontsize=12)

        # colormap definition
        cmap = LinearSegmentedColormap.from_list(
            "custom blue", ["#bbccdd", "#ee3300"], N=len(self.tasks)
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
                task_solution = self.tasks[task_name]
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
            for i, resource_name in enumerate(self.resources):
                ress = self.resources[resource_name]
                # each interval from the busy_intervals list is rendered as a bar
                for task_name, start, end in ress.assignments:
                    # unavailabilities are rendered with a grey dashed bar
                    if "NotAvailable" in task_name:
                        hatch = "//"
                        bar_color = "white"
                        text_to_display = ""
                    else:
                        hatch = None
                        bar_color = task_colors[task_name]
                        text_to_display = task_name
                    draw_broken_barh_with_text(
                        start, end - start, bar_color, text_to_display, hatch
                    )
        # display indicator values in the legend area
        if self.indicators and show_indicators:
            for indicator_name in self.indicators:
                gantt_chart.plot(
                    [],
                    [],
                    " ",
                    label=f"{indicator_name}: {self.indicators[indicator_name]}",
                )
            gantt_chart.legend(
                title="Indicators", title_fontsize="large", framealpha=0.5
            )

        # buffers, show a plot for all buffers
        if self.buffers:
            buffer_chart.set_title("Buffers")
            buffer_chart.set_xlim(0, self.horizon)
            buffer_chart.set_xticks(range(self.horizon + 1))
            buffer_chart.grid(True)
            buffer_chart.set_xlabel("Timeline")
            buffer_chart.set_ylabel("Buffer level")

            for buffer in self.buffers.values():
                all_x = [0] + buffer.state_change_times + [self.horizon]
                # build data from the state and state_change_times
                i = 0
                X = []
                Y = []
                for y in buffer.state:
                    X += [all_x[i], all_x[i + 1], np.nan]
                    Y += [y, y, np.nan]
                    i += 1

                plt.plot(X, Y, linewidth=2, label=f"{buffer.name}")
            buffer_chart.legend()
        if fig_filename is not None:
            plt.savefig(fig_filename)

        if show_plot:
            plt.show()

    #
    # File export
    #
    def export_to_excel_file(self, excel_filename, colors=False):
        return export_solution_to_excel_file(self, excel_filename, colors)
