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


import processscheduler as ps

from pydantic import ValidationError

import pytest


def test_cost_basic() -> None:
    ps.SchedulingProblem(name="CostBasic", horizon=12)
    ress_cost = ps.ConstantCostPerPeriod(value=5)
    ps.Worker(name="Worker1", cost=ress_cost)


def test_cost_polynomial_1() -> None:
    ps.SchedulingProblem(name="PolynomialCost1", horizon=12)

    def c(t):
        return 0.5 * t * t + 50

    ress_cost = ps.PolynomialCostFunction(cost_function=c)
    ps.Worker(name="Worker1", cost=ress_cost)


def test_cost_polynomial_lambda() -> None:
    ps.SchedulingProblem(name="PolynomialCostLambdaFunction", horizon=12)
    ress_cost = ps.PolynomialCostFunction(cost_function=lambda t: 2 * t + 10)
    ps.Worker(name="Worker1", cost=ress_cost)


def test_cost_failure() -> None:
    ps.SchedulingProblem(name="CostWrongType", horizon=12)
    with pytest.raises(ValidationError):
        ps.Worker(name="ress1", cost=5)  # only accepts a Cost instance
    with pytest.raises(ValidationError):
        ps.PolynomialCostFunction(cost_function="f")  # only accepts a callable


def test_constant_cost_per_period_0() -> None:
    ps.SchedulingProblem(name="IndicatorResourceConstantCostPerPeriod0")
    c = ps.ConstantCostPerPeriod(value=7)
    assert c(1) == 7
    assert c(10) == 7
    assert c(0) == 7


def test_constant_cost_per_period_1() -> None:
    problem = ps.SchedulingProblem(name="IndicatorResourceConstantCostPerPeriod1")
    t_1 = ps.FixedDurationTask(name="t1", duration=11)
    worker_1 = ps.Worker(name="Worker1", cost=ps.ConstantCostPerPeriod(value=7))
    t_1.add_required_resource(worker_1)
    cost_ind = problem.add_indicator_resource_cost([worker_1])

    solution = ps.SchedulingSolver(problem=problem).solve()

    assert solution
    assert solution.indicators[cost_ind.name] == 77


def test_constant_cost_per_period_2() -> None:
    problem = ps.SchedulingProblem(name="IndicatorResourceConstantCostPerPeriod2")
    t_1 = ps.VariableDurationTask(name="t1", work_amount=100)
    worker_1 = ps.Worker(
        name="Worker1", productivity=4, cost=ps.ConstantCostPerPeriod(value=10)
    )
    worker_2 = ps.Worker(
        name="Worker2", productivity=7, cost=ps.ConstantCostPerPeriod(value=20)
    )
    all_workers = [worker_1, worker_2]
    problem.add_objective_makespan()
    t_1.add_required_resources(all_workers)
    cost_ind = problem.add_indicator_resource_cost(all_workers)

    solution = ps.SchedulingSolver(problem=problem).solve()

    assert solution
    assert solution.indicators[cost_ind.name] == 300


def test_linear_cost_1() -> None:
    problem = ps.SchedulingProblem(name="IndicatorResourcePolynomialCost1")

    t_1 = ps.FixedDurationTask(name="t1", duration=17)

    def int_cost_function(t):
        return 23 * t + 3

    worker_1 = ps.Worker(
        name="Worker1",
        cost=ps.PolynomialCostFunction(cost_function=int_cost_function),
    )
    t_1.add_required_resource(worker_1)

    ps.TaskStartAt(task=t_1, value=13)
    cost_ind = problem.add_indicator_resource_cost([worker_1])

    solution = ps.SchedulingSolver(problem=problem).solve()

    assert solution
    # expected cost should be 8457
    expected_cost = int(((int_cost_function(13) + int_cost_function(13 + 17)) * 17) / 2)
    assert solution.indicators[cost_ind.name] == expected_cost


def test_optimize_linear_cost_1() -> None:
    # same cost function as above, we minimize the cst,
    # the task should be scheduled at 0 (because the cost function increases)
    problem = ps.SchedulingProblem(name="OptimizeLinearCost1")

    t_1 = ps.FixedDurationTask(name="t1", duration=17)

    def int_cost_function(t):
        return 23 * t + 3

    worker_1 = ps.Worker(
        name="Worker1",
        cost=ps.PolynomialCostFunction(cost_function=int_cost_function),
    )
    t_1.add_required_resource(worker_1)

    cost_ind = problem.add_indicator_resource_cost([worker_1])
    problem.add_objective_resource_cost([worker_1])

    solution = ps.SchedulingSolver(problem=problem).solve()

    assert solution
    # the task is scheduled at the beginning of the workplan
    assert solution.tasks[t_1.name].start == 0
    # expected cost should be 3374
    expected_cost = int(((int_cost_function(0) + int_cost_function(17)) * 17) / 2)
    assert solution.indicators[cost_ind.name] == expected_cost


