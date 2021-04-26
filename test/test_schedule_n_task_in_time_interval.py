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
    def test_1(self) -> None:
        pb = ps.SchedulingProblem('ScheduleNTasksInTimeIntervals1', horizon=20)
        task_1 = ps.FixedDurationTask('task1', duration = 3)
        task_2 = ps.FixedDurationTask('task2', duration = 3)

        cstrt = ps.ScheduleNTasksInTimeIntervals([task_1, task_2],
                                                 nb_tasks_to_schedule= 2,
                                                 list_of_time_intervals = [[10, 13]])
        pb.add_constraint(cstrt)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        # both tasks start and ends at the same time
        self.assertTrue(solution.tasks[task_1.name].start == 10)
        self.assertTrue(solution.tasks[task_1.name].end == 13)
        self.assertTrue(solution.tasks[task_2.name].start == 10)
        self.assertTrue(solution.tasks[task_2.name].end == 13)

    def test_2(self) -> None:
        pb = ps.SchedulingProblem('ScheduleNTasksInTimeIntervals2', horizon=20)
        task_1 = ps.FixedDurationTask('task1', duration = 3)
        task_2 = ps.FixedDurationTask('task2', duration = 3)

        cstrt = ps.ScheduleNTasksInTimeIntervals([task_1, task_2],
                                                 nb_tasks_to_schedule= 0,
                                                 list_of_time_intervals = [[10, 20]])
        pb.add_constraint(cstrt)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        # both tasks are necessarily scheduled before 10
        self.assertTrue(solution.tasks[task_1.name].end <= 10)
        self.assertTrue(solution.tasks[task_2.name].end <= 10)



    def test_3(self) -> None:
        pb = ps.SchedulingProblem('ScheduleNTasksInTimeIntervals3', horizon=20)
        task_1 = ps.FixedDurationTask('task1', duration = 3)
        task_2 = ps.FixedDurationTask('task2', duration = 3)

        cstrt = ps.ScheduleNTasksInTimeIntervals([task_1, task_2],
                                                 nb_tasks_to_schedule= 1,
                                                 list_of_time_intervals = [[10, 20]])
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

    def test_4(self) -> None:
        pb = ps.SchedulingProblem('ScheduleNTasksInTimeIntervals4', horizon=20)
        task_1 = ps.FixedDurationTask('task1', duration = 3)
        task_2 = ps.FixedDurationTask('task2', duration = 3)

        cstrt = ps.ScheduleNTasksInTimeIntervals([task_1, task_2],
                                                 nb_tasks_to_schedule= 3,  # impossible!!
                                                 list_of_time_intervals = [[10, 20]])
        pb.add_constraint(cstrt)
        solver = ps.SchedulingSolver(pb, verbosity=True)
        solution = solver.solve()
        self.assertFalse(solution)


if __name__ == "__main__":
    unittest.main()
