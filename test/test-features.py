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

class TestFeatures(unittest.TestCase):
    def test_create_problem_with_horizon(self) -> None:
        pb = ps.SchedulingProblem('ProblemWithHorizon', horizon=10)
        self.assertIsInstance(pb, ps.SchedulingProblem)

    def test_create_problem_without_horizon(self) -> None:
        pb = ps.SchedulingProblem('ProblemWithoutHorizon')
        self.assertIsInstance(pb, ps.SchedulingProblem)

    #
    # Tasks
    #
    def test_create_task_zero_duration(self) -> None:
        task = ps.ZeroDurationTask('zdt')
        self.assertIsInstance(task, ps.ZeroDurationTask)

    def test_create_task_fixed_duration(self) -> None:
        task = ps.FixedDurationTask('fdt', 1)
        self.assertIsInstance(task, ps.FixedDurationTask)

    def test_create_task_variable_duration(self) -> None:
        task = ps.VariableDurationTask('vdt')
        self.assertIsInstance(task, ps.VariableDurationTask)

    #
    # Workers
    #
    def test_create_worker(self) -> None:
        worker = ps.Worker('wkr')
        self.assertIsInstance(worker, ps.Worker)

    def test_create_alternative_workers(self) -> None:
        worker_1 = ps.Worker('wkr_1')
        worker_2 = ps.Worker('wkr_2')
        worker_3 = ps.Worker('wkr_3')
        single_alternative_workers = ps.AlternativeWorkers([worker_1,
                                                            worker_2], 1)
        self.assertIsInstance(single_alternative_workers,
                              ps.AlternativeWorkers)
        double_alternative_workers = ps.AlternativeWorkers([worker_1,
                                                            worker_2,
                                                            worker_3], 2)
        self.assertIsInstance(double_alternative_workers,
                              ps.AlternativeWorkers)

    def test_eq_overloading(self) -> None:
        task_1 = ps.ZeroDurationTask('task1')
        task_2 = ps.ZeroDurationTask('task2')
        self.assertEqual(task_1, task_1)
        self.assertNotEqual(task_1, task_2)

    #
    # Single task constraints
    #
    def test_create_task_start_at(self) -> None:
        task = ps.FixedDurationTask('task', 2)
        c = ps.TaskStartAt(task, 1)
        self.assertIsInstance(c, ps.TaskStartAt)
        self.assertFalse(task.lower_bounded)
        self.assertFalse(task.upper_bounded)
        self.assertEqual(c.value, 1)

    def test_create_task_start_after_strict(self) -> None:
        task = ps.FixedDurationTask('task', 2)
        c = ps.TaskStartAfterStrict(task, 3)
        self.assertIsInstance(c, ps.TaskStartAfterStrict)
        self.assertTrue(task.lower_bounded)
        self.assertFalse(task.upper_bounded)
        self.assertEqual(c.value, 3)

    def test_create_task_start_after_lax(self) -> None:
        task = ps.FixedDurationTask('task', 2)
        c = ps.TaskStartAfterLax(task, 3)
        self.assertIsInstance(c, ps.TaskStartAfterLax)
        self.assertTrue(task.lower_bounded)
        self.assertFalse(task.upper_bounded)
        self.assertEqual(c.value, 3)

    def test_create_task_end_at(self) -> None:
        task = ps.FixedDurationTask('task', 2)
        c = ps.TaskEndAt(task, 3)
        self.assertIsInstance(c, ps.TaskEndAt)
        self.assertFalse(task.lower_bounded)
        self.assertTrue(task.upper_bounded)
        self.assertEqual(c.value, 3)

    def test_create_task_before_strict(self) -> None:
        task = ps.FixedDurationTask('task', 2)
        c = ps.TaskEndBeforeStrict(task, 3)
        self.assertIsInstance(c, ps.TaskEndBeforeStrict)
        self.assertFalse(task.lower_bounded)
        self.assertTrue(task.upper_bounded)
        self.assertEqual(c.value, 3)

    def test_create_task_before_lax(self) -> None:
        task = ps.FixedDurationTask('task', 2)
        c = ps.TaskEndBeforeLax(task, 3)
        self.assertIsInstance(c, ps.TaskEndBeforeLax)
        self.assertFalse(task.lower_bounded)
        self.assertTrue(task.upper_bounded)
        self.assertEqual(c.value, 3)

    #
    # Two tasks constraints
    #
    def test_tasks_dont_overlap(self) -> None:
        t_1 = ps.FixedDurationTask('t1', duration=2)
        t_2 = ps.FixedDurationTask('t2', duration=3)
        c_2 = ps.TasksDontOverlap(t_1, t_2)

    def test_tasks_start_sync(self) -> None:
        t_1 = ps.FixedDurationTask('t1', duration=2)
        t_2 = ps.FixedDurationTask('t2', duration=3)
        c_2 = ps.TasksStartSynced(t_1, t_2)

    def test_tasks_end_sync(self) -> None:
        t_1 = ps.FixedDurationTask('t1', duration=2)
        t_2 = ps.FixedDurationTask('t2', duration=3)
        c_2 = ps.TasksEndSynced(t_1, t_2)

    #
    # Boolean operators
    #
    def test_not(self) -> None:
        t_1 = ps.FixedDurationTask('t1', duration=2)
        c2 = ps.not_(ps.TaskStartAt(t_1, 1))
        self.assertIsInstance(c2, ps.BoolRef)

if __name__ == "__main__":
    unittest.main()
