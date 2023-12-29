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

import pytest

import processscheduler as ps


def build_complex_problem(name: str, n: int) -> ps.SchedulingProblem:
    """returns a problem with n tasks and n * 3 workers"""
    problem = ps.SchedulingProblem(name=name)

    nb_mandatory_tasks = 3 * n
    nb_optional_tasks = n
    nb_workers = 4 * n

    mandatory_tasks = [
        ps.FixedDurationTask(name=f"mand_task{i}", duration=i % 8 + 1)
        for i in range(nb_mandatory_tasks)
    ]

    # n/10 optional tasks
    optional_tasks = [
        ps.FixedDurationTask(name=f"opt_task{i}", duration=i % 8 + 1, optional=True)
        for i in range(nb_optional_tasks)
    ]

    all_tasks = mandatory_tasks + optional_tasks

    workers = [ps.Worker(name=f"task{i}") for i in range(nb_workers)]

    # for each task, add three single required workers
    for i, task in enumerate(all_tasks):
        j = i + 1  # an overlap
        task.add_required_resources(workers[j - 1 : i + 3])

    return problem


def solve_problem(problem, debug=True):
    """create a solver instance, return True if sat else False"""
    solver = ps.SchedulingSolver(problem=problem, debug=debug)
    return solver.solve()


def test_schedule_single_fixed_duration_task() -> None:
    problem = ps.SchedulingProblem(name="SingleFixedDurationTaskScheduling", horizon=2)
    task = ps.FixedDurationTask(name="task", duration=2)

    solution = solve_problem(problem=problem)
    assert solution
    # task should have been scheduled with start at 0
    # and end at 2
    task_solution = solution.tasks[task.name]
    assert task_solution.start == 0
    assert task_solution.end == 2


def test_schedule_single_variable_duration_task() -> None:
    problem = ps.SchedulingProblem(name="SingleVariableDurationTaskScheduling")
    task = ps.VariableDurationTask(name="task")

    # add two constraints to set start and end
    ps.TaskStartAt(task=task, value=1)
    ps.TaskEndAt(task=task, value=4)

    solution = solve_problem(problem=problem)
    assert solution
    # task should have been scheduled with start at 0
    # and end at 2
    task_solution = solution.tasks[task.name]
    assert task_solution.start == 1
    assert task_solution.duration == 3
    assert task_solution.end == 4


def test_schedule_two_fixed_duration_task_with_precedence() -> None:
    problem = ps.SchedulingProblem(
        name="TwoFixedDurationTasksWithPrecedence", horizon=5
    )
    task_1 = ps.FixedDurationTask(name="task1", duration=2)
    task_2 = ps.FixedDurationTask(name="task2", duration=3)

    # add two constraints to set start and end
    ps.TaskStartAt(task=task_1, value=0)
    ps.TaskPrecedence(task_before=task_1, task_after=task_2)
    solution = solve_problem(problem=problem)
    assert solution

    task_1_solution = solution.tasks[task_1.name]
    task_2_solution = solution.tasks[task_2.name]

    assert task_1_solution.start == 0
    assert task_1_solution.end == 2
    assert task_2_solution.start == 2
    assert task_2_solution.end == 5


def test_schedule_single_task_single_resource() -> None:
    problem = ps.SchedulingProblem(name="SingleTaskSingleResource", horizon=7)

    task = ps.FixedDurationTask(name="task", duration=7)

    worker = ps.Worker(name="worker")

    task.add_required_resource(worker)

    solution = solve_problem(problem)
    assert solution
    # task should have been scheduled with start at 0
    # and end at 2
    task_solution = solution.tasks[task.name]

    assert task_solution.start == 0
    assert task_solution.end == 7
    assert task_solution.assigned_resources == ["worker"]


def test_schedule_two_tasks_two_alternative_workers() -> None:
    problem = ps.SchedulingProblem(name="TwoTasksTwoSelectWorkers", horizon=4)
    # two tasks
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    task_2 = ps.FixedDurationTask(name="task2", duration=2)
    # two workers
    worker_1 = ps.Worker(name="worker1")
    worker_2 = ps.Worker(name="worker2")

    task_1.add_required_resource(
        ps.SelectWorkers(list_of_workers=[worker_1, worker_2], nb_workers_to_select=1)
    )
    task_2.add_required_resource(
        ps.SelectWorkers(list_of_workers=[worker_1, worker_2], nb_workers_to_select=1)
    )

    solution = solve_problem(problem=problem)
    assert solution
    # each task should have one worker assigned
    task_1_solution = solution.tasks[task_1.name]
    task_2_solution = solution.tasks[task_2.name]
    assert len(task_1_solution.assigned_resources) == 1
    assert len(task_1_solution.assigned_resources) == 1
    assert task_1_solution.assigned_resources != task_2_solution.assigned_resources


