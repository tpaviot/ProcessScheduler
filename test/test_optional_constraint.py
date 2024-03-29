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


def test_optional_constraint_start_at_1() -> None:
    pb = ps.SchedulingProblem(name="OptionalTaskStartAt1", horizon=6)
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    # the following tasks should conflict if they are mandatory
    ps.TaskStartAt(task=task_1, value=1, optional=True)
    ps.TaskStartAt(task=task_1, value=2, optional=True)
    ps.TaskEndAt(task=task_1, value=3, optional=True)

    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution


def test_force_apply_n_optional_constraints() -> None:
    pb = ps.SchedulingProblem(name="OptionalTaskStartAt1", horizon=6)
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    # the following tasks should conflict if they are mandatory
    cstr1 = ps.TaskStartAt(task=task_1, value=1, optional=True)
    cstr2 = ps.TaskStartAt(task=task_1, value=2, optional=True)
    cstr3 = ps.TaskEndAt(task=task_1, value=3, optional=True)
    # force to apply exactly one constraint
    ps.ForceApplyNOptionalConstraints(
        list_of_optional_constraints=[cstr1, cstr2, cstr3],
        nb_constraints_to_apply=1,
    )

    solver = ps.SchedulingSolver(problem=pb)

    solution = solver.solve()
    assert solution
