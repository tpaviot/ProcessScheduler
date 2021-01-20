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

import json

from typing import Optional, Tuple

try:
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    HAVE_MATPLOTLIB = True
except ImportError:
    HAVE_MATPLOTLIB = False

class SolutionJSONEncoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__

class TaskSolution:
    """ a name, a start, a duration, an end, a list of assigned resources """
    def __init__(self, name: str):
        self.name = name
        self.type = ''  # the name of the task type
        self.start = 0
        self.end = 0
        self.duration = 0
        self.optional = False
        self.scheduled = False
        # the name of assigned resources
        self.assigned_resources = []

class ResourceSolution:
    """ a name, a list of tasks, start, end. """
    def __init__(self, name: str):
        self.name = name
        self.type = ''  # the name of the task type
        # an assignment is a list of tuples : [(Task_name, start, end), (task_2name, start2, end2) etc.]
        self.assignments = []

class SchedulingSolution:
    """ A class that represent the solution of a scheduling problem. Can be rendered
    to a matplotlib Gannt chart, or exported to json
    """
    def __init__(self, problem_name: str):
        self.problem_name = problem_name
        self.horizon = 0
        self.tasks = {} # the dict of tasks
        self.resources = {}  # the dict of all resources
        self.indicators = {}  # the dict of inicators values

    def __repr__(self):
        return self.to_string()

    def get_all_tasks_but_unavailable(self):
        """Return all tasks except those of the type UnavailebleResource."""
        tasks_to_return = {}
        for task in self.tasks:
            if not "NotAvailable" in task:
                tasks_to_return[task] = self.tasks[task]
        return tasks_to_return

    def to_string(self) -> str:
        """ displays the result as an ascii string """
        return str(self.tasks)

    def to_json_string(self) -> str:
        """ export the solution to a json string """
        d = {}
        d['horizon'] = self.horizon
        d['tasks'] = self.tasks
        d['resources'] = self.resources
        d['indicators'] = self.indicators
        return json.dumps(d, indent=4, sort_keys=True, cls=SolutionJSONEncoder)

    def add_indicator_solution(self, indicator_name: str, indicator_value: int) -> None:
        """Add indicator solution."""
        self.indicators[indicator_name] = indicator_value

    def add_task_solution(self, task_solution: TaskSolution) -> None:
        """Add task solution."""
        self.tasks[task_solution.name] = task_solution

    def add_resource_solution(self, resource_solution: ResourceSolution) -> None:
        """Add resource solution."""
        self.resources[resource_solution.name] = resource_solution

    def render_gantt_matplotlib(self,
                                fig_size:Optional[Tuple[int, int]] = (9,6),
                                show_plot: Optional[bool] = True,
                                show_indicators: Optional[bool] = True,
                                render_mode: Optional[str] = 'Resources',
                                fig_filename: Optional[str] = None) -> None:
        """ generate a gantt diagram using matplotlib.
        Inspired by
        https://www.geeksforgeeks.org/python-basic-gantt-chart-using-matplotlib/
        """
        if not self.resources:
            render_mode = 'Tasks'

        # tasks to render
        if render_mode == 'Tasks':
            tasks_to_render = self.get_all_tasks_but_unavailable()
        else:
            tasks_to_render = self.tasks

        # render mode is Resource by default, can be set to 'Task'
        if render_mode == 'Resources':
            plot_title = 'Resources schedule - %s' % self.problem_name
            plot_ylabel = 'Resources'
            plot_ticklabels = list(self.resources.keys())
            nbr_y_values = len(self.resources)
        elif render_mode == 'Tasks':
            plot_title = 'Task schedule - %s' % self.problem_name
            plot_ylabel = 'Tasks'
            plot_ticklabels = list(tasks_to_render.keys())
            nbr_y_values = len(tasks_to_render)
        else:
            raise ValueError("rendermode must be either 'Resources' or 'Tasks'")

        gantt = plt.subplots(1, 1, figsize=fig_size)[1]
        gantt.set_title(plot_title)
        gantt.set_xlim(0, self.horizon)
        gantt.set_xticks(range(self.horizon + 1))
        # Setting labels for x-axis and y-axis
        gantt.set_xlabel('Time (%i periods)' % self.horizon, fontsize=12)
        gantt.set_ylabel(plot_ylabel, fontsize=12)

        # colormap definition
        cmap = LinearSegmentedColormap.from_list('custom blue',
                                                 ['#bbccdd','#ee3300'],
                                                 N = len(self.tasks) * 2) # nbr of colors
        # defined a mapping between the tasks and the colors, so that
        # each task has the same color on both graphs
        task_colors = {}
        for i, task_name in enumerate(tasks_to_render):
            task_colors[task_name] = cmap(i)
        # the task color is defined from the task name, this way the task has
        # already the same color, even if it is defined after
        gantt.set_ylim(0, 2 * nbr_y_values)
        gantt.set_yticks(range(1, 2 * nbr_y_values, 2))
        gantt.set_yticklabels(plot_ticklabels)
        # in Resources mode, create one line per resource on the y axis
        gantt.grid(axis='x', linestyle='dashed')

        def draw_broken_barh_with_text(start, length, bar_color, text, hatch=None):
            # first compute the bar dimension
            if length == 0:  # zero duration tasks, to be visible
                bar_dimension = (start - 0.05, 0.1)
            else:
                bar_dimension = (start, length)
            gantt.broken_barh([bar_dimension], (i * 2, 2),
                              edgecolor='black', linewidth=1,
                              facecolors=bar_color, hatch=hatch)
            gantt.text(x=start + length / 2, y=i * 2 + 1,
                       s=text, ha='center', va='center', color='black')

        # in Tasks mode, create one line per task on the y axis
        if render_mode == 'Tasks':
            for i, task_name in enumerate(tasks_to_render):
                # build the bar text string
                task_solution = self.tasks[task_name]
                if task_solution.assigned_resources:
                    text = ','.join(task_solution.assigned_resources)
                else:
                    text = r'($\emptyset$)'
                draw_broken_barh_with_text(task_solution.start,
                                           task_solution.duration,
                                           task_colors[task_name],
                                           text)
        elif render_mode == 'Resources':
            for i, resource_name in enumerate(self.resources):
                ress = self.resources[resource_name]
                # each interval from the busy_intervals list is rendered as a bar
                for task_name, start, end in ress.assignments:
                    # unavailabilities are rendered with a grey dashed bar
                    if 'NotAvailable' in task_name:
                        hatch = '//'
                        bar_color = 'white'
                        text_to_display =''
                    else:
                        hatch = None
                        bar_color = task_colors[task_name]
                        text_to_display = task_name
                    draw_broken_barh_with_text(start,
                                               end - start,
                                               bar_color,
                                               text_to_display,
                                               hatch)
        # display indicator values in the legend area
        if self.indicators and show_indicators:
            for indicator_name in self.indicators:
                gantt.plot([], [], ' ', label="%s: %i" % (indicator_name,
                                                          self.indicators[indicator_name]))
            gantt.legend(title='Indicators', title_fontsize='large', framealpha=0.5)

        if fig_filename is not None:
            plt.savefig(fig_filename)

        if show_plot:
            plt.show()