def test_schedule_three_tasks_three_alternative_workers() -> None:
    problem = ps.SchedulingProblem(name="ThreeTasksThreeSelectWorkers")
    # two tasks
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    task_2 = ps.FixedDurationTask(name="task2", duration=2)
    task_3 = ps.FixedDurationTask(name="task3", duration=2)

    # three workers
    worker_1 = ps.Worker(name="worker1")
    worker_2 = ps.Worker(name="worker2")
    worker_3 = ps.Worker(name="worker3")

    all_workers = [worker_1, worker_2, worker_3]
    task_1.add_required_resource(
        ps.SelectWorkers(list_of_workers=all_workers, nb_workers_to_select=1)
    )
    task_2.add_required_resource(
        ps.SelectWorkers(list_of_workers=all_workers, nb_workers_to_select=2)
    )
    task_3.add_required_resource(
        ps.SelectWorkers(list_of_workers=all_workers, nb_workers_to_select=3)
    )

    solution = solve_problem(problem=problem)
    assert solution
    # each task should have one worker assigned
    assert len(solution.tasks[task_1.name].assigned_resources) == 1
    assert len(solution.tasks[task_2.name].assigned_resources) == 2
    assert len(solution.tasks[task_3.name].assigned_resources) == 3


def test_alternative_workers_2() -> None:
    # problem
    pb_alt = ps.SchedulingProblem(name="AlternativeWorkerExample")

    # tasks
    t1 = ps.FixedDurationTask(name="t1", duration=3)
    t2 = ps.FixedDurationTask(name="t2", duration=2)
    t3 = ps.FixedDurationTask(name="t3", duration=2)
    t4 = ps.FixedDurationTask(name="t4", duration=2)
    t5 = ps.FixedDurationTask(name="t5", duration=2)

    # resource requirements
    w1 = ps.Worker(name="W1")
    w2 = ps.Worker(name="W2")
    w3 = ps.Worker(name="W3")
    w4 = ps.SelectWorkers(
        list_of_workers=[w1, w2, w3], nb_workers_to_select=1, kind="exact"
    )
    w5 = ps.SelectWorkers(
        list_of_workers=[w1, w2, w3], nb_workers_to_select=2, kind="max"
    )
    w6 = ps.SelectWorkers(
        list_of_workers=[w1, w2, w3], nb_workers_to_select=3, kind="min"
    )

    # resource assignment
    t1.add_required_resource(w1)  # t1 only needs w1
    t2.add_required_resource(w2)  # t2 only needs w2
    t3.add_required_resource(w4)  # t3 needs one of w1, 2 or 3
    t4.add_required_resource(w5)  # t4 needs at most 2 of w1, w2 or 3
    t5.add_required_resource(w6)  # t5 needs at least 3 of w1, w2 or w3

    # add a makespan objective
    ps.ObjectiveMinimizeMakespan()

    # solve
    solver1 = ps.SchedulingSolver(problem=pb_alt, debug=False)
    solution = solver1.solve()

    assert solution.horizon == 5


def test_unsat_1():
    problem = ps.SchedulingProblem(name="Unsat1")

    task = ps.FixedDurationTask(name="task", duration=7)

    # add two constraints to set start and end
    # impossible to satisfy both
    ps.TaskStartAt(task=task, value=1)
    ps.TaskEndAt(task=task, value=4)

    assert not solve_problem(problem)


def test_solve_parallel():
    """a stress test with parallel mode solving"""
    problem = build_complex_problem("SolveParallel", 50)
    parallel_solver = ps.SchedulingSolver(problem=problem, parallel=True)
    solution = parallel_solver.solve()
    assert solution


def test_solve_max_time():
    """a stress test which"""
    problem = build_complex_problem("SolveMaxTime", 1000)
    ps.ObjectiveMinimizeMakespan()
    # 1s is not enough to solve this problem
    max_time_solver = ps.SchedulingSolver(problem=problem, max_time=1)
    solution = max_time_solver.solve()
    assert not solution


def test_solve_non_integer_max_time():
    """a stress test which"""
    problem = build_complex_problem(name="SolveMaxTime", n=1000)
    ps.ObjectiveMinimizeMakespan()
    # 0.5s is not enough to solve this problem
    max_time_solver = ps.SchedulingSolver(problem=problem, max_time=0.05)
    solution = max_time_solver.solve()
    assert not solution


