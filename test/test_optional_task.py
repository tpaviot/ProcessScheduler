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
        pb = ps.SchedulingProblem(name="OptionalTaskStartAt1", horizon=6)
        task_1 = ps.FixedDurationTask(name="task1", duration=3, optional=True)
        ps.TaskStartAt(task=task_1, value=1)

        # Force schedule, otherwise by default it is not scheduled
        pb.add_constraint(task_1._scheduled == True)
        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertEqual(solution.tasks[task_1.name].start, 1)
        self.assertEqual(solution.tasks[task_1.name].end, 4)

    def test_optional_task_start_at_2(self) -> None:
        """Task cannot be scheduled."""
        pb = ps.SchedulingProblem(name="OptionalTaskStartAt2", horizon=2)
        task_1 = ps.FixedDurationTask(name="task1", duration=3, optional=True)
        ps.TaskStartAt(task=task_1, value=1)

        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertFalse(solution.tasks[task_1.name].scheduled)

    def test_optional_task_end_at_1(self) -> None:
        """Task can be scheduled."""
        pb = ps.SchedulingProblem(name="OptionalTaskEndAt1", horizon=6)
        task_1 = ps.FixedDurationTask(name="task1", duration=3, optional=True)
        ps.TaskEndAt(task=task_1, value=4)

        # Force schedule, otherwise by default it is not scheduled
        pb.add_constraint(task_1._scheduled == True)
        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertEqual(solution.tasks[task_1.name].start, 1)
        self.assertEqual(solution.tasks[task_1.name].end, 4)

    def test_optional_task_end_at_2(self) -> None:
        """Task cannot be scheduled."""
        pb = ps.SchedulingProblem(name="OptionalTaskEndAt2", horizon=2)
        task_1 = ps.FixedDurationTask(name="task1", duration=3, optional=True)
        ps.TaskEndAt(task=task_1, value=4)

        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertFalse(solution.tasks[task_1.name].scheduled)

    def test_optional_tasks_start_sync_1(self) -> None:
        """Tasks can be scheduled."""
        pb = ps.SchedulingProblem(name="OptionalTasksStartSynced1", horizon=6)
        task_1 = ps.FixedDurationTask(name="task1", duration=3)  # mandatory
        task_2 = ps.FixedDurationTask(
            name="task2", duration=4, optional=True
        )  # optional

        ps.TaskStartAt(task=task_1, value=2)
        ps.TasksStartSynced(task_1=task_1, task_2=task_2)

        # Force schedule, otherwise by default it is not scheduled
        pb.add_constraint(task_2._scheduled == True)

        solver = ps.SchedulingSolver(problem=pb)
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
        pb = ps.SchedulingProblem(name="OptionalTasksStartSynced2", horizon=5)
        task_1 = ps.FixedDurationTask(name="task1", duration=3)  # mandatory
        task_2 = ps.FixedDurationTask(
            name="task2", duration=4, optional=True
        )  # optional

        ps.TaskStartAt(task=task_1, value=2)
        ps.TasksStartSynced(task_1=task_1, task_2=task_2)

        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertFalse(solution.tasks[task_2.name].scheduled)
        self.assertEqual(solution.tasks[task_1.name].start, 2)
        self.assertEqual(solution.tasks[task_1.name].end, 5)

    def test_optional_tasks_end_sync_1(self) -> None:
        """Tasks can be scheduled."""
        pb = ps.SchedulingProblem(name="OptionalTasksEndSynced1", horizon=6)
        task_1 = ps.FixedDurationTask(name="task1", duration=3)  # mandatory
        task_2 = ps.FixedDurationTask(
            name="task2", duration=4, optional=True
        )  # optional

        ps.TaskEndAt(task=task_1, value=6)
        ps.TasksEndSynced(task_1=task_1, task_2=task_2)

        # Force schedule, otherwise by default it is not scheduled
        pb.add_constraint(task_2._scheduled == True)

        solver = ps.SchedulingSolver(problem=pb)
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
        pb = ps.SchedulingProblem(name="OptionalTasksEndSynced2", horizon=3)
        task_1 = ps.FixedDurationTask(name="task1", duration=3)  # mandatory
        task_2 = ps.FixedDurationTask(
            name="task2", duration=4, optional=True
        )  # optional

        ps.TaskEndAt(task=task_1, value=3)
        ps.TasksStartSynced(task_1=task_1, task_2=task_2)

        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertFalse(solution.tasks[task_2.name].scheduled)
        self.assertEqual(solution.tasks[task_1.name].start, 0)
        self.assertEqual(solution.tasks[task_1.name].end, 3)

    def test_optional_tasks_dont_overlap_1(self) -> None:
        """Tasks can be scheduled."""
        pb = ps.SchedulingProblem(name="OptionalTasksDontOverlap1", horizon=7)
        task_1 = ps.FixedDurationTask(name="task1", duration=3)  # mandatory
        task_2 = ps.FixedDurationTask(
            name="task2", duration=4, optional=True
        )  # optional

        ps.TaskStartAt(task=task_1, value=0)
        ps.TasksDontOverlap(task_1=task_1, task_2=task_2)

        # Force schedule, otherwise by default it is not scheduled
        pb.add_constraint(task_2._scheduled == True)

        solver = ps.SchedulingSolver(problem=pb)
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
        pb = ps.SchedulingProblem(name="OptionalTasksDontOverlap2", horizon=3)
        task_1 = ps.FixedDurationTask(name="task1", duration=3)  # mandatory
        task_2 = ps.FixedDurationTask(
            name="task2", duration=4, optional=True
        )  # optional

        ps.TaskStartAt(task=task_1, value=0)
        ps.TasksDontOverlap(task_1=task_1, task_2=task_2)

        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertFalse(solution.tasks[task_2.name].scheduled)
        self.assertEqual(solution.tasks[task_1.name].start, 0)
        self.assertEqual(solution.tasks[task_1.name].end, 3)

    def test_optional_tasks_precedence_1(self) -> None:
        """Tasks can be scheduled."""
        pb = ps.SchedulingProblem(name="OptionalTasksPrecedence1", horizon=9)
        task_1 = ps.FixedDurationTask(name="task1", duration=3)  # mandatory
        task_2 = ps.FixedDurationTask(
            name="task2", duration=4, optional=True
        )  # optional

        ps.TaskStartAt(task=task_1, value=0)
        ps.TaskPrecedence(task_before=task_1, task_after=task_2, offset=2)

        # Force schedule, otherwise by default it is not scheduled
        pb.add_constraint(task_2._scheduled == True)

        solver = ps.SchedulingSolver(problem=pb)
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
        pb = ps.SchedulingProblem(name="OptionalTasksPrecedence2", horizon=8)
        task_1 = ps.FixedDurationTask(name="task1", duration=3)  # mandatory
        task_2 = ps.FixedDurationTask(
            name="task2", duration=4, optional=True
        )  # optional

        ps.TaskStartAt(task=task_1, value=0)
        ps.TaskPrecedence(task_before=task_1, task_after=task_2, offset=2)

        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertFalse(solution.tasks[task_2.name].scheduled)
        self.assertEqual(solution.tasks[task_1.name].start, 0)
        self.assertEqual(solution.tasks[task_1.name].end, 3)

    def test_optional_tasks_start_after_strict_start_after_lax(self) -> None:
        pb = ps.SchedulingProblem(name="OptionalTasksStartAfter", horizon=8)
        task_1 = ps.FixedDurationTask(name="task1", duration=3)  # mandatory
        task_2 = ps.FixedDurationTask(
            name="task2", duration=4, optional=True
        )  # optional

        # force task_2 to be scheduled
        pb.add_constraint(task_2._scheduled == True)

        ps.TaskStartAfter(task=task_2, value=1, kind="strict")
        ps.TaskStartAfter(task=task_2, value=4, kind="lax")

        solver = ps.SchedulingSolver(problem=pb, debug=True)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertTrue(solution.tasks[task_2.name].scheduled)
        self.assertEqual(solution.tasks[task_2.name].start, 4)
        self.assertEqual(solution.tasks[task_2.name].end, 8)

    def test_optional_tasks_end_before_strict_end_before_lax(self) -> None:
        pb = ps.SchedulingProblem(name="OptionalTasksEndBefore", horizon=8)
        task_1 = ps.FixedDurationTask(name="task1", duration=3)  # mandatory
        task_2 = ps.FixedDurationTask(
            name="task2", duration=4, optional=True
        )  # optional

        # force task_2 to be scheduled
        pb.add_constraint(task_2._scheduled == True)

        ps.TaskEndBefore(task=task_2, value=7, kind="strict")
        ps.TaskEndBefore(task=task_2, value=4, kind="lax")

        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertTrue(solution.tasks[task_2.name].scheduled)
        self.assertEqual(solution.tasks[task_2.name].start, 0)
        self.assertEqual(solution.tasks[task_2.name].end, 4)

    def test_optional_condition_1(self) -> None:
        """A task scheduled only if the horizon is > 10."""
        pb = ps.SchedulingProblem(name="OptionalCondition1")
        task_1 = ps.FixedDurationTask(name="task1", duration=13)  # mandatory
        task_2 = ps.FixedDurationTask(
            name="task2", duration=4, optional=True
        )  # optional

        ps.OptionalTaskConditionSchedule(task=task_2, condition=pb._horizon > 10)

        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertTrue(solution.tasks[task_2.name].scheduled)

    def test_optional_condition_2(self) -> None:
        """A task scheduled only if the horizon is > 10."""
        pb = ps.SchedulingProblem(name="OptionalCondition2", horizon=9)
        task_1 = ps.FixedDurationTask(name="task1", duration=9)  # mandatory
        task_2 = ps.FixedDurationTask(
            name="task2", duration=4, optional=True
        )  # optional

        ps.OptionalTaskConditionSchedule(task=task_2, condition=pb._horizon > 10)

        solver = ps.SchedulingSolver(problem=pb, random_values=True)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertFalse(solution.tasks[task_2.name].scheduled)

    def test_optional_task_dependency_1(self) -> None:
        """task_2 is scheduled, because task_1 is."""
        pb = ps.SchedulingProblem(name="OptionalDependency1")
        task_1 = ps.FixedDurationTask(name="task1", duration=9)  # mandatory
        task_2 = ps.FixedDurationTask(
            name="task2", duration=4, optional=True
        )  # optional

        ps.OptionalTasksDependency(task_1=task_1, task_2=task_2)

        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertTrue(solution.tasks[task_2.name].scheduled)

    def test_optional_task_dependency_2(self) -> None:
        """task_3 is not scheduled, because task_2 should not."""
        pb = ps.SchedulingProblem(name="OptionalDependency2", horizon=9)
        task_1 = ps.FixedDurationTask(name="task1", duration=5)  # mandatory
        task_2 = ps.FixedDurationTask(
            name="task2", duration=4, optional=True
        )  # optional
        task_3 = ps.FixedDurationTask(
            name="task3", duration=1, optional=True
        )  # optional

        ps.OptionalTaskConditionSchedule(task=task_2, condition=pb._horizon > 10)
        ps.OptionalTasksDependency(task_1=task_2, task_2=task_3)

        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertFalse(solution.tasks[task_2.name].scheduled)
        self.assertFalse(solution.tasks[task_3.name].scheduled)

    def test_optional_task_dependency_3(self) -> None:
        """Type checking."""
        pb = ps.SchedulingProblem(name="OptionalDependency3", horizon=9)
        task_1 = ps.FixedDurationTask(name="task1", duration=5)  # mandatory
        task_2 = ps.FixedDurationTask(name="task2", duration=4)  # mandatory
        task_3 = ps.FixedDurationTask(name="task3", duration=1)  # mandatory

        with self.assertRaises(TypeError):
            ps.OptionalTaskConditionSchedule(task=task_1, condition=pb._horizon > 10)

        with self.assertRaises(TypeError):
            ps.OptionalTasksDependency(task_1=task_2, task_2=task_3)

    def test_optional_task_single_worker_1(self) -> None:
        pb = ps.SchedulingProblem(name="OptionalTaskSingleWorker1", horizon=6)
        task_1 = ps.FixedDurationTask(name="task1", duration=3, optional=True)
        ps.TaskStartAt(task=task_1, value=1)
        worker_1 = ps.Worker(name="Worker1")
        task_1.add_required_resource(worker_1)
        # Force schedule, otherwise by default it is not scheduled
        pb.add_constraint(task_1._scheduled == True)
        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)

    def test_optional_task_singleworker_2(self) -> None:
        pb = ps.SchedulingProblem(name="OptionalTaskSingleWorker2", horizon=6)
        task_1 = ps.FixedDurationTask(name="task1", duration=3, optional=True)
        ps.TaskStartAt(task=task_1, value=1)
        worker_1 = ps.Worker(name="Worker1")
        task_1.add_required_resource(worker_1)
        # Force schedule to False
        pb.add_constraint(task_1._scheduled == False)
        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertFalse(solution.tasks[task_1.name].scheduled)

    def test_optional_task_two_workers_1(self) -> None:
        pb = ps.SchedulingProblem(name="OptionalTaskTwoWorkers1", horizon=6)
        task_1 = ps.FixedDurationTask(name="task1", duration=3, optional=True)
        ps.TaskStartAt(task=task_1, value=1)
        worker_1 = ps.Worker(name="Worker1")
        worker_2 = ps.Worker(name="Worker2")
        task_1.add_required_resources([worker_1, worker_2])
        # Force schedule, otherwise by default it is not scheduled
        pb.add_constraint(task_1._scheduled == True)
        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)

    def test_optional_task_two_workers_2(self) -> None:
        pb = ps.SchedulingProblem(name="OptionalTaskTwoWorkers2")
        task_1 = ps.FixedDurationTask(name="task1", duration=3, optional=True)

        worker_1 = ps.Worker(name="Worker1")
        worker_2 = ps.Worker(name="Worker2")
        task_1.add_required_resources([worker_1, worker_2])
        # Force schedule, otherwise by default it is not scheduled
        pb.add_constraint(task_1._scheduled == False)
        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertFalse(solution.tasks[task_1.name].scheduled)

    def test_optional_task_select_workers_1(self) -> None:
        pb = ps.SchedulingProblem(name="OptionalTaskSelectWorkers1")
        task_1 = ps.FixedDurationTask(name="task1", duration=3, optional=True)
        ps.TaskStartAt(task=task_1, value=1)
        worker_1 = ps.Worker(name="Worker1")
        worker_2 = ps.Worker(name="Worker2")
        task_1.add_required_resource(
            ps.SelectWorkers(
                list_of_workers=[worker_1, worker_2], nb_workers_to_select=1
            )
        )
        # Force schedule, otherwise by default it is not scheduled
        pb.add_constraint(task_1._scheduled == True)
        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].scheduled)
        self.assertEqual(len(solution.tasks[task_1.name].assigned_resources), 1)

    def test_optional_task_select_workers_2(self) -> None:
        pb = ps.SchedulingProblem(name="OptionalTaskSelectWorkers2")
        task_1 = ps.FixedDurationTask(name="task1", duration=3, optional=True)
        ps.TaskStartAt(task=task_1, value=1)
        worker_1 = ps.Worker(name="Worker1")
        worker_2 = ps.Worker(name="Worker2")
        task_1.add_required_resource(
            ps.SelectWorkers(
                list_of_workers=[worker_1, worker_2], nb_workers_to_select=1
            )
        )
        # Force schedule False
        pb.add_constraint(task_1._scheduled == False)
        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertFalse(solution.tasks[task_1.name].scheduled)
        self.assertEqual(len(solution.tasks[task_1.name].assigned_resources), 0)

    def test_force_schedule_optional_tasks(self) -> None:
        """task_3 is not scheduled, because task_2 should not."""
        pb = ps.SchedulingProblem(name="ForceScheduleOptionalTasks", horizon=9)
        task_1 = ps.VariableDurationTask(name="task1", optional=True)
        task_2 = ps.FixedDurationTask(name="task2", duration=4, optional=True)
        task_3 = ps.FixedDurationTask(name="task3", duration=1, optional=True)

        ps.ForceScheduleNOptionalTasks(
            list_of_optional_tasks=[task_1, task_2, task_3], nb_tasks_to_schedule=1
        )

        solver = ps.SchedulingSolver(problem=pb)
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
        pb = ps.SchedulingProblem(name="ForceScheduleOptionalTasks2", horizon=14)
        task_1 = ps.VariableDurationTask(name="task1", optional=True)
        task_2 = ps.FixedDurationTask(name="task2", duration=7, optional=True)
        task_3 = ps.FixedDurationTask(name="task3", duration=2, optional=True)

        ps.ForceScheduleNOptionalTasks(
            list_of_optional_tasks=[task_1, task_2, task_3], nb_tasks_to_schedule=2
        )

        solver = ps.SchedulingSolver(problem=pb)
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
        ps.SchedulingProblem(name="ForceScheduleOptionalTasks3", horizon=14)
        task_1 = ps.VariableDurationTask(name="task1")  # this one is not optional
        task_2 = ps.FixedDurationTask(name="task2", duration=7, optional=True)

        with self.assertRaises(TypeError):
            ps.ForceScheduleNOptionalTasks(
                list_of_optional_tasks=[task_1, task_2], nb_tasks_to_schedule=2
            )

    def test_get_scheduled_tasks(self) -> None:
        # task_1 cannot be scheduled, only tasks 2 and 3 can be
        pb = ps.SchedulingProblem(name="GetScheduledTasks", horizon=14)
        task_1 = ps.FixedDurationTask(name="task1", duration=15, optional=True)
        task_2 = ps.FixedDurationTask(name="task2", duration=7, optional=True)
        task_3 = ps.FixedDurationTask(name="task3", duration=2, optional=True)

        ps.ForceScheduleNOptionalTasks(
            list_of_optional_tasks=[task_1, task_2, task_3], nb_tasks_to_schedule=2
        )

        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()

        self.assertTrue(solution)

        scheduled_tasks_dictionary = solution.get_scheduled_tasks()

        self.assertEqual(len(scheduled_tasks_dictionary), 2)
        self.assertTrue("task2" in scheduled_tasks_dictionary)
        self.assertTrue("task3" in scheduled_tasks_dictionary)


if __name__ == "__main__":
    unittest.main()
