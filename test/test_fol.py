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


class TestFirstOrderLogic(unittest.TestCase):
    #
    # Boolean operators
    #
    def test_operator_not_1(self) -> None:
        pb = ps.SchedulingProblem("OperatorNot1", horizon=3)
        t_1 = ps.FixedDurationTask("t1", duration=2)
        not_constraint = ps.not_(ps.TaskStartAt(t_1, 0))
        self.assertIsInstance(not_constraint, ps.BoolRef)

        pb.add_constraint(not_constraint)
        solution = ps.SchedulingSolver(pb).solve()

        self.assertTrue(solution)
        self.assertEqual(solution.tasks["t1"].start, 1)

    def test_operator_or_1(self) -> None:
        pb = ps.SchedulingProblem("OperatorOr1", horizon=8)
        t_1 = ps.FixedDurationTask("t1", duration=2)

        or_constraint = ps.or_([ps.TaskStartAt(t_1, 3), ps.TaskStartAt(t_1, 6)])
        self.assertIsInstance(or_constraint, ps.BoolRef)

        pb.add_constraint(or_constraint)
        solution = ps.SchedulingSolver(pb).solve()

        self.assertTrue(solution)
        self.assertTrue(solution.tasks["t1"].start in [3, 6])

    def test_operator_or_2(self) -> None:
        pb = ps.SchedulingProblem("OperatorOr2", horizon=2)
        t_1 = ps.FixedDurationTask("t1", duration=2)
        t_2 = ps.FixedDurationTask("t2", duration=2)

        or_constraint = ps.or_([ps.TaskStartAt(t_1, 0), ps.TaskStartAt(t_2, 0)])
        self.assertIsInstance(or_constraint, ps.BoolRef)

        pb.add_constraint(or_constraint)
        solution = ps.SchedulingSolver(pb).solve()

        self.assertTrue(solution)
        self.assertEqual(solution.tasks["t1"].start, 0)
        self.assertEqual(solution.tasks["t2"].start, 0)

    def test_operator_xor_1(self) -> None:
        # same as OperatorOr2 but with an exlusive or, there
        # is no solution
        pb = ps.SchedulingProblem("OperatorXor1", horizon=2)
        t_1 = ps.FixedDurationTask("t1", duration=2)
        t_2 = ps.FixedDurationTask("t2", duration=2)

        xor_constraint = ps.xor_([ps.TaskStartAt(t_1, 0), ps.TaskStartAt(t_2, 0)])
        self.assertIsInstance(xor_constraint, ps.BoolRef)

        pb.add_constraint(xor_constraint)
        solution = ps.SchedulingSolver(pb).solve()

        self.assertFalse(solution)

    def test_operator_xor_2(self) -> None:
        # same as OperatorXOr1 but with a larger horizon
        # then there should be a solution
        pb = ps.SchedulingProblem("OperatorXor2", horizon=3)
        t_1 = ps.FixedDurationTask("t1", duration=2)
        t_2 = ps.FixedDurationTask("t2", duration=2)

        xor_constraint = ps.xor_([ps.TaskStartAt(t_1, 0), ps.TaskStartAt(t_2, 0)])
        self.assertIsInstance(xor_constraint, ps.BoolRef)

        pb.add_constraint(xor_constraint)
        solution = ps.SchedulingSolver(pb).solve()

        self.assertTrue(solution)
        self.assertTrue(solution.tasks["t1"].start != solution.tasks["t2"].start)
        self.assertTrue(
            solution.tasks["t1"].start == 0 or solution.tasks["t2"].start == 0
        )

    def test_operator_and_1(self) -> None:
        pb = ps.SchedulingProblem("OperatorAnd1", horizon=23)
        t_1 = ps.FixedDurationTask("t1", duration=2)
        and_constraint = ps.and_(
            [ps.TaskStartAfterLax(t_1, 3), ps.TaskEndBeforeLax(t_1, 5)]
        )
        self.assertIsInstance(and_constraint, ps.BoolRef)
        pb.add_constraint(and_constraint)
        solution = ps.SchedulingSolver(pb).solve()

        self.assertTrue(solution)
        self.assertEqual(solution.tasks["t1"].start, 3)

    def test_nested_boolean_operators_1(self) -> None:
        pb = ps.SchedulingProblem("NestedBooleanOperators1", horizon=37)
        t_1 = ps.FixedDurationTask("t1", duration=2)
        t_2 = ps.FixedDurationTask("t2", duration=2)
        or_constraint_1 = ps.or_([ps.TaskStartAt(t_1, 10), ps.TaskStartAt(t_1, 12)])
        or_constraint_2 = ps.or_([ps.TaskStartAt(t_2, 14), ps.TaskStartAt(t_2, 15)])
        and_constraint = ps.and_([or_constraint_1, or_constraint_2])

        pb.add_constraint(and_constraint)
        solution = ps.SchedulingSolver(pb).solve()

        self.assertTrue(solution)
        self.assertTrue(solution.tasks["t1"].start in [10, 12])
        self.assertTrue(solution.tasks["t2"].start in [14, 15])

    #
    # Implies
    #
    def test_implies(self) -> None:
        pb = ps.SchedulingProblem("Implies1", horizon=37)
        t_1 = ps.FixedDurationTask("t1", 2)
        t_2 = ps.FixedDurationTask("t2", 4)
        t_3 = ps.FixedDurationTask("t3", 7)

        # force task t_1 to start at 1
        ps.TaskStartAt(t_1, 1)
        implies_constraint = ps.implies(
            t_1.start == 1, [ps.TaskStartAt(t_2, 3), ps.TaskStartAt(t_3, 17)]
        )
        self.assertIsInstance(implies_constraint, ps.BoolRef)

        pb.add_constraint(implies_constraint)
        solution = ps.SchedulingSolver(pb).solve()

        self.assertTrue(solution)
        self.assertEqual(solution.tasks["t1"].start, 1)
        self.assertEqual(solution.tasks["t2"].start, 3)
        self.assertEqual(solution.tasks["t3"].start, 17)

    #
    # If/Then/Else
    #
    def test_if_then_else(self) -> None:
        pb = ps.SchedulingProblem("IfThenElse1", horizon=29)
        t_1 = ps.FixedDurationTask("t1", 3)
        t_2 = ps.FixedDurationTask("t2", 3)
        ite_constraint = ps.if_then_else(
            t_1.start == 1,  # condition
            [ps.TaskStartAt(t_2, 3)],  # then
            [ps.TaskStartAt(t_2, 6)],  # else
        )
        self.assertIsInstance(ite_constraint, ps.BoolRef)

        # force task t_1 to start at 2
        ps.TaskStartAt(t_1, 2)

        pb.add_constraint(ite_constraint)
        solution = ps.SchedulingSolver(pb).solve()

        self.assertTrue(solution)
        self.assertEqual(solution.tasks["t1"].start, 2)
        self.assertEqual(solution.tasks["t2"].start, 6)


if __name__ == "__main__":
    unittest.main()
