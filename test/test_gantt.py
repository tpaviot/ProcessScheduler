#Copyright 2020 Thomas Paviot (tpaviot@gmail.com)
#
#Licensed to the Apache Software Foundation (ASF) under one
#or more contributor license agreements.  See the NOTICE file
#distributed with this work for additional information
#regarding copyright ownership.  The ASF licenses this file
#to you under the Apache License, Version 2.0 (the
#"License"); you may not use this file except in compliance
#with the License.  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing,
#software distributed under the License is distributed on an
#"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#KIND, either express or implied.  See the License for the
#specific language governing permissions and limitations
#under the License.

import os
import unittest

import processscheduler as ps

class TestGantt(unittest.TestCase):
    def test_gantt_base(self):
        """ take the single task/single resource and display output """
        problem = ps.SchedulingProblem('RenderSolution', horizon=7)
        task = ps.FixedDurationTask('task', duration=7)
        #problem.add_task(task)
        worker = ps.Worker('worker')
        #problem.add_resource(worker)
        task.add_required_resource(worker)
        solver = ps.SchedulingSolver(problem)
        solution = solver.solve()
        self.assertTrue(solution)

        # display solution, using both ascii or matplotlib
        solution.render_gantt_matplotlib(render_mode='Resources',
                                        show_plot=False,
                                        fig_filename='test_render_resources.svg')
        solution.render_gantt_matplotlib(render_mode='Tasks',
                                        show_plot=False,
                                        fig_filename='test_render_tasks.svg')
        self.assertTrue(os.path.isfile('test_render_resources.svg'))
        self.assertTrue(os.path.isfile('test_render_tasks.svg'))


    def test_gantt_indicator(self):
        problem = ps.SchedulingProblem('GanttIndicator', horizon = 10)

        t_1 = ps.FixedDurationTask('T1', duration=5)
        ps.FixedDurationTask('T2', duration=5)  # task with no resource
        worker_1 = ps.Worker('Worker1')
        t_1.add_required_resource(worker_1)

        problem.add_indicator_resource_utilization(worker_1)

        solution = ps.SchedulingSolver(problem).solve()

        self.assertTrue(solution)
        # display solution, using both ascii or matplotlib
        solution.render_gantt_matplotlib(render_mode='Resources',
                                         show_plot=False)

    def test_gantt_unavaible_resource(self):
        pb = ps.SchedulingProblem('GanttResourceUnavailable', horizon=10)
        task_1 = ps.FixedDurationTask('task1', duration = 3)
        worker_1 = ps.Worker('Worker1')
        task_1.add_required_resource(worker_1)
        c1 = ps.ResourceUnavailable(worker_1, [(1, 3)])
        pb.add_constraint(c1)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        solution.render_gantt_matplotlib(render_mode='Resources',
                                         show_plot=False)

    def test_gantt_no_resource(self):
        pb = ps.SchedulingProblem('GanttNoResource', horizon=10)
        task_1 = ps.FixedDurationTask('task1', duration = 3)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        solution.render_gantt_matplotlib(show_plot=False)

    def test_gantt_wrong_render_mode(self):
        pb = ps.SchedulingProblem('GanttWrongRenderMode', horizon=10)
        task_1 = ps.FixedDurationTask('task1', duration = 3)
        worker_1 = ps.Worker('Worker1')
        task_1.add_required_resource(worker_1)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        with self.assertRaises(ValueError):
            solution.render_gantt_matplotlib(render_mode='foo', show_plot=False)

if __name__ == "__main__":
    unittest.main()
