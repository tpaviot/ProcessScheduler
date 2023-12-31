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

# def test_general_cost_function_1() -> None:
#     def my_function(t):
#         return 0.5 * t * t + 50

#     c = ps.GeneralCostFunction(func=my_function)
#     assert c(0) == 50
#     assert c(2) == 52


def test_worker_cost_const() -> None:
    ps.SchedulingProblem(name="CostBasic", horizon=12)
    ress_cost = ps.ConstantFunction(value=5)
    ps.Worker(name="Worker1", cost=ress_cost)


# def test_general_cost_lambda() -> None:
#     ps.SchedulingProblem(name="PolynomialCostLambdaFunction", horizon=12)
#     ress_cost = ps.GeneralCostFunction(func=lambda t: 2 * t + 10)
#     assert ress_cost(-5) == 0
#     assert ress_cost(10) == 30

#     ps.Worker(name="Worker1", cost=ress_cost)


def test_constant_cost_per_period_1() -> None:
    problem = ps.SchedulingProblem(name="IndicatorResourceConstantCostPerPeriod1")
    t_1 = ps.FixedDurationTask(name="t1", duration=11)
    worker_1 = ps.Worker(name="Worker1", cost=ps.ConstantFunction(value=7))
    t_1.add_required_resource(worker_1)
    cost_ind = ps.IndicatorResourceCost(list_of_resources=[worker_1])

    solution = ps.SchedulingSolver(problem=problem).solve()

    assert solution
    assert solution.indicators[cost_ind.name] == 77


def test_constant_cost_per_period_2() -> None:
    problem = ps.SchedulingProblem(name="IndicatorResourceConstantCostPerPeriod2")
    t_1 = ps.VariableDurationTask(name="t1", work_amount=100)
    worker_1 = ps.Worker(
        name="Worker1", productivity=4, cost=ps.ConstantFunction(value=10)
    )
    worker_2 = ps.Worker(
        name="Worker2", productivity=7, cost=ps.ConstantFunction(value=20)
    )
    all_workers = [worker_1, worker_2]

    t_1.add_required_resources(all_workers)

    cost_ind = ps.IndicatorResourceCost(list_of_resources=all_workers)

    ps.ObjectiveMinimizeMakespan()

    solution = ps.SchedulingSolver(problem=problem).solve()

    assert solution
    assert solution.indicators[cost_ind.name] == 300


def test_linear_cost_1() -> None:
    problem = ps.SchedulingProblem(name="IndicatorResourcePolynomialCost1")

    t_1 = ps.FixedDurationTask(name="t1", duration=17)

    worker_1 = ps.Worker(
        name="Worker1",
        cost=ps.LinearFunction(slope=23, intercept=3),
    )
    t_1.add_required_resource(worker_1)

    ps.TaskStartAt(task=t_1, value=13)
    cost_ind = ps.IndicatorResourceCost(list_of_resources=[worker_1])

    solution = ps.SchedulingSolver(problem=problem).solve()

    assert solution

    # expected cost should be 8457
    def int_cost_function(t):
        return 23 * t + 3

    expected_cost = int(((int_cost_function(13) + int_cost_function(13 + 17)) * 17) / 2)
    assert solution.indicators[cost_ind.name] == expected_cost


def test_optimize_linear_cost_1() -> None:
    # same cost function as above, we minimize the cst,
    # the task should be scheduled at 0 (because the cost function increases)
    problem = ps.SchedulingProblem(name="OptimizeLinearCost1")

    t_1 = ps.FixedDurationTask(name="t1", duration=17)

    worker_1 = ps.Worker(
        name="Worker1",
        cost=ps.LinearFunction(slope=23, intercept=3),
    )
    t_1.add_required_resource(worker_1)

    cost_ind = ps.IndicatorResourceCost(list_of_resources=[worker_1])

    ps.ObjectiveMinimizeResourceCost(list_of_resources=[worker_1])

    solution = ps.SchedulingSolver(problem=problem).solve()

    assert solution
    # the task is scheduled at the beginning of the workplan
    assert solution.tasks[t_1.name].start == 0

    # expected cost should be 3374
    def int_cost_function(t):
        return 23 * t + 3

    expected_cost = int(((int_cost_function(0) + int_cost_function(17)) * 17) / 2)
    assert solution.indicators[cost_ind.name] == expected_cost


def test_optimize_linear_cost_2() -> None:
    # now we have a cost function that decreases over time,
    # then minimizing the cost should schedule the task at the end.
    # so we define an horizon for the problem
    problem = ps.SchedulingProblem(name="OptimizeLinear2", horizon=87)

    t_1 = ps.FixedDurationTask(name="t1", duration=13)

    worker_1 = ps.Worker(
        name="Worker1",
        cost=ps.LinearFunction(slope=-5, intercept=711),
    )
    t_1.add_required_resource(worker_1)

    cost_ind = ps.IndicatorResourceCost(list_of_resources=[worker_1])

    ps.ObjectiveMinimizeResourceCost(list_of_resources=[worker_1])

    solution = ps.SchedulingSolver(problem=problem).solve()

    assert solution
    # the task is scheduled at the beginning of the workplan
    assert solution.tasks[t_1.name].start == 74

    # expected cost should be 3374
    def int_cost_function(t):
        return 711 - 5 * t

    expected_cost = int(((int_cost_function(74) + int_cost_function(87)) * 13) / 2)
    assert solution.indicators[cost_ind.name] == expected_cost


