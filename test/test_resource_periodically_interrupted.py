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


def test_resource_periodically_interrupted_fixed_duration() -> None:
    pb = ps.SchedulingProblem(name="fixed_duration")
    task_1 = ps.FixedDurationTask(name="task1", duration=2)
    task_2 = ps.FixedDurationTask(name="task2", duration=4)
    worker_1 = ps.Worker(name="Worker1")
    task_1.add_required_resource(worker_1)
    task_2.add_required_resource(worker_1)
    ps.ResourcePeriodicallyInterrupted(
        resource=worker_1,
        list_of_time_intervals=[(1, 2), (4, 5)],
        period=10
    )

    ps.ObjectiveMinimizeMakespan()
    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.tasks[task_1.name].start == 2
    assert solution.tasks[task_1.name].end == 4
    assert solution.tasks[task_2.name].start == 5
    assert solution.tasks[task_2.name].end == 9


def test_resource_periodically_interrupted_variable_duration() -> None:
    pb = ps.SchedulingProblem(name="variable_duration")
    task_1 = ps.VariableDurationTask(name="task1", min_duration=3)
    task_2 = ps.FixedDurationTask(name="task2", duration=4)
    ps.TaskStartAt(task=task_1, value=0) # pin to have a more stable outcome
    worker_1 = ps.Worker(name="Worker1")
    task_1.add_required_resource(worker_1)
    task_2.add_required_resource(worker_1)
    ps.ResourcePeriodicallyInterrupted(
        resource=worker_1,
        list_of_time_intervals=[(1, 2), (4, 5)],
        period=10
    )

    ps.ObjectiveMinimizeMakespan()
    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.tasks[task_1.name].start == 0
    assert solution.tasks[task_1.name].end == 4
    assert solution.tasks[task_2.name].start == 5
    assert solution.tasks[task_2.name].end == 9


def test_resource_periodically_interrupted_assignment_assertion() -> None:
    ps.SchedulingProblem(name="assignment_assertion")
    worker_1 = ps.Worker(name="Worker1")
    with pytest.raises(AssertionError):
        ps.ResourcePeriodicallyInterrupted(resource=worker_1, list_of_time_intervals=[(1, 3)], period=6)


def test_resource_periodically_interrupted_period_assertion() -> None:
    ps.SchedulingProblem(name="period_assertion")
    worker_1 = ps.Worker(name="Worker1")
    with pytest.raises(AssertionError):
        ps.ResourcePeriodicallyInterrupted(resource=worker_1, list_of_time_intervals=[(1, 2), (3, 5)], period=4)
