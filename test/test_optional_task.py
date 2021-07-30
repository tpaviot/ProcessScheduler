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

import unittest

import processscheduler as ps


class TestOptionalTask(unittest.TestCase):
    """For each of these tests, we consider two tests: whether the optional task
    is scheduled or not.
    """

    def test_optional_task_start_at_1(self) -> None:
        """Task can be scheduled."""
        pb = ps.SchedulingProblem("OptionalTaskStartAt1", horizon=6)
        task_1 = ps.FixedDurationTask("task1", duration=3, optional=True)
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
        pb = ps.SchedulingProblem("OptionalTaskStartAt2", horizon=2)
        task_1 = ps.FixedDurationTask("task1", duration=3, optional=True)
        pb.add_constraint(ps.TaskStartAt(task_1, 1))

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertFalse(solution.tasks[task_1.name].scheduled)

    def test_optional_task_end_at_1(self) -> None:
        """Task can be scheduled."""
        pb = ps.SchedulingProblem("OptionalTaskEndAt1", horizon=6)
        task_1 = ps.FixedDurationTask("task1", duration=3, optional=True)
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
        pb = ps.SchedulingProblem("OptionalTaskEndAt2", horizon=2)
        task_1 = ps.FixedDurationTask("task1", duration=3, optional=True)
        pb.add_constraint(ps.TaskEndAt(task_1, 4))

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertFalse(solution.tasks[task_1.name].scheduled)

    def test_optional_tasks_start_sync_1(self) -> None:
        """Tasks can be scheduled."""
        pb = ps.SchedulingProblem("OptionalTasksStartSynced1", horizon=6)
        task_1 = ps.FixedDurationTask("task1", duration=3)  # mandatory
        task_2 = ps.FixedDurationTask("task2", duration=4, optional=True)  # optional

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
        pb = ps.SchedulingProblem("OptionalTasksStartSynced2", horizon=5)
        task_1 = ps.FixedDurationTask("task1", duration=3)  # mandatory
        task_2 = ps.FixedDurationTask("task2", duration=4, optional=True)  # optional

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
        pb = ps.SchedulingProblem("OptionalTasksEndSynced1", horizon=6)
        task_1 = ps.FixedDurationTask("task1", duration=3)  # mandatory
        task_2 = ps.FixedDurationTask("task2", duration=4, optional=True)  # optional

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
        pb = ps.SchedulingProblem("OptionalTasksEndSynced2", horizon=3)
        task_1 = ps.FixedDurationTask("task1", duration=3)  # mandatory
        task_2 = ps.FixedDurationTask("task2", duration=4, optional=True)  # optional

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
        pb = ps.SchedulingProblem("OptionalTasksDontOverlap1", horizon=7)
        task_1 = ps.FixedDurationTask("task1", duration=3)  # mandatory
        task_2 = ps.FixedDurationTask("task2", duration=4, optional=True)  # optional

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
        pb = ps.SchedulingProblem("OptionalTasksDontOverlap2", horizon=3)
        task_1 = ps.FixedDurationTask("task1", duration=3)  # mandatory
        task_2 = ps.FixedDurationTask("task2", duration=4, optional=True)  # optional

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
        pb = ps.SchedulingProblem("OptionalTasksPrecedence1", horizon=9)
        task_1 = ps.FixedDurationTask("task1", duration=3)  # mandatory
        task_2 = ps.FixedDurationTask("task2", duration=4, optional=True)  # optional

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
        pb = ps.SchedulingProblem("OptionalTasksPrecedence2", horizon=8)
        task_1 = ps.FixedDurationTask("task1", duration=3)  # mandatory
        task_2 = ps.FixedDurationTask("task2", duration=4, optional=True)  # optional

        pb.add_constraint(ps.TaskStartAt(task_1, 0))
        pb.add_constraint(ps.TaskPrecedence(task_1, task_2, offset=2))

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertFalse(solution.tasks[task_2.name].scheduled)
        self.assertEqual(solution.tasks[task_1.name].start, 0)
        self.assertEqual(solution.tasks[task_1.name].end, 3)

    def test_optional_tasks_start_after_strict_start_after_lax(self) -> None:
        pb = ps.SchedulingProblem("OptionalTasksStartAfter", horizon=8)
        task_1 = ps.FixedDurationTask("task1", duration=3)  # mandatory
        task_2 = ps.FixedDurationTask("task2", duration=4, optional=True)  # optional

        # force task_2 to be scheduled
        pb.add_constraint(task_2.scheduled == True)

        pb.add_constraint(ps.TaskStartAfterStrict(task_2, 1))
        pb.add_constraint(ps.TaskStartAfterLax(task_2, 4))

        solver = ps.SchedulingSolver(pb, debug=True)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertTrue(solution.tasks[task_2.name].scheduled)
        self.assertEqual(solution.tasks[task_2.name].start, 4)
        self.assertEqual(solution.tasks[task_2.name].end, 8)

    def test_optional_tasks_end_before_strict_end_before_lax(self) -> None:
        pb = ps.SchedulingProblem("OptionalTasksEndBefore", horizon=8)
        task_1 = ps.FixedDurationTask("task1", duration=3)  # mandatory
        task_2 = ps.FixedDurationTask("task2", duration=4, optional=True)  # optional

        # force task_2 to be scheduled
        pb.add_constraint(task_2.scheduled == True)

        pb.add_constraint(ps.TaskEndBeforeStrict(task_2, 7))
        pb.add_constraint(ps.TaskEndBeforeLax(task_2, 4))

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertTrue(solution.tasks[task_2.name].scheduled)
        self.assertEqual(solution.tasks[task_2.name].start, 0)
        self.assertEqual(solution.tasks[task_2.name].end, 4)

    def test_optional_condition_1(self) -> None:
        """A task scheduled only if the horizon is > 10."""
        pb = ps.SchedulingProblem("OptionalCondition1")
        task_1 = ps.FixedDurationTask("task1", duration=13)  # mandatory
        task_2 = ps.FixedDurationTask("task2", duration=4, optional=True)  # optional

        cond = ps.OptionalTaskConditionSchedule(task_2, pb.horizon > 10)
        pb.add_constraint(cond)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertTrue(solution.tasks[task_2.name].scheduled)

    def test_optional_condition_2(self) -> None:
        """A task scheduled only if the horizon is > 10."""
        pb = ps.SchedulingProblem("OptionalCondition2", horizon=9)
        task_1 = ps.FixedDurationTask("task1", duration=9)  # mandatory
        task_2 = ps.FixedDurationTask("task2", duration=4, optional=True)  # optional

        cond = ps.OptionalTaskConditionSchedule(task_2, pb.horizon > 10)
        pb.add_constraint(cond)

        solver = ps.SchedulingSolver(pb, random_values=True)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertFalse(solution.tasks[task_2.name].scheduled)

    def test_optional_task_dependency_1(self) -> None:
        """task_2 is scheduled, because task_1 is."""
        pb = ps.SchedulingProblem("OptionalDependency1")
        task_1 = ps.FixedDurationTask("task1", duration=9)  # mandatory
        task_2 = ps.FixedDurationTask("task2", duration=4, optional=True)  # optional

        cond = ps.OptionalTasksDependency(task_1, task_2)
        pb.add_constraint(cond)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertTrue(solution.tasks[task_2.name].scheduled)

    def test_optional_task_dependency_2(self) -> None:
        """task_3 is not scheduled, because task_2 should not."""
        pb = ps.SchedulingProblem("OptionalDependency2", horizon=9)
        task_1 = ps.FixedDurationTask("task1", duration=5)  # mandatory
        task_2 = ps.FixedDurationTask("task2", duration=4, optional=True)  # optional
        task_3 = ps.FixedDurationTask("task3", duration=1, optional=True)  # optional

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

    def test_optional_task_dependency_3(self) -> None:
        """Type checking."""
        pb = ps.SchedulingProblem("OptionalDependency3", horizon=9)
        task_1 = ps.FixedDurationTask("task1", duration=5)  # mandatory
        task_2 = ps.FixedDurationTask("task2", duration=4)  # mandatory
        task_3 = ps.FixedDurationTask("task3", duration=1)  # mandatory

        with self.assertRaises(TypeError):
            ps.OptionalTaskConditionSchedule(task_1, pb.horizon > 10)

        with self.assertRaises(TypeError):
            ps.OptionalTasksDependency(task_2, task_3)

    def test_optional_task_single_worker_1(self) -> None:
        pb = ps.SchedulingProblem("OptionalTaskSingleWorker1", horizon=6)
        task_1 = ps.FixedDurationTask("task1", duration=3, optional=True)
        pb.add_constraint(ps.TaskStartAt(task_1, 1))
        worker_1 = ps.Worker("Worker1")
        task_1.add_required_resource(worker_1)
        # Force schedule, otherwise by default it is not scheduled
        pb.add_constraint(task_1.scheduled == True)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)

    def test_optional_task_singleworker_2(self) -> None:
        pb = ps.SchedulingProblem("OptionalTaskSingleWorker2", horizon=6)
        task_1 = ps.FixedDurationTask("task1", duration=3, optional=True)
        pb.add_constraint(ps.TaskStartAt(task_1, 1))
        worker_1 = ps.Worker("Worker1")
        task_1.add_required_resource(worker_1)
        # Force schedule to False
        pb.add_constraint(task_1.scheduled == False)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertFalse(solution.tasks[task_1.name].scheduled)

    def test_optional_task_two_workers_1(self) -> None:
        pb = ps.SchedulingProblem("OptionalTaskTwoWorkers1", horizon=6)
        task_1 = ps.FixedDurationTask("task1", duration=3, optional=True)
        pb.add_constraint(ps.TaskStartAt(task_1, 1))
        worker_1 = ps.Worker("Worker1")
        worker_2 = ps.Worker("Worker2")
        task_1.add_required_resources([worker_1, worker_2])
        # Force schedule, otherwise by default it is not scheduled
        pb.add_constraint(task_1.scheduled == True)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)

    def test_optional_task_two_workers_2(self) -> None:
        pb = ps.SchedulingProblem("OptionalTaskTwoWorkers2")
        task_1 = ps.FixedDurationTask("task1", duration=3, optional=True)

        worker_1 = ps.Worker("Worker1")
        worker_2 = ps.Worker("Worker2")
        task_1.add_required_resources([worker_1, worker_2])
        # Force schedule, otherwise by default it is not scheduled
        pb.add_constraint(task_1.scheduled == False)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertFalse(solution.tasks[task_1.name].scheduled)

    def test_optional_task_select_workers_1(self) -> None:
        pb = ps.SchedulingProblem("OptionalTaskSelectWorkers1")
        task_1 = ps.FixedDurationTask("task1", duration=3, optional=True)
        pb.add_constraint(ps.TaskStartAt(task_1, 1))
        worker_1 = ps.Worker("Worker1")
        worker_2 = ps.Worker("Worker2")
        task_1.add_required_resource(ps.SelectWorkers([worker_1, worker_2], 1))
        # Force schedule, otherwise by default it is not scheduled
        pb.add_constraint(task_1.scheduled == True)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertEqual(len(solution.tasks[task_1.name].assigned_resources), 1)

    def test_optional_task_select_workers_2(self) -> None:
        pb = ps.SchedulingProblem("OptionalTaskSelectWorkers2")
        task_1 = ps.FixedDurationTask("task1", duration=3, optional=True)
        pb.add_constraint(ps.TaskStartAt(task_1, 1))
        worker_1 = ps.Worker("Worker1")
        worker_2 = ps.Worker("Worker2")
        task_1.add_required_resource(ps.SelectWorkers([worker_1, worker_2], 1))
        # Force schedule False
        pb.add_constraint(task_1.scheduled == False)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertFalse(solution.tasks[task_1.name].scheduled)
        self.assertEqual(len(solution.tasks[task_1.name].assigned_resources), 0)

    def test_force_schedule_optional_tasks(self) -> None:
        """task_3 is not scheduled, because task_2 should not."""
        pb = ps.SchedulingProblem("ForceScheduleOptionalTasks", horizon=9)
        task_1 = ps.VariableDurationTask("task1", optional=True)
        task_2 = ps.FixedDurationTask("task2", duration=4, optional=True)
        task_3 = ps.FixedDurationTask("task3", duration=1, optional=True)

        cond = ps.ForceScheduleNOptionalTasks([task_1, task_2, task_3], 1)
        pb.add_constraint(cond)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)

        results = [
            solution.tasks[task_1.name].scheduled,
            solution.tasks[task_2.name].scheduled,
            solution.tasks[task_3.name].scheduled,
        ]

        self.assertEqual(results.count(True), 1)

    def test_force_schedule_optional_tasks_2(self) -> None:
        """Just change the number of tasks to be scheduled."""
        pb = ps.SchedulingProblem("ForceScheduleOptionalTasks2", horizon=14)
        task_1 = ps.VariableDurationTask("task1", optional=True)
        task_2 = ps.FixedDurationTask("task2", duration=7, optional=True)
        task_3 = ps.FixedDurationTask("task3", duration=2, optional=True)

        cond = ps.ForceScheduleNOptionalTasks([task_1, task_2, task_3], 2)
        pb.add_constraint(cond)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)

        results = [
            solution.tasks[task_1.name].scheduled,
            solution.tasks[task_2.name].scheduled,
            solution.tasks[task_3.name].scheduled,
        ]

        self.assertEqual(results.count(True), 2)

    def test_force_schedule_optional_tasks_3(self) -> None:
        """Check an error is raised if ever one of the task is not optional."""
        pb = ps.SchedulingProblem("ForceScheduleOptionalTasks3", horizon=14)
        task_1 = ps.VariableDurationTask("task1")  # this one is not optional
        task_2 = ps.FixedDurationTask("task2", duration=7, optional=True)

        with self.assertRaises(TypeError):
            cond = ps.ForceScheduleNOptionalTasks([task_1, task_2], 2)
            pb.add_constraint(cond)

    def test_get_scheduled_tasks(self) -> None:
        # task_1 cannot be scheduled, only tasks 2 and 3 can be
        pb = ps.SchedulingProblem("GetScheduledTasks", horizon=14)
        task_1 = ps.FixedDurationTask("task1", duration=15, optional=True)
        task_2 = ps.FixedDurationTask("task2", duration=7, optional=True)
        task_3 = ps.FixedDurationTask("task3", duration=2, optional=True)

        cond = ps.ForceScheduleNOptionalTasks([task_1, task_2, task_3], 2)
        pb.add_constraint(cond)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()

        self.assertTrue(solution)

        scheduled_tasks_dictionary = solution.get_scheduled_tasks()

        self.assertEqual(len(scheduled_tasks_dictionary), 2)
        self.assertTrue("task2" in scheduled_tasks_dictionary)
        self.assertTrue("task3" in scheduled_tasks_dictionary)


if __name__ == "__main__":
    unittest.main()
