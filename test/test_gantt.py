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
import unittest
from datetime import datetime, timedelta

import processscheduler as ps


class TestGantt(unittest.TestCase):
    def test_gantt_matplotlib_base(self):
        """take the single task/single resource and display output"""
        problem = ps.SchedulingProblem(name="RenderSolution", horizon=7)
        task = ps.FixedDurationTask(name="task", duration=7)
        # problem.add_task(task)
        worker = ps.Worker(name="worker")
        # problem.add_resource(worker)
        task.add_required_resource(worker)
        solver = ps.SchedulingSolver(problem=problem)
        solution = solver.solve()
        self.assertTrue(solution)

        # display solution, using both ascii or matplotlib
        solution.render_gantt_matplotlib(
            render_mode="Resource",
            show_plot=False,
            fig_filename="test_render_resources_matplotlib.svg",
        )
        solution.render_gantt_matplotlib(
            render_mode="Task",
            show_plot=False,
            fig_filename="test_render_tasks_matplotlib.svg",
        )
        self.assertTrue(os.path.isfile("test_render_resources_matplotlib.svg"))
        self.assertTrue(os.path.isfile("test_render_tasks_matplotlib.svg"))

    def test_gantt_matplotlib_indicator(self):
        problem = ps.SchedulingProblem(name="GanttIndicator", horizon=10)

        t_1 = ps.FixedDurationTask(name="T1", duration=5)
        ps.FixedDurationTask(name="T2", duration=5)  # task with no resource
        worker_1 = ps.Worker(name="Worker1")
        t_1.add_required_resource(worker_1)

        problem.add_indicator_resource_utilization(worker_1)

        solution = ps.SchedulingSolver(problem=problem).solve()

        self.assertTrue(solution)
        # display solution, using both ascii or matplotlib
        solution.render_gantt_matplotlib(render_mode="Resource", show_plot=False)

    def test_gantt_matplotlib_navaible_resource(self):
        pb = ps.SchedulingProblem(name="GanttResourceUnavailable", horizon=10)
        task_1 = ps.FixedDurationTask(name="task1", duration=3)
        worker_1 = ps.Worker(name="Worker1")
        task_1.add_required_resource(worker_1)
        ps.ResourceUnavailable(resource=worker_1, list_of_time_intervals=[(1, 3)])

        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)
        solution.render_gantt_matplotlib(render_mode="Resource", show_plot=False)

    def test_gantt_matplotlib_no_resource(self):
        pb = ps.SchedulingProblem(name="GanttNoResource", horizon=10)
        ps.FixedDurationTask(name="task1", duration=3)
        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)
        solution.render_gantt_matplotlib(render_mode="Resource", show_plot=False)

    def test_gantt_matplotlib_resource_unavailable(self) -> None:
        pb = ps.SchedulingProblem(name="GanttResourceUnavailable1", horizon=10)
        task_1 = ps.FixedDurationTask(name="task1", duration=3)
        worker_1 = ps.Worker(name="Worker1")
        task_1.add_required_resource(worker_1)
        ps.ResourceUnavailable(resource=worker_1, list_of_time_intervals=[(1, 3)])

        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)
        solution.render_gantt_matplotlib(show_plot=False)

    def test_gantt_matplotlib_zero_duration_task(self):
        pb = ps.SchedulingProblem(name="GanttZeroDuration", horizon=10)
        ps.ZeroDurationTask(name="task1")
        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)
        solution.render_gantt_matplotlib(show_plot=False)

    def test_gantt_matplotlib_real_date_1(self):
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
        self.assertTrue(solution)
        solution.render_gantt_matplotlib(render_mode="Task", show_plot=False)
        solution.render_gantt_matplotlib(render_mode="Resource", show_plot=False)

    def test_gantt_matplotlib_real_date_no_start_time(self):
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
        self.assertTrue(solution)
        solution.render_gantt_matplotlib(render_mode="Task", show_plot=False)
        solution.render_gantt_matplotlib(render_mode="Resource", show_plot=False)

    def test_gantt_matplotlib_wrong_render_mode(self):
        pb = ps.SchedulingProblem(name="GanttWrongRenderMode", horizon=10)
        task_1 = ps.FixedDurationTask(name="task1", duration=3)
        worker_1 = ps.Worker(name="Worker1")
        task_1.add_required_resource(worker_1)
        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)
        with self.assertRaises(ValueError):
            solution.render_gantt_matplotlib(render_mode="foo", show_plot=False)

    def test_gantt_plotly_base(self):
        """take the single task/single resource and display output"""
        problem = ps.SchedulingProblem(name="RenderSolutionPlotly", horizon=7)
        task = ps.FixedDurationTask(name="task", duration=7)
        # problem.add_task(task)
        worker = ps.Worker(name="worker")
        # problem.add_resource(worker)
        task.add_required_resource(worker)
        solver = ps.SchedulingSolver(problem=problem)
        solution = solver.solve()
        self.assertTrue(solution)

        # display solution, using both ascii or matplotlib
        solution.render_gantt_plotly(
            render_mode="Resource",
            show_plot=False,
            sort="Resource",
            fig_filename="test_render_resources_plotly.svg",
        )
        solution.render_gantt_plotly(
            render_mode="Task",
            show_plot=False,
            sort="Task",
            fig_filename="test_render_tasks_plotly.svg",
        )
        solution.render_gantt_plotly(
            render_mode="Resource",
            show_plot=False,
            sort="Start",
            html_filename="test_render_resources_plotly.html",
        )
        solution.render_gantt_plotly(
            render_mode="Task",
            show_plot=False,
            sort="Finish",
            html_filename="test_render_tasks_plotly.html",
        )
        self.assertTrue(os.path.isfile("test_render_resources_plotly.svg"))
        self.assertTrue(os.path.isfile("test_render_tasks_plotly.svg"))
        self.assertTrue(os.path.isfile("test_render_resources_plotly.html"))
        self.assertTrue(os.path.isfile("test_render_tasks_plotly.html"))

    def test_gantt_plotly_with_indicators_figsize(self):
        problem = ps.SchedulingProblem(name="GanttIndicator", horizon=10)

        t_1 = ps.FixedDurationTask(name="T1", duration=5)
        ps.FixedDurationTask(name="T2", duration=5)  # task with no resource
        worker_1 = ps.Worker(name="Worker1")
        t_1.add_required_resource(worker_1)

        problem.add_indicator_resource_utilization(worker_1)

        solution = ps.SchedulingSolver(problem=problem).solve()

        self.assertTrue(solution)
        # display solution, using both ascii or matplotlib
        solution.render_gantt_plotly(
            render_mode="Resource", show_plot=False, fig_size=(400, 300)
        )

    def test_gantt_plotly_raise_wrong_type(self):
        problem = ps.SchedulingProblem(name="GanttIndicator", horizon=10)

        t_1 = ps.FixedDurationTask(name="T1", duration=5)
        ps.FixedDurationTask(name="T2", duration=5)  # task with no resource
        worker_1 = ps.Worker(name="Worker1")
        t_1.add_required_resource(worker_1)

        solution = ps.SchedulingSolver(problem=problem).solve()

        self.assertTrue(solution)
        # display solution, using both ascii or matplotlib
        with self.assertRaises(ValueError):
            solution.render_gantt_plotly(render_mode="foo")


if __name__ == "__main__":
    unittest.main()
