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


class TestCost(unittest.TestCase):
    def test_cost_basic(self) -> None:
        ps.SchedulingProblem("CostBasic", horizon=12)
        ress_cost = ps.ConstantCostPerPeriod(5)
        ps.Worker("Worker1", cost=ress_cost)

    def test_cost_assertion_fail(self) -> None:
        with self.assertRaises(ValueError):
            ps.ConstantCostPerPeriod(-4)

    def test_cost_polynomial_1(self) -> None:
        ps.SchedulingProblem("PolynomialCost1", horizon=12)

        def c(t):
            return 0.5 * t ** 2 + 50

        ress_cost = ps.PolynomialCostFunction(c)
        ps.Worker("Worker1", cost=ress_cost)

    def test_cost_polynomial_lambda(self) -> None:
        ps.SchedulingProblem("PolynomialCostLambdaFunction", horizon=12)
        ress_cost = ps.PolynomialCostFunction(lambda t: 2 * t + 10)
        ps.Worker("Worker1", cost=ress_cost)

    def test_cost_failure(self) -> None:
        ps.SchedulingProblem("CostWrongType", horizon=12)
        with self.assertRaises(TypeError):
            ps.Worker("ress1", cost=5)  # only accepts a _Cost instance
        with self.assertRaises(TypeError):
            ps.PolynomialCostFunction("f")  # only accepts a callable

    def test_constant_cost_per_period_1(self) -> None:
        problem = ps.SchedulingProblem("IndicatorResourceConstantCostPerPeriod1")
        t_1 = ps.FixedDurationTask("t1", duration=11)
        worker_1 = ps.Worker("Worker1", cost=ps.ConstantCostPerPeriod(7))
        t_1.add_required_resource(worker_1)
        cost_ind = problem.add_indicator_resource_cost([worker_1])

        solution = ps.SchedulingSolver(problem).solve()

        self.assertTrue(solution)
        self.assertEqual(solution.indicators[cost_ind.name], 77)

    def test_constant_cost_per_period_2(self) -> None:
        problem = ps.SchedulingProblem("IndicatorResourceConstantCostPerPeriod12")
        t_1 = ps.VariableDurationTask("t1", work_amount=100)
        worker_1 = ps.Worker(
            "Worker1", productivity=4, cost=ps.ConstantCostPerPeriod(10)
        )
        worker_2 = ps.Worker(
            "Worker2", productivity=7, cost=ps.ConstantCostPerPeriod(20)
        )
        all_workers = [worker_1, worker_2]
        problem.add_objective_makespan()
        t_1.add_required_resources(all_workers)
        cost_ind = problem.add_indicator_resource_cost(all_workers)

        solution = ps.SchedulingSolver(problem).solve()

        self.assertTrue(solution)
        self.assertEqual(solution.indicators[cost_ind.name], 300)

    def test_linear_cost_1(self) -> None:
        problem = ps.SchedulingProblem("IndicatorResourcePolynomialCost1")

        t_1 = ps.FixedDurationTask("t1", duration=17)

        def int_cost_function(t):
            return 23 * t + 3

        worker_1 = ps.Worker(
            "Worker1", cost=ps.PolynomialCostFunction(int_cost_function)
        )
        t_1.add_required_resource(worker_1)

        problem.add_constraint(ps.TaskStartAt(t_1, 13))
        cost_ind = problem.add_indicator_resource_cost([worker_1])

        solution = ps.SchedulingSolver(problem).solve()

        self.assertTrue(solution)
        # expected cost should be 8457
        expected_cost = int(
            ((int_cost_function(13) + int_cost_function(13 + 17)) * 17) / 2
        )
        self.assertEqual(solution.indicators[cost_ind.name], expected_cost)

    def test_optimize_linear_cost_1(self) -> None:
        # same cost function as above, we minimize the cst,
        # the task should be scheduled at 0 (because the cost function increases)
        problem = ps.SchedulingProblem("OptimizeLinearCost1")

        t_1 = ps.FixedDurationTask("t1", duration=17)

        def int_cost_function(t):
            return 23 * t + 3

        worker_1 = ps.Worker(
            "Worker1", cost=ps.PolynomialCostFunction(int_cost_function)
        )
        t_1.add_required_resource(worker_1)

        cost_ind = problem.add_indicator_resource_cost([worker_1])
        problem.add_objective_resource_cost([worker_1])

        solution = ps.SchedulingSolver(problem).solve()

        self.assertTrue(solution)
        # the task is scheduled at the beginning of the workplan
        self.assertEqual(solution.tasks[t_1.name].start, 0)
        # expected cost should be 3374
        expected_cost = int(((int_cost_function(0) + int_cost_function(17)) * 17) / 2)
        self.assertEqual(solution.indicators[cost_ind.name], expected_cost)

    def test_optimize_linear_cost_2(self) -> None:
        # now we have a cost function that decreases over time,
        # then minimizing the cost should schedule the task at the end.
        # so we define an horizon for the problem
        problem = ps.SchedulingProblem("OptimizeLinear2", horizon=87)

        t_1 = ps.FixedDurationTask("t1", duration=13)

        # be sure however that this function is positive on the interval
        def int_cost_function(t):
            return 711 - 5 * t

        worker_1 = ps.Worker(
            "Worker1", cost=ps.PolynomialCostFunction(int_cost_function)
        )
        t_1.add_required_resource(worker_1)

        cost_ind = problem.add_indicator_resource_cost([worker_1])
        problem.add_objective_resource_cost([worker_1])

        solution = ps.SchedulingSolver(problem).solve()

        self.assertTrue(solution)
        # the task is scheduled at the beginning of the workplan
        self.assertEqual(solution.tasks[t_1.name].start, 74)

        # expected cost should be 3374
        expected_cost = int(((int_cost_function(74) + int_cost_function(87)) * 13) / 2)
        self.assertEqual(solution.indicators[cost_ind.name], expected_cost)

    def test_optimize_linear_cost_3(self) -> None:
        # same cost function as above, we minimize the cst,
        # the task should be scheduled at 0 (because the cost function increases)
        problem = ps.SchedulingProblem("OptimizeLinearCost3")

        t_1 = ps.FixedDurationTask("t1", duration=17)

        def real_cost_function(t):
            return 23.112 * t + 3.5

        worker_1 = ps.Worker(
            "Worker1", cost=ps.PolynomialCostFunction(real_cost_function)
        )
        t_1.add_required_resource(worker_1)

        cost_ind = problem.add_indicator_resource_cost([worker_1])
        problem.add_objective_resource_cost([worker_1])

        solution = ps.SchedulingSolver(problem).solve()

        self.assertTrue(solution)
        # the task is scheduled at the beginning of the workplan
        self.assertEqual(solution.tasks[t_1.name].start, 0)
        # expected cost should be 3374
        expected_cost = ((real_cost_function(0) + real_cost_function(17)) * 17) / 2
        # Because there are Int type conversions, the result may not be exactly
        # the one expected, let's assume 99% is a good approx.
        err = abs(solution.indicators[cost_ind.name] / expected_cost - 1)
        self.assertLessEqual(err, 0.01)

    def test_quadratic_cost_1(self) -> None:
        problem = ps.SchedulingProblem("IndicatorResourceQuadraticCost1")

        t_1 = ps.FixedDurationTask("t1", duration=17)

        def int_cost_function(t):
            return 23 * t ** 2 - 13 * t + 513

        worker_1 = ps.Worker(
            "Worker1", cost=ps.PolynomialCostFunction(int_cost_function)
        )
        t_1.add_required_resource(worker_1)

        problem.add_constraint(ps.TaskStartAt(t_1, 13))
        cost_ind = problem.add_indicator_resource_cost([worker_1])

        solution = ps.SchedulingSolver(problem).solve()

        self.assertTrue(solution)
        # expected cost should be 8457
        expected_cost = int(
            ((int_cost_function(13) + int_cost_function(13 + 17)) * 17) / 2
        )
        self.assertEqual(solution.indicators[cost_ind.name], expected_cost)

    def test_optimize_quadratic_cost_2(self) -> None:
        # TODO: add an horizon, it should return the expected result
        # but there's an issue, see
        # https://github.com/Z3Prover/z3/issues/5254
        problem = ps.SchedulingProblem("OptimizeQuadraticCost2", horizon=20)

        t_1 = ps.FixedDurationTask("t1", duration=4)

        # we chosse a function where we know the minimum is
        # let's imagine the minimum is at t=37
        def int_cost_function(t):
            return (t - 8) ** 2 + 100

        worker_1 = ps.Worker(
            "Worker1", cost=ps.PolynomialCostFunction(int_cost_function)
        )
        t_1.add_required_resource(worker_1)

        cost_ind = problem.add_indicator_resource_cost([worker_1])
        problem.minimize_indicator(cost_ind)

        solution = ps.SchedulingSolver(problem).solve()

        self.assertTrue(solution)
        # TODO: to be fixed; Non linear solver gives weirf results.
        # This was repored to z3 team see
        # https://github.com/Z3Prover/z3/issues/5254
        # Fix to be released in the next z3 version 4.8.11.0
        # sometimes it's 6, sometime it's 7 TODO weird
        # self.assertTrue(solution.tasks[t_1.name].start in [6, 7])

        # sometimes it's 416, sometimes 420 TODO
        # self.assertTrue(solution.indicators[cost_ind.name] in [416, 420])

    def test_plot_cost_function(self) -> None:
        # TODO: add an horizon, it should return the expected result
        # but there's an issue, see
        # https://github.com/Z3Prover/z3/issues/5254

        # we chosse a function where we know the minimum is
        # let's imagine the minimum is at t=37
        def int_cost_function(t):
            return (t - 37) ** 2 + 513

        cost = ps.PolynomialCostFunction(int_cost_function)

        cost.plot([0, 40], show_plot=False)

    def test_cumulative_cost(self):
        problem = ps.SchedulingProblem("CumulativeCost", horizon=5)
        t_1 = ps.FixedDurationTask("t1", duration=5)
        t_2 = ps.FixedDurationTask("t2", duration=5)
        t_3 = ps.FixedDurationTask("t3", duration=5)
        worker_1 = ps.CumulativeWorker(
            "CumulWorker", size=3, cost=ps.ConstantCostPerPeriod(5)
        )
        t_1.add_required_resource(worker_1)
        t_2.add_required_resource(worker_1)
        t_3.add_required_resource(worker_1)

        cost_ind = problem.add_indicator_resource_cost([worker_1])

        solution = ps.SchedulingSolver(problem).solve()

        self.assertTrue(solution)
        self.assertEqual(solution.indicators[cost_ind.name], 25)
        solution = ps.SchedulingSolver(problem).solve()
        self.assertTrue(solution)

    def test_incremental_optimizer_linear_cost_1(self) -> None:
        # same cost function as above, we minimize the cst,
        # the task should be scheduled at 0 (because the cost function increases)
        problem = ps.SchedulingProblem("IncrementalOptimizerLinearCost1", horizon=40)

        t_1 = ps.FixedDurationTask("t1", duration=17)

        # the task should be scheduled at the end
        def int_cost_function(t):
            return -23 * t + 321

        worker_1 = ps.Worker(
            "Worker1", cost=ps.PolynomialCostFunction(int_cost_function)
        )
        t_1.add_required_resource(worker_1)

        cost_ind = problem.add_indicator_resource_cost([worker_1])
        problem.minimize_indicator(cost_ind)

        solver = ps.SchedulingSolver(problem, random_values=True)

        solution = solver.solve()

        self.assertTrue(solution)
        self.assertEqual(solution.tasks[t_1.name].start, 23)


if __name__ == "__main__":
    unittest.main()
