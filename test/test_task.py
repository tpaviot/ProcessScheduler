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

import processscheduler.base
import pytest

from pydantic import ValidationError


def test_create_task_zero_duration() -> None:
    ps.SchedulingProblem(name="ProblemWithoutHorizon")
    task = ps.ZeroDurationTask(name="zdt")
    assert isinstance(task, ps.ZeroDurationTask)


def test_create_task_fixed_duration() -> None:
    ps.SchedulingProblem(name="CreateTaskFixedDUration")
    task = ps.FixedDurationTask(name="fdt", duration=1)
    assert isinstance(task, ps.FixedDurationTask)
    ps.FixedDurationTask(name="FloatDuration", duration=1.0)
    with pytest.raises(ValidationError):
        ps.FixedDurationTask(name="NullInteger", duration=0)
    with pytest.raises(ValidationError):
        ps.FixedDurationTask(name="NegativeInteger", duration=-1)
    ps.FixedDurationTask(name="FloatWorkAmount", duration=2, work_amount=1.0)
    with pytest.raises(ValidationError):
        ps.FixedDurationTask(name="NegativeWorkAmount", duration=2, work_amount=-3)


def test_create_task_variable_duration() -> None:
    pb = ps.SchedulingProblem(name="CreateVariableDurationTask")

    ps.VariableDurationTask(name="vdt1")
    vdt_2 = ps.VariableDurationTask(name="vdt2", max_duration=4)
    vdt_3 = ps.VariableDurationTask(name="vdt3", min_duration=5)

    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()

    assert solution
    assert solution.tasks[vdt_2.name].duration <= 4
    assert solution.tasks[vdt_3.name].duration >= 5


def test_create_task_variable_duration_from_list() -> None:
    pb = ps.SchedulingProblem(name="CreateVariableDurationTaskFromList")

    vdt_1 = ps.VariableDurationTask(name="vdt1", allowed_durations=[3, 4])
    vdt_2 = ps.VariableDurationTask(name="vdt2", allowed_durations=[5, 6])
    vdt_3 = ps.VariableDurationTask(name="vdt3", allowed_durations=[7, 8])

    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()

    assert solution
    assert solution.tasks[vdt_1.name].duration in [3, 4]
    assert solution.tasks[vdt_2.name].duration in [5, 6]
    assert solution.tasks[vdt_3.name].duration in [7, 8]


def test_task_types() -> None:
    ps.SchedulingProblem(name="CreateTasksValidationError")
    with pytest.raises(ValidationError):
        ps.VariableDurationTask(name="vdt5", max_duration=4.5)
    with pytest.raises(ValidationError):
        ps.VariableDurationTask(name="vdt6", max_duration=-1)
    with pytest.raises(ValidationError):
        ps.VariableDurationTask(name="vdt7", min_duration=-1)
    with pytest.raises(ValidationError):
        ps.VariableDurationTask(name="vdt8", work_amount=-1)
    with pytest.raises(ValidationError):
        ps.VariableDurationTask(name="vdt9", work_amount=1.5)
    with pytest.raises(ValidationError):
        ps.VariableDurationTask(name="vdt10", work_amount=None)


def test_task_same_names() -> None:
    ps.SchedulingProblem(name="TaskSameNames")
    ps.VariableDurationTask(name="t1")
    with pytest.raises(ValueError):
        ps.VariableDurationTask(name="t1")


def test_eq_overloading() -> None:
    ps.SchedulingProblem(name="EqOverloading")
    task_1 = ps.ZeroDurationTask(name="task1")
    task_2 = ps.ZeroDurationTask(name="task2")
    assert task_1, task_1
    assert task_1 != task_2


def test_redundant_tasks_resources() -> None:
    pb = ps.SchedulingProblem(name="SameNameTasks")
    # we should not be able to add twice the same resource or task
    task_1 = ps.ZeroDurationTask(name="task1")
    assert list(pb.tasks.values()) == [task_1]
    # do the same for resources
    worker_1 = ps.Worker(name="Worker1")
    assert list(pb.workers.values()) == [worker_1]


