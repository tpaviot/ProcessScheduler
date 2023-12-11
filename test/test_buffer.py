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

import random

import processscheduler as ps

import pytest


def test_wrong_instanciation_buffer_1() -> None:
    """error because no initial and final states"""
    ps.SchedulingProblem(name="BufferBasic", horizon=12)
    with pytest.raises(AssertionError):
        ps.NonConcurrentBuffer(name="Buffer1")


def test_instanciate_buffer() -> None:
    ps.SchedulingProblem(name="BufferBasic", horizon=12)
    ps.NonConcurrentBuffer(name="Buffer1", initial_state=10)


def test_instanciate_buffer_error() -> None:
    ps.SchedulingProblem(name="BufferError", horizon=12)
    ps.NonConcurrentBuffer(name="Buffer1", initial_state=10)
    # a buffer with that name already exist, adding a new
    # one with the same name should raise an ValueError exception
    with pytest.raises(ValueError):
        ps.NonConcurrentBuffer(name="Buffer1", initial_state=10)


# TODO: fix
# def test_no_load_or_unload_buffer() -> None:
#      # only one buffer and one task
#     pb = ps.SchedulingProblem(name="NoLoadUnloadBuffer")
#     buffer = ps.NonConcurrentBuffer(name="Buffer1", final_state=10)
#     solver = ps.SchedulingSolver(problem=pb, debug=True)
#     solution = solver.solve()
#     assert solution
#     assert solution.buffers[buffer.name].state == [10]


def test_unload_buffer_1() -> None:
    # only one buffer and one task
    pb = ps.SchedulingProblem(name="UnloadBuffer1")

    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    buffer = ps.NonConcurrentBuffer(name="Buffer1", initial_state=10)

    ps.TaskStartAt(task=task_1, value=5)
    ps.TaskUnloadBuffer(task=task_1, buffer=buffer, quantity=3)

    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.buffers[buffer.name].state == [10, 7]
    assert solution.buffers[buffer.name].state_change_times == [5]


def test_unload_buffer_2() -> None:
    """one buffer and two tasks"""
    pb = ps.SchedulingProblem(name="UnloadBuffer2")

    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    task_2 = ps.FixedDurationTask(name="task2", duration=3)
    task_3 = ps.FixedDurationTask(name="task3", duration=3)
    buffer = ps.NonConcurrentBuffer(name="Buffer1", initial_state=10)

    ps.TaskStartAt(task=task_1, value=5)
    ps.TaskStartAt(task=task_2, value=10)
    ps.TaskUnloadBuffer(task=task_1, buffer=buffer, quantity=3)
    ps.TaskUnloadBuffer(task=task_2, buffer=buffer, quantity=2)

    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.buffers[buffer.name].state == [10, 7, 5]
    assert solution.buffers[buffer.name].state_change_times == [5, 10]


def test_unload_buffer_3() -> None:
    pb = ps.SchedulingProblem(name="UnloadBuffer3")

    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    task_2 = ps.FixedDurationTask(name="task2", duration=3)
    task_3 = ps.FixedDurationTask(name="task3", duration=3)
    buffer = ps.NonConcurrentBuffer(name="Buffer1", initial_state=10)

    ps.TaskStartAt(task=task_1, value=5)
    ps.TaskStartAt(task=task_2, value=10)
    ps.TaskStartAt(task=task_3, value=15)
    ps.TaskUnloadBuffer(task=task_1, buffer=buffer, quantity=3)
    ps.TaskUnloadBuffer(task=task_2, buffer=buffer, quantity=2)
    ps.TaskUnloadBuffer(task=task_3, buffer=buffer, quantity=1)

    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.buffers[buffer.name].state == [10, 7, 5, 4]
    assert solution.buffers[buffer.name].state_change_times == [5, 10, 15]


def test_unload_buffer_4() -> None:
    """unload a buffer defined from the final state"""
    pb = ps.SchedulingProblem(name="UnloadBuffer4")
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    buffer = ps.NonConcurrentBuffer(name="Buffer1", final_state=15)
    ps.TaskUnloadBuffer(task=task_1, buffer=buffer, quantity=3)
    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.buffers[buffer.name].state == [18, 15]


def test_load_buffer_1() -> None:
    # only one buffer and one task
    pb = ps.SchedulingProblem(name="LoadBuffer1")

    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    buffer = ps.NonConcurrentBuffer(name="Buffer1", initial_state=10)

    ps.TaskStartAt(task=task_1, value=5)
    ps.TaskLoadBuffer(task=task_1, buffer=buffer, quantity=3)

    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.buffers[buffer.name].state == [10, 13]
    assert solution.buffers[buffer.name].state_change_times == [8]


