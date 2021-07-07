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

# in this test, two tasks. The start of the first one and the end of the second
# one are constrained by a linear function
# the maximum of task_1.end is 20 (in this case task_1.start is 0)
# the maximum of task_2.end is 20 (in this case task_2.start is 0)
# what happens if we look for the maximum of both task_1 and task_2 ends ?


class MultiObjective(unittest.TestCase):
    def test_multi_two_tasks_1(self) -> None:
        pb = ps.SchedulingProblem("MultiObjective1", horizon=20)
        task_1 = ps.FixedDurationTask("task1", duration=3)
        task_2 = ps.FixedDurationTask("task2", duration=3)

        pb.add_constraint(task_1.end == 20 - task_2.start)

        # Maximize only task_1 end
        ind = ps.Indicator("Task1End", task_1.end)
        pb.maximize_indicator(ind)

        solution = ps.SchedulingSolver(pb).solve()

        self.assertTrue(solution)
        self.assertEqual(solution.tasks[task_1.name].end, 20)
        self.assertEqual(solution.tasks[task_2.name].start, 0)

    def test_multi_two_tasks_lex(self) -> None:
        # the same model, optimize task2 end
        pb = ps.SchedulingProblem("MultiObjective2", horizon=20)
        task_1 = ps.FixedDurationTask("task1", duration=3)
        task_2 = ps.FixedDurationTask("task2", duration=3)

        pb.add_constraint(task_1.end == 20 - task_2.start)

        # Maximize only task_2 end
        ind = ps.Indicator("Task2End", task_2.end)
        pb.maximize_indicator(ind)

        solution = ps.SchedulingSolver(pb).solve()

        self.assertTrue(solution)
        self.assertEqual(solution.tasks[task_1.name].start, 0)
        self.assertEqual(solution.tasks[task_2.name].end, 20)


if __name__ == "__main__":
    unittest.main()
