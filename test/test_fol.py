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
        pb = ps.SchedulingProblem(name="OperatorNot1", horizon=3)
        t_1 = ps.FixedDurationTask(name="t1", duration=2)
        not_constraint = ps.not_(ps.TaskStartAt(task=t_1, value=0))
        self.assertIsInstance(not_constraint, ps.BoolRef)

        pb.add_constraint(not_constraint)
        solution = ps.SchedulingSolver(problem=pb).solve()

        self.assertTrue(solution)
        self.assertEqual(solution.tasks["t1"].start, 1)

    def test_operator_not_2(self):
        problem = ps.SchedulingProblem(name="OperatorNot2", horizon=4)
        # only one task, the solver should schedule a start time at 0
        task_1 = ps.FixedDurationTask(name="task1", duration=2)

        not_constraint_1 = ps.not_(ps.TaskStartAt(task=task_1, value=0))
        not_constraint_2 = ps.not_(ps.TaskStartAt(task=task_1, value=1))
        problem.add_constraint(not_constraint_1)
        problem.add_constraint(not_constraint_2)
        solution = ps.SchedulingSolver(problem=problem).solve()
        self.assertTrue(solution)
        # check that the task is not scheduled to start at 0 or 1
        # the only solution is 2
        self.assertTrue(solution.tasks[task_1.name].start == 2)

    def test_operator_not_and_1(self):
        problem = ps.SchedulingProblem(name="OperatorNotAnd1", horizon=6)
        # only one task, the solver should schedule a start time at 0
        task_1 = ps.FixedDurationTask(name="task1", duration=2)
        fol_1 = ps.and_(
            [
                ps.not_(ps.TaskStartAt(task=task_1, value=0)),
                ps.not_(ps.TaskStartAt(task=task_1, value=1)),
                ps.not_(ps.TaskStartAt(task=task_1, value=2)),
                ps.not_(ps.TaskStartAt(task=task_1, value=3)),
            ]
        )
        problem.add_constraint(fol_1)
        solution = ps.SchedulingSolver(problem=problem).solve()
        self.assertTrue(solution)
        # the only solution is to start at 4
        self.assertTrue(solution.tasks[task_1.name].start == 4)

    def test_operator_or_1(self) -> None:
        pb = ps.SchedulingProblem(name="OperatorOr1", horizon=8)
        t_1 = ps.FixedDurationTask(name="t1", duration=2)

        or_constraint = ps.or_(
            [ps.TaskStartAt(task=t_1, value=3), ps.TaskStartAt(task=t_1, value=6)]
        )
        self.assertIsInstance(or_constraint, ps.BoolRef)

        pb.add_constraint(or_constraint)
        solution = ps.SchedulingSolver(problem=pb).solve()

        self.assertTrue(solution)
        self.assertTrue(solution.tasks["t1"].start in [3, 6])

    def test_operator_or_2(self) -> None:
        pb = ps.SchedulingProblem(name="OperatorOr2", horizon=2)
        t_1 = ps.FixedDurationTask(name="t1", duration=2)
        t_2 = ps.FixedDurationTask(name="t2", duration=2)

        or_constraint = ps.or_(
            [ps.TaskStartAt(task=t_1, value=0), ps.TaskStartAt(task=t_2, value=0)]
        )
        self.assertIsInstance(or_constraint, ps.BoolRef)

        pb.add_constraint(or_constraint)
        solution = ps.SchedulingSolver(problem=pb).solve()

        self.assertTrue(solution)
        self.assertEqual(solution.tasks["t1"].start, 0)
        self.assertEqual(solution.tasks["t2"].start, 0)

    def test_operator_xor_1(self) -> None:
        # same as OperatorOr2 but with an exlusive or, there
        # is no solution
        pb = ps.SchedulingProblem(name="OperatorXor1", horizon=2)
        t_1 = ps.FixedDurationTask(name="t1", duration=2)
        t_2 = ps.FixedDurationTask(name="t2", duration=2)

        xor_constraint = ps.xor_(
            [ps.TaskStartAt(task=t_1, value=0), ps.TaskStartAt(task=t_2, value=0)]
        )
        self.assertIsInstance(xor_constraint, ps.BoolRef)

        pb.add_constraint(xor_constraint)
        solution = ps.SchedulingSolver(problem=pb).solve()

        self.assertFalse(solution)

    def test_operator_xor_2(self) -> None:
        # same as OperatorXOr1 but with a larger horizon
        # then there should be a solution
        pb = ps.SchedulingProblem(name="OperatorXor2", horizon=3)
        t_1 = ps.FixedDurationTask(name="t1", duration=2)
        t_2 = ps.FixedDurationTask(name="t2", duration=2)

        xor_constraint = ps.xor_(
            [ps.TaskStartAt(task=t_1, value=0), ps.TaskStartAt(task=t_2, value=0)]
        )
        self.assertIsInstance(xor_constraint, ps.BoolRef)

        pb.add_constraint(xor_constraint)
        solution = ps.SchedulingSolver(problem=pb).solve()

        self.assertTrue(solution)
        self.assertTrue(solution.tasks["t1"].start != solution.tasks["t2"].start)
        self.assertTrue(
            solution.tasks["t1"].start == 0 or solution.tasks["t2"].start == 0
        )

    def test_operator_and_1(self) -> None:
        pb = ps.SchedulingProblem(name="OperatorAnd1", horizon=23)
        t_1 = ps.FixedDurationTask(name="t1", duration=2)
        and_constraint = ps.and_(
            [ps.TaskStartAfter(task=t_1, value=3), ps.TaskEndBefore(task=t_1, value=5)]
        )
        self.assertIsInstance(and_constraint, ps.BoolRef)
        pb.add_constraint(and_constraint)
        solution = ps.SchedulingSolver(problem=pb).solve()

        self.assertTrue(solution)
        self.assertEqual(solution.tasks["t1"].start, 3)

    def test_nested_boolean_operators_1(self) -> None:
        pb = ps.SchedulingProblem(name="NestedBooleanOperators1", horizon=37)
        t_1 = ps.FixedDurationTask(name="t1", duration=2)
        t_2 = ps.FixedDurationTask(name="t2", duration=2)
        or_constraint_1 = ps.or_(
            [ps.TaskStartAt(task=t_1, value=10), ps.TaskStartAt(task=t_1, value=12)]
        )
        or_constraint_2 = ps.or_(
            [ps.TaskStartAt(task=t_2, value=14), ps.TaskStartAt(task=t_2, value=15)]
        )
        and_constraint = ps.and_([or_constraint_1, or_constraint_2])

        pb.add_constraint(and_constraint)
        solution = ps.SchedulingSolver(problem=pb).solve()

        self.assertTrue(solution)
        self.assertTrue(solution.tasks["t1"].start in [10, 12])
        self.assertTrue(solution.tasks["t2"].start in [14, 15])

    #
    # Implies
    #
    def test_implies_1(self):
        problem = ps.SchedulingProblem(name="Implies1", horizon=6)
        # only one task, the solver should schedule a start time at 0
        task_1 = ps.FixedDurationTask(name="task1", duration=2)
        task_2 = ps.FixedDurationTask(name="task2", duration=2)
        ps.TaskStartAt(task=task_1, value=1)
        fol_1 = ps.implies(task_1._start == 1, [ps.TaskStartAt(task=task_2, value=4)])
        problem.add_constraint(fol_1)
        solution = ps.SchedulingSolver(problem=problem).solve()
        self.assertTrue(solution)
        # the only solution is to start at 2
        self.assertTrue(solution.tasks[task_1.name].start == 1)
        self.assertTrue(solution.tasks[task_2.name].start == 4)

    def test_implies_2(self) -> None:
        pb = ps.SchedulingProblem(name="Implies2", horizon=37)
        t_1 = ps.FixedDurationTask(name="t1", duration=2)
        t_2 = ps.FixedDurationTask(name="t2", duration=4)
        t_3 = ps.FixedDurationTask(name="t3", duration=7)

        # force task t_1 to start at 1
        ps.TaskStartAt(task=t_1, value=1)
        implies_constraint = ps.implies(
            t_1._start == 1,
            [ps.TaskStartAt(task=t_2, value=3), ps.TaskStartAt(task=t_3, value=17)],
        )
        self.assertIsInstance(implies_constraint, ps.BoolRef)

        pb.add_constraint(implies_constraint)
        solution = ps.SchedulingSolver(problem=pb).solve()

        self.assertTrue(solution)
        self.assertEqual(solution.tasks["t1"].start, 1)
        self.assertEqual(solution.tasks["t2"].start, 3)
        self.assertEqual(solution.tasks["t3"].start, 17)

    #
    # If/Then/Else
    #
    def test_if_then_else_1(self) -> None:
        pb = ps.SchedulingProblem(name="IfThenElse1", horizon=29)
        t_1 = ps.FixedDurationTask(name="t1", duration=3)
        t_2 = ps.FixedDurationTask(name="t2", duration=3)
        ite_constraint = ps.if_then_else(
            t_1._start == 1,  # condition
            [ps.TaskStartAt(task=t_2, value=3)],  # then
            [ps.TaskStartAt(task=t_2, value=6)],  # else
        )
        self.assertIsInstance(ite_constraint, ps.BoolRef)

        # force task t_1 to start at 2
        ps.TaskStartAt(task=t_1, value=2)

        pb.add_constraint(ite_constraint)
        solution = ps.SchedulingSolver(problem=pb).solve()

        self.assertTrue(solution)
        self.assertEqual(solution.tasks["t1"].start, 2)
        self.assertEqual(solution.tasks["t2"].start, 6)

    #
    # If then else
    #
    def test_if_then_else_2(self):
        pb = ps.SchedulingProblem(name="IfThenElse2", horizon=6)
        # only one task, the solver should schedule a start time at 0
        task_1 = ps.FixedDurationTask(name="task1", duration=2)
        task_2 = ps.FixedDurationTask(name="task2", duration=2)
        ps.TaskStartAt(task=task_1, value=1)
        fol_1 = ps.if_then_else(
            task_1._start == 0,  # this condition is False
            [ps.TaskStartAt(task=task_2, value=4)],  # assertion not set
            [ps.TaskStartAt(task=task_2, value=2)],
        )
        pb.add_constraint(fol_1)
        solution = ps.SchedulingSolver(problem=pb).solve()
        self.assertTrue(solution)
        # the only solution is to start at 2
        self.assertTrue(solution.tasks[task_1.name].start == 1)
        self.assertTrue(solution.tasks[task_2.name].start == 2)


if __name__ == "__main__":
    unittest.main()