#
# Objectives
#
def test_makespan_objective():
    problem = build_complex_problem(name="SolveMakeSpanObjective", n=20)
    # first look for a solution without optimization
    solution_1 = solve_problem(problem)
    assert solution_1

    horizon_without_optimization = solution_1.horizon
    # then add the objective and look for another solution
    ps.ObjectiveMinimizeMakespan()
    # another solution
    solution_2 = solve_problem(problem)
    assert solution_2

    horizon_with_optimization = solution_2.horizon
    # horizon_with_optimization should be less than horizon_without_optimization
    assert horizon_with_optimization < horizon_without_optimization


def test_flowtime_objective_big_problem():
    problem = build_complex_problem("SolveFlowTimeObjective", 5)  # long to compute
    ps.ObjectiveMinimizeFlowtime()
    assert solve_problem(problem)


def test_create_start_latest_objective_big_problem():
    problem = build_complex_problem("SolveStartLatestObjective", 10)
    ps.ObjectiveTasksStartLatest()
    assert solve_problem(problem)


def test_create_start_earliest_objective_big_problem():
    problem = build_complex_problem("SolveStartEarliestObjective", 10)
    ps.ObjectiveTasksStartEarliest()
    assert solve_problem(problem)


def test_start_earliest_1():
    problem = ps.SchedulingProblem(name="SolveStartEarliest1", horizon=30)

    task_1 = ps.FixedDurationTask(name="task1", duration=5)
    task_2 = ps.FixedDurationTask(name="task2", duration=3)

    ps.TaskStartAfter(task=task_1, value=10, kind="lax")
    ps.TaskPrecedence(task_before=task_1, task_after=task_2)

    ps.ObjectiveTasksStartEarliest()

    solution = solve_problem(problem)
    assert solution
    assert solution.tasks[task_1.name].start == 10
    assert solution.tasks[task_2.name].start == 15


def test_start_earliest_2():
    problem = ps.SchedulingProblem(name="SolveStartEarliest2", horizon=30)
    # only tasks 2 and 3 are constrained to be earliest
    task_1 = ps.FixedDurationTask(name="task1", duration=5)
    task_2 = ps.FixedDurationTask(name="task2", duration=3)
    task_3 = ps.FixedDurationTask(name="task3", duration=7)

    ps.TaskStartAt(task=task_1, value=8)
    ps.TaskPrecedence(task_before=task_1, task_after=task_2)

    ob = ps.ObjectiveTasksStartEarliest(list_of_tasks=[task_2, task_3])

    solution = solve_problem(problem)
    assert solution
    # the weighted start time should be:
    # 0 * 1 + 8 * 1 + 13 * 1
    assert solution.indicators[ob.target.name] == 21


def test_start_latest_1():
    problem = ps.SchedulingProblem(name="SolveStartLatest1", horizon=51)
    # only one task, the solver should schedule a start time at 0
    task_1 = ps.FixedDurationTask(name="task1", duration=2)
    task_2 = ps.FixedDurationTask(name="task2", duration=3)

    ps.TaskPrecedence(task_before=task_1, task_after=task_2)

    ps.ObjectiveTasksStartLatest()

    solution = solve_problem(problem)
    assert solution
    # check that the task is not scheduled to start à 0
    # the only solution is 1
    assert solution.tasks[task_1.name].start == 51 - (3 + 2)
    assert solution.tasks[task_2.name].start == 51 - 3


def test_minimize_greatest_start_time():
    problem = ps.SchedulingProblem(name="MinimizeGreatestStartTime")
    # only one task, the solver should schedule a start time at 0
    task_1 = ps.FixedDurationTask(name="task1", duration=2)
    task_2 = ps.FixedDurationTask(name="task2", duration=3)
    ps.TaskPrecedence(task_before=task_2, task_after=task_1)
    ps.TaskStartAt(task=task_2, value=8)
    ob = ps.ObjectiveMinimizeGreatestStartTime()
    solution = solve_problem(problem)
    assert solution
    assert solution.indicators[ob.target.name] == 11
    assert solution.tasks[task_1.name].start == 11
    assert solution.tasks[task_2.name].start == 8


def test_priorities():
    problem = ps.SchedulingProblem(name="SolvePriorities")
    task_1 = ps.FixedDurationTask(name="task1", duration=2, priority=1)
    task_2 = ps.FixedDurationTask(name="task2", duration=2, priority=10)
    task_3 = ps.FixedDurationTask(name="task3", duration=2, priority=100)

    ps.TasksDontOverlap(task_1=task_1, task_2=task_2)
    ps.TasksDontOverlap(task_1=task_2, task_2=task_3)
    ps.TasksDontOverlap(task_1=task_1, task_2=task_3)

    ps.ObjectivePriorities()

    # set debug to False because assert_and_track
    # does not properly handles optimization
    solution = solve_problem(problem, debug=False)
    assert solution
    # check that the task is not scheduled to start à 0
    # the only solution is 1
    assert solution.tasks[task_3.name].start < solution.tasks[task_2.name].start
    assert solution.tasks[task_2.name].start < solution.tasks[task_1.name].start


