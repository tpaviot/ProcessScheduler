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

import unittest

import processscheduler as ps

class TestSolver(unittest.TestCase):
    def test_schedule_single_fixed_duration_task(self) -> None:
        pb = ps.SchedulingProblem('SingleFixedDurationTaskScheduling', horizon=2)
        task = ps.FixedDurationTask('task', duration=2)
        pb.add_task(task)
        solver = ps.SchedulingSolver(pb)
        success = solver.solve()
        self.assertTrue(success)
        # task should have been scheduled with start at 0
        # and end at 2
        self.assertEqual(task.scheduled_start, 0)
        self.assertEqual(task.scheduled_end, 2)

    def test_schedule_single_variable_duration_task(self) -> None:
        pb = ps.SchedulingProblem('SingleVariableDurationTaskScheduling')
        task = ps.VariableDurationTask('task')
        pb.add_task(task)

        # add two constraints to set start and end
        pb.add_constraint(ps.TaskStartAt(task, 1))
        pb.add_constraint(ps.TaskEndAt(task, 4))

        solver = ps.SchedulingSolver(pb, verbosity=True)
        success = solver.solve()
        self.assertTrue(success)
        # task should have been scheduled with start at 0
        # and end at 2
        self.assertEqual(task.scheduled_start, 1)
        self.assertEqual(task.scheduled_duration, 3)
        self.assertEqual(task.scheduled_end, 4)

    def test_schedule_two_fixed_duration_task_with_precedence(self) -> None:
        pb = ps.SchedulingProblem('TwoFixedDurationTasksWithPrecedence', horizon=5)
        task_1 = ps.FixedDurationTask('task1', duration=2)
        task_2 = ps.FixedDurationTask('task2', duration=3)
        pb.add_tasks([task_1, task_2])

        # add two constraints to set start and end
        pb.add_constraint(ps.TaskStartAt(task_1, 0))
        pb.add_constraint(ps.TaskPrecedence(task_before=task_1,
                                            task_after=task_2))

        solver = ps.SchedulingSolver(pb)
        success = solver.solve()
        self.assertTrue(success)
        self.assertEqual(task_1.scheduled_start, 0)
        self.assertEqual(task_1.scheduled_end, 2)
        self.assertEqual(task_2.scheduled_start, 2)
        self.assertEqual(task_2.scheduled_end, 5)

    def test_schedule_single_task_single_resource(self) -> None:
        pb = ps.SchedulingProblem('SingleTaskSingleResource', horizon=7)

        task = ps.FixedDurationTask('task', duration=7)
        pb.add_task(task)

        worker = ps.Worker('worker')
        pb.add_resource(worker)

        task.add_required_resource(worker)

        solver = ps.SchedulingSolver(pb)
        success = solver.solve()
        self.assertTrue(success)

        # task should have been scheduled with start at 0
        # and end at 2
        self.assertEqual(task.scheduled_start, 0)
        self.assertEqual(task.scheduled_end, 7)
        self.assertEqual(task.assigned_resources, [worker])

    def test_schedule_two_tasks_two_alternative_workers(self) -> None:
        pb = ps.SchedulingProblem('TwoTasksTwoAlternativeWorkers', horizon=4)
        # two tasks
        task_1 = ps.FixedDurationTask('task1', duration=3)
        task_2 = ps.FixedDurationTask('task2', duration=2)
        pb.add_tasks([task_1, task_2])
        # two workers
        worker_1 = ps.Worker('worker1')
        worker_2 = ps.Worker('worker2')
        pb.add_resources([worker_1, worker_2])

        task_1.add_required_resource(ps.AlternativeWorkers([worker_1, worker_2], 1))
        task_2.add_required_resource(ps.AlternativeWorkers([worker_1, worker_2], 1))

        solver = ps.SchedulingSolver(pb)
        success = solver.solve()
        self.assertTrue(success)
        # each task should have one worker assigned
        self.assertEqual(len(task_1.assigned_resources), 1)
        self.assertEqual(len(task_2.assigned_resources), 1)
        self.assertFalse(task_1.assigned_resources == task_2.assigned_resources)

    def test_unsat_1(self):
        pb = ps.SchedulingProblem('Unsat1')

        task = ps.FixedDurationTask('task', duration=7)
        pb.add_task(task)

        # add two constraints to set start and end
        # impossible to satisfy both
        pb.add_constraint(ps.TaskStartAt(task, 1))
        pb.add_constraint(ps.TaskEndAt(task, 4))

        solver = ps.SchedulingSolver(pb)
        success = solver.solve()
        self.assertFalse(success)

    def test_render_solution(self):
        """ take the single task/single resource and display output """
        pb = ps.SchedulingProblem('RenderSolution', horizon=7)
        task = ps.FixedDurationTask('task', duration=7)
        pb.add_task(task)
        worker = ps.Worker('worker')
        pb.add_resource(worker)
        task.add_required_resource(worker)
        solver = ps.SchedulingSolver(pb)
        success = solver.solve()
        self.assertTrue(success)
        # display solution, using both ascii or matplotlib
        pb.print_solution()
        pb.render_gantt_matplotlib(render_mode='Resources', show_plot=False)
        pb.render_gantt_matplotlib(render_mode='Tasks', show_plot=False)


if __name__ == "__main__":
    unittest.main()
