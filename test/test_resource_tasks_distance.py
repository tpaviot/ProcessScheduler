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


class TestResourceTasksDistance(unittest.TestCase):
    def test_resource_tasks_distance_1(self) -> None:
        pb = ps.SchedulingProblem("ResourceTasksDistance1", horizon=20)
        task_1 = ps.FixedDurationTask("task1", duration=8)
        task_2 = ps.FixedDurationTask("task2", duration=4)
        worker_1 = ps.Worker("Worker1")
        task_1.add_required_resource(worker_1)
        task_2.add_required_resource(worker_1)

        c1 = ps.ResourceTasksDistance(worker_1, distance=4, mode="exact")
        pb.add_constraint(c1)

        pb.add_constraint(ps.TaskStartAt(task_1, 1))

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)

        t1_start = solution.tasks[task_1.name].start
        t2_start = solution.tasks[task_2.name].start
        t1_end = solution.tasks[task_1.name].end
        t2_end = solution.tasks[task_2.name].end
        self.assertEqual(t1_start, 1)
        self.assertEqual(t1_end, 9)
        self.assertEqual(t2_start, 13)
        self.assertEqual(t2_end, 17)

    def test_resource_tasks_distance_2(self) -> None:
        pb = ps.SchedulingProblem("ResourceTasksDistance2")
        task_1 = ps.FixedDurationTask("task1", duration=8)
        task_2 = ps.FixedDurationTask("task2", duration=4)
        worker_1 = ps.Worker("Worker1")
        task_1.add_required_resource(worker_1)
        task_2.add_required_resource(worker_1)

        c1 = ps.ResourceTasksDistance(worker_1, distance=4, mode="max")
        pb.add_constraint(c1)

        pb.add_constraint(ps.TaskStartAt(task_1, 1))

        pb.add_objective_makespan()

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)

        t1_start = solution.tasks[task_1.name].start
        t2_start = solution.tasks[task_2.name].start
        t1_end = solution.tasks[task_1.name].end
        t2_end = solution.tasks[task_2.name].end
        self.assertEqual(t1_start, 1)
        self.assertEqual(t1_end, 9)
        self.assertEqual(t2_start, 9)
        self.assertEqual(t2_end, 13)

    def test_resource_tasks_distance_3(self) -> None:
        pb = ps.SchedulingProblem("ResourceTasksDistanceContiguous3")
        task_1 = ps.FixedDurationTask("task1", duration=8)
        task_2 = ps.FixedDurationTask("task2", duration=4)
        task_3 = ps.FixedDurationTask("task3", duration=5)
        worker_1 = ps.Worker("Worker1")
        task_1.add_required_resource(worker_1)
        task_2.add_required_resource(worker_1)
        task_3.add_required_resource(worker_1)

        # a constraint to tell tasks are contiguous
        c1 = ps.ResourceTasksDistance(worker_1, distance=0, mode="exact")
        pb.add_constraint(c1)

        pb.add_constraint(ps.TaskStartAt(task_1, 2))

        pb.add_objective_makespan()

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)

        t1_start = solution.tasks[task_1.name].start
        t2_start = solution.tasks[task_2.name].start
        t3_start = solution.tasks[task_3.name].start
        t1_end = solution.tasks[task_1.name].end
        t2_end = solution.tasks[task_2.name].end
        t3_end = solution.tasks[task_3.name].end

        self.assertEqual(t1_start, 2)
        self.assertEqual(t1_end, 10)
        self.assertTrue(t3_start == 10 or t3_start == 14)
        self.assertTrue(t2_start == 10 or t2_start == 15)

    def test_resource_tasks_distance_4(self) -> None:
        """Adding one or more non scheduled optional tasks should not change anything"""
        pb = ps.SchedulingProblem("ResourceTasksDistance4OptionalTasks", horizon=20)
        task_1 = ps.FixedDurationTask("task1", duration=8)
        task_2 = ps.FixedDurationTask("task2", duration=4)
        task_3 = ps.FixedDurationTask("task3", duration=3, optional=True)
        task_4 = ps.FixedDurationTask("task4", duration=2, optional=True)
        task_5 = ps.FixedDurationTask("task5", duration=1, optional=True)
        worker_1 = ps.Worker("Worker1")
        task_1.add_required_resource(worker_1)
        task_2.add_required_resource(worker_1)

        c1 = ps.ResourceTasksDistance(worker_1, distance=4, mode="exact")
        pb.add_constraint(c1)

        pb.add_constraint(ps.TaskStartAt(task_1, 1))

        solver = ps.SchedulingSolver(pb)
        # for optional tasks to not be scheduled
        solver.add_constraint(task_3.scheduled == False)
        solver.add_constraint(task_4.scheduled == False)
        solver.add_constraint(task_5.scheduled == False)

        solution = solver.solve()

        self.assertTrue(solution)

        t1_start = solution.tasks[task_1.name].start
        t2_start = solution.tasks[task_2.name].start
        t1_end = solution.tasks[task_1.name].end
        t2_end = solution.tasks[task_2.name].end
        self.assertEqual(t1_start, 1)
        self.assertEqual(t1_end, 9)
        self.assertEqual(t2_start, 13)
        self.assertEqual(t2_end, 17)


if __name__ == "__main__":
    unittest.main()
