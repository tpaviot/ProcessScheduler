# Copyright (c) 2021 Thomas Paviot (tpaviot@gmail.com)
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

from datetime import datetime

from processscheduler.problem import SchedulingProblem
from processscheduler.resource import Worker, CumulativeWorker
from processscheduler.task import ZeroDurationTask, FixedDurationTask, VariableDurationTask
from processscheduler.task_constraint import *
from processscheduler.resource_constraint import *
from processscheduler.solver import SchedulingSolver

import isodate
import ipywidgets as widgets

#
# Problem UI
#
problem_name_widget = widgets.Text(
    value='MySchedulingProblem',
    placeholder='Enter scheduling problem name',
    description='Name:',
    disabled=False
)
set_horizon_widget = widgets.Checkbox(
    value=False,
    description='Set horizon',
    disabled=False,
    indent=False,
    layout={'width': '200px'}
)
horizon_widget = widgets.IntText(
    description='Horizon:',
    disabled=True,
    layout={'width': '200px'}
)
def on_set_horizon_clicked(b):
    horizon_widget.disabled = not set_horizon_widget.value
set_horizon_widget.observe(on_set_horizon_clicked)
create_problem_button = widgets.Button(
    description='Create problem',
    disabled=False,
    button_style='',
    tooltip='Click to create a new SchedulingProblem'
)
start_time_widget = widgets.Text(
    value='',
    placeholder='Optional, you can leave blank',
    description='Start Time:',
    disabled=False
)
end_time_widget = widgets.Text(
    value='',
    placeholder='Optional, you can leave blank',
    description='End time:',
    disabled=False
)
delta_time_widget = widgets.Text(
    value='',
    placeholder='Optional, you can leave blank',
    description='Delta time:',
    disabled=False
)
problem_output = widgets.Output()
def on_create_problem_button_clicked(b) -> bool:
    global pb
    problem_name = problem_name_widget.value
    # start time
    start_time = None
    if start_time_widget.value != '':
        start_time = isodate.parse_datetime(start_time_widget.value)
        try:
            start_time = isodate.parse_datetime(start_time_widget.value)
        except ValueError:
            print('Not a valid isodate format for start_time')
            start_time = None
            return False
    # end time
    end_time = None
    if end_time_widget.value != '':
        try:
            end_time = isodate.parse_datetime(end_time_widget.value)
        except ValueError:
            print('Not a valid isodate format for end_time')
            end_time = None
            return False
    # timedelta
    delta_time = None
    if delta_time_widget.value != '':
        try:
            delta_time = isodate.parse_duration(delta_time_widget.value)
        except:
            print('Not a valid isodate format for delta_time')
            delta_time = None
            return False
    if set_horizon_widget.value:
        pb = SchedulingProblem(problem_name, horizon_widget.value)
    else:
        pb = SchedulingProblem(problem_name)
    with problem_output:
        print('Scheduling problem', problem_name, 'successfully created.')
    create_problem_button.disabled = True
    return True
create_problem_button.on_click(on_create_problem_button_clicked)
problem_ui = widgets.VBox([widgets.HBox([problem_name_widget,
                                         widgets.VBox([widgets.HBox([horizon_widget,
                                                                     set_horizon_widget,]),
                                                       start_time_widget,
                                                       delta_time_widget,
                                                       end_time_widget]),
                                        create_problem_button]),
                           problem_output])
#
# Resource UI
#
resource_types = {'Worker': Worker,
                  'CumulativeWorker': CumulativeWorker}
resource_type_widget = widgets.Dropdown(
    options=list(resource_types),
    value='Worker',
    description='Task type:',
    disabled=False,
)
resource_name_widget = widgets.Text(
    value='',
    placeholder='Enter resource name',
    description='Name:',
    disabled=False,
    layout={'width': '200px'}
)
resource_size_widget = widgets.IntText(
    value=2,
    disabled=True,
    description='Size:',
    layout={'width': '200px'}
)
def on_change_resource_type(change):
    #print("popo", change)
    if change['type'] == 'change' and change['name'] == 'value':
        new_value = '%s' % change['new']
        if new_value == 'CumulativeWorker':
            resource_size_widget.disabled = False
        elif new_value == 'Worker':
            resource_size_widget.disabled = True
resource_type_widget.observe(on_change_resource_type)

create_resource_button = widgets.Button(
    description='Create resource',
    disabled=False,
    button_style='',
    tooltip='Click to create a new Resource'
)
resource_output = widgets.Output()
def on_create_resource_button_clicked(b):
    resource_name = resource_name_widget.value
    resource_type = resource_types[resource_type_widget.value]
    if resource_type == Worker:
        new_resource = resource_type(resource_name)
    elif resource_type == CumulativeWorker:
        new_resource = resource_type(resource_name, size=resource_size_widget.value)
    # rebuild option list for the task list
    resources_list_of_tuples = []
    for resource in pb.context.resources:
        resources_list_of_tuples.append((resource.name, resource))
    resources_select_widget.options = resources_list_of_tuples
    with resource_output:
        print('Resource', new_resource.name, 'successfully created.')
