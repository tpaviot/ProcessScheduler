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


class TestGroupOfTasks(unittest.TestCase):
    def test_unordered_group_task_1(self) -> None:
        """Task can be scheduled."""
        pb = ps.SchedulingProblem("UnorderedGroupOfTasks1", horizon=20)
        task_1 = ps.FixedDurationTask("task1", duration=3)
        task_2 = ps.FixedDurationTask("task2", duration=7)
        task_3 = ps.FixedDurationTask("task3", duration=2)
        ps.UnorderedTaskGroup([task_1, task_2, task_3], time_interval=[6, 17])
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task_1.name].start <= 6)
        self.assertTrue(solution.tasks[task_1.name].end <= 17)
        self.assertTrue(solution.tasks[task_2.name].start <= 6)
        self.assertTrue(solution.tasks[task_2.name].end <= 17)
        self.assertTrue(solution.tasks[task_3.name].start <= 6)
        self.assertTrue(solution.tasks[task_3.name].end <= 17)

    def test_unordered_group_task_2(self) -> None:
        """Task can be scheduled."""
        pb = ps.SchedulingProblem("UnorderedGroupOfTasks2", horizon=20)
        task_1 = ps.FixedDurationTask("task1", duration=3)
        task_2 = ps.FixedDurationTask("task2", duration=7)
        task_3 = ps.FixedDurationTask("task3", duration=2)
        ps.UnorderedTaskGroup([task_1, task_2, task_3], time_interval_length=8)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        s_1 = solution.tasks[task_1.name].start
        e_1 = solution.tasks[task_1.name].end
        s_2 = solution.tasks[task_2.name].start
        e_2 = solution.tasks[task_2.name].end
        s_3 = solution.tasks[task_3.name].start
        e_3 = solution.tasks[task_3.name].end

        self.assertTrue(max([e_1, e_2, e_3]) - min([s_1, s_2, s_3]) <= 8)

    def test_unordered_group_task_precedence_1(self) -> None:
        """Task can be scheduled."""
        pb = ps.SchedulingProblem("UnorderedGroupOfTasks3", horizon=20)
        task_1 = ps.FixedDurationTask("task1", duration=3)
        task_2 = ps.FixedDurationTask("task2", duration=7)
        task_3 = ps.FixedDurationTask("task3", duration=2)
        task_4 = ps.FixedDurationTask("task4", duration=2)
        group1 = ps.UnorderedTaskGroup([task_1, task_2], time_interval_length=8)
        group2 = ps.UnorderedTaskGroup([task_3, task_4], time_interval_length=8)
        ps.TaskPrecedence(group1, group2)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        s_1 = solution.tasks[task_1.name].start
        e_1 = solution.tasks[task_1.name].end
        s_2 = solution.tasks[task_2.name].start
        e_2 = solution.tasks[task_2.name].end
        s_3 = solution.tasks[task_3.name].start
        e_3 = solution.tasks[task_3.name].end
        s_4 = solution.tasks[task_4.name].start
        e_4 = solution.tasks[task_4.name].end
        self.assertTrue(e_1 <= s_3)
        self.assertTrue(e_1 <= s_4)
        self.assertTrue(e_2 <= s_3)
        self.assertTrue(e_2 <= s_4)

    def test_ordered_group_task_1(self) -> None:
        """Task can be scheduled."""
        pb = ps.SchedulingProblem("OrderedGroupOfTasks1", horizon=40)
        task_1 = ps.FixedDurationTask("task1", duration=3)
        task_2 = ps.FixedDurationTask("task2", duration=7)
        task_3 = ps.FixedDurationTask("task3", duration=2)
        task_4 = ps.FixedDurationTask("task4", duration=2)
        group1 = ps.OrderedTaskGroup(
            [task_1, task_2, task_3, task_4], kind="tight", time_interval=[23, 39]
        )

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        s_1 = solution.tasks[task_1.name].start
        e_1 = solution.tasks[task_1.name].end
        s_2 = solution.tasks[task_2.name].start
        e_2 = solution.tasks[task_2.name].end
        s_3 = solution.tasks[task_3.name].start
        e_3 = solution.tasks[task_3.name].end
        s_4 = solution.tasks[task_4.name].start
        e_4 = solution.tasks[task_4.name].end
        self.assertEqual(e_1, s_2)
        self.assertEqual(e_2, s_3)
        self.assertEqual(e_3, s_4)
        self.assertTrue(s_1 >= 23)
        self.assertTrue(s_4 <= 39)


if __name__ == "__main__":
    unittest.main()
