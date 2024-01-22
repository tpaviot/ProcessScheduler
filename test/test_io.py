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

import os

import processscheduler as ps


def build_excavator_problem() -> ps.SchedulingProblem:
    """returns a problem with n tasks and n * 3 workers"""
    problem = ps.SchedulingProblem(name="Excavators")

    # three tasks
    dig_small_hole = ps.VariableDurationTask(name="DigSmallHole", work_amount=3)
    dig_medium_hole = ps.VariableDurationTask(name="DigMediumHole", work_amount=7)
    dig_huge_hole = ps.VariableDurationTask(name="DigHugeHole", work_amount=15)
    # medium_exc_cost = ps.PolynomialFunction(cost_function=cost_function_medium_exc)

    # two workers
    small_exc = ps.Worker(
        name="SmallExcavator", productivity=4, cost=ps.ConstantFunction(value=5)
    )
    medium_ex = ps.Worker(
        name="MediumExcavator", productivity=6, cost=ps.ConstantFunction(value=10)
    )

    dig_small_hole.add_required_resource(
        ps.SelectWorkers(
            list_of_workers=[small_exc, medium_ex], nb_workers_to_select=1, kind="min"
        )
    )
    dig_medium_hole.add_required_resource(
        ps.SelectWorkers(
            list_of_workers=[small_exc, medium_ex], nb_workers_to_select=1, kind="min"
        )
    )
    dig_huge_hole.add_required_resource(
        ps.SelectWorkers(
            list_of_workers=[small_exc, medium_ex], nb_workers_to_select=1, kind="min"
        )
    )

    # problem.add_objective_makespan() ## ERROR Serialization

    # problem.add_indicator_resource_cost([small_exc, medium_ex])

    return problem


PROBLEM = build_excavator_problem()
SOLVER = ps.SchedulingSolver(problem=PROBLEM)
SOLUTION = SOLVER.solve()


def test_export_to_smt2():
    SOLVER.export_to_smt2("excavator_problem.smt2")
    assert os.path.isfile("excavator_problem.smt2")


def test_export_problem_to_json():
    PROBLEM.to_json()


def test_export_problem_to_json_file():
    PROBLEM.to_json_file("excavator_problem.json")
    assert os.path.isfile("excavator_problem.json")


def test_export_solution_to_json():
    SOLUTION.to_json()


def test_export_solution_to_json_file():
    SOLUTION.to_json_file("excavator_solution.json")
    assert os.path.isfile("excavator_solution.json")


def test_export_solution_to_excel_file():
    SOLUTION.to_excel_file("excavator_nb.xlsx")
    assert os.path.isfile("excavator_nb.xlsx")
    SOLUTION.to_excel_file("excavator_colors.xlsx", colors=True)
    assert os.path.isfile("excavator_colors.xlsx")


def test_export_solution_to_pandas_dataframe():
    SOLUTION.to_df()


def test_print_solution_as_pandas_dataframe():
    print(SOLUTION)
