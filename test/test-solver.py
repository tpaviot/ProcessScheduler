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

        pb.print_solution()
        # task should have been scheduled with start at 0
        # and end at 2
        self.assertEqual(task.scheduled_start, 0)
        self.assertEqual(task.scheduled_end, 7)
        self.assertEqual(task.assigned_resources, [worker])


if __name__ == "__main__":
    unittest.main()
