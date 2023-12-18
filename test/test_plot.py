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

import os
from datetime import datetime, timedelta

import processscheduler as ps

import pytest


def test_gantt_matplotlib_base():
    """take the single task/single resource and display output"""
    problem = ps.SchedulingProblem(name="RenderSolution", horizon=7)
    task = ps.FixedDurationTask(name="task", duration=7)
    # problem.add_task(task)
    worker = ps.Worker(name="worker")
    # problem.add_resource(worker)
    task.add_required_resource(worker)
    solver = ps.SchedulingSolver(problem=problem)
    solution = solver.solve()
    assert solution

    # display solution, using both ascii or matplotlib
    ps.render_gantt_matplotlib(
        solution,
        render_mode="Resource",
        show_plot=False,
        fig_filename="test_render_resources_matplotlib.svg",
    )
    ps.render_gantt_matplotlib(
        solution,
        render_mode="Task",
        show_plot=False,
        fig_filename="test_render_tasks_matplotlib.svg",
    )
    assert os.path.isfile("test_render_resources_matplotlib.svg")
    assert os.path.isfile("test_render_tasks_matplotlib.svg")


def test_gantt_matplotlib_indicator():
    problem = ps.SchedulingProblem(name="GanttIndicator", horizon=10)

    t_1 = ps.FixedDurationTask(name="T1", duration=5)
    ps.FixedDurationTask(name="T2", duration=5)  # task with no resource
    worker_1 = ps.Worker(name="Worker1", cost=ps.LinearFunction(slope=23, intercept=3))
    t_1.add_required_resource(worker_1)

    ff = ps.IndicatorResourceCost(list_of_resources=[worker_1])

    solution = ps.SchedulingSolver(problem=problem).solve()

    assert solution
    # display solution, using both ascii or matplotlib
    ps.render_gantt_matplotlib(solution, render_mode="Resource", show_plot=False)


def test_gantt_matplotlib_navaible_resource():
    pb = ps.SchedulingProblem(name="GanttResourceUnavailable", horizon=10)
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    worker_1 = ps.Worker(name="Worker1")
    task_1.add_required_resource(worker_1)
    ps.ResourceUnavailable(resource=worker_1, list_of_time_intervals=[(1, 3)])

    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    ps.render_gantt_matplotlib(solution, render_mode="Resource", show_plot=False)


def test_gantt_matplotlib_no_resource():
    pb = ps.SchedulingProblem(name="GanttNoResource", horizon=10)
    ps.FixedDurationTask(name="task1", duration=3)
    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    ps.render_gantt_matplotlib(solution, render_mode="Resource", show_plot=False)


def test_gantt_matplotlib_resource_unavailable() -> None:
    pb = ps.SchedulingProblem(name="GanttResourceUnavailable1", horizon=10)
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    worker_1 = ps.Worker(name="Worker1")
    task_1.add_required_resource(worker_1)
    ps.ResourceUnavailable(resource=worker_1, list_of_time_intervals=[(1, 3)])

    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    ps.render_gantt_matplotlib(solution, show_plot=False)


def test_gantt_matplotlib_zero_duration_task():
    pb = ps.SchedulingProblem(name="GanttZeroDuration", horizon=10)
    ps.ZeroDurationTask(name="task1")
    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    ps.render_gantt_matplotlib(solution, show_plot=False)


def test_gantt_matplotlib_real_date_1():
    pb = ps.SchedulingProblem(
        name="GanttMatplotLibRealDate1",
        horizon=10,
        start_time=datetime.now(),
        delta_time=timedelta(minutes=15),
    )
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    worker_1 = ps.Worker(name="Worker1")
    task_1.add_required_resource(worker_1)
    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    ps.render_gantt_matplotlib(solution, render_mode="Task", show_plot=False)
    ps.render_gantt_matplotlib(solution, render_mode="Resource", show_plot=False)


def test_gantt_matplotlib_real_date_no_start_time():
    pb = ps.SchedulingProblem(
        name="GanttMatplotLibRealDateNoStartTime",
        horizon=10,
        delta_time=timedelta(hours=2),
    )
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    worker_1 = ps.Worker(name="Worker1")
    task_1.add_required_resource(worker_1)
    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    ps.render_gantt_matplotlib(solution, render_mode="Task", show_plot=False)
    ps.render_gantt_matplotlib(solution, render_mode="Resource", show_plot=False)


