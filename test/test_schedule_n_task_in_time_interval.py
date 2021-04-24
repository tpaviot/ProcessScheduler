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
    """For each of these tests, we consider two tests: whether the optional task
    is scheduled or not.
    """
    def test_1(self) -> None:
        """Task can be scheduled."""
        pb = ps.SchedulingProblem('ScheduleNTasksInTimeIntervals', horizon=20)
        task_1 = ps.FixedDurationTask('task1', duration = 3)
        task_2 = ps.FixedDurationTask('task2', duration = 3)
        task_3 = ps.FixedDurationTask('task3', duration = 3)

        cstrt = ps.ScheduleNTasksInTimeIntervals([task_1, task_2, task_3],
                                                 nb_tasks_to_schedule= 0,
                                                 list_of_time_intervals = [[1, 10], [13, 20]])
        pb.add_constraint(cstrt)

        # Force schedule, otherwise by default it is not scheduled
        solver = ps.SchedulingSolver(pb, verbosity=True)
        solution = solver.solve()
        self.assertTrue(solution)
        print(solution)


if __name__ == "__main__":
    unittest.main()