def test_optimize_linear_cost_3() -> None:
    # if the cost function involves float numbers, this will
    # result in a ToReal conversion of z3 integer variables,
    # and may lead to unepexted behaviours
    problem = ps.SchedulingProblem(name="OptimizeLinearCost3")

    t_1 = ps.FixedDurationTask(name="t1", duration=17)

    cf = ps.LinearFunction(slope=23.12, intercept=3.4)

    worker_1 = ps.Worker(name="Worker1", cost=cf)
    t_1.add_required_resource(worker_1)

    # because float parameters, should use ToReal conversion
    # and a warning emitted
    # TODO: wait for the next z3 release, otherwise no warning is emitted
    # with pytest.warns(UserWarning):
    #    cost_ind = ps.IndicatorResourceCost(list_of_resources=[worker_1])
    cost_ind = ps.IndicatorResourceCost(list_of_resources=[worker_1])


def test_quadratic_cost_1() -> None:
    problem = ps.SchedulingProblem(name="IndicatorResourceQuadraticCost1")

    t_1 = ps.FixedDurationTask(name="t1", duration=17)

    worker_1 = ps.Worker(
        name="Worker1",
        cost=ps.PolynomialFunction(coefficients=[23, 13, 513]),
    )
    t_1.add_required_resource(worker_1)

    ps.TaskStartAt(task=t_1, value=13)
    cost_ind = ps.IndicatorResourceCost(list_of_resources=[worker_1])

    solution = ps.SchedulingSolver(problem=problem).solve()

    assert solution

    # expected cost should be 8457
    def int_cost_function(t):
        return 23 * t * t - 13 * t + 513

    expected_cost = int(((int_cost_function(13) + int_cost_function(13 + 17)) * 17) / 2)
    # TODO: assert solution.indicators[cost_ind.name] == expected_cost
    # E       assert 222462 == 212959
    # test_cost.py:254: AssertionError


def test_optimize_quadratic_cost_2() -> None:
    # TODO: add an horizon, it should return the expected result
    # but there's an issue, see
    # https://github.com/Z3Prover/z3/issues/5254
    problem = ps.SchedulingProblem(name="OptimizeQuadraticCost2", horizon=20)

    t_1 = ps.FixedDurationTask(name="t1", duration=4)
    # let's imagine the minimum is at t=8
    # cost_function(t)= (t - 8) * (t - 8) + 100

    worker_1 = ps.Worker(
        name="Worker1", cost=ps.PolynomialFunction(coefficients=[1, -16, 164])
    )
    t_1.add_required_resource(worker_1)

    cost_ind = ps.IndicatorResourceCost(list_of_resources=[worker_1])
    ps.Objective(name="MinimizeQuadraticCost2", target=cost_ind, kind="minimize")
    solution = ps.SchedulingSolver(problem=problem).solve()

    assert solution
    assert solution.tasks[t_1.name].start == 6
    assert solution.indicators[cost_ind.name] == 416


# def test_plot_cost_function() -> None:
#     def int_cost_function(t):
#         return (t - 8) * (t - 8) + 513

#     cost = ps.PolynomialFunction(cost_function=int_cost_function)

#     cost.plot([0, 40], show_plot=False)


def test_cumulative_cost():
    problem = ps.SchedulingProblem(name="CumulativeCost", horizon=5)
    t_1 = ps.FixedDurationTask(name="t1", duration=5)
    t_2 = ps.FixedDurationTask(name="t2", duration=5)
    t_3 = ps.FixedDurationTask(name="t3", duration=5)
    worker_1 = ps.CumulativeWorker(
        name="CumulWorker", size=3, cost=ps.ConstantFunction(value=5)
    )
    t_1.add_required_resource(worker_1)
    t_2.add_required_resource(worker_1)
    t_3.add_required_resource(worker_1)

    cost_ind = ps.IndicatorResourceCost(list_of_resources=[worker_1])

    solution = ps.SchedulingSolver(problem=problem).solve()

    assert solution
    assert solution.indicators[cost_ind.name] == 25


def test_incremental_optimizer_linear_cost_1() -> None:
    # same cost function as above, we minimize the cst,
    # the task should be scheduled at 0 (because the cost function increases)
    problem = ps.SchedulingProblem(name="IncrementalOptimizerLinearCost1", horizon=40)

    t_1 = ps.FixedDurationTask(name="t1", duration=17)

    # the task should be scheduled at the end

    worker_1 = ps.Worker(
        name="Worker1",
        cost=ps.LinearFunction(slope=-23, intercept=321),
    )
    t_1.add_required_resource(worker_1)

    cost_ind = ps.IndicatorResourceCost(list_of_resources=[worker_1])

    ps.Objective(
        name="MinimizeIncrementalOptimizerLinearCost1", target=cost_ind, kind="minimize"
    )

    solver = ps.SchedulingSolver(problem=problem, random_values=True)

    solution = solver.solve()

    assert solution
    assert solution.tasks[t_1.name].start == 23