def test_optimize_linear_cost_2() -> None:
    # now we have a cost function that decreases over time,
    # then minimizing the cost should schedule the task at the end.
    # so we define an horizon for the problem
    problem = ps.SchedulingProblem(name="OptimizeLinear2", horizon=87)

    t_1 = ps.FixedDurationTask(name="t1", duration=13)

    # be sure however that this function is positive on the interval
    def int_cost_function(t):
        return 711 - 5 * t

    worker_1 = ps.Worker(
        name="Worker1",
        cost=ps.PolynomialCostFunction(cost_function=int_cost_function),
    )
    t_1.add_required_resource(worker_1)

    cost_ind = problem.add_indicator_resource_cost([worker_1])
    problem.add_objective_resource_cost([worker_1])

    solution = ps.SchedulingSolver(problem=problem).solve()

    assert solution
    # the task is scheduled at the beginning of the workplan
    assert solution.tasks[t_1.name].start == 74

    # expected cost should be 3374
    expected_cost = int(((int_cost_function(74) + int_cost_function(87)) * 13) / 2)
    assert solution.indicators[cost_ind.name] == expected_cost


# def test_optimize_linear_cost_3()  -> None:
#     # if the cost function involves float numbers, this will
#     # result in a ToReal conversion of z3 interger variables,
#     # and may lead to unepexted behaviours
#     problem = ps.SchedulingProblem(name="OptimizeLinearCost3")

#     t_1 = ps.FixedDurationTask(name="t1", duration=17)

#     def real_cost_function(t):
#         return 23.12 * t + 3.4

#     worker_1 = ps.Worker(
#         name="Worker1",
#         cost=ps.PolynomialCostFunction(cost_function=real_cost_function),
#     )
#     t_1.add_required_resource(worker_1)

#     with pytest.raises(AssertionError):
#         cost_ind = problem.add_indicator_resource_cost([worker_1])


def test_quadratic_cost_1() -> None:
    problem = ps.SchedulingProblem(name="IndicatorResourceQuadraticCost1")

    t_1 = ps.FixedDurationTask(name="t1", duration=17)

    def int_cost_function(t):
        return 23 * t * t - 13 * t + 513

    worker_1 = ps.Worker(
        name="Worker1",
        cost=ps.PolynomialCostFunction(cost_function=int_cost_function),
    )
    t_1.add_required_resource(worker_1)

    ps.TaskStartAt(task=t_1, value=13)
    cost_ind = problem.add_indicator_resource_cost([worker_1])

    solution = ps.SchedulingSolver(problem=problem).solve()

    assert solution
    # expected cost should be 8457
    expected_cost = int(((int_cost_function(13) + int_cost_function(13 + 17)) * 17) / 2)
    assert solution.indicators[cost_ind.name] == expected_cost


def test_optimize_quadratic_cost_2() -> None:
    # TODO: add an horizon, it should return the expected result
    # but there's an issue, see
    # https://github.com/Z3Prover/z3/issues/5254
    problem = ps.SchedulingProblem(name="OptimizeQuadraticCost2", horizon=20)

    t_1 = ps.FixedDurationTask(name="t1", duration=4)

    # we chosse a function where we know the minimum is
    # let's imagine the minimum is at t=8
    def int_cost_function(t):
        return (t - 8) * (t - 8) + 100

    worker_1 = ps.Worker(
        name="Worker1",
        cost=ps.PolynomialCostFunction(cost_function=int_cost_function),
    )
    t_1.add_required_resource(worker_1)

    cost_ind = problem.add_indicator_resource_cost([worker_1])
    problem.minimize_indicator(cost_ind)

    solution = ps.SchedulingSolver(problem=problem).solve()

    assert solution
    assert solution.tasks[t_1.name].start == 6
    assert solution.indicators[cost_ind.name] == 416


def test_plot_cost_function() -> None:
    def int_cost_function(t):
        return (t - 8) * (t - 8) + 513

    cost = ps.PolynomialCostFunction(cost_function=int_cost_function)

    cost.plot([0, 40], show_plot=False)


def test_cumulative_cost():
    problem = ps.SchedulingProblem(name="CumulativeCost", horizon=5)
    t_1 = ps.FixedDurationTask(name="t1", duration=5)
    t_2 = ps.FixedDurationTask(name="t2", duration=5)
    t_3 = ps.FixedDurationTask(name="t3", duration=5)
    worker_1 = ps.CumulativeWorker(
        name="CumulWorker", size=3, cost=ps.ConstantCostPerPeriod(value=5)
    )
    t_1.add_required_resource(worker_1)
    t_2.add_required_resource(worker_1)
    t_3.add_required_resource(worker_1)

    cost_ind = problem.add_indicator_resource_cost([worker_1])

    solution = ps.SchedulingSolver(problem=problem).solve()

    assert solution
    assert solution.indicators[cost_ind.name] == 25
    solution = ps.SchedulingSolver(problem=problem).solve()
    assert solution


def test_incremental_optimizer_linear_cost_1() -> None:
    # same cost function as above, we minimize the cst,
    # the task should be scheduled at 0 (because the cost function increases)
    problem = ps.SchedulingProblem(name="IncrementalOptimizerLinearCost1", horizon=40)

    t_1 = ps.FixedDurationTask(name="t1", duration=17)

    # the task should be scheduled at the end
    def int_cost_function(t):
        return -23 * t + 321

    worker_1 = ps.Worker(
        name="Worker1",
        cost=ps.PolynomialCostFunction(cost_function=int_cost_function),
    )
    t_1.add_required_resource(worker_1)

    cost_ind = problem.add_indicator_resource_cost([worker_1])
    problem.minimize_indicator(cost_ind)

    solver = ps.SchedulingSolver(problem=problem, random_values=True)

    solution = solver.solve()

    assert solution
    assert solution.tasks[t_1.name].start == 23
