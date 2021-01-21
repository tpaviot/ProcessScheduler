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

class TestOptionalTask(unittest.TestCase):
    """For each of these tests, we consider two tests: whether the optional task
    is scheduled or not.
    """
    def test_optional_task_start_at_1(self) -> None:
        """Task can be scheduled."""
        pb = ps.SchedulingProblem('OptionalTaskStartAt1', horizon=6)
        task_1 = ps.FixedDurationTask('task1', duration = 3, optional=True)
        pb.add_constraint(ps.TaskStartAt(task_1, 1))

        # Force schedule, otherwise by default it is not scheduled
        pb.add_constraint(task_1.scheduled == True)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertEqual(solution.tasks[task_1.name].start, 1)
        self.assertEqual(solution.tasks[task_1.name].end, 4)

    def test_optional_task_start_at_2(self) -> None:
        """Task cannot be scheduled."""
        pb = ps.SchedulingProblem('OptionalTaskStartAt2', horizon=2)
        task_1 = ps.FixedDurationTask('task1', duration = 3, optional=True)
        pb.add_constraint(ps.TaskStartAt(task_1, 1))

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertFalse(solution.tasks[task_1.name].scheduled)

    def test_optional_task_end_at_1(self) -> None:
        """Task can be scheduled."""
        pb = ps.SchedulingProblem('OptionalTaskEndAt1', horizon=6)
        task_1 = ps.FixedDurationTask('task1', duration = 3, optional=True)
        pb.add_constraint(ps.TaskEndAt(task_1, 4))

        # Force schedule, otherwise by default it is not scheduled
        pb.add_constraint(task_1.scheduled == True)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertEqual(solution.tasks[task_1.name].start, 1)
        self.assertEqual(solution.tasks[task_1.name].end, 4)

    def test_optional_task_end_at_2(self) -> None:
        """Task cannot be scheduled."""
        pb = ps.SchedulingProblem('OptionalTaskEndAt2', horizon=2)
        task_1 = ps.FixedDurationTask('task1', duration = 3, optional=True)
        pb.add_constraint(ps.TaskEndAt(task_1, 4))

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertFalse(solution.tasks[task_1.name].scheduled)

    def test_optional_tasks_start_sync_1(self) -> None:
        """Tasks can be scheduled."""
        pb = ps.SchedulingProblem('OptionalTasksStartSynced1', horizon=6)
        task_1 = ps.FixedDurationTask('task1', duration = 3)  # mandatory
        task_2 = ps.FixedDurationTask('task2', duration = 4, optional=True) # optional

        pb.add_constraint(ps.TaskStartAt(task_1, 2))
        pb.add_constraint(ps.TasksStartSynced(task_1, task_2))

        # Force schedule, otherwise by default it is not scheduled
        pb.add_constraint(task_2.scheduled == True)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertTrue(solution.tasks[task_2.name].scheduled)
        self.assertEqual(solution.tasks[task_1.name].start, 2)
        self.assertEqual(solution.tasks[task_1.name].end, 5)
        self.assertEqual(solution.tasks[task_2.name].start, 2)
        self.assertEqual(solution.tasks[task_2.name].end, 6)

    def test_optional_tasks_start_sync_2(self) -> None:
        """Task 2 cannot be scheduled."""
        pb = ps.SchedulingProblem('OptionalTasksStartSynced2', horizon=5)
        task_1 = ps.FixedDurationTask('task1', duration = 3)  # mandatory
        task_2 = ps.FixedDurationTask('task2', duration = 4, optional=True) # optional

        pb.add_constraint(ps.TaskStartAt(task_1, 2))
        pb.add_constraint(ps.TasksStartSynced(task_1, task_2))

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertFalse(solution.tasks[task_2.name].scheduled)
        self.assertEqual(solution.tasks[task_1.name].start, 2)
        self.assertEqual(solution.tasks[task_1.name].end, 5)

    def test_optional_tasks_end_sync_1(self) -> None:
        """Tasks can be scheduled."""
        pb = ps.SchedulingProblem('OptionalTasksEndSynced1', horizon=6)
        task_1 = ps.FixedDurationTask('task1', duration = 3)  # mandatory
        task_2 = ps.FixedDurationTask('task2', duration = 4, optional=True) # optional

        pb.add_constraint(ps.TaskEndAt(task_1, 6))
        pb.add_constraint(ps.TasksEndSynced(task_1, task_2))

        # Force schedule, otherwise by default it is not scheduled
        pb.add_constraint(task_2.scheduled == True)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertTrue(solution.tasks[task_2.name].scheduled)
        self.assertEqual(solution.tasks[task_1.name].start, 3)
        self.assertEqual(solution.tasks[task_1.name].end, 6)
        self.assertEqual(solution.tasks[task_2.name].start, 2)
        self.assertEqual(solution.tasks[task_2.name].end, 6)

    def test_optional_tasks_end_sync_2(self) -> None:
        """Task 2 cannot be scheduled."""
        pb = ps.SchedulingProblem('OptionalTasksEndSynced2', horizon=3)
        task_1 = ps.FixedDurationTask('task1', duration = 3)  # mandatory
        task_2 = ps.FixedDurationTask('task2', duration = 4, optional=True) # optional

        pb.add_constraint(ps.TaskEndAt(task_1, 3))
        pb.add_constraint(ps.TasksStartSynced(task_1, task_2))

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertFalse(solution.tasks[task_2.name].scheduled)
        self.assertEqual(solution.tasks[task_1.name].start, 0)
        self.assertEqual(solution.tasks[task_1.name].end, 3)

    def test_optional_tasks_dont_overlap_1(self) -> None:
        """Tasks can be scheduled."""
        pb = ps.SchedulingProblem('OptionalTasksDontOverlap1', horizon=7)
        task_1 = ps.FixedDurationTask('task1', duration = 3)  # mandatory
        task_2 = ps.FixedDurationTask('task2', duration = 4, optional=True) # optional

        pb.add_constraint(ps.TaskStartAt(task_1, 0))
        pb.add_constraint(ps.TasksDontOverlap(task_1, task_2))

        # Force schedule, otherwise by default it is not scheduled
        pb.add_constraint(task_2.scheduled == True)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertTrue(solution.tasks[task_2.name].scheduled)
        self.assertEqual(solution.tasks[task_1.name].start, 0)
        self.assertEqual(solution.tasks[task_1.name].end, 3)
        self.assertEqual(solution.tasks[task_2.name].start, 3)
        self.assertEqual(solution.tasks[task_2.name].end, 7)

    def test_optional_tasks_dont_overlap_2(self) -> None:
        """Task 2 cannot be scheduled."""
        pb = ps.SchedulingProblem('OptionalTasksDontOverlap2', horizon=3)
        task_1 = ps.FixedDurationTask('task1', duration = 3)  # mandatory
        task_2 = ps.FixedDurationTask('task2', duration = 4, optional=True) # optional

        pb.add_constraint(ps.TaskStartAt(task_1, 0))
        pb.add_constraint(ps.TasksDontOverlap(task_1, task_2))

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertFalse(solution.tasks[task_2.name].scheduled)
        self.assertEqual(solution.tasks[task_1.name].start, 0)
        self.assertEqual(solution.tasks[task_1.name].end, 3)

    def test_optional_tasks_precedence_1(self) -> None:
        """Tasks can be scheduled."""
        pb = ps.SchedulingProblem('OptionalTasksPrecedence1', horizon=9)
        task_1 = ps.FixedDurationTask('task1', duration = 3)  # mandatory
        task_2 = ps.FixedDurationTask('task2', duration = 4, optional=True) # optional

        pb.add_constraint(ps.TaskStartAt(task_1, 0))
        pb.add_constraint(ps.TaskPrecedence(task_1, task_2, offset=2))

        # Force schedule, otherwise by default it is not scheduled
        pb.add_constraint(task_2.scheduled == True)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertTrue(solution.tasks[task_2.name].scheduled)
        self.assertEqual(solution.tasks[task_1.name].start, 0)
        self.assertEqual(solution.tasks[task_1.name].end, 3)
        self.assertEqual(solution.tasks[task_2.name].start, 5)
        self.assertEqual(solution.tasks[task_2.name].end, 9)

    def test_optional_tasks_precedence_2(self) -> None:
        """Task 2 cannot be scheduled."""
        pb = ps.SchedulingProblem('OptionalTasksPrecedence2', horizon=8)
        task_1 = ps.FixedDurationTask('task1', duration = 3)  # mandatory
        task_2 = ps.FixedDurationTask('task2', duration = 4, optional=True) # optional

        pb.add_constraint(ps.TaskStartAt(task_1, 0))
        pb.add_constraint(ps.TaskPrecedence(task_1, task_2, offset=2))

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertFalse(solution.tasks[task_2.name].scheduled)
        self.assertEqual(solution.tasks[task_1.name].start, 0)
        self.assertEqual(solution.tasks[task_1.name].end, 3)

    def test_optional_condition_1(self) -> None:
        """A task scheduled only if the horizon is > 10."""
        pb = ps.SchedulingProblem('OptionalCondition1')
        task_1 = ps.FixedDurationTask('task1', duration = 13)  # mandatory
        task_2 = ps.FixedDurationTask('task2', duration = 4, optional=True) # optional

        # Force schedule, otherwise by default it is not scheduled
        pb.add_constraint(task_2.scheduled == True)

        cond = ps.OptionalTaskConditionSchedule(task_2, pb.horizon > 10)
        pb.add_constraint(cond)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertTrue(solution.tasks[task_2.name].scheduled)

    def test_optional_condition_2(self) -> None:
        """A task scheduled only if the horizon is > 10."""
        pb = ps.SchedulingProblem('OptionalCondition2', horizon=9)
        task_1 = ps.FixedDurationTask('task1', duration = 9)  # mandatory
        task_2 = ps.FixedDurationTask('task2', duration = 4, optional=True) # optional

        cond = ps.OptionalTaskConditionSchedule(task_2, pb.horizon > 10)
        pb.add_constraint(cond)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertFalse(solution.tasks[task_2.name].scheduled)

    def test_optional_task_dependency_1(self) -> None:
        """task_2 is scheduled, because task_1 is."""
        pb = ps.SchedulingProblem('OptionalDependency1')
        task_1 = ps.FixedDurationTask('task1', duration = 9)  # mandatory
        task_2 = ps.FixedDurationTask('task2', duration = 4, optional=True) # optional

        cond = ps.OptionalTasksDependency(task_1, task_2)
        pb.add_constraint(cond)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertTrue(solution.tasks[task_2.name].scheduled)

    def test_optional_task_dependency_2(self) -> None:
        """task_3 is not scheduled, because task_2 should not."""
        pb = ps.SchedulingProblem('OptionalDependency2', horizon=9)
        task_1 = ps.FixedDurationTask('task1', duration = 5)  # mandatory
        task_2 = ps.FixedDurationTask('task2', duration = 4, optional=True) # optional
        task_3 = ps.FixedDurationTask('task3', duration = 1, optional=True) # optional

        cond = ps.OptionalTaskConditionSchedule(task_2, pb.horizon > 10)
        pb.add_constraint(cond)

        dep = ps.OptionalTasksDependency(task_2, task_3)
        pb.add_constraint(dep)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertFalse(solution.tasks[task_2.name].scheduled)
        self.assertFalse(solution.tasks[task_3.name].scheduled)

    def test_optional_task_single_worker_1(self) -> None:
        pb = ps.SchedulingProblem('OptionalTaskSingleWorker1', horizon=6)
        task_1 = ps.FixedDurationTask('task1', duration = 3, optional=True)
        pb.add_constraint(ps.TaskStartAt(task_1, 1))
        worker_1 = ps.Worker('Worker1')
        task_1.add_required_resource(worker_1)
        # Force schedule, otherwise by default it is not scheduled
        pb.add_constraint(task_1.scheduled == True)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)

    def test_optional_task_singleworker_2(self) -> None:
        pb = ps.SchedulingProblem('OptionalTaskSingleWorker2', horizon=6)
        task_1 = ps.FixedDurationTask('task1', duration = 3, optional=True)
        pb.add_constraint(ps.TaskStartAt(task_1, 1))
        worker_1 = ps.Worker('Worker1')
        task_1.add_required_resource(worker_1)
        # Force schedule to False
        pb.add_constraint(task_1.scheduled == False)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertFalse(solution.tasks[task_1.name].scheduled)

    def test_optional_task_two_workers_1(self) -> None:
        pb = ps.SchedulingProblem('OptionalTaskTwoWorkers1', horizon=6)
        task_1 = ps.FixedDurationTask('task1', duration = 3, optional=True)
        pb.add_constraint(ps.TaskStartAt(task_1, 1))
        worker_1 = ps.Worker('Worker1')
        worker_2 = ps.Worker('Worker2')
        task_1.add_required_resources([worker_1, worker_2])
        # Force schedule, otherwise by default it is not scheduled
        pb.add_constraint(task_1.scheduled == True)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)

    def test_optional_task_two_workers_2(self) -> None:
        pb = ps.SchedulingProblem('OptionalTaskTwoWorkers2')
        task_1 = ps.FixedDurationTask('task1', duration = 3, optional=True)

        worker_1 = ps.Worker('Worker1')
        worker_2 = ps.Worker('Worker2')
        task_1.add_required_resources([worker_1, worker_2])
        # Force schedule, otherwise by default it is not scheduled
        pb.add_constraint(task_1.scheduled == False)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertFalse(solution.tasks[task_1.name].scheduled)

    def test_optional_task_select_workers_1(self) -> None:
        pb = ps.SchedulingProblem('OptionalTaskSelectWorkers1')
        task_1 = ps.FixedDurationTask('task1', duration = 3, optional=True)
        pb.add_constraint(ps.TaskStartAt(task_1, 1))
        worker_1 = ps.Worker('Worker1')
        worker_2 = ps.Worker('Worker2')
        task_1.add_required_resource(ps.SelectWorkers([worker_1, worker_2], 1))
        # Force schedule, otherwise by default it is not scheduled
        pb.add_constraint(task_1.scheduled == True)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertEqual(len(solution.tasks[task_1.name].assigned_resources), 1)

    def test_optional_task_select_workers_2(self) -> None:
        pb = ps.SchedulingProblem('OptionalTaskSelectWorkers2')
        task_1 = ps.FixedDurationTask('task1', duration = 3, optional=True)
        pb.add_constraint(ps.TaskStartAt(task_1, 1))
        worker_1 = ps.Worker('Worker1')
        worker_2 = ps.Worker('Worker2')
        task_1.add_required_resource(ps.SelectWorkers([worker_1, worker_2], 1))
        # Force schedule False
        pb.add_constraint(task_1.scheduled == False)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertFalse(solution.tasks[task_1.name].scheduled)
        self.assertEqual(len(solution.tasks[task_1.name].assigned_resources), 0)


if __name__ == "__main__":
    unittest.main()