create_resource_button.on_click(on_create_resource_button_clicked)
resource_ui = widgets.VBox([widgets.HBox([resource_type_widget,
                                          widgets.VBox([resource_name_widget,
                                                        resource_size_widget]),
                                          create_resource_button]),
                            resource_output])

#
# Task UI
#
task_types = {'ZeroDurationTask': ZeroDurationTask,
              'FixedDurationTask': FixedDurationTask,
              'VariableDurationTask': VariableDurationTask}
task_type_widget = widgets.Dropdown(
    options=list(task_types),
    value='FixedDurationTask',
    description='Task type:',
    disabled=False,
)
def on_change_task_type(change):
    #print("popo", change)
    if change['type'] == 'change' and change['name'] == 'value':
        new_value = '%s' % change['new']
        if new_value == 'FixedDurationTask':
            task_duration_widget.disabled = False
        elif new_value == 'ZeroDurationTask':
            task_duration_widget.disabled = True
        elif new_value == 'VariableDurationTask':
            task_duration_widget.disabled = True
task_type_widget.observe(on_change_task_type)

task_name_widget = widgets.Text(
    value='',
    placeholder='Enter task name',
    description='Task name:',
    disabled=False,
    layout={'width': '200px'}
)
is_optional_widget = widgets.Checkbox(
    value=False,
    description='Optional',
    disabled=False,
    indent=False,
    layout={'width': '200px'}
)
task_duration_widget = widgets.IntText(
    value=1,
    description='Duration:',
    disabled=False,
    layout={'width': '200px'}
)
task_priority_widget = widgets.IntText(
    value=1,
    description='Priority:',
    disabled=False,
    layout={'width': '200px'}
)
task_work_amount_widget = widgets.IntText(
    value=1,
    description='Work amounts:',
    disabled=False,
    layout={'width': '200px'}
)
create_task_button = widgets.Button(
    description='Create task',
    disabled=False,
    button_style='',
    tooltip='Click me'
)
task_output = widgets.Output()
def on_create_task_button_clicked(b):
    task_optional = is_optional_widget.value
    task_name = task_name_widget.value
    task_class = task_types[task_type_widget.value]
    if task_class == ZeroDurationTask:
        new_class = task_class(task_name)
    elif task_class == VariableDurationTask:
        new_class = task_class(task_name,
                               #priority=task_priority_widget.value,
                               #work_amount=task_work_amount_widget.value,
                               optional=task_optional)
    else:
        new_class = task_class(task_name,
                               duration=task_duration_widget.value,
                               #priority=task_priority_widget.value,
                               #work_amount=task_work_amount_widget.value,
                               optional=task_optional)
    # rebuild option list for the task list
    tasks_list_of_tuples = []
    for task in pb.context.tasks:
        tasks_list_of_tuples.append((task.name, task))
    tasks_select_widget.options = tasks_list_of_tuples
    with task_output:
        print('Task', task_name, 'successfully created.')
create_task_button.on_click(on_create_task_button_clicked)
task_ui = widgets.VBox([widgets.HBox([is_optional_widget, task_type_widget,
                                      widgets.VBox([task_name_widget,
                                      task_duration_widget,
                                      task_priority_widget,
                                      task_work_amount_widget]), create_task_button]),                       
                       task_output])
#
# Constraints UI, both tasks and resources
#
tasks_select_widget = widgets.SelectMultiple(
    description='Tasks:',
    disabled=False
)
resources_select_widget = widgets.SelectMultiple(
    description='Resources:',
    disabled=False
)
task_constraint_types = {'TaskPrecedence': TaskPrecedence,
                         'TasksStartSynced': TasksStartSynced,
                         'TasksEndSynced': TasksEndSynced,
                         'TasksDontOverlap':TasksDontOverlap,
                         'TaskStartAt': TaskStartAt,
                         'TaskStartAfterStrict': TaskStartAfterStrict,
                         'TaskStartAfterLax': TaskStartAfterLax,
                         'TaskEndAt': TaskEndAt,
                         'TaskEndBeforeStrict': TaskEndBeforeStrict,
                         'TaskEndBeforeLax': TaskEndBeforeLax,
                         'OptionalTaskConditionSchedule': OptionalTaskConditionSchedule,
                         'OptionalTasksDependency': OptionalTasksDependency,
                         'ForceScheduleNOptionalTasks': ForceScheduleNOptionalTasks,
                         'ScheduleNTasksInTimeIntervals': ScheduleNTasksInTimeIntervals
                         }