def test_gantt_matplotlib_wrong_render_mode():
    pb = ps.SchedulingProblem(name="GanttWrongRenderMode", horizon=10)
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    worker_1 = ps.Worker(name="Worker1")
    task_1.add_required_resource(worker_1)
    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    with pytest.raises(ValueError):
        ps.render_gantt_matplotlib(solution, render_mode="foo", show_plot=False)


def test_gantt_plotly_base():
    """take the single task/single resource and display output"""
    problem = ps.SchedulingProblem(name="RenderSolutionPlotly", horizon=7)
    task = ps.FixedDurationTask(name="task", duration=7)
    # problem.add_task(task)
    worker = ps.Worker(name="worker")
    # problem.add_resource(worker)
    task.add_required_resource(worker)
    solver = ps.SchedulingSolver(problem=problem)
    solution = solver.solve()
    assert solution

    # display solution, using both ascii or matplotlib
    ps.render_gantt_plotly(
        solution,
        render_mode="Resource",
        show_plot=False,
        sort="Resource",
        fig_filename="test_render_resources_plotly.svg",
    )
    ps.render_gantt_plotly(
        solution,
        render_mode="Task",
        show_plot=False,
        sort="Task",
        fig_filename="test_render_tasks_plotly.svg",
    )
    ps.render_gantt_plotly(
        solution,
        render_mode="Resource",
        show_plot=False,
        sort="Start",
        html_filename="test_render_resources_plotly.html",
    )
    ps.render_gantt_plotly(
        solution,
        render_mode="Task",
        show_plot=False,
        sort="Finish",
        html_filename="test_render_tasks_plotly.html",
    )
    assert os.path.isfile("test_render_resources_plotly.svg")
    assert os.path.isfile("test_render_tasks_plotly.svg")
    assert os.path.isfile("test_render_resources_plotly.html")
    assert os.path.isfile("test_render_tasks_plotly.html")


def test_gantt_plotly_with_indicators_figsize():
    problem = ps.SchedulingProblem(name="GanttIndicator", horizon=10)

    t_1 = ps.FixedDurationTask(name="T1", duration=5)
    ps.FixedDurationTask(name="T2", duration=5)  # task with no resource
    worker_1 = ps.Worker(name="Worker1", cost=ps.ConstantFunction(value=74))
    t_1.add_required_resource(worker_1)

    ps.IndicatorResourceCost(list_of_resources=[worker_1])

    solution = ps.SchedulingSolver(problem=problem).solve()

    assert solution
    # display solution, using both ascii or matplotlib
    ps.render_gantt_plotly(
        solution, render_mode="Resource", show_plot=False, fig_size=(400, 300)
    )


def test_gantt_plotly_raise_wrong_type():
    problem = ps.SchedulingProblem(name="GanttIndicator", horizon=10)

    t_1 = ps.FixedDurationTask(name="T1", duration=5)
    ps.FixedDurationTask(name="T2", duration=5)  # task with no resource
    worker_1 = ps.Worker(name="Worker1")
    t_1.add_required_resource(worker_1)

    solution = ps.SchedulingSolver(problem=problem).solve()

    assert solution
    # display solution, using both ascii or matplotlib
    with pytest.raises(ValueError):
        ps.render_gantt_plotly(solution, render_mode="foo")


def test_load_unload_feed_buffers_1() -> None:
    # one task that consumes and feed two different buffers
    pb = ps.SchedulingProblem(name="LoadUnloadBuffer1")

    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    buffer_1 = ps.NonConcurrentBuffer(name="Buffer1", initial_level=10)
    buffer_2 = ps.NonConcurrentBuffer(name="Buffer2", initial_level=0)

    ps.TaskStartAt(task=task_1, value=5)
    ps.TaskUnloadBuffer(task=task_1, buffer=buffer_1, quantity=3)
    ps.TaskLoadBuffer(task=task_1, buffer=buffer_2, quantity=2)

    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.buffers[buffer_1.name].state == [10, 7]
    assert solution.buffers[buffer_1.name].state_change_times == [5]
    assert solution.buffers[buffer_2.name].state == [0, 2]
    assert solution.buffers[buffer_2.name].state_change_times == [8]

    # plot buffers
    ps.render_gantt_matplotlib(solution, show_plot=False)
