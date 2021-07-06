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


class TestWorkLoad(unittest.TestCase):
    def test_resource_work_load_basic(self) -> None:
        pb = ps.SchedulingProblem("ResourceWorkLoadBasic", horizon=12)
        task_1 = ps.FixedDurationTask("task1", duration=8)

        worker_1 = ps.Worker("Worker1")
        task_1.add_required_resource(worker_1)

        c1 = ps.WorkLoad(worker_1, {(0, 6): 2})
        pb.add_constraint(c1)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        # the only possible solution is that the task is scheduled form 4 to 12
        self.assertEqual(solution.tasks[task_1.name].start, 4)
        self.assertEqual(solution.tasks[task_1.name].end, 12)

    def test_resource_work_load_eq(self) -> None:
        pb = ps.SchedulingProblem("ResourceWorkLoadEq", horizon=12)
        task_1 = ps.FixedDurationTask("task1", duration=7)

        worker_1 = ps.Worker("Worker1")
        task_1.add_required_resource(worker_1)

        c1 = ps.WorkLoad(worker_1, {(0, 6): 3}, kind="exact")
        pb.add_constraint(c1)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        # the only possible solution is that the task is scheduled form 3 to 9
        self.assertEqual(solution.tasks[task_1.name].start, 3)
        self.assertEqual(solution.tasks[task_1.name].end, 10)

    def test_resource_work_load_min(self) -> None:
        pb = ps.SchedulingProblem("ResourceWorkLoadMin", horizon=20)
        task_1 = ps.FixedDurationTask("task1", duration=7)

        worker_1 = ps.Worker("Worker1")
        task_1.add_required_resource(worker_1)

        c1 = ps.WorkLoad(worker_1, {(6, 8): 2}, kind="min")
        pb.add_constraint(c1)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()

        self.assertTrue(solution)
        # the only possible solution is that the task is scheduled form 3 to 9
        self.assertTrue(solution.tasks[task_1.name].start <= 6)
        self.assertTrue(solution.tasks[task_1.name].end >= 8)

    def test_resource_work_load_3(self) -> None:
        # same problem, but we force two tasks to be scheduled at start and end
        # of the planning
        pb = ps.SchedulingProblem("ResourceWorkLoadUnavailability", horizon=12)
        task_1 = ps.FixedDurationTask("task1", duration=4)
        task_2 = ps.FixedDurationTask("task2", duration=4)
        worker_1 = ps.Worker("Worker1")
        task_1.add_required_resource(worker_1)
        task_2.add_required_resource(worker_1)

        c1 = ps.WorkLoad(worker_1, {(4, 8): 0})
        pb.add_constraint(c1)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        # there should be one task from 0 to 4 and one task from 8 to 12.
        self.assertTrue(
            solution.tasks[task_1.name].start == 0
            or solution.tasks[task_2.name].start == 0
        )
        self.assertTrue(
            solution.tasks[task_1.name].start == 8
            or solution.tasks[task_2.name].start == 8
        )

    def test_resource_work_load_exception(self) -> None:
        ps.SchedulingProblem("ResourceWorkLoadException", horizon=12)

        worker_1 = ps.Worker("Worker1")

        with self.assertRaises(ValueError):
            ps.WorkLoad(worker_1, {(0, 6): 2}, kind="foo")

    def test_selectworker_work_load_1(self) -> None:
        pb = ps.SchedulingProblem("SelectWorkerWorkLoad1", horizon=12)

        worker_1 = ps.Worker("Worker1")
        worker_2 = ps.Worker("Worker2")

        task1 = ps.FixedDurationTask("Task1", duration=10)

        task1.add_required_resource(ps.SelectWorkers([worker_1, worker_2], 1, "min"))
        # the workload on worker_1 forces 0 between 4 and 8
        # then the worker_1 can not be assigned
        c1 = ps.WorkLoad(worker_1, {(4, 8): 0})
        pb.add_constraint(c1)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        print(solution)
        self.assertTrue(solution)
        self.assertTrue(
            solution.tasks[task1.name].assigned_resources == [worker_2.name]
        )

    def test_multiple_workers_work_load_1(self) -> None:
        pb = ps.SchedulingProblem("MultipleWorkersWorkLoad1", horizon=12)

        worker_1 = ps.Worker("Worker1")
        worker_2 = ps.Worker("Worker2")

        task1 = ps.FixedDurationTask("Task1", duration=10)
        task1.add_required_resources([worker_1, worker_2])

        c1 = ps.WorkLoad(worker_1, {(0, 4): 2})
        pb.add_constraint(c1)
        c2 = ps.WorkLoad(worker_2, {(2, 6): 2}, kind="min")
        pb.add_constraint(c2)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[task1.name].start == 2)

    def test_multiple_workers_work_load_2(self) -> None:
        ### the same as above but changing 'min' to 'exact', there's no solution
        pb = ps.SchedulingProblem("MultipleWorkersWorkLoad2", horizon=12)

        worker_1 = ps.Worker("Worker1")
        worker_2 = ps.Worker("Worker2")

        task1 = ps.FixedDurationTask("Task1", duration=10)
        task1.add_required_resources([worker_1, worker_2])

        c1 = ps.WorkLoad(worker_1, {(0, 4): 2})
        pb.add_constraint(c1)
        c2 = ps.WorkLoad(worker_2, {(2, 6): 2}, kind="exact")
        pb.add_constraint(c2)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertFalse(solution)


if __name__ == "__main__":
    unittest.main()
