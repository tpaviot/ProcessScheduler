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


def test_create_cumulative():
    """take the single task/single resource and display output"""
    ps.SchedulingProblem(name="CreateCumulative", horizon=10)
    # work = ps.Worker(name="Mac", cost=None)
    cumulative_worker = ps.CumulativeWorker(name="MachineA", size=4)
    assert len(cumulative_worker._cumulative_workers) == 4


def test_create_cumulative_wrong_type():
    """take the single task/single resource and display output"""
    ps.SchedulingProblem(name="CreateCumulativeWrongType", horizon=10)
    with pytest.raises(ValidationError):
        ps.CumulativeWorker(name="MachineA", size=1)
    with pytest.raises(ValidationError):
        ps.CumulativeWorker(name="MachineA", size=2.5)


def test_cumulative_1():
    pb_bs = ps.SchedulingProblem(name="Cumulative1", horizon=3)
    # tasks
    t1 = ps.FixedDurationTask(name="T1", duration=2)
    t2 = ps.FixedDurationTask(name="T2", duration=2)
    t3 = ps.FixedDurationTask(name="T3", duration=2)

    # workers
    r1 = ps.CumulativeWorker(name="Machine1", size=3)
    # resource assignment
    t1.add_required_resource(r1)
    t2.add_required_resource(r1)
    t3.add_required_resource(r1)

    # constraints
    ps.TaskStartAt(task=t2, value=1)

    # plot solution
    solver = ps.SchedulingSolver(problem=pb_bs)
    solution = solver.solve()
    assert solution


def test_cumulative_2():
    pb_bs = ps.SchedulingProblem(name="Cumulative2", horizon=3)
    # tasks
    t1 = ps.FixedDurationTask(name="T1", duration=2)
    t2 = ps.FixedDurationTask(name="T2", duration=2)

    # workers
    r1 = ps.CumulativeWorker(name="Machine1", size=2)
    # resource assignment
    t1.add_required_resource(r1)
    t2.add_required_resource(r1)

    # constraints
    ps.TaskStartAt(task=t2, value=1)

    solver = ps.SchedulingSolver(problem=pb_bs)
    solution = solver.solve()
    assert solution


def test_optional_cumulative():
    """Same as above, but with an optional taskand an horizon of 2.
    t2 should not be scheduled."""
    pb_bs = ps.SchedulingProblem(name="OptionalCumulative", horizon=2)
    # tasks
    t1 = ps.FixedDurationTask(name="T1", duration=2)
    t2 = ps.FixedDurationTask(name="T2", duration=2, optional=True)
    t3 = ps.FixedDurationTask(name="T3", duration=2)

    # workers
    r1 = ps.CumulativeWorker(name="Machine1", size=2)
    # resource assignment
    t1.add_required_resource(r1)
    t2.add_required_resource(r1)

    # constraints
    ps.TaskStartAt(task=t2, value=1)

    # plot solution
    solver = ps.SchedulingSolver(problem=pb_bs)
    solution = solver.solve()
    assert solution
    assert solution.tasks[t1.name].scheduled
    assert solution.tasks[t3.name].scheduled
    assert not solution.tasks[t2.name].scheduled


def test_cumulative_select_worker_1():
    pb_bs = ps.SchedulingProblem(name="CumulativeSelectWorker", horizon=2)
    # tasks
    t1 = ps.FixedDurationTask(name="T1", duration=2)
    t2 = ps.FixedDurationTask(name="T2", duration=2)

    # workers
    r1 = ps.CumulativeWorker(name="Machine1", size=2)
    r2 = ps.CumulativeWorker(name="Machine2", size=2)
    r3 = ps.Worker(name="Machine3")
    # resource assignment

    t1.add_required_resource(
        ps.SelectWorkers(list_of_workers=[r1, r2], nb_workers_to_select=1)
    )
    t2.add_required_resource(
        ps.SelectWorkers(list_of_workers=[r1, r3], nb_workers_to_select=1)
    )

    # plot solution
    solver = ps.SchedulingSolver(problem=pb_bs)
    solution = solver.solve()
    assert solution


def test_cumulative_hosp():
    n = 16
    capa = 4
    pb_bs = ps.SchedulingProblem(name="Hospital", horizon=n // capa)
    # workers
    r1 = ps.CumulativeWorker(name="Room", size=capa)

    for i in range(n):
        t = ps.FixedDurationTask(name=f"T{i+1}", duration=1)
        t.add_required_resource(r1)

    solver = ps.SchedulingSolver(problem=pb_bs)
    solution = solver.solve()
    assert solution


def test_cumulative_productivity():
    """Horizon should be 4, 100/29=3.44."""
    problem = ps.SchedulingProblem(name="CumulativeProductivity")
    t_1 = ps.VariableDurationTask(name="t1", work_amount=100)

    worker_1 = ps.CumulativeWorker(name="CumulWorker", size=3, productivity=29)
    t_1.add_required_resource(worker_1)

    ps.ObjectiveMinimizeMakespan()

    solution = ps.SchedulingSolver(problem=problem).solve()
    assert solution
    assert solution.horizon == 4
