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
import unittest

import processscheduler as ps


def build_excavator_problem() -> ps.SchedulingProblem:
    """returns a problem with n tasks and n * 3 workers"""
    problem = ps.SchedulingProblem("Excavators")

    # three tasks
    dig_small_hole = ps.VariableDurationTask("DigSmallHole", work_amount=3)
    dig_medium_hole = ps.VariableDurationTask("DigMediumHole", work_amount=7)
    dig_huge_hole = ps.VariableDurationTask("DigHugeHole", work_amount=15)

    # cost function for the small excavator is linear
    def cost_function_small_exc(t):
        """Linear cost function"""
        return 10 * t + 20

    small_exc_cost = ps.PolynomialCostFunction(cost_function_small_exc)

    # cost function for the medium excavator is quadratic, max at the middle
    def cost_function_medium_exc(t):
        """Quadratic cost function"""
        return 400 - (t - 20) * (t - 20)

    medium_exc_cost = ps.PolynomialCostFunction(cost_function_medium_exc)

    # two workers
    small_exc = ps.Worker(
        "SmallExcavator", productivity=4, cost=ps.ConstantCostPerPeriod(5)
    )
    medium_ex = ps.Worker(
        "MediumExcavator", productivity=6, cost=ps.ConstantCostPerPeriod(10)
    )

    dig_small_hole.add_required_resource(
        ps.SelectWorkers([small_exc, medium_ex], 1, kind="min")
    )
    dig_medium_hole.add_required_resource(
        ps.SelectWorkers([small_exc, medium_ex], 1, kind="min")
    )
    dig_huge_hole.add_required_resource(
        ps.SelectWorkers([small_exc, medium_ex], 1, kind="min")
    )

    problem.add_objective_makespan()

    problem.add_indicator_resource_cost([small_exc, medium_ex])

    return problem


PROBLEM = build_excavator_problem()
SOLVER = ps.SchedulingSolver(PROBLEM)
SOLUTION = SOLVER.solve()

if not SOLUTION:
    raise AssertionError("problem has no solution")


class TestIO(unittest.TestCase):
    def test_export_to_smt2(self):
        SOLVER.export_to_smt2("excavator_problem.smt2")
        self.assertTrue(os.path.isfile("excavator_problem.smt2"))

    def test_export_solution_to_json_string(self):
        self.assertTrue(SOLUTION)
        SOLUTION.to_json_string()

    def test_export_solution_to_json_file(self):
        self.assertTrue(SOLUTION)
        SOLUTION.export_to_json_file("excavator_solution.json")
        self.assertTrue(os.path.isfile("excavator_solution.json"))

    def test_export_solution_to_excel_file(self):
        self.assertTrue(SOLUTION)
        SOLUTION.export_to_excel_file("excavator_nb.xlsx")
        self.assertTrue(os.path.isfile("excavator_nb.xlsx"))
        SOLUTION.export_to_excel_file("excavator_colors.xlsx", colors=True)
        self.assertTrue(os.path.isfile("excavator_colors.xlsx"))


if __name__ == "__main__":
    unittest.main()
