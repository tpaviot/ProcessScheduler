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
    pb_alt.add_objective_makespan()

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


# # TODO: failing test on some azure instances
# # def test_solve_max_time():
# #     """ a stress test which  """
# #     problem = build_complex_problem('SolveMaxTime', 1000)
# #     problem.add_objective_makespan()
# #     # 1s is not enough to solve this problem
# #     max_time_solver = ps.SchedulingSolver(problem, max_time=1)
# #     solution = max_time_solver.solve()
# #     assert not (solution)


def test_solve_non_integer_max_time():
    """a stress test which"""
    problem = build_complex_problem(name="SolveMaxTime", n=1000)
    problem.add_objective_makespan()
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
    problem.add_objective_makespan()
    # another solution
    solution_2 = solve_problem(problem)
    assert solution_2

    horizon_with_optimization = solution_2.horizon
    # horizon_with_optimization should be less than horizon_without_optimization
    assert horizon_with_optimization < horizon_without_optimization


def test_flowtime_objective_big_problem():
    problem = build_complex_problem("SolveFlowTimeObjective", 5)  # long to compute
    problem.add_objective_flowtime()
    assert solve_problem(problem)


def test_start_latest_objective_big_problem():
    problem = build_complex_problem("SolveStartLatestObjective", 10)
    problem.add_objective_start_latest()
    assert solve_problem(problem)


def test_start_earliest_objective_big_problem():
    problem = build_complex_problem("SolveStartEarliestObjective", 10)
    problem.add_objective_start_earliest()
    assert solve_problem(problem)


def test_start_latest():
    problem = ps.SchedulingProblem(name="SolveStartLatest", horizon=51)
    # only one task, the solver should schedule a start time at 0
    task_1 = ps.FixedDurationTask(name="task1", duration=2)
    task_2 = ps.FixedDurationTask(name="task2", duration=3)

    ps.TaskPrecedence(task_before=task_1, task_after=task_2)

    problem.add_objective_start_latest()
    solution = solve_problem(problem)
    assert solution
    # check that the task is not scheduled to start à 0
    # the only solution is 1
    assert solution.tasks[task_1.name].start == 51 - (3 + 2)
    assert solution.tasks[task_2.name].start == 51 - 3


def test_priorities():
    problem = ps.SchedulingProblem(name="SolvePriorities")
    task_1 = ps.FixedDurationTask(name="task1", duration=2, priority=1)
    task_2 = ps.FixedDurationTask(name="task2", duration=2, priority=10)
    task_3 = ps.FixedDurationTask(name="task3", duration=2, priority=100)

    ps.TasksDontOverlap(task_1=task_1, task_2=task_2)
    ps.TasksDontOverlap(task_1=task_2, task_2=task_3)
    ps.TasksDontOverlap(task_1=task_1, task_2=task_3)

    problem.add_objective_priorities()

    # set debug to False because assert_and_track
    # does not properly handles optimization
    solution = solve_problem(problem, debug=False)
    assert solution
    # check that the task is not scheduled to start à 0
    # the only solution is 1
    assert solution.tasks[task_3.name].start < solution.tasks[task_2.name].start
    assert solution.tasks[task_2.name].start < solution.tasks[task_1.name].start


#
# Find other solution
#
def test_find_another_solution():
    problem = ps.SchedulingProblem(name="FindAnotherSolution", horizon=6)
    solutions = []

    task_1 = ps.FixedDurationTask(name="task1", duration=2)
    solver = ps.SchedulingSolver(problem=problem)
    solution = solver.solve()

    while solution:
        solutions.append(solution.tasks[task_1.name].start)
        solution = solver.find_another_solution(task_1._start)
    # there should be 5 solutions
    assert solutions == [0, 1, 2, 3, 4]


def test_find_another_solution_solve_before():
    problem = ps.SchedulingProblem(name="FindAnotherSolutionSolveBefore", horizon=6)

    task_1 = ps.FixedDurationTask(name="task1", duration=2)
    solver = ps.SchedulingSolver(problem=problem)
    with pytest.raises(AssertionError):
        solver.find_another_solution(task_1._start)


#
# Total work_amount, resource productivity
#
def test_work_amount_1():
    problem = ps.SchedulingProblem(name="WorkAmount")

    task_1 = ps.VariableDurationTask(name="task1", work_amount=11)
    # create one worker with a productivity of 2
    worker_1 = ps.Worker(name="Worker1", productivity=2)
    task_1.add_required_resource(worker_1)
    # solve
    solution = solve_problem(problem)
    assert solution
    # the expected duration for task 1 is 6
    assert solution.tasks[task_1.name].duration == 6


def test_work_amount_2():
    # try the same problem than above, but with one more resource
    # check that the task duration is lower
    problem = ps.SchedulingProblem(name="WorkAmount", horizon=4)

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