def test_load_buffer_2() -> None:
    pb = ps.SchedulingProblem(name="LoadBuffer2")

    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    task_2 = ps.FixedDurationTask(name="task2", duration=3)
    task_3 = ps.FixedDurationTask(name="task3", duration=3)
    buffer = ps.NonConcurrentBuffer(name="Buffer1", initial_state=10)

    ps.TaskStartAt(task=task_1, value=5)
    ps.TaskStartAt(task=task_2, value=10)
    ps.TaskStartAt(task=task_3, value=15)
    ps.TaskLoadBuffer(task=task_1, buffer=buffer, quantity=3)
    ps.TaskLoadBuffer(task=task_2, buffer=buffer, quantity=2)
    ps.TaskLoadBuffer(task=task_3, buffer=buffer, quantity=1)

    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.buffers[buffer.name].state == [10, 13, 15, 16]
    assert solution.buffers[buffer.name].state_change_times == [8, 13, 18]


def test_load_unload_feed_buffers_1() -> None:
    # one task that consumes and feed two different buffers
    pb = ps.SchedulingProblem(name="LoadUnloadBuffer1")

    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    buffer_1 = ps.NonConcurrentBuffer(name="Buffer1", initial_state=10)
    buffer_2 = ps.NonConcurrentBuffer(name="Buffer2", initial_state=0)

    ps.TaskStartAt(task=task_1, value=5)
    ps.TaskUnloadBuffer(task=task_1, buffer=buffer_1, quantity=3)
    ps.TaskLoadBuffer(task=task_1, buffer=buffer_2, quantity=2)

    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.buffers[buffer_1.name].state == [10, 7]
    assert solution.buffers[buffer_1.name].state_change_times == [5]
    assert solution.buffers[buffer_2.name].state == [0, 2]
    assert solution.buffers[buffer_2.name].state_change_times == [8]


def test_buffer_bounds_1() -> None:
    # n tasks take 1, n tasks feed one. Bounds 0 to 1
    pb = ps.SchedulingProblem(name="BufferBounds1")

    n = 3
    unloading_tasks = [
        ps.FixedDurationTask(name=f"LoadTask_{i}", duration=3) for i in range(n)
    ]
    loading_tasks = [
        ps.FixedDurationTask(name=f"UnloadTask_{i}", duration=3) for i in range(n)
    ]
    # create buffer
    buffer = ps.NonConcurrentBuffer(
        name="Buffer1", lower_bound=0, upper_bound=1, initial_state=1
    )

    for t in unloading_tasks:
        ps.TaskUnloadBuffer(task=t, buffer=buffer, quantity=1)

    for t in loading_tasks:
        ps.TaskLoadBuffer(task=t, buffer=buffer, quantity=1)

    ps.ObjectiveMinimizeMakespan()

    solver = ps.SchedulingSolver(problem=pb, max_time=300)
    solution = solver.solve()
    assert solution
    assert solution.horizon == 9


def test_unload_buffer_multiple_1() -> None:
    """two tasks which unload a buffer at two different times"""
    pb = ps.SchedulingProblem(name="TestUnloadBufferMultiple1")

    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    task_2 = ps.FixedDurationTask(name="task2", duration=3)

    buffer = ps.NonConcurrentBuffer(name="Buffer1", initial_state=10)

    ps.TaskStartAt(task=task_1, value=5)
    ps.TaskStartAt(task=task_2, value=6)
    ps.TaskUnloadBuffer(task=task_1, buffer=buffer, quantity=3)
    ps.TaskUnloadBuffer(task=task_2, buffer=buffer, quantity=4)

    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.buffers[buffer.name].state == [10, 7, 3]
    assert solution.buffers[buffer.name].state_change_times == [5, 6]


def test_unload_buffer_multiple_3() -> None:
    """three tasks which unload a buffer at the same time but with
    same quantities, and another that loads buffer"""
    pb = ps.SchedulingProblem(name="TestUnloadBufferMultiple3")

    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    task_2 = ps.FixedDurationTask(name="task2", duration=3)
    task_3 = ps.FixedDurationTask(name="task3", duration=4)

    buffer = ps.NonConcurrentBuffer(name="Buffer1", initial_state=13)

    ps.TaskStartAt(task=task_1, value=7)
    ps.TaskStartAt(task=task_2, value=8)
    ps.TaskStartAt(task=task_3, value=15)
    ps.TaskUnloadBuffer(task=task_1, buffer=buffer, quantity=4)
    ps.TaskUnloadBuffer(task=task_2, buffer=buffer, quantity=4)
    ps.TaskLoadBuffer(task=task_3, buffer=buffer, quantity=8)

    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.buffers[buffer.name].state == [13, 9, 5, 13]
    assert solution.buffers[buffer.name].state_change_times == [7, 8, 19]


