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


class TestResourceUnavailable(unittest.TestCase):
    def test_resource_unavailable_1(self) -> None:
        pb = ps.SchedulingProblem("ResourceUnavailable1", horizon=10)
        task_1 = ps.FixedDurationTask("task1", duration=3)
        worker_1 = ps.Worker("Worker1")
        task_1.add_required_resource(worker_1)
        c1 = ps.ResourceUnavailable(worker_1, [(1, 3), (6, 8)])
        pb.add_constraint(c1)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertEqual(solution.tasks[task_1.name].start, 3)
        self.assertEqual(solution.tasks[task_1.name].end, 6)

    def test_resource_unavailable_2(self) -> None:
        pb = ps.SchedulingProblem("ResourceUnavailable2", horizon=10)
        task_1 = ps.FixedDurationTask("task1", duration=3)
        worker_1 = ps.Worker("Worker1")
        task_1.add_required_resource(worker_1)
        # difference with the first one: build 2 constraints
        # merged using a and_
        c1 = ps.ResourceUnavailable(worker_1, [(1, 3)])
        c2 = ps.ResourceUnavailable(worker_1, [(6, 8)])
        pb.add_constraint(ps.and_([c1, c2]))
        # that should not change the problem solution
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertEqual(solution.tasks[task_1.name].start, 3)
        self.assertEqual(solution.tasks[task_1.name].end, 6)

    def test_resource_unavailable_3(self) -> None:
        pb = ps.SchedulingProblem("ResourceUnavailable3", horizon=10)
        task_1 = ps.FixedDurationTask("task1", duration=3)
        worker_1 = ps.Worker("Worker1")
        task_1.add_required_resource(worker_1)
        # difference with the previous ones: too much unavailability,
        # so possible solution
        # merged using a and_
        c1 = ps.ResourceUnavailable(worker_1, [(1, 3)])
        c2 = ps.ResourceUnavailable(worker_1, [(5, 8)])
        pb.add_constraint(ps.and_([c1, c2]))
        # that should not change the problem solution
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertFalse(solution)

    def test_cumulative_4(self):
        pb_bs = ps.SchedulingProblem("ResourceUnavailableCumulative1", 10)
        # tasks
        t1 = ps.FixedDurationTask("T1", duration=2)
        t2 = ps.FixedDurationTask("T2", duration=2)
        t3 = ps.FixedDurationTask("T3", duration=2)

        # workers
        r1 = ps.CumulativeWorker("Machine1", size=3)

        # resource assignment
        t1.add_required_resource(r1)
        t2.add_required_resource(r1)
        t3.add_required_resource(r1)

        c1 = ps.ResourceUnavailable(r1, [(1, 10)])
        pb_bs.add_constraint(c1)

        # plot solution
        solver = ps.SchedulingSolver(pb_bs)  # , debug=True)
        solution = solver.solve()
        self.assertFalse(solution)


if __name__ == "__main__":
    unittest.main()