def test_resource_requirements() -> None:
    pb = ps.SchedulingProblem(name="ResourceRequirements")

    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    worker_1 = ps.Worker(name="Worker1")
    worker_2 = ps.Worker(name="Worker2")
    worker_3 = ps.Worker(name="Worker3")
    worker_4 = ps.Worker(name="Worker4")
    task_1.add_required_resource(worker_1)
    task_1.add_required_resource(worker_2)
    task_1.add_required_resources([worker_3, worker_4])
    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert len(solution.tasks["task1"].assigned_resources) == 4


def test_wrong_assignement() -> None:
    ps.SchedulingProblem(name="WrongAssignment")
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    worker_1 = ps.Worker(name="Worker1")
    task_1.add_required_resource(worker_1)
    with pytest.raises(TypeError):
        task_1.add_required_resource(3)
    with pytest.raises(TypeError):
        task_1.add_required_resources("a_string")
    with pytest.raises(ValueError):
        task_1.add_required_resource(worker_1)


#
# Single task constraints
#
def test_create_task_start_at() -> None:
    ps.SchedulingProblem(name="CreateTaskStartAt")
    t_1 = ps.FixedDurationTask(name="task_1", duration=2)
    c = ps.TaskStartAt(task=t_1, value=1)
    assert isinstance(c, ps.TaskStartAt)
    assert c.value == 1


def test_create_task_start_after_strict() -> None:
    ps.SchedulingProblem(name="CreateTaskStartAfterStrict")
    t_1 = ps.FixedDurationTask(name="task_1", duration=2)
    c = ps.TaskStartAfter(task=t_1, value=3, kind="strict")
    assert isinstance(c, ps.TaskStartAfter)
    assert c.value == 3


def test_create_task_start_after_lax() -> None:
    ps.SchedulingProblem(name="CreateTaskStartAfterLax")
    t_1 = ps.FixedDurationTask(name="task_1", duration=2)
    c = ps.TaskStartAfter(task=t_1, value=3, kind="lax")
    assert isinstance(c, ps.TaskStartAfter)
    assert c.value == 3


def test_create_task_end_at() -> None:
    ps.SchedulingProblem(name="CreateTaskEndAt")
    t_1 = ps.FixedDurationTask(name="task", duration=2)
    c = ps.TaskEndAt(task=t_1, value=3)
    assert isinstance(c, ps.TaskEndAt)
    assert c.value == 3


def test_create_task_end_before_strict() -> None:
    ps.SchedulingProblem(name="CreateTaskEndBeforeStrict")
    t_1 = ps.FixedDurationTask(name="task", duration=2)
    c = ps.TaskEndBefore(task=t_1, value=3, kind="strict")
    assert isinstance(c, ps.TaskEndBefore)
    assert c.value == 3


def test_create_task_end_before_lax() -> None:
    ps.SchedulingProblem(name="CreateTaskEndBeforeLax")
    t_1 = ps.FixedDurationTask(name="task", duration=2)
    c = ps.TaskEndBefore(task=t_1, value=3, kind="lax")
    assert isinstance(c, ps.TaskEndBefore)
    assert c.value == 3


def test_task_duration_depend_on_start() -> None:
    pb = ps.SchedulingProblem(name="TaskDurationDependsOnStart", horizon=30)

    task_1 = ps.VariableDurationTask(name="Task1")
    task_2 = ps.VariableDurationTask(name="Task2")

    ps.TaskStartAt(task=task_1, value=5)
    pb.add_constraint(task_1._duration == task_1._start * 3)

    ps.TaskStartAt(task=task_2, value=11)
    ps.IfThenElse(
        condition=task_2._start < 10,
        then_list_of_constraints=[task_2._duration == 3],
        else_list_of_constraints=[task_2._duration == 1],
    )

    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.tasks["Task1"].duration == 15
    assert solution.tasks["Task2"].duration == 1


#
# Two tasks constraints
#
def test_create_task_precedence_lax() -> None:
    ps.SchedulingProblem(name="CreateTaskPrecedenceLax")
    t_1 = ps.FixedDurationTask(name="t1", duration=2)
    t_2 = ps.FixedDurationTask(name="t2", duration=3)
    precedence_constraint = ps.TaskPrecedence(
        task_before=t_1, task_after=t_2, offset=1, kind="lax"
    )
    assert isinstance(precedence_constraint, ps.TaskPrecedence)


