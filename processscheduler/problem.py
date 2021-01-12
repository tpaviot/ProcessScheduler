""" ProcessScheduler, Copyright 2020 Thomas Paviot (tpaviot@gmail.com)

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.
"""

from typing import Dict, List, Optional, Tuple, Union
import warnings

from z3 import Bool, BoolRef, Int, ModelRef, Or, Sum

from processscheduler.base import _NamedUIDObject, is_strict_positive_integer
from processscheduler.objective import Indicator, MaximizeObjective, MinimizeObjective, BuiltinIndicator
from processscheduler.resource import _Resource
from processscheduler.task import Task
#from processscheduler.task_constraint import _Constraint
import processscheduler.context as ps_context

class SchedulingProblem(_NamedUIDObject):
    """A scheduling problem

    :param name: the problem name, a string type
    :param horizon: an optional integer, the final instant of the timeline
    """
    def __init__(self, name: str, horizon: Optional[int] = None):
        super().__init__(name)
        # the problem context, where all will be stored
        # at creation
        self.context = ps_context.SchedulingContext()
        # set this context as global
        ps_context.main_context = self.context
        # the list of tasks to be scheduled in this scenario
        # self._tasks = {} # type: Dict[str, Task]
        # # the list of resources available in this scenario
        # self.resources = {} # type: Dict[str, _Resource]
        # # the constraints are defined in the scenario
        # self._constraints = [] # type: List[BoolRef]
        # # list of define indicators
        # self.indicators = [] # type: List[Indicator]
        # self.objectives = [] # type: List[Union[Indicator, ArithRef]]
        # the solution
        self._solution = None # type: ModelRef
        # define the horizon variable
        self.horizon = Int('horizon')
        self.fixed_horizon = False  # set to True is horizon is fixed
        if is_strict_positive_integer(horizon):  # fixed_horizon
            self.context.add_constraint(self.horizon == horizon)
            self.fixed_horizon = True
        elif horizon is not None:
            raise TypeError('horizon must either be a strict positive integer or None')
        # the scheduled_horizon is set to 0 by default, it will be
        # set by the solver
        self.scheduled_horizon = 0

    def set_solution(self, solution: ModelRef) -> None:
        """ for each task, set the resource, start and length values """
        self._solution = solution

        # set tasks start, end and duration solution
        for task in self.context.tasks:
            task.scheduled_start = solution[task.start].as_long()
            task.scheduled_end = solution[task.end].as_long()
            task.scheduled_duration = solution[task.duration].as_long()

        # traverse all tasks to perform resources assignment
        # all required workers should be assigned
        for task in self.context.tasks:
            # parse resources
            for req_res in task.required_resources:
                # by default, resource_should_be_assigned is set to True
                # if will be set to False if the resource is an alternative worker
                resource_should_be_assigned = True
                # among those workers, some of them
                # are busy "in the past", that is to say they
                # should not be assigned to the related task
                # for each interval
                lower_bound, _ = req_res.busy_intervals[task]
                if solution[lower_bound].as_long() < 0:
                    # should not be scheduled
                    resource_should_be_assigned = False
                # add this resource to assigned resources, anytime
                if resource_should_be_assigned and req_res not in task.assigned_resources:
                    task.assigned_resources.append(req_res)

        # set the horizon solution
        self.scheduled_horizon = solution[self.horizon].as_long()

        # set the indicators values
        for indicator in self.context.indicators:
            indicator.scheduled_value = solution[indicator.indicator_variable].as_long()

    # def add_indicator(self, indicator: Indicator) -> bool:
    #     """ add an indicatr to the problem """
    #     if not isinstance(indicator, Indicator):
    #         raise TypeError('indicator must be a Indicator object')
    #     if indicator not in self.indicators:
    #         self.indicators.append(indicator)
    #     else:
    #         warnings.warn('indicator %s already part of the problem' % indicator)
    #         return False
    #     return True

    # def add_task(self, task: Task) -> bool:
    #     """ add a single task to the problem """
    #     if not isinstance(task, Task):
    #         raise TypeError('task must be a Task object')
    #     task_name = task.name
    #     if task_name not in self._tasks:
    #         self._tasks[task_name] = task
    #     else:
    #         warnings.warn('task %s already part of the problem' % task)
    #         return False
    #     return True

    # def add_tasks(self, list_of_tasks: List[Task]) -> None:
    #     """ adds tasks to the problem """
    #     for task in list_of_tasks:
    #         self.add_task(task)

    # def add_resource(self, resource: _Resource) -> bool:
    #     """ add a single resource to the problem """
    #     # Prevent an AlternativeWorker to be added
    #     if not isinstance(resource, _Resource):
    #         raise TypeError('resource must be a _Resource object')
    #     resource_name = resource.name
    #     if resource_name not in self.resources:
    #         self.resources[resource_name] = resource
    #     else:
    #         warnings.warn('Resource %s already part of the problem' % resource)
    #         return False
    #     return True

    # def add_resources(self, list_of_resources: List[_Resource]) -> None:
    #     """ add resources to the problem """
    #     for resource in list_of_resources:
    #         self.add_resource(resource)

    # def get_tasks(self) -> ValuesView[Task]:
    #     """ return the list of tasks """
    #     return self._tasks.values()

    # def get_resources(self) -> ValuesView[_Resource]:
    #     """ return the list of tasks """
    #     return self.resources.values()

    def add_constraint(self, constraint):
        self.context.add_constraint(constraint)
    # def add_constraint(self, constraint: Union[_Constraint, BoolRef]) -> None:
    #     """ add a constraint to the problem """
    #     if isinstance(constraint, _Constraint):
    #         self._constraints.append(constraint.get_assertions())
    #     elif isinstance(constraint, BoolRef):
    #         self._constraints.append(constraint)
    #     else:
    #         raise TypeError("You must provide either a _Constraint or BoolRef instance.")

    def add_constraints(self, list_of_constraints) -> None:
        """ adds constraints to the problem """
        self.context.add_constraints(list_of_constraints)

    # def add_objective(self, objective: Objective) -> None:
    #     self.objectives.append(objective)

    def add_objective_makespan(self) -> bool:
        """ makespan objective
        """
        if self.fixed_horizon:
            warnings.warn('Horizon constrained to be fixed, no horizon optimization possible.')
            return False
        MinimizeObjective('MakeSpan', self.horizon)
        return True

    def add_objective_start_latest(self) -> None:
        """ maximize the minimum start time, i.e. all the tasks
        are scheduled as late as possible """
        mini = Int('SmallestStartTime')
        a = BuiltinIndicator('GreatestStartTime')
        a.add_assertion(Or([mini == task.start for task in self.context.tasks]))
        for tsk in self.context.tasks:
            a.add_assertion(mini <= tsk.start)
        a.indicator_variable=mini
        MaximizeObjective('SmallestStartTime', mini)

    def add_objective_start_earliest(self) -> None:
        """ minimize the greatest start time, i.e. tasks are schedules
        as early as possible """
        maxi = Int('GreatestStartTime')
        a = BuiltinIndicator('GreatestStartTime')
        a.add_assertion(Or([maxi == task.start for task in self.context.tasks]))
        for tsk in self.context.tasks:
            a.add_assertion(maxi >= tsk.start)
        a.indicator_variable=maxi
        MinimizeObjective('GreatestStartTimeObjective', maxi)

    def add_objective_flowtime(self) -> None:
        """ the flowtime is the sum of all ends, minimize. Be carful that
        it is contradictory with makespan """
        flow_time_expr = Sum([task.end for task in self.context.tasks])
        smallest_start_time_indicator = Indicator('FlowTime', flow_time_expr)
        MinimizeObjective('FlowTimeObjective', smallest_start_time_indicator)

    def print_solution(self) -> None:
        """ print solution to console """
        print("Problem %s solution:" % self.name)
        print("\thorizon: %i" % self.scheduled_horizon)
        if self._solution is not None:
            for task in self.context.tasks:
                ress = task.assigned_resources
                print("\t", task.name, ":", ress, end=";")
                print('start:', task.scheduled_start, end=";")
                print('end:', task.scheduled_end)
        else:
            warnings.warn("No solution to display.")

    def render_gantt_matplotlib(self,
                                fig_size:Optional[Tuple[int, int]] = (9,6),
                                show_plot: Optional[Bool] = True,
                                show_indicators: Optional[Bool] = True,
                                render_mode: Optional[str] = 'Resources',
                                fig_filename: Optional[str] = None) -> None:
        """ generate a gantt diagram using matplotlib.
        Inspired by
        https://www.geeksforgeeks.org/python-basic-gantt-chart-using-matplotlib/
        """
        if self._solution is None:
            warnings.warn("No solution to plot.")
            return None
        try:
            import matplotlib.pyplot as plt
            from matplotlib.colors import LinearSegmentedColormap
        except ImportError:
            warnings.warn('matplotlib not installed')
            return None

        if not self.context.resources:
            render_mode = 'Tasks'

        # render mode is Resource by default, can be set to 'Task'
        if render_mode == 'Resources':
            plot_title = 'Resources schedule - %s' % self.name
            plot_ylabel = 'Resources'
            plot_ticklabels = map(str, self.context.resources)
            nbr_y_values = len(self.context.resources)
        elif render_mode == 'Tasks':
            plot_title = 'Task schedule - %s' % self.name
            plot_ylabel = 'Tasks'
            plot_ticklabels = map(str, self.context.tasks)
            nbr_y_values = len(self.context.tasks)
        else:
            raise ValueError("rendermode must be either 'Resources' or 'Tasks'")

        gantt = plt.subplots(1, 1, figsize=fig_size)[1]
        gantt.set_title(plot_title)
        gantt.set_xlim(0, self.scheduled_horizon)
        gantt.set_xticks(range(self.scheduled_horizon + 1))
        # Setting labels for x-axis and y-axis
        gantt.set_xlabel('Time (%i periods)' % self.scheduled_horizon, fontsize=12)
        gantt.set_ylabel(plot_ylabel, fontsize=12)

        # colormap definition
        cmap = LinearSegmentedColormap.from_list('custom blue',
                                                 ['#bbccdd','#ee3300'],
                                                 N = len(self.context.tasks * 2)) # nbr of colors
        # defined a mapping between the tasks and the colors, so that
        # each task has the same color on both graphs
        task_colors = {}
        for i, task in enumerate(self.context.tasks):
            task_colors[task.name] = cmap(i)
        # the task color is defined from the task name, this way the task has
        # already the same color, even if it is defined after
        gantt.set_ylim(0, 2 * nbr_y_values)
        gantt.set_yticks(range(1, 2 * nbr_y_values, 2))
        gantt.set_yticklabels(plot_ticklabels)
        # in Resources mode, create one line per resource on the y axis
        gantt.grid(axis='x', linestyle='dashed')

        def draw_broken_barh_with_text(start, length, bar_color, text):
            # first compute the bar dimension
            if length == 0:  # zero duration tasks, to be visible
                bar_dimension = (start - 0.05, 0.1)
            else:
                bar_dimension = (start, length)
            gantt.broken_barh([bar_dimension], (i * 2, 2),
                              edgecolor='black', linewidth=1,
                              facecolors=bar_color)
            gantt.text(x=start + length / 2, y=i * 2 + 1,
                       s=text, ha='center', va='center', color='black')

        # in Tasks mode, create one line per task on the y axis
        if render_mode == 'Tasks':
            for i, task in enumerate(self.context.tasks):
                # build the bar text string
                text = '%s' % task
                if task.assigned_resources:
                    resources_names = ['%s' % c for c in task.assigned_resources]
                    resources_names.sort()  # alphabetical sort
                    text += '(' + ','.join(resources_names) + ')'
                else:
                    text += r'($\emptyset$)'
                draw_broken_barh_with_text(task.scheduled_start,
                                           task.scheduled_duration,
                                           task_colors[task.name],
                                           text)
        elif render_mode == 'Resources':
            for i, ress in enumerate(self.context.resources):
                #each interval from the busy_intervals list is rendered as a bar
                for task in ress.busy_intervals.keys():
                    task_name = task.name
                    st_var, end_var = ress.busy_intervals[task]
                    start = self._solution[st_var].as_long()
                    end = self._solution[end_var].as_long()
                    if start >= 0 and end >= 0:  # only assigned resource
                        draw_broken_barh_with_text(start,
                                                   end - start,
                                                   task_colors[task_name],
                                                   task_name)
        # display indicator values in the legend area
        if self.context.indicators and show_indicators:
            for indicator in self.context.indicators:
                gantt.plot([], [], ' ', label="%s: %i" % (indicator.name,
                                                          indicator.scheduled_value))
            gantt.legend(title='Indicators', title_fontsize='large')

        if fig_filename is not None:
            plt.savefig(fig_filename)

        if show_plot:
            plt.show()

        return None