#
# Total work_amount, resource productivity
#
def test_work_amount_1() -> None:
    pb = ps.SchedulingProblem(name="WorkAmount1", horizon=20)
    task_1 = ps.VariableDurationTask(name="task1", work_amount=15)
    machine_1 = ps.Worker(name="M1", productivity=5)
    task_1.add_required_resource(machine_1)
    solution = ps.SchedulingSolver(problem=pb).solve()
    assert solution
    assert solution.tasks[task_1.name].duration == 3


def test_work_amount_2():
    problem = ps.SchedulingProblem(name="WorkAmount2")

    task_1 = ps.VariableDurationTask(name="task1", work_amount=11)
    # create one worker with a productivity of 2
    worker_1 = ps.Worker(name="Worker1", productivity=2)
    task_1.add_required_resource(worker_1)
    # solve
    solution = solve_problem(problem)
    assert solution
    # the expected duration for task 1 is 6
    assert solution.tasks[task_1.name].duration == 6


def test_work_amount_3():
    # try the same problem than above, but with one more resource
    # check that the task duration is lower
    problem = ps.SchedulingProblem(name="WorkAmount3", horizon=4)

    task_1 = ps.VariableDurationTask(name="task1", work_amount=11)
    # create two workers
    worker_1 = ps.Worker(name="Worker1", productivity=2)
    worker_2 = ps.Worker(name="Worker2", productivity=3)
    task_1.add_required_resources([worker_1, worker_2])
    # solve
    solution = solve_problem(problem)
    assert solution
    assert solution.tasks[task_1.name].duration < 6


#
# Pinedo
#
def test_pinedo_2_3_2() -> None:
    """Example 4.1.5 of the Pinedo book. The solution is expected to be:
    1,3,6,5,4,2"""
    problem = ps.SchedulingProblem(name="PinedoExample2.3.2")

    durations = [8, 7, 7, 2, 3, 2, 2, 8, 8, 15]

    jobs = []

    i = 1
    for pj in durations:
        jobs.append(ps.FixedDurationTask(name=f"task{i}", duration=pj))
        i += 1

    # precedences
    precs_graph = [
        (1, 2),
        (1, 3),
        (2, 10),
        (3, 10),
        (5, 3),
        (4, 5),
        (4, 6),
        (5, 8),
        (6, 7),
        (7, 9),
        (5, 9),
        (7, 8),
    ]

    for i, j in precs_graph:
        ps.TaskPrecedence(task_before=jobs[i - 1], task_after=jobs[j - 1])
    # two machines
    machine_1 = ps.Worker(name="M1")
    machine_2 = ps.Worker(name="M2")

    for j in jobs:
        j.add_required_resource(
            ps.SelectWorkers(list_of_workers=[machine_1, machine_2])
        )  # , machine_3]))

    # non delay schedule
    ps.ResourceNonDelay(resource=machine_1)
    ps.ResourceNonDelay(resource=machine_2)

    ps.ObjectiveMinimizeMakespan()

    solver = ps.SchedulingSolver(problem=problem, max_time=30)
    solution = solver.solve()

    assert solution.horizon == 31


def test_pinedo_3_2_5() -> None:
    """Example 3.2.5 of the Pinedo book. The solution is expected to be:
    1,3,6,5,4,2"""
    problem = ps.SchedulingProblem(name="PinedoExample3.2.5")

    J1 = ps.FixedDurationTask(
        name="J1", duration=4, release_date=0, due_date=8, due_date_is_deadline=False
    )
    J2 = ps.FixedDurationTask(
        name="J2", duration=2, release_date=1, due_date=12, due_date_is_deadline=False
    )
    J3 = ps.FixedDurationTask(
        name="J3", duration=6, release_date=3, due_date=11, due_date_is_deadline=False
    )
    J4 = ps.FixedDurationTask(
        name="J4", duration=5, release_date=5, due_date=10, due_date_is_deadline=False
    )

    M1 = ps.Worker(name="M1")
    J1.add_required_resource(M1)
    J2.add_required_resource(M1)
    J3.add_required_resource(M1)
    J4.add_required_resource(M1)

    ind = ps.IndicatorMaximumLateness()
    ps.ObjectiveMinimizeIndicator(target=ind, weight=1)

    solver = ps.SchedulingSolver(problem=problem)
    solution = solver.solve()
    assert solution
    assert solution.tasks["J1"].start == 0
    assert solution.tasks["J3"].start == 4
    assert solution.tasks["J4"].start == 10
    assert solution.tasks["J2"].start == 15


