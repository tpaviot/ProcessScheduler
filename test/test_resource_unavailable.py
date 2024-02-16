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

import pytest


def test_resource_unavailable_1() -> None:
    pb = ps.SchedulingProblem(name="ResourceUnavailable1", horizon=10)
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    worker_1 = ps.Worker(name="Worker1")
    task_1.add_required_resource(worker_1)
    ps.ResourceUnavailable(resource=worker_1, list_of_time_intervals=[(1, 3), (6, 8)])

    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.tasks[task_1.name].start == 3
    assert solution.tasks[task_1.name].end == 6


def test_resource_unavailable_2() -> None:
    pb = ps.SchedulingProblem(name="ResourceUnavailable2", horizon=10)
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    worker_1 = ps.Worker(name="Worker1")
    task_1.add_required_resource(worker_1)
    # difference with the first one: build 2 constraints
    # merged using a and_
    ps.ResourceUnavailable(resource=worker_1, list_of_time_intervals=[(1, 3)])
    ps.ResourceUnavailable(resource=worker_1, list_of_time_intervals=[(6, 8)])

    # that should not change the problem solution
    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.tasks[task_1.name].start == 3
    assert solution.tasks[task_1.name].end == 6


def test_resource_unavailable_3() -> None:
    pb = ps.SchedulingProblem(name="ResourceUnavailable3", horizon=10)
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    worker_1 = ps.Worker(name="Worker1")
    task_1.add_required_resource(worker_1)
    # difference with the previous ones: too much unavailability,
    # so possible solution
    # merged using a and_
    ps.ResourceUnavailable(resource=worker_1, list_of_time_intervals=[(1, 3)])
    ps.ResourceUnavailable(resource=worker_1, list_of_time_intervals=[(5, 8)])

    # that should not change the problem solution
    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert not solution


def test_resource_unavailable_4() -> None:
    pb = ps.SchedulingProblem(name="ResourceUnavailable4")
    task_1 = ps.FixedDurationTask(name="task1", duration=4)
    worker_1 = ps.Worker(name="Worker1")
    task_1.add_required_resource(worker_1)
    # create 10 unavailabilities with a length of 3 and try
    # to schedule a task with length 4, it should be scheduled
    # at the end
    maxi = 50
    intervs = [(i, i + 3) for i in range(0, maxi, 6)]

    ps.ResourceUnavailable(resource=worker_1, list_of_time_intervals=intervs)
    ps.ObjectiveMinimizeMakespan()

    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.tasks[task_1.name].start == maxi + 1


def test_resource_unavailable_raise_issue() -> None:
    ps.SchedulingProblem(name="ResourceUnavailableRaiseException", horizon=10)
    worker_1 = ps.Worker(name="Worker1")
    with pytest.raises(AssertionError):
        ps.ResourceUnavailable(resource=worker_1, list_of_time_intervals=[(1, 3)])


def test_resource_unavailable_cumulative_1():
    pb_bs = ps.SchedulingProblem(name="ResourceUnavailableCumulative1", horizon=10)
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

    ps.ResourceUnavailable(resource=r1, list_of_time_intervals=[(1, 10)])

    # plot solution
    solver = ps.SchedulingSolver(problem=pb_bs)
    solution = solver.solve()
    assert not solution


def test_resource_unavailable_cumulative_2():
    # same as the previous one, but this time there should be one and only
    # one solution
    pb_bs = ps.SchedulingProblem(name="ResourceUnavailableCumulative1", horizon=12)
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

    ps.ResourceUnavailable(resource=r1, list_of_time_intervals=[(1, 10)])

    # plot solution
    solver = ps.SchedulingSolver(problem=pb_bs)
    solution = solver.solve()
    assert solution.tasks[t1.name].start == 10
    assert solution.tasks[t2.name].start == 10
    assert solution.tasks[t3.name].start == 10