task_constraint_type_widget = widgets.Dropdown(options=list(task_constraint_types),
                                               description='',
                                               disabled=False)
resource_constraint_types = {'WorkLoad': WorkLoad,
                             'ResourceUnavailable': ResourceUnavailable,
                             'AllSameSelected': AllSameSelected,
                             'AllDifferentSelected':AllDifferentSelected
                             }
resource_constraint_type_widget = widgets.Dropdown(options=list(resource_constraint_types),
                                                   description='',
                                                   disabled=False)
create_task_constraint_button = widgets.Button(
    description='Create task constraint',
    disabled=False,
    button_style='',
    tooltip='Create task constraint'
)
create_resource_constraint_button = widgets.Button(
    description='Create resource constraint',
    disabled=False,
    button_style='',
    tooltip='Create resource constraint'
)
assign_all_workers_resource_button = widgets.Button(
    description='Assign workers',
    disabled=False,
    indent=True
)
assign_resource_output = widgets.Output()
def assign_all_workers_resource_button_clicked(b):
    # create the solver
    with assign_resource_output:
        if len(tasks_select_widget.value) != 1:
            print("Warning: select one and only one task.")
            return False
        selected_task = tasks_select_widget.value[0]
        if len(resources_select_widget.value) < 1:
            print("Warning: select at least 1 resources for SelectWorkers.")
            return False
        selected_resources = resources_select_widget.value
        # assign resources to task
        selected_task.add_required_resources(selected_resources)
        print("Add required resources", selected_resources, "to task", selected_task)
assign_all_workers_resource_button.on_click(assign_all_workers_resource_button_clicked)

assign_alternative_workers_resource_button = widgets.Button(
    description='Assign alt. workers',
    disabled=False,
    indent=True
)
def assign_alternative_workers_resource_button_clicked(b) -> bool:
    # create the solver
    with assign_resource_output:
        if len(tasks_select_widget.value) != 1:
            print("Warning: select one and only one task.")
            return False
        selected_task = tasks_select_widget.value[0]
        if len(resources_select_widget.value) <= 1:
            print("Warning: select at least 2 resources for SelectWorkers.")
            return False
        selected_resources = resources_select_widget.value
        # assign resources to task
        selected_task.add_required_resources(SelectWorker(list_of_workers=selected_resources,
                                                          nb_workers_to_select=1,
                                                          kind='exact'))
assign_alternative_workers_resource_button.on_click(assign_alternative_workers_resource_button_clicked)


constraint_ui = widgets.VBox([widgets.HBox([resources_select_widget, resource_constraint_type_widget,
                                            create_resource_constraint_button]),
                              widgets.HBox([assign_all_workers_resource_button,
                                            assign_alternative_workers_resource_button]),
                              widgets.HBox([tasks_select_widget, task_constraint_type_widget,
                                            create_task_constraint_button]),
                              assign_resource_output])
#
# Solver UI
#
is_debug_solver_widget = widgets.Checkbox(
    value=False,
    description='Debug',
    disabled=False,
    indent=False,
    layout={'width': '200px'}
)
is_parallel_solver_widget = widgets.Checkbox(
    value=False,
    description='Parallel',
    disabled=False,
    indent=False,
    layout={'width': '200px'}
)
max_time_widget = widgets.IntText(
    value=60,
    description='Max time (s):',
    disabled=False,
    layout={'width': '200px'}
)
priority_widget = widgets.Select(
    options=['lex', 'box', 'pareto'],
    description='Priority:',
    disabled=False,
    layout={'width': '200px'}
)
solve_button = widgets.Button(
    description='Solve',
    disabled=False)
solve_output = widgets.Output()
def on_solve_task_button_clicked(b):
    # create the solver
    solve_output.clear_output()
    with solve_output:
        solver = SchedulingSolver(pb,
                                  debug=is_debug_solver_widget.value,
                                  max_time=max_time_widget.value,
                                  optimize_priority=priority_widget.value,
                                  parallel=is_parallel_solver_widget.value)
        solution = solver.solve()
        # choose the gantt renderer
        if pb.start_time is not None and pb.delta_time is not None:
            solution.render_gantt_plotly(render_mode='Resource')
        else:
            solution.render_gantt_matplotlib(render_mode='Resource')
solve_button.on_click(on_solve_task_button_clicked)
solver_ui = widgets.VBox([widgets.HBox([max_time_widget, priority_widget,
                          widgets.VBox([is_debug_solver_widget, is_parallel_solver_widget]),
                          solve_button,]),
                          solve_output])