#
# Concurrentbuffer:Access to a buffer for unloading at the same time
#
def test_unload_buffer_concurrent_1() -> None:
    """two tasks which unload a buffer at the same time but with
    same quantities"""
    pb = ps.SchedulingProblem(name="TestUnloadBufferConcurrent1")

    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    task_2 = ps.FixedDurationTask(name="task2", duration=4)
    task_3 = ps.FixedDurationTask(name="task3", duration=5)

    buffer = ps.ConcurrentBuffer(name="Buffer1", initial_state=100)

    ps.TaskStartAt(task=task_1, value=7)
    ps.TaskStartAt(task=task_2, value=7)
    ps.TaskStartAt(task=task_3, value=7)

    ps.TaskUnloadBuffer(task=task_1, buffer=buffer, quantity=23)
    ps.TaskUnloadBuffer(task=task_2, buffer=buffer, quantity=39)
    ps.TaskUnloadBuffer(task=task_3, buffer=buffer, quantity=17)

    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.buffers[buffer.name].state == [100, 100 - (23 + 39 + 17)]
    assert solution.buffers[buffer.name].state_change_times == [7]


def test_unload_buffer_concurrent_2() -> None:
    """two tasks which unload a buffer at the same time but with
    same quantities"""
    pb = ps.SchedulingProblem(name="TestUnloadBufferConcurrent2")

    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    task_2 = ps.FixedDurationTask(name="task2", duration=4)
    task_3 = ps.FixedDurationTask(name="task3", duration=5)

    buffer = ps.ConcurrentBuffer(name="Buffer1", initial_state=100)

    ps.TaskStartAt(task=task_1, value=7)
    ps.TaskStartAt(task=task_2, value=7)
    ps.TaskStartAt(task=task_3, value=8)

    ps.TaskUnloadBuffer(task=task_1, buffer=buffer, quantity=23)
    ps.TaskUnloadBuffer(task=task_2, buffer=buffer, quantity=39)
    ps.TaskUnloadBuffer(task=task_3, buffer=buffer, quantity=17)

    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.buffers[buffer.name].state == [
        100,
        100 - (23 + 39),
        100 - (23 + 39 + 17),
    ]
    assert solution.buffers[buffer.name].state_change_times == [7, 8]


def test_unload_buffer_multiple_4() -> None:
    # only one buffer and one task
    pb = ps.SchedulingProblem(name="TestUnloadBufferMultiple4")

    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    task_2 = ps.FixedDurationTask(name="task2", duration=3)
    task_3 = ps.FixedDurationTask(name="task3", duration=3)
    task_4 = ps.FixedDurationTask(name="task4", duration=3)

    buffer = ps.ConcurrentBuffer(name="Buffer1", initial_state=20)

    ps.TaskStartAt(task=task_1, value=5)
    ps.TaskStartAt(task=task_2, value=5)
    ps.TaskStartAt(task=task_3, value=6)
    ps.TaskStartAt(task=task_4, value=6)
    ps.TaskUnloadBuffer(task=task_1, buffer=buffer, quantity=3)
    ps.TaskUnloadBuffer(task=task_2, buffer=buffer, quantity=3)
    ps.TaskUnloadBuffer(task=task_3, buffer=buffer, quantity=3)
    ps.TaskUnloadBuffer(task=task_4, buffer=buffer, quantity=3)

    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.buffers[buffer.name].state == [20, 14, 8]
    assert solution.buffers[buffer.name].state_change_times == [5, 6]


def test_load_unload_concurrent_1() -> None:
    # n loading tasks and n unloading tasks with the same quantity
    # at the end of the schedule, the buffer level should be
    # the same than at the initial time
    pb = ps.SchedulingProblem(name="TestLoadUnloadConcurrent1")

    n = 6
    load_tasks = []
    unload_tasks = []

    for i in range(n):
        load_tasks.append(
            ps.FixedDurationTask(name=f"load_task_{i}", duration=random.randint(5, 50))
        )
        unload_tasks.append(
            ps.FixedDurationTask(
                name=f"unload_task_{i}", duration=random.randint(5, 50)
            )
        )

    # one buffer
    buffer = ps.ConcurrentBuffer(name="Buffer1", initial_state=179)

    # as many load tasks
    for t in load_tasks:
        ps.TaskLoadBuffer(task=t, buffer=buffer, quantity=3)
    # than unloadings
    for t in unload_tasks:
        ps.TaskUnloadBuffer(task=t, buffer=buffer, quantity=3)

    solver = ps.SchedulingSolver(problem=pb, max_time=20)
    solution = solver.solve()
    assert solution
    assert solution.buffers[buffer.name].state[-1] == 179


