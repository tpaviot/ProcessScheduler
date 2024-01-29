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


def new_problem_or_clear() -> None:
    """clear the current context. If no context is defined,
    create a SchedulingProject object"""
    ps.SchedulingProblem(name="NewProblem")


def test_create_problem_with_horizon() -> None:
    pb = ps.SchedulingProblem(name="ProblemWithHorizon", horizon=10)
    assert isinstance(pb, ps.SchedulingProblem)
    with pytest.raises(ValidationError):
        ps.SchedulingProblem(name=4)  # name not string
    with pytest.raises(ValidationError):
        ps.SchedulingProblem(name="NullIntegerHorizon", horizon=0)
    with pytest.raises(ValidationError):
        ps.SchedulingProblem(name="FloatHorizon", horizon=3.5)
    with pytest.raises(ValidationError):
        ps.SchedulingProblem(name="NegativeIntegerHorizon", horizon=-2)


def test_create_problem_without_horizon() -> None:
    pb = ps.SchedulingProblem(name="ProblemWithoutHorizon")
    assert isinstance(pb, ps.SchedulingProblem)


#
# Workers
#
def test_create_worker_without_problem() -> None:
    ps.base.active_problem = None
    # no active problem defined, no way to create a resource
    with pytest.raises(AssertionError):
        ps.Worker(name="Bob")


def test_create_worker() -> None:
    new_problem_or_clear()
    worker = ps.Worker(name="wkr")
    assert isinstance(worker, ps.Worker)
    with pytest.raises(ValidationError):
        ps.Worker(name="WorkerNegativeIntProductivity", productivity=-3)
    with pytest.raises(ValidationError):
        ps.Worker(name="WorkerFloatProductivity", productivity=3.14)


def test_create_select_workers() -> None:
    new_problem_or_clear()
    worker_1 = ps.Worker(name="wkr_1")
    worker_2 = ps.Worker(name="wkr_2")
    worker_3 = ps.Worker(name="wkr_3")
    single_alternative_workers = ps.SelectWorkers(
        list_of_workers=[worker_1, worker_2], nb_workers_to_select=1
    )
    assert isinstance(single_alternative_workers, ps.SelectWorkers)
    double_alternative_workers = ps.SelectWorkers(
        list_of_workers=[worker_1, worker_2, worker_3], nb_workers_to_select=2
    )
    assert isinstance(double_alternative_workers, ps.SelectWorkers)


def test_select_worker_wrong_number_of_workers() -> None:
    new_problem_or_clear()
    worker_1 = ps.Worker(name="wkr_1")
    worker_2 = ps.Worker(name="wkr_2")
    ps.SelectWorkers(list_of_workers=[worker_1, worker_2], nb_workers_to_select=2)
    ps.SelectWorkers(list_of_workers=[worker_1, worker_2], nb_workers_to_select=1)
    with pytest.raises(ValueError):
        ps.SelectWorkers(list_of_workers=[worker_1, worker_2], nb_workers_to_select=3)
    with pytest.raises(ValidationError):
        ps.SelectWorkers(list_of_workers=[worker_1, worker_2], nb_workers_to_select=-1)


def test_select_worker_bad_type() -> None:
    new_problem_or_clear()
    worker_1 = ps.Worker(name="wkr_1")
    assert isinstance(worker_1, ps.Worker)
    worker_2 = ps.Worker(name="wkr_2")
    with pytest.raises(ValidationError):
        ps.SelectWorkers(
            list_of_workers=[worker_1, worker_2], nb_workers_to_select=1, kind="ee"
        )


def test_worker_same_name() -> None:
    new_problem_or_clear()
    worker_1 = ps.Worker(name="wkr_1")
    assert isinstance(worker_1, ps.Worker)
    with pytest.raises(ValueError):
        ps.Worker(name="wkr_1")


def test_select_worker_same_name() -> None:
    new_problem_or_clear()
    worker_1 = ps.Worker(name="wkr_1")
    assert isinstance(worker_1, ps.Worker)
    worker_2 = ps.Worker(name="wkr_2")
    ps.SelectWorkers(name="sw1", list_of_workers=[worker_1, worker_2])
    ps.SelectWorkers(name="sw2", list_of_workers=[worker_1, worker_2])
    with pytest.raises(ValueError):
        ps.SelectWorkers(name="sw1", list_of_workers=[worker_1, worker_2])
