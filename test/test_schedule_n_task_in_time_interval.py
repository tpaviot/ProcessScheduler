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


class ScheduleNTasksInTimeIntervals(unittest.TestCase):
    def test_single_interval_1(self) -> None:
        pb = ps.SchedulingProblem("ScheduleNTasksInTimeIntervals1", horizon=20)
        task_1 = ps.FixedDurationTask("task1", duration=3)
        task_2 = ps.FixedDurationTask("task2", duration=3)

        cstrt = ps.ScheduleNTasksInTimeIntervals(
            [task_1, task_2], nb_tasks_to_schedule=2, list_of_time_intervals=[[10, 13]]
        )
        pb.add_constraint(cstrt)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        # both tasks start and ends at the same time
        self.assertTrue(solution.tasks[task_1.name].start == 10)
        self.assertTrue(solution.tasks[task_1.name].end == 13)
        self.assertTrue(solution.tasks[task_2.name].start == 10)
        self.assertTrue(solution.tasks[task_2.name].end == 13)

    def test_single_interval_2(self) -> None:
        pb = ps.SchedulingProblem("ScheduleNTasksInTimeIntervals2", horizon=20)
        task_1 = ps.FixedDurationTask("task1", duration=3)
        task_2 = ps.FixedDurationTask("task2", duration=3)

        cstrt = ps.ScheduleNTasksInTimeIntervals(
            [task_1, task_2], nb_tasks_to_schedule=0, list_of_time_intervals=[[10, 20]]
        )
        pb.add_constraint(cstrt)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        # both tasks are necessarily scheduled before 10
        self.assertTrue(solution.tasks[task_1.name].end <= 10)
        self.assertTrue(solution.tasks[task_2.name].end <= 10)

    def test_single_interval_3(self) -> None:
        pb = ps.SchedulingProblem("ScheduleNTasksInTimeIntervals3", horizon=20)
        task_1 = ps.FixedDurationTask("task1", duration=3)
        task_2 = ps.FixedDurationTask("task2", duration=3)

        cstrt = ps.ScheduleNTasksInTimeIntervals(
            [task_1, task_2], nb_tasks_to_schedule=1, list_of_time_intervals=[[10, 20]]
        )
        pb.add_constraint(cstrt)
        # force task_1 to be shceduled after 10. So the only solution is that task 2 is scheduled
        # before 10
        cstrt1 = ps.TaskStartAfterLax(task_1, 10)
        pb.add_constraint(cstrt1)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        # both tasks are necessarily scheduled before 10
        self.assertTrue(solution.tasks[task_1.name].start >= 10)
        self.assertTrue(solution.tasks[task_2.name].end <= 10)

    def test_single_interval_no_solution(self) -> None:
        pb = ps.SchedulingProblem("ScheduleNTasksInTimeIntervalsNoSolution", horizon=20)
        task_1 = ps.FixedDurationTask("task1", duration=3)
        task_2 = ps.FixedDurationTask("task2", duration=3)

        cstrt = ps.ScheduleNTasksInTimeIntervals(
            [task_1, task_2],
            nb_tasks_to_schedule=3,  # impossible!!
            list_of_time_intervals=[[10, 20]],
        )
        pb.add_constraint(cstrt)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertFalse(solution)

    def test_single_interval_too_small(self) -> None:
        # no way to schedule tasks with duration 3 in a slot with range 2
        pb = ps.SchedulingProblem("ScheduleNTasksInTimeIntervalsTooSmall", horizon=20)
        task_1 = ps.FixedDurationTask("task1", duration=3)
        task_2 = ps.FixedDurationTask("task2", duration=3)

        cstrt = ps.ScheduleNTasksInTimeIntervals(
            [task_1, task_2], nb_tasks_to_schedule=2, list_of_time_intervals=[[10, 12]]
        )
        pb.add_constraint(cstrt)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertFalse(solution)

    def test_double_interval_1(self) -> None:
        pb = ps.SchedulingProblem(
            "ScheduleNTasksInTimeIntervalsDoubleInterval1", horizon=20
        )
        task_1 = ps.FixedDurationTask("task1", duration=3)

        cstrt = ps.ScheduleNTasksInTimeIntervals(
            [task_1], nb_tasks_to_schedule=1, list_of_time_intervals=[[5, 7], [15, 18]]
        )
        pb.add_constraint(cstrt)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertEqual(solution.tasks[task_1.name].start, 15)
        self.assertEqual(solution.tasks[task_1.name].end, 18)

    def test_double_interval_2(self) -> None:
        pb = ps.SchedulingProblem(
            "ScheduleNTasksInTimeIntervalsDoubleInterval2", horizon=20
        )
        task_1 = ps.FixedDurationTask("task1", duration=3)
        task_2 = ps.FixedDurationTask("task2", duration=3)

        cstrt = ps.ScheduleNTasksInTimeIntervals(
            [task_1, task_2],
            nb_tasks_to_schedule=2,
            list_of_time_intervals=[[5, 7], [15, 18]],
        )
        pb.add_constraint(cstrt)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)

    def test_triple_interval_1(self) -> None:
        pb = ps.SchedulingProblem(
            "ScheduleNTasksInTimeIntervalsTripleInterval1", horizon=20
        )
        task_1 = ps.FixedDurationTask("task1", duration=3)
        task_2 = ps.FixedDurationTask("task2", duration=3)

        cstrt = ps.ScheduleNTasksInTimeIntervals(
            [task_1, task_2],
            nb_tasks_to_schedule=2,
            list_of_time_intervals=[[5, 7], [11, 14], [15, 17]],
        )
        pb.add_constraint(cstrt)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertEqual(solution.tasks[task_1.name].start, 11)
        self.assertEqual(solution.tasks[task_1.name].end, 14)
        self.assertEqual(solution.tasks[task_2.name].start, 11)
        self.assertEqual(solution.tasks[task_2.name].end, 14)

    def test_triple_interval_that_overlap(self) -> None:
        pb = ps.SchedulingProblem(
            "ScheduleNTasksInTimeIntervalsTripleIntervalOverlap", horizon=20
        )
        task_1 = ps.FixedDurationTask("task1", duration=3)
        task_2 = ps.FixedDurationTask("task2", duration=3)

        cstrt = ps.ScheduleNTasksInTimeIntervals(
            [task_1, task_2],
            nb_tasks_to_schedule=2,
            list_of_time_intervals=[[5, 7], [6, 8], [15, 17]],
        )
        pb.add_constraint(cstrt)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertFalse(solution)

    def test_multi_constraintsp(self) -> None:
        # we want to schedule one task in slot [1,5] and one task into slot [7, 12]
        pb = ps.SchedulingProblem(
            "ScheduleNTasksInTimeIntervalsMultipleConstraints", horizon=20
        )
        task_1 = ps.FixedDurationTask("task1", duration=3)
        task_2 = ps.FixedDurationTask("task2", duration=3)

        cstrt1 = ps.ScheduleNTasksInTimeIntervals(
            [task_1, task_2], nb_tasks_to_schedule=1, list_of_time_intervals=[[1, 5]]
        )
        pb.add_constraint(cstrt1)

        cstrt2 = ps.ScheduleNTasksInTimeIntervals(
            [task_1, task_2], nb_tasks_to_schedule=1, list_of_time_intervals=[[7, 12]]
        )
        pb.add_constraint(cstrt2)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        # check the solution
        task1_start = solution.tasks[task_1.name].start
        task1_end = solution.tasks[task_1.name].end
        task2_start = solution.tasks[task_2.name].start
        task2_end = solution.tasks[task_2.name].end

        task1_in_interval_1 = task1_start >= 1 and task1_end <= 5
        task2_in_interval_1 = task2_start >= 1 and task2_end <= 5
        self.assertTrue(task1_in_interval_1 != task2_in_interval_1)  # xor

        task1_in_interval_2 = task1_start >= 7 and task1_end <= 12
        task2_in_interval_2 = task2_start >= 7 and task2_end <= 12
        self.assertTrue(task1_in_interval_2 != task2_in_interval_2)  # xor

        self.assertTrue(task1_in_interval_1 != task2_in_interval_1)  # xor
        self.assertTrue(task1_in_interval_2 != task2_in_interval_2)  # xor


if __name__ == "__main__":
    unittest.main()
