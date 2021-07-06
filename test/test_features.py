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
import processscheduler.context as ps_context


def new_problem_or_clear() -> None:
    """clear the current context. If no context is defined,
    create a SchedulingProject object"""
    if ps_context.main_context is None:
        ps.SchedulingProblem("NewProblem")
    else:
        ps_context.main_context.clear()


class TestFeatures(unittest.TestCase):
    def test_clear_context(self) -> None:
        ps_context.main_context = None
        new_problem_or_clear()
        self.assertIsInstance(ps_context.main_context, ps.SchedulingContext)

    def test_create_problem_with_horizon(self) -> None:
        pb = ps.SchedulingProblem("ProblemWithHorizon", horizon=10)
        self.assertIsInstance(pb, ps.SchedulingProblem)
        with self.assertRaises(TypeError):
            ps.SchedulingProblem(4)  # name not string
        with self.assertRaises(TypeError):
            ps.SchedulingProblem("NullIntegerHorizon", horizon=0)
        with self.assertRaises(TypeError):
            ps.SchedulingProblem("FloatHorizon", horizon=3.5)
        with self.assertRaises(TypeError):
            ps.SchedulingProblem("NegativeIntegerHorizon", horizon=-2)

    def test_create_problem_without_horizon(self) -> None:
        pb = ps.SchedulingProblem("ProblemWithoutHorizon")
        self.assertIsInstance(pb, ps.SchedulingProblem)

    #
    # Workers
    #
    def test_create_worker(self) -> None:
        new_problem_or_clear()
        worker = ps.Worker("wkr")
        self.assertIsInstance(worker, ps.Worker)
        with self.assertRaises(TypeError):
            ps.Worker("WorkerNegativeIntProductivity", productivity=-3)
        with self.assertRaises(TypeError):
            ps.Worker("WorkerFloatProductivity", productivity=3.14)

    def test_create_select_workers(self) -> None:
        new_problem_or_clear()
        worker_1 = ps.Worker("wkr_1")
        worker_2 = ps.Worker("wkr_2")
        worker_3 = ps.Worker("wkr_3")
        single_alternative_workers = ps.SelectWorkers([worker_1, worker_2], 1)
        self.assertIsInstance(single_alternative_workers, ps.SelectWorkers)
        double_alternative_workers = ps.SelectWorkers([worker_1, worker_2, worker_3], 2)
        self.assertIsInstance(double_alternative_workers, ps.SelectWorkers)

    def test_select_worker_wrong_number_of_workers(self) -> None:
        new_problem_or_clear()
        worker_1 = ps.Worker("wkr_1")
        worker_2 = ps.Worker("wkr_2")
        ps.SelectWorkers([worker_1, worker_2], 2)
        ps.SelectWorkers([worker_1, worker_2], 1)
        with self.assertRaises(ValueError):
            ps.SelectWorkers([worker_1, worker_2], 3)
        with self.assertRaises(TypeError):
            ps.SelectWorkers([worker_1, worker_2], -1)

    def test_select_worker_bad_type(self) -> None:
        new_problem_or_clear()
        worker_1 = ps.Worker("wkr_1")
        self.assertIsInstance(worker_1, ps.Worker)
        worker_2 = ps.Worker("wkr_2")
        with self.assertRaises(ValueError):
            ps.SelectWorkers([worker_1, worker_2], 1, kind="ee")

    def test_worker_same_name(self) -> None:
        new_problem_or_clear()
        worker_1 = ps.Worker("wkr_1")
        self.assertIsInstance(worker_1, ps.Worker)
        with self.assertRaises(ValueError):
            ps.Worker("wkr_1")

    #
    # Boolean operators
    #
    def test_operator_not_(self) -> None:
        new_problem_or_clear()
        t_1 = ps.FixedDurationTask("t1", duration=2)
        not_constraint = ps.not_(ps.TaskStartAt(t_1, 1))
        self.assertIsInstance(not_constraint, ps.BoolRef)

    def test_operator_or_(self) -> None:
        new_problem_or_clear()
        t_1 = ps.FixedDurationTask("t1", duration=2)
        or_constraint = ps.or_([ps.TaskStartAt(t_1, 1), ps.TaskStartAt(t_1, 2)])
        self.assertIsInstance(or_constraint, ps.BoolRef)

    def test_operator_xor_(self) -> None:
        new_problem_or_clear()
        t_1 = ps.FixedDurationTask("t1", duration=2)
        xor_constraint = ps.xor_([ps.TaskStartAt(t_1, 1), ps.TaskStartAt(t_1, 2)])
        self.assertIsInstance(xor_constraint, ps.BoolRef)

    def test_operator_xor_2(self) -> None:
        new_problem_or_clear()
        t_1 = ps.FixedDurationTask("t1", duration=2)
        with self.assertRaises(TypeError):
            ps.xor_(
                [ps.TaskStartAt(t_1, 1), ps.TaskStartAt(t_1, 2), ps.TaskStartAt(t_1, 3)]
            )

    def test_operator_and_(self) -> None:
        new_problem_or_clear()
        t_1 = ps.FixedDurationTask("t1", duration=2)
        and_constraint = ps.and_(
            [ps.TaskStartAfterLax(t_1, 1), ps.TaskEndBeforeLax(t_1, 7)]
        )
        self.assertIsInstance(and_constraint, ps.BoolRef)

    def test_nested_boolean_operators(self) -> None:
        new_problem_or_clear()
        t_1 = ps.VariableDurationTask("t1")
        or_constraint_1 = ps.or_([ps.TaskStartAt(t_1, 1), ps.TaskStartAt(t_1, 2)])
        or_constraint_2 = ps.or_([ps.TaskStartAt(t_1, 4), ps.TaskStartAt(t_1, 5)])
        and_constraint = ps.and_([or_constraint_1, or_constraint_2])
        self.assertIsInstance(and_constraint, ps.BoolRef)

    def test_add_constraint(self) -> None:
        pb = ps.SchedulingProblem("AddConstraint")
        t_1 = ps.FixedDurationTask("t1", duration=2)
        or_constraint = ps.or_([ps.TaskStartAt(t_1, 1), ps.TaskStartAt(t_1, 2)])
        not_constraint = ps.not_(ps.TaskEndAt(t_1, 5))
        self.assertIsInstance(or_constraint, ps.BoolRef)
        self.assertIsInstance(not_constraint, ps.BoolRef)
        pb.add_constraint(or_constraint)
        pb.add_constraint(not_constraint)

    #
    # Implies
    #
    def test_implies(self) -> None:
        new_problem_or_clear()
        t_1 = ps.FixedDurationTask("t1", 2)
        t_2 = ps.FixedDurationTask("t2", 2)
        implies_constraint = ps.implies(t_1.start == 1, [ps.TaskStartAt(t_2, 3)])
        self.assertIsInstance(implies_constraint, ps.BoolRef)

    #
    # If/Then/Else
    #
    def test_if_then_else(self) -> None:
        new_problem_or_clear()
        t_1 = ps.FixedDurationTask("t1", 2)
        t_2 = ps.FixedDurationTask("t2", 2)
        ite_constraint = ps.if_then_else(
            t_1.start == 1,  # condition
            [ps.TaskStartAt(t_2, 3)],  # then
            [ps.TaskStartAt(t_2, 6)],
        )  # else
        self.assertIsInstance(ite_constraint, ps.BoolRef)

    #
    # Indicators
    #
    def test_create_indicator(self) -> None:
        pb = ps.SchedulingProblem("CreateIndicator", horizon=3)
        i_1 = ps.Indicator("SquareHorizon", pb.horizon ** 2)  # ArithRef
        self.assertIsInstance(i_1, ps.Indicator)
        i_2 = ps.Indicator("IsLooooong ?", pb.horizon > 1000)  # BoolRef
        self.assertIsInstance(i_2, ps.Indicator)
        with self.assertRaises(TypeError):
            ps.Indicator("foo", 4)

    #
    # Print _NamedUIDObject
    #
    def test_print_objects(self) -> None:
        new_problem_or_clear()
        t1 = ps.FixedDurationTask("task_1", duration=1)
        t2 = ps.VariableDurationTask("task_2")
        worker_1 = ps.Worker("W1")
        self.assertTrue("task_1" in "%s" % t1)
        self.assertTrue("task_2" in "%s" % t2)
        self.assertTrue("W1" in "%s" % worker_1)


if __name__ == "__main__":
    unittest.main()
