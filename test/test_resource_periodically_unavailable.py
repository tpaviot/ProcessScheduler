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


def test_resource_periodically_unavailable_1() -> None:
    pb = ps.SchedulingProblem(name="ResourcePeriodicallyUnavailable1", horizon=10)
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    worker_1 = ps.Worker(name="Worker1")
    task_1.add_required_resource(worker_1)
    ps.ResourcePeriodicallyUnavailable(resource=worker_1, list_of_time_intervals=[(1, 3), (6, 8)], period=10)

    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.tasks[task_1.name].start == 3
    assert solution.tasks[task_1.name].end == 6


def test_resource_periodically_unavailable_2() -> None:
    pb = ps.SchedulingProblem(name="ResourcePeriodicallyUnavailable2", horizon=10)
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    worker_1 = ps.Worker(name="Worker1")
    task_1.add_required_resource(worker_1)
    # difference with the first one: build 2 constraints
    # merged using a and_
    ps.ResourcePeriodicallyUnavailable(resource=worker_1, list_of_time_intervals=[(1, 3)], period=10)
    ps.ResourcePeriodicallyUnavailable(resource=worker_1, list_of_time_intervals=[(6, 8)], period=10)

    # that should not change the problem solution
    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.tasks[task_1.name].start == 3
    assert solution.tasks[task_1.name].end == 6


def test_resource_periodically_unavailable_3() -> None:
    pb = ps.SchedulingProblem(name="ResourcePeriodicallyUnavailable3", horizon=10)
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    worker_1 = ps.Worker(name="Worker1")
    task_1.add_required_resource(worker_1)
    # difference with the previous ones: too much unavailability,
    # so possible solution
    # merged using a and_
    ps.ResourcePeriodicallyUnavailable(resource=worker_1, list_of_time_intervals=[(1, 3)], period=10)
    ps.ResourcePeriodicallyUnavailable(resource=worker_1, list_of_time_intervals=[(5, 8)], period=10)

    # that should not change the problem solution
    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert not solution


def test_resource_periodically_unavailable_4() -> None:
    ps.SchedulingProblem(name="ResourcePeriodicallyUnavailable4", horizon=10)
    worker_1 = ps.Worker(name="Worker1")
    with pytest.raises(AssertionError):
        ps.ResourcePeriodicallyUnavailable(resource=worker_1, list_of_time_intervals=[(1, 3)], period=10)


def test_resource_periodically_unavailable_5() -> None:
    pb = ps.SchedulingProblem(name="ResourcePeriodicallyUnavailable5", horizon=15)
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    task_2 = ps.FixedDurationTask(name="task2", duration=3)
    task_3 = ps.FixedDurationTask(name="task3", duration=3)
    ps.TaskPrecedence(task_before=task_1, task_after=task_2)
    ps.TaskPrecedence(task_before=task_2, task_after=task_3)
    worker_1 = ps.Worker(name="Worker1")
    for task in (task_1, task_2, task_3):
        task.add_required_resource(worker_1)
    ps.ResourcePeriodicallyUnavailable(
        resource=worker_1,
        list_of_time_intervals=[(3, 5)],
        period=5
    )

    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.tasks[task_1.name].start == 0
    assert solution.tasks[task_1.name].end == 3
    assert solution.tasks[task_2.name].start == 5
    assert solution.tasks[task_2.name].end == 8
    assert solution.tasks[task_3.name].start == 10
    assert solution.tasks[task_3.name].end == 13


def test_resource_periodically_unavailable_6() -> None:
    pb = ps.SchedulingProblem(name="ResourcePeriodicallyUnavailable6", horizon=17)
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    task_2 = ps.FixedDurationTask(name="task2", duration=3)
    task_3 = ps.FixedDurationTask(name="task3", duration=3)
    task_4 = ps.FixedDurationTask(name="task4", duration=3)
    ps.TaskPrecedence(task_before=task_1, task_after=task_2)
    ps.TaskPrecedence(task_before=task_2, task_after=task_3)
    ps.TaskPrecedence(task_before=task_3, task_after=task_4)
    worker_1 = ps.Worker(name="Worker1")
    for task in (task_1, task_2, task_3, task_4):
        task.add_required_resource(worker_1)
    ps.ResourcePeriodicallyUnavailable(
        resource=worker_1,
        list_of_time_intervals=[(2, 4)],
        offset=2, # shift interval to (4, 6)
        start=3,  # end_task_i <= start, so it must be set to the task duration
        end=14,   # unavailability interval at (14, 16), but it should be ignored
        period=5
    )
    ps.ResourceUnavailable(
        resource=worker_1,
        list_of_time_intervals=[(3, 4)] # leaving task_1 starting at 0 as only option
    )

    ps.ObjectiveMinimizeMakespan() # ensure dense packing
    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.tasks[task_1.name].start == 0  # unavailability at (0, 1) ignored
    assert solution.tasks[task_1.name].end == 3
    assert solution.tasks[task_2.name].start == 6
    assert solution.tasks[task_2.name].end == 9    # expected unavailability
    assert solution.tasks[task_3.name].start == 11
    assert solution.tasks[task_3.name].end == 14
    assert solution.tasks[task_4.name].start == 14 # unavailability at (14, 16) ignored
    assert solution.tasks[task_4.name].end == 17
