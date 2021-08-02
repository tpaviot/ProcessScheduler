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


class TestCumulative(unittest.TestCase):
    def test_create_cumulative(self):
        """take the single task/single resource and display output"""
        ps.SchedulingProblem("CreateCumulative", horizon=10)
        cumulative_worker = ps.CumulativeWorker("MachineA", size=4)
        self.assertEqual(len(cumulative_worker.cumulative_workers), 4)

    def test_create_cumulative_wrong_type(self):
        """take the single task/single resource and display output"""
        ps.SchedulingProblem("CreateCumulativeWrongType", horizon=10)
        with self.assertRaises(ValueError):
            ps.CumulativeWorker("MachineA", size=1)
        with self.assertRaises(ValueError):
            ps.CumulativeWorker("MachineA", size=2.5)

    def test_cumulative_1(self):
        pb_bs = ps.SchedulingProblem("Cumulative1", 3)
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

        # constraints
        pb_bs.add_constraint(ps.TaskStartAt(t2, 1))

        # plot solution
        solver = ps.SchedulingSolver(pb_bs)
        solution = solver.solve()
        self.assertTrue(solution)

    def test_cumulative_2(self):
        pb_bs = ps.SchedulingProblem("Cumulative2", 3)
        # tasks
        t1 = ps.FixedDurationTask("T1", duration=2)
        t2 = ps.FixedDurationTask("T2", duration=2)

        # workers
        r1 = ps.CumulativeWorker("Machine1", size=2)
        # resource assignment
        t1.add_required_resource(r1)
        t2.add_required_resource(r1)

        # constraints
        pb_bs.add_constraint(ps.TaskStartAt(t2, 1))

        # plot solution
        solver = ps.SchedulingSolver(pb_bs)
        solution = solver.solve()
        self.assertTrue(solution)

    def test_optional_cumulative(self):
        """Same as above, but with an optional taskand an horizon of 2.
        t2 should not be scheduled."""
        pb_bs = ps.SchedulingProblem("OptionalCumulative", 2)
        # tasks
        t1 = ps.FixedDurationTask("T1", duration=2)
        t2 = ps.FixedDurationTask("T2", duration=2, optional=True)
        t3 = ps.FixedDurationTask("T3", duration=2)

        # workers
        r1 = ps.CumulativeWorker("Machine1", size=2)
        # resource assignment
        t1.add_required_resource(r1)
        t2.add_required_resource(r1)

        # constraints
        pb_bs.add_constraint(ps.TaskStartAt(t2, 1))

        # plot solution
        solver = ps.SchedulingSolver(pb_bs)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[t1.name].scheduled)
        self.assertTrue(solution.tasks[t3.name].scheduled)
        self.assertFalse(solution.tasks[t2.name].scheduled)

    def test_cumulative_select_worker_1(self):
        pb_bs = ps.SchedulingProblem("CumulativeSelectWorker", 2)
        # tasks
        t1 = ps.FixedDurationTask("T1", duration=2)
        t2 = ps.FixedDurationTask("T2", duration=2)

        # workers
        r1 = ps.CumulativeWorker("Machine1", size=2)
        r2 = ps.CumulativeWorker("Machine2", size=2)
        # resource assignment
        t1.add_required_resource(ps.SelectWorkers([r1, r2], 1))
        t2.add_required_resource(ps.SelectWorkers([r1, r2], 1))

        # plot solution
        solver = ps.SchedulingSolver(pb_bs)
        solution = solver.solve()
        self.assertTrue(solution)

    def test_cumulative_hosp(self):
        n = 16
        capa = 4
        pb_bs = ps.SchedulingProblem("Hospital", horizon=int(n / capa))
        # workers
        r1 = ps.CumulativeWorker("Room", size=capa)

        for i in range(n):
            t = ps.FixedDurationTask("T%i" % (i + 1), duration=1)
            t.add_required_resource(r1)

        solver = ps.SchedulingSolver(pb_bs)
        solution = solver.solve()
        self.assertTrue(solution)

    def test_cumulative_productivity(self):
        """Horizon should be 4, 100/29=3.44."""
        problem = ps.SchedulingProblem("CumulativeProductivity")
        t_1 = ps.VariableDurationTask("t1", work_amount=100)

        worker_1 = ps.CumulativeWorker("CumulWorker", size=3, productivity=29)
        t_1.add_required_resource(worker_1)

        problem.add_objective_makespan()
        solution = ps.SchedulingSolver(problem).solve()
        self.assertTrue(solution)
        self.assertEqual(solution.horizon, 4)


if __name__ == "__main__":
    unittest.main()