def test_pinedo_3_3_3() -> None:
    problem = ps.SchedulingProblem(name="PinedoExample3.3.3")

    J1 = ps.FixedDurationTask(
        name="J1", duration=7, due_date=9, due_date_is_deadline=False
    )
    J2 = ps.FixedDurationTask(
        name="J2", duration=8, due_date=17, due_date_is_deadline=False
    )
    J3 = ps.FixedDurationTask(
        name="J3", duration=4, due_date=18, due_date_is_deadline=False
    )
    J4 = ps.FixedDurationTask(
        name="J4", duration=6, due_date=19, due_date_is_deadline=False
    )
    J5 = ps.FixedDurationTask(
        name="J5", duration=6, due_date=21, due_date_is_deadline=False
    )

    M1 = ps.Worker(name="M1")

    for j in [J1, J2, J3, J4, J5]:
        j.add_required_resource(M1)

    ind = ps.IndicatorNumberOfTardyTasks()
    ps.ObjectiveMinimizeIndicator(target=ind, weight=1)

    solver = ps.SchedulingSolver(problem=problem, debug=True)
    solution = solver.solve()

    assert solution
    assert solution.indicators[ind.name] == 2


def test_pinedo_3_4_5() -> None:
    problem = ps.SchedulingProblem(name="PinedoExample3.4.5")

    J1 = ps.FixedDurationTask(
        name="J1", duration=121, due_date=260, due_date_is_deadline=False
    )
    J2 = ps.FixedDurationTask(
        name="J2", duration=79, due_date=266, due_date_is_deadline=False
    )
    J3 = ps.FixedDurationTask(
        name="J3", duration=147, due_date=266, due_date_is_deadline=False
    )
    J4 = ps.FixedDurationTask(
        name="J4", duration=83, due_date=336, due_date_is_deadline=False
    )
    J5 = ps.FixedDurationTask(
        name="J5", duration=130, due_date=337, due_date_is_deadline=False
    )

    M1 = ps.Worker(name="M1")

    for j in [J1, J2, J3, J4, J5]:
        j.add_required_resource(M1)

    ind = ps.IndicatorTardiness()
    ps.ObjectiveMinimizeIndicator(target=ind, weight=1)

    solver = ps.SchedulingSolver(problem=problem, debug=False)
    solution = solver.solve()

    assert solution
    assert solution.indicators[ind.name] == 370


def test_pinedo_3_6_3() -> None:
    problem = ps.SchedulingProblem(name="PinedoExample3.6.3")
    J1 = ps.FixedDurationTask(
        name="J1", priority=4, duration=12, due_date=16, due_date_is_deadline=False
    )
    J2 = ps.FixedDurationTask(
        name="J2", priority=5, duration=8, due_date=26, due_date_is_deadline=False
    )
    J3 = ps.FixedDurationTask(
        name="J3", priority=3, duration=15, due_date=25, due_date_is_deadline=False
    )
    J4 = ps.FixedDurationTask(
        name="J4", priority=5, duration=9, due_date=27, due_date_is_deadline=False
    )

    M1 = ps.Worker(name="M1")

    for j in [J1, J2, J3, J4]:
        j.add_required_resource(M1)

    ind = ps.IndicatorTardiness()
    ps.ObjectiveMinimizeIndicator(target=ind, weight=1)

    solver = ps.SchedulingSolver(problem=problem)
    solution = solver.solve()

    assert solution
    assert solution.indicators[ind.name] == 67


def test_pinedo_4_1_5() -> None:
    """Example 4.1.5 of the Pinedo book. In the book, the heuristics leads to
    1,3,6,5,4,2"""
    problem = ps.SchedulingProblem(name="PinedoExample4.1.5")

    task_1 = ps.FixedDurationTask(
        name="task1", duration=106, due_date=180, due_date_is_deadline=False
    )
    task_2 = ps.FixedDurationTask(
        name="task2", duration=100, due_date=180, due_date_is_deadline=False
    )
    task_3 = ps.FixedDurationTask(
        name="task3", duration=96, due_date=180, due_date_is_deadline=False
    )
    task_4 = ps.FixedDurationTask(
        name="task4", duration=22, due_date=180, due_date_is_deadline=False
    )
    task_5 = ps.FixedDurationTask(
        name="task5", duration=20, due_date=180, due_date_is_deadline=False
    )
    task_6 = ps.FixedDurationTask(
        name="task6", duration=2, due_date=180, due_date_is_deadline=False
    )

    single_machine = ps.Worker(name="Worker1")

    all_tasks = [task_1, task_2, task_3, task_4, task_5, task_6]

    for t in all_tasks:  # all the tasks are processed on the same machine
        t.add_required_resource(single_machine)

    total_tardiness = ps.IndicatorTardiness(list_of_tasks=all_tasks)
    total_earliness = ps.IndicatorEarliness(list_of_tasks=all_tasks)

    ob1 = ps.ObjectiveMinimizeIndicator(target=total_tardiness, weight=1)
    ob2 = ps.ObjectiveMinimizeIndicator(target=total_earliness, weight=1)

    solution = solve_problem(problem)
    assert solution
    # here, the solution is a bit different: 1, 4, 5, 6, 3, 2
    # the optimial sum is 360
    assert (
        solution.indicators[total_tardiness.name]
        + solution.indicators[total_earliness.name]
        == 360
    )


