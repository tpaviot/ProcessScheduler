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

from datetime import datetime, timedelta

import processscheduler as ps


def test_datetime_1():
    """take the single task/single resource and display output"""
    problem = ps.SchedulingProblem(
        name="DateTimeBase",
        horizon=7,
        delta_time=timedelta(minutes=15),
        start_time=datetime.now(),
    )
    task = ps.FixedDurationTask(name="task", duration=7)
    # problem.add_task(task)
    worker = ps.Worker(name="worker")
    # problem.add_resource(worker)
    task.add_required_resource(worker)
    solver = ps.SchedulingSolver(problem=problem)
    solution = solver.solve()
    assert solution
    print(solution)


def test_datetime_time():
    """take the single task/single resource and display output"""
    problem = ps.SchedulingProblem(
        name="DateTimeBase", horizon=7, delta_time=timedelta(minutes=15)
    )
    task = ps.FixedDurationTask(name="task", duration=7)
    # problem.add_task(task)
    worker = ps.Worker(name="worker")
    task.add_required_resource(worker)
    solver = ps.SchedulingSolver(problem=problem)
    solution = solver.solve()
    assert solution
    print(solution)


def test_datetime_export_to_json():
    problem = ps.SchedulingProblem(
        name="DateTimeJson",
        delta_time=timedelta(hours=1),
        start_time=datetime.now(),
    )
    task = ps.FixedDurationTask(name="task", duration=7)
    # problem.add_task(task)
    worker = ps.Worker(name="worker")
    task.add_required_resource(worker)
    solver = ps.SchedulingSolver(problem=problem)
    solution = solver.solve()
    assert solution
    solution.to_json()