def test_load_unload_non_concurrent_1() -> None:
    # tha same than the previous one but with a NonConccurent buffer
    pb = ps.SchedulingProblem(name="TestLoadUnloadNonConcurrent1")

    n = 4
    load_tasks = []
    unload_tasks = []

    for i in range(n):
        load_tasks.append(
            ps.FixedDurationTask(name=f"load_task_{i}", duration=random.randint(5, 50))
        )
        unload_tasks.append(
            ps.FixedDurationTask(
                name=f"unload_task_{i}", duration=random.randint(5, 50)
            )
        )

    # one buffer
    buffer = ps.NonConcurrentBuffer(name="Buffer1", initial_state=179)

    # as many load tasks
    for t in load_tasks:
        ps.TaskLoadBuffer(task=t, buffer=buffer, quantity=3)
    # than unloadings
    for t in unload_tasks:
        ps.TaskUnloadBuffer(task=t, buffer=buffer, quantity=3)

    solver = ps.SchedulingSolver(problem=pb, max_time=20)
    solution = solver.solve()
    assert solution
    assert solution.buffers[buffer.name].state[-1] == 179


#
# Buffer indicator
#
def test_buffer_indicator_1() -> None:
    # one task that consumes and feed two different buffers
    pb = ps.SchedulingProblem(name="BufferIndicator1")

    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    buffer_1 = ps.NonConcurrentBuffer(name="Buffer1", initial_state=10)
    ps.TaskUnloadBuffer(task=task_1, buffer=buffer_1, quantity=3)
    ps.TaskStartAt(task=task_1, value=0)
    indic_max = ps.IndicatorMaxBufferLevel(buffer=buffer_1)
    indic_min = ps.IndicatorMinBufferLevel(buffer=buffer_1)
    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.buffers[buffer_1.name].state == [10, 7]
    assert solution.buffers[buffer_1.name].state_change_times == [0]
    assert solution.indicators[indic_max.name] == 10
    assert solution.indicators[indic_min.name] == 7


#
# Buffer objective max level
#
def test_objective_maximize_max_buffer_level_1() -> None:
    # one task that consumes and feed two different buffers
    pb = ps.SchedulingProblem(name="ObjectiveMaximizeMaxBufferLevel1")

    # two tasks, one loads one unloads
    # if we need to maximize highest buffer level then we need
    # to first load and then unload
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    task_2 = ps.FixedDurationTask(name="task2", duration=3)

    buffer_1 = ps.NonConcurrentBuffer(name="Buffer1", initial_state=10)

    ps.TaskUnloadBuffer(task=task_1, buffer=buffer_1, quantity=3)
    ps.TaskLoadBuffer(task=task_2, buffer=buffer_1, quantity=8)

    oo = ps.ObjectiveMaximizeMaxBufferLevel(buffer=buffer_1)

    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution

    assert solution.tasks["task2"].end < solution.tasks["task1"].start
    assert solution.indicators[oo.target.name] == 10 + 8


def test_objective_minimize_max_buffer_level_1() -> None:
    """the same use case as previously, but choose minimize max level"""
    pb = ps.SchedulingProblem(name="ObjectiveMinimizeMaxBufferLevel")

    # two tasks, one loads one unloads
    # if we need to minimize the highest buffer level then we need
    # to first unload (-3) and then load (+8)
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    task_2 = ps.FixedDurationTask(name="task2", duration=3)

    buffer_1 = ps.NonConcurrentBuffer(name="Buffer1", initial_state=10)

    ps.TaskUnloadBuffer(task=task_1, buffer=buffer_1, quantity=3)
    ps.TaskLoadBuffer(task=task_2, buffer=buffer_1, quantity=8)

    oo = ps.ObjectiveMinimizeMaxBufferLevel(buffer=buffer_1)

    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution

    assert solution.tasks["task1"].start < solution.tasks["task2"].end
    assert solution.indicators[oo.target.name] == 10 - 3 + 8
