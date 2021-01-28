#Copyright 2020 Thomas Paviot (tpaviot@gmail.com)
#
#Licensed to the Apache Software Foundation (ASF) under one
#or more contributor license agreements.  See the NOTICE file
#distributed with this work for additional information
#regarding copyright ownership.  The ASF licenses this file
#to you under the Apache License, Version 2.0 (the
#"License"); you may not use this file except in compliance
#with the License.  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing,
#software distributed under the License is distributed on an
#"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#KIND, either express or implied.  See the License for the
#specific language governing permissions and limitations
#under the License.

import unittest

import processscheduler as ps
from processscheduler.resource import _distribute_p_over_n

class TestCumulative(unittest.TestCase):
    def test_distribute_p_over_n(self):
        res1 = _distribute_p_over_n(7, 3)
        self.assertEqual(res1, [3, 2, 2])
        res2 = _distribute_p_over_n(6, 2)
        self.assertEqual(res2, [3, 3])
        res3 = _distribute_p_over_n(9, 3)
        self.assertEqual(res3, [3, 3, 3])
        res4 = _distribute_p_over_n(1, 5)
        self.assertEqual(res4, [1, 0, 0, 0, 0])
        res4 = _distribute_p_over_n(29, 3)
        self.assertEqual(res4, [11, 9, 9])

    def test_create_cumulative(self):
        """ take the single task/single resource and display output """
        ps.SchedulingProblem('CreateCumulative', horizon=10)
        cumulative_worker = ps.CumulativeWorker('MachineA', size=4)
        self.assertEqual(len(cumulative_worker.cumulative_workers), 4)

    def test_create_cumulative_wrong_type(self):
        """ take the single task/single resource and display output """
        ps.SchedulingProblem('CreateCumulativeWrongType', horizon=10)
        with self.assertRaises(ValueError):
            ps.CumulativeWorker('MachineA', size=1)
        with self.assertRaises(ValueError):
            ps.CumulativeWorker('MachineA', size=2.5)

    def test_cumulative_1(self):
        pb_bs = ps.SchedulingProblem("Cumulative1", 3)
        # tasks
        t1 = ps.FixedDurationTask('T1', duration=2)
        t2 = ps.FixedDurationTask('T2', duration=2)
        t3 = ps.FixedDurationTask('T3', duration=2)

        # workers
        r1 = ps.CumulativeWorker('Machine1', size=3)
        # resource assignment
        t1.add_required_resource(r1)
        t2.add_required_resource(r1)
        t3.add_required_resource(r1)

        # constraints
        pb_bs.add_constraint(ps.TaskStartAt(t2, 1))

        # plot solution
        solver = ps.SchedulingSolver(pb_bs, verbosity=False)
        solution = solver.solve()
        self.assertTrue(solution)

    def test_cumulative_2(self):
        pb_bs = ps.SchedulingProblem("Cumulative2", 3)
        # tasks
        t1 = ps.FixedDurationTask('T1', duration=2)
        t2 = ps.FixedDurationTask('T2', duration=2)
        t3 = ps.FixedDurationTask('T3', duration=2)

        # workers
        r1 = ps.CumulativeWorker('Machine1', size=2)
        # resource assignment
        t1.add_required_resource(r1)
        t2.add_required_resource(r1)

        # constraints
        pb_bs.add_constraint(ps.TaskStartAt(t2, 1))

        # plot solution
        solver = ps.SchedulingSolver(pb_bs, verbosity=False)
        solution = solver.solve()
        self.assertTrue(solution)

    def test_optional_cumulative(self):
        """Same as above, but with an optional taskand an horizon of 2.
        t2 should not be scheduled."""
        pb_bs = ps.SchedulingProblem("OptionalCumulative", 2)
        # tasks
        t1 = ps.FixedDurationTask('T1', duration=2)
        t2 = ps.FixedDurationTask('T2', duration=2, optional=True)
        t3 = ps.FixedDurationTask('T3', duration=2)

        # workers
        r1 = ps.CumulativeWorker('Machine1', size=2)
        # resource assignment
        t1.add_required_resource(r1)
        t2.add_required_resource(r1)

        # constraints
        pb_bs.add_constraint(ps.TaskStartAt(t2, 1))

        # plot solution
        solver = ps.SchedulingSolver(pb_bs, verbosity=False)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertTrue(solution.tasks[t1.name].scheduled)
        self.assertTrue(solution.tasks[t3.name].scheduled)
        self.assertFalse(solution.tasks[t2.name].scheduled)
        

    def test_cumulative_select_worker_1(self):
        pb_bs = ps.SchedulingProblem("CumulativeSelectWorker", 2)
        # tasks
        t1 = ps.FixedDurationTask('T1', duration=2)
        t2 = ps.FixedDurationTask('T2', duration=2)

        # workers
        r1 = ps.CumulativeWorker('Machine1', size=2)
        r2 = ps.CumulativeWorker('Machine2', size=2)
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
        pb_bs = ps.SchedulingProblem("Hospital", horizon= int(n / capa))
        # workers
        r1 = ps.CumulativeWorker('Room', size=capa)

        for i in range(n):
            t = ps.FixedDurationTask('T%i' % (i+1), duration=1)
            t.add_required_resource(r1)

        solver = ps.SchedulingSolver(pb_bs, logic='QF_IDL')
        solution = solver.solve()
        self.assertTrue(solution)

    def test_cumulative_productivity(self):
        """Horizon should be 4, 100/29=3.44."""
        problem = ps.SchedulingProblem("CumulativeProductivity")
        t_1 = ps.VariableDurationTask('t1', work_amount=100)

        worker_1 = ps.CumulativeWorker('CumulWorker', size=3, productivity=29)
        t_1.add_required_resource(worker_1)

        problem.add_objective_makespan()
        solution = ps.SchedulingSolver(problem).solve()
        self.assertTrue(solution)
        self.assertEqual(solution.horizon, 4)

    def test_cumulative_cost(self):
        problem = ps.SchedulingProblem("CumulativeCost", horizon=5)
        t_1 = ps.FixedDurationTask('t1', duration=5)

        worker_1 = ps.CumulativeWorker('CumulWorker', size=3, cost_per_period=5)
        t_1.add_required_resource(worker_1)

        cost_ind = problem.add_indicator_resource_cost([worker_1])

        solution = ps.SchedulingSolver(problem).solve()

        self.assertTrue(solution)
        self.assertEqual(solution.indicators[cost_ind.name], 25)
        solution = ps.SchedulingSolver(problem).solve()
        self.assertTrue(solution)


if __name__ == "__main__":
    unittest.main()