def test_pinedo_4_2_3() -> None:
    problem = ps.SchedulingProblem(name="PinedoExample4.2.3")

    task_1 = ps.FixedDurationTask(
        name="task1", duration=4, due_date=10, due_date_is_deadline=True
    )
    task_2 = ps.FixedDurationTask(
        name="task2", duration=6, due_date=12, due_date_is_deadline=True
    )
    task_3 = ps.FixedDurationTask(
        name="task3", duration=2, due_date=14, due_date_is_deadline=True
    )
    task_4 = ps.FixedDurationTask(
        name="task4", duration=4, due_date=18, due_date_is_deadline=True
    )
    task_5 = ps.FixedDurationTask(
        name="task5", duration=2, due_date=18, due_date_is_deadline=True
    )

    single_machine = ps.Worker(name="Worker1")

    all_tasks = [task_1, task_2, task_3, task_4, task_5]

    for t in all_tasks:  # all the tasks are processed on the same machine
        t.add_required_resource(single_machine)

    ob1 = ps.ObjectiveMinimizeFlowtime()

    solver = ps.SchedulingSolver(problem=problem)
    solution_1 = solver.solve()

    assert solution_1
    assert solution_1.indicators[ob1.target.name] == 52


def test_pinedo_6_1_6() -> None:
    pb = ps.SchedulingProblem(name="Pinedo6.1.6")
    durations = [[5, 4, 4, 3], [5, 4, 4, 6], [3, 2, 3, 3], [6, 4, 4, 2], [3, 4, 1, 5]]

    # create machines
    M1 = ps.Worker(name="M1")
    M2 = ps.Worker(name="M2")
    M3 = ps.Worker(name="M3")
    M4 = ps.Worker(name="M4")

    machines = [M1, M2, M3, M4]

    # create tasks
    job_number = 1
    for job_number in range(5):
        j = 0
        tasks_for_this_job = []
        for d in durations[job_number]:
            t = ps.FixedDurationTask(name=f"{d}(T{job_number+1},{j+1})", duration=d)
            t.add_required_resource(machines[j])
            tasks_for_this_job.append(t)
            j += 1
        # and precedence
        for i in range(len(tasks_for_this_job) - 1):
            ps.TaskPrecedence(
                task_before=tasks_for_this_job[i], task_after=tasks_for_this_job[i + 1]
            )

    ps.ObjectiveMinimizeMakespan()
    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()

    assert solution
    assert solution.horizon == 32


#
# Resource constraints
#
def test_all_same_distinct_workers():
    pb = ps.SchedulingProblem(name="AllSameDistinctWorkers")

    task_1 = ps.FixedDurationTask(name="task1", duration=2)
    task_2 = ps.FixedDurationTask(name="task2", duration=2)
    task_3 = ps.FixedDurationTask(name="task3", duration=2)
    task_4 = ps.FixedDurationTask(name="task4", duration=2)

    worker_1 = ps.Worker(name="John")
    worker_2 = ps.Worker(name="Bob")

    res_for_t1 = ps.SelectWorkers(
        list_of_workers=[worker_1, worker_2], nb_workers_to_select=1
    )
    res_for_t2 = ps.SelectWorkers(
        list_of_workers=[worker_1, worker_2], nb_workers_to_select=1
    )
    res_for_t3 = ps.SelectWorkers(
        list_of_workers=[worker_1, worker_2], nb_workers_to_select=1
    )
    res_for_t4 = ps.SelectWorkers(
        list_of_workers=[worker_1, worker_2], nb_workers_to_select=1
    )

    task_1.add_required_resource(res_for_t1)
    task_2.add_required_resource(res_for_t2)
    task_3.add_required_resource(res_for_t3)
    task_4.add_required_resource(res_for_t4)

    ps.SameWorkers(select_workers_1=res_for_t1, select_workers_2=res_for_t2)
    ps.SameWorkers(select_workers_1=res_for_t3, select_workers_2=res_for_t4)
    ps.DistinctWorkers(select_workers_1=res_for_t2, select_workers_2=res_for_t4)

    solver = ps.SchedulingSolver(problem=pb)
    solution = solver.solve()
    assert solution
    assert solution.horizon == 4


