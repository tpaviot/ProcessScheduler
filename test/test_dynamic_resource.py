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


class TestDynamicResource(unittest.TestCase):
    def test_dynamic_1(self) -> None:
        pb = ps.SchedulingProblem("DynamicTest1")
        task_1 = ps.FixedDurationTask("task1", duration=10, work_amount=10)
        task_2 = ps.FixedDurationTask("task2", duration=5)
        task_3 = ps.FixedDurationTask("task3", duration=5)

        pb.add_constraint(ps.TaskStartAt(task_3, 0))
        pb.add_constraint(ps.TaskEndAt(task_2, 10))

        worker_1 = ps.Worker("Worker1", productivity=1)
        worker_2 = ps.Worker("Worker2", productivity=1)

        task_1.add_required_resources([worker_1, worker_2], dynamic=True)
        task_2.add_required_resource(worker_1)
        task_3.add_required_resource(worker_2)

        pb.add_objective_makespan()

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertEqual(solution.horizon, 10)

    def test_non_dynamic_1(self) -> None:
        # same test as previously
        # but the task_1 workers are non dynamic.
        # so the horizon must be 20.
        pb = ps.SchedulingProblem("NonDynamicTest1")
        task_1 = ps.FixedDurationTask("task1", duration=10, work_amount=10)
        task_2 = ps.FixedDurationTask("task2", duration=5)
        task_3 = ps.FixedDurationTask("task3", duration=5)

        pb.add_constraint(ps.TaskStartAt(task_3, 0))
        pb.add_constraint(ps.TaskEndAt(task_2, 10))

        worker_1 = ps.Worker("Worker1", productivity=1)
        worker_2 = ps.Worker("Worker2", productivity=1)

        task_1.add_required_resources([worker_1, worker_2])  # dynamic False by default
        task_2.add_required_resource(worker_1)
        task_3.add_required_resource(worker_2)

        pb.add_objective_makespan()

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertEqual(solution.horizon, 20)


if __name__ == "__main__":
    unittest.main()
