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
        ps.SchedulingProblem(name="NewProblem")
    else:
        ps_context.main_context.clear()


class TestFeatures(unittest.TestCase):
    def test_clear_context(self) -> None:
        ps_context.main_context = None
        new_problem_or_clear()
        self.assertIsInstance(ps_context.main_context, ps.SchedulingContext)

    def test_create_problem_with_horizon(self) -> None:
        pb = ps.SchedulingProblem(name="ProblemWithHorizon", horizon=10)
        self.assertIsInstance(pb, ps.SchedulingProblem)
        with self.assertRaises(TypeError):
            ps.SchedulingProblem(4)  # name not string
        with self.assertRaises(TypeError):
            ps.SchedulingProblem(name="NullIntegerHorizon", horizon=0)
        with self.assertRaises(TypeError):
            ps.SchedulingProblem(name="FloatHorizon", horizon=3.5)
        with self.assertRaises(TypeError):
            ps.SchedulingProblem(name="NegativeIntegerHorizon", horizon=-2)

    def test_create_problem_without_horizon(self) -> None:
        pb = ps.SchedulingProblem(name="ProblemWithoutHorizon")
        self.assertIsInstance(pb, ps.SchedulingProblem)

    #
    # Workers
    #
    def test_create_worker(self) -> None:
        new_problem_or_clear()
        worker = ps.Worker(name="wkr")
        self.assertIsInstance(worker, ps.Worker)
        with self.assertRaises(TypeError):
            ps.Worker(name="WorkerNegativeIntProductivity", productivity=-3)
        with self.assertRaises(TypeError):
            ps.Worker(name="WorkerFloatProductivity", productivity=3.14)

    def test_create_select_workers(self) -> None:
        new_problem_or_clear()
        worker_1 = ps.Worker(name="wkr_1")
        worker_2 = ps.Worker(name="wkr_2")
        worker_3 = ps.Worker(name="wkr_3")
        single_alternative_workers = ps.SelectWorkers(
            list_of_workers=[worker_1, worker_2], nb_workers_to_select=1
        )
        self.assertIsInstance(single_alternative_workers, ps.SelectWorkers)
        double_alternative_workers = ps.SelectWorkers(
            list_of_workers=[worker_1, worker_2, worker_3], nb_workers_to_select=2
        )
        self.assertIsInstance(double_alternative_workers, ps.SelectWorkers)

    def test_select_worker_wrong_number_of_workers(self) -> None:
        new_problem_or_clear()
        worker_1 = ps.Worker(name="wkr_1")
        worker_2 = ps.Worker(name="wkr_2")
        ps.SelectWorkers(list_of_workers=[worker_1, worker_2], nb_workers_to_select=2)
        ps.SelectWorkers(list_of_workers=[worker_1, worker_2], nb_workers_to_select=1)
        with self.assertRaises(ValueError):
            ps.SelectWorkers([worker_1, worker_2], 3)
        with self.assertRaises(TypeError):
            ps.SelectWorkers([worker_1, worker_2], -1)

    def test_select_worker_bad_type(self) -> None:
        new_problem_or_clear()
        worker_1 = ps.Worker(name="wkr_1")
        self.assertIsInstance(worker_1, ps.Worker)
        worker_2 = ps.Worker(name="wkr_2")
        ps.SelectWorkers(
            list_of_workers=[worker_1, worker_2], nb_workers_to_select=1, kind="ee"
        )

    def test_worker_same_name(self) -> None:
        new_problem_or_clear()
        worker_1 = ps.Worker(name="wkr_1")
        self.assertIsInstance(worker_1, ps.Worker)
        with self.assertRaises(ValueError):
            ps.Worker(name="wkr_1")

    #
    # Indicators
    #
    def test_create_indicator(self) -> None:
        pb = ps.SchedulingProblem(name="CreateIndicator", horizon=3)
        i_1 = ps.Indicator(name="SquareHorizon", expression=pb.horizon**2)  # ArithRef
        self.assertIsInstance(i_1, ps.Indicator)
        i_2 = ps.Indicator(name="IsLooooong ?", expression=pb.horizon > 1000)  # BoolRef
        self.assertIsInstance(i_2, ps.Indicator)

    #
    # Print _NamedUIDObject
    #
    def test_print_objects(self) -> None:
        new_problem_or_clear()
        t1 = ps.FixedDurationTask(name="task_1", duration=1)
        t2 = ps.VariableDurationTask(name="task_2")
        worker_1 = ps.Worker(name="W1")
        self.assertTrue("task_1" in f"{t1}")
        self.assertTrue("task_2" in f"{t2}")
        self.assertTrue("W1" in f"{worker_1}")


if __name__ == "__main__":
    unittest.main()