#
# Export parameters
#
def test_export_parameters():
    pb = ps.SchedulingProblem(name="ExportParameters")
    solver = ps.SchedulingSolver(problem=pb)
    solver.initialize()
    solver.get_parameters_description()


def test_single_math_indicator_1():
    pb = ps.SchedulingProblem(name="SingleObjectiveMath", horizon=20)
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    indicator_1 = ps.IndicatorFromMathExpression(
        name="Task1End", expression=task_1._end
    )
    ps.ObjectiveMaximizeIndicator(name="MaximizeTask1End", target=indicator_1)
    solution = ps.SchedulingSolver(problem=pb).solve()
    assert solution
    assert solution.tasks[task_1.name].end == 20


#
# Muti optimizer
#
def test_multi_weighted_1():
    pb = ps.SchedulingProblem(name="MultiObjective1Weigthed", horizon=20)
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    task_2 = ps.FixedDurationTask(name="task2", duration=3)
    ps.ConstraintFromExpression(expression=task_1._end == 20 - task_2._start)
    indicator_1 = ps.IndicatorFromMathExpression(
        name="Task1End", expression=task_1._end
    )
    indicator_2 = ps.IndicatorFromMathExpression(
        name="Task2Start", expression=task_2._start
    )
    ps.ObjectiveMaximizeIndicator(name="MaximizeTask1End", target=indicator_1, weight=1)
    ps.ObjectiveMaximizeIndicator(
        name="MaximizeTask2Start", target=indicator_2, weight=1
    )
    solution = ps.SchedulingSolver(problem=pb).solve()
    assert solution
    assert (
        solution.indicators[indicator_1.name] + solution.indicators[indicator_2.name]
        == 20
    )


def test_multi_weighted_2():
    pb = ps.SchedulingProblem(name="MultiObjectiveWeighted2", horizon=20)
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    task_2 = ps.FixedDurationTask(name="task2", duration=3)
    ps.ConstraintFromExpression(expression=task_1._end == 20 - task_2._start)
    indicator_1 = ps.IndicatorFromMathExpression(
        name="Task1End", expression=task_1._end
    )
    indicator_2 = ps.IndicatorFromMathExpression(
        name="Task2Start", expression=task_2._start
    )
    ps.ObjectiveMaximizeIndicator(name="MaximizeTask1End", target=indicator_1, weight=1)
    ps.ObjectiveMaximizeIndicator(
        name="MaximizeTask2Start", target=indicator_2, weight=2
    )
    solution = ps.SchedulingSolver(problem=pb).solve()

    assert solution
    assert (
        solution.indicators[indicator_1.name]
        + 2 * solution.indicators[indicator_2.name]
        == 37
    )


def test_multi_optimize_lex():
    # lex
    pb = ps.SchedulingProblem(name="MultiObjectiveOptimizeLex", horizon=20)
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    task_2 = ps.FixedDurationTask(name="task2", duration=3)
    ps.ConstraintFromExpression(expression=task_1._end == 20 - task_2._start)
    indicator_1 = ps.IndicatorFromMathExpression(
        name="Task1End", expression=task_1._end
    )
    indicator_2 = ps.IndicatorFromMathExpression(
        name="Task2Start", expression=task_2._start
    )
    ps.ObjectiveMaximizeIndicator(name="MaximizeTask1End", target=indicator_1)
    ps.ObjectiveMaximizeIndicator(name="MaximizeTask2Start", target=indicator_2)

    solver = ps.SchedulingSolver(
        problem=pb, optimizer="optimize", optimize_priority="lex"
    )
    solution = solver.solve()
    assert solution
    assert (
        solution.indicators[indicator_1.name] + solution.indicators[indicator_2.name]
        == 20
    )


def test_multi_optimize_box():
    # box
    pb = ps.SchedulingProblem(name="MultiObjectiveOptimizeBox", horizon=20)
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    task_2 = ps.FixedDurationTask(name="task2", duration=3)
    ps.ConstraintFromExpression(expression=task_1._end == 20 - task_2._start)
    indicator_1 = ps.IndicatorFromMathExpression(
        name="Task1End", expression=task_1._end
    )
    indicator_2 = ps.IndicatorFromMathExpression(
        name="Task2Start", expression=task_2._start
    )
    ps.ObjectiveMaximizeIndicator(name="MaximizeTask1End", target=indicator_1)
    ps.ObjectiveMaximizeIndicator(name="MaximizeTask2Start", target=indicator_2)

    solver = ps.SchedulingSolver(
        problem=pb, optimizer="optimize", optimize_priority="box"
    )
    solution = solver.solve()
    assert solution
    assert (
        solution.indicators[indicator_1.name] + solution.indicators[indicator_2.name]
        == 20
    )