def test_create_task_precedence_tight() -> None:
    ps.SchedulingProblem(name="CreateTaskPrecedenceTight")
    t_1 = ps.FixedDurationTask(name="t1", duration=2)
    t_2 = ps.FixedDurationTask(name="t2", duration=3)
    precedence_constraint = ps.TaskPrecedence(
        task_before=t_1, task_after=t_2, offset=1, kind="tight"
    )
    assert isinstance(precedence_constraint, ps.TaskPrecedence)


def test_create_task_precedence_strict() -> None:
    pb = ps.SchedulingProblem(name="TaskPrecedenceStrict")
    t_1 = ps.FixedDurationTask(name="t1", duration=2)
    t_2 = ps.FixedDurationTask(name="t2", duration=3)
    ps.TaskPrecedence(task_before=t_1, task_after=t_2, offset=1, kind="strict")
    pb.add_objective_makespan()
    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.tasks[t_2.name].start == solution.tasks[t_1.name].end + 2


def test_create_task_precedence_raise_exception_kind() -> None:
    ps.SchedulingProblem(name="CreateTaskPrecedenceKindRaiseException")
    t_1 = ps.FixedDurationTask(name="t1", duration=2)
    t_2 = ps.FixedDurationTask(name="t2", duration=3)
    with pytest.raises(ValidationError):
        ps.TaskPrecedence(task_before=t_1, task_after=t_2, offset=1, kind="foo")


def test_create_task_precedence_raise_exception_offset_int() -> None:
    ps.SchedulingProblem(name="CreateTaskPrecedenceRaiseOffsetInt")
    t_1 = ps.FixedDurationTask(name="t1", duration=2)
    t_2 = ps.FixedDurationTask(name="t2", duration=3)
    with pytest.raises(ValidationError):
        ps.TaskPrecedence(
            task_before=t_1, task_after=t_2, offset=1.5, kind="lax"
        )  # should be int


def test_tasks_dont_overlap() -> None:
    pb = ps.SchedulingProblem(name="TasksDontOverlap")
    t_1 = ps.FixedDurationTask(name="t1", duration=7)
    t_2 = ps.FixedDurationTask(name="t2", duration=11)
    ps.TasksDontOverlap(task_1=t_1, task_2=t_2)
    pb.add_objective_makespan()
    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.horizon == 18


def test_tasks_start_sync() -> None:
    pb = ps.SchedulingProblem(name="TasksStartSync")
    t_1 = ps.FixedDurationTask(name="t1", duration=2)
    t_2 = ps.FixedDurationTask(name="t2", duration=3)
    ps.TaskStartAt(task=t_1, value=7)
    ps.TasksStartSynced(task_1=t_1, task_2=t_2)
    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.tasks[t_1.name].start == solution.tasks[t_2.name].start


def test_tasks_end_sync() -> None:
    pb = ps.SchedulingProblem(name="TasksEndSync")
    t_1 = ps.FixedDurationTask(name="t1", duration=2)
    t_2 = ps.FixedDurationTask(name="t2", duration=3)
    ps.TasksEndSynced(task_1=t_1, task_2=t_2)
    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.tasks[t_1.name].end == solution.tasks[t_2.name].end


#
# List of tasks constraints
#
def test_tasks_contiguous() -> None:
    pb = ps.SchedulingProblem(name="TasksContiguous")
    n = 7
    tasks_w1 = [ps.FixedDurationTask(name=f"t_w1_{i}", duration=3) for i in range(n)]
    tasks_w2 = [ps.FixedDurationTask(name=f"t_w2_{i}", duration=5) for i in range(n)]
    worker_1 = ps.Worker(name="Worker1")
    worker_2 = ps.Worker(name="Worker2")
    for t in tasks_w1:
        t.add_required_resource(worker_1)
    for t in tasks_w2:
        t.add_required_resource(worker_2)

    ps.TasksContiguous(list_of_tasks=tasks_w1 + tasks_w2)

    pb.add_objective_makespan()

    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.horizon == 56