def test_multi_optimize_pareto():
    # Pareto
    pb = ps.SchedulingProblem(name="MultiObjectiveOptimizePareto", horizon=20)
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    task_2 = ps.FixedDurationTask(name="task2", duration=3)
    ps.ConstraintFromExpression(expression=task_1._end == 20 - task_2._start)
    indicator_1 = ps.IndicatorFromMathExpression(
        name="Task1End", expression=task_1._end
    )
    indicator_2 = ps.IndicatorFromMathExpression(
        name="Task2Start", expression=task_2._start
    )
    ps.ObjectiveMaximizeIndicator(name="MaximizeTask1End", target=indicator_1)
    ps.ObjectiveMaximizeIndicator(name="MaximizeTask2Start", target=indicator_2)

    solver = ps.SchedulingSolver(
        problem=pb, optimizer="optimize", optimize_priority="pareto"
    )
    solution = solver.solve()
    nb_solution = 0
    while solution:
        print("Found solution:")
        print("\t task_1.end: f{solution.tasks[task_1.end]}")
        print("\t task_2.start: f{solution.tasks[task_2.start]}")
        solution = solver.solve()
        nb_solution += 1

    assert nb_solution == 18


#
# Dynamic resource assignment
#
def test_dynamic_resource_assignment():
    pb = ps.SchedulingProblem(name="DynamicAssignment")

    T_1 = ps.VariableDurationTask(name="T_1", work_amount=150)

    M_1 = ps.Worker(name="M_1", productivity=5)
    M_2 = ps.Worker(name="M_2", productivity=20)

    # not dynamic
    # T_1.add_required_resources([M_1, M_2])

    # dynamic
    T_1.add_required_resource(M_1)
    T_1.add_required_resource(M_2, dynamic=True)

    ps.ResourceUnavailable(resource=M_2, list_of_time_intervals=[(0, 10)])

    ps.ObjectiveMinimizeMakespan()

    solver = ps.SchedulingSolver(problem=pb)

    solution = solver.solve()
    assert solution
    assert solution.horizon == 14


#
# Find another solution
#
def test_find_another_solution_solve_before():
    problem = ps.SchedulingProblem(name="FindAnotherSolutionSolveBefore", horizon=6)
    task_1 = ps.FixedDurationTask(name="task1", duration=2)
    solver = ps.SchedulingSolver(problem=problem)
    with pytest.raises(AssertionError):
        solver.find_another_solution_for_variable(task_1._start)


def test_find_another_solution_variable_1():
    problem = ps.SchedulingProblem(name="FindAnotherSolutionSingleVariable1", horizon=6)
    solutions = []

    task_1 = ps.FixedDurationTask(name="task1", duration=2)
    solver = ps.SchedulingSolver(problem=problem)
    solution = solver.solve()

    while solution:
        solutions.append(solution.tasks[task_1.name].start)
        solution = solver.find_another_solution_for_variable(task_1._start)
    # there should be 5 solutions
    assert solutions == [0, 1, 2, 3, 4]


def test_find_another_solution_variable_2() -> None:
    pb = ps.SchedulingProblem(name="FindAnotherSolutionSingleVariable2", horizon=4)
    t = ps.FixedDurationTask(name="T1", duration=2)
    # three are three possible schedules : start=0, start=1 or start=2
    s = ps.SchedulingSolver(problem=pb)
    solution = s.solve()
    assert solution
    s.find_another_solution_for_variable(t._start)
    solution2 = s.solve()
    assert solution2
    s.find_another_solution_for_variable(t._start)
    solution3 = s.solve()
    assert solution2
    s.find_another_solution_for_variable(t._start)
    solution = s.solve()
    assert not solution


def test_find_another_solution_global_1() -> None:
    pb = ps.SchedulingProblem(name="FindAnotherSolution", horizon=4)
    t1 = ps.FixedDurationTask(name="T1", duration=2)
    t2 = ps.FixedDurationTask(name="T2", duration=2)
    t3 = ps.FixedDurationTask(name="T3", duration=2)
    # three are 3 ** 3 = 27 different schedules
    s = ps.SchedulingSolver(problem=pb)
    nb_sol = 0
    solution = s.solve()
    while solution:
        s.find_another_solution()
        solution = s.solve()
        nb_sol += 1
    assert nb_sol == 27


#
# Logics
#
def test_qf_idl_logics():
    problem = ps.SchedulingProblem(name="LogicsQFIDL", horizon=6)
    task_1 = ps.FixedDurationTask(name="task1", duration=2)
    solver = ps.SchedulingSolver(problem=problem, logics="QF_UFIDL")
    assert solver.solve()
