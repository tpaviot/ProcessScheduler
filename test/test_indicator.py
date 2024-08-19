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


#
# Flowtime
#
def test_indicator_flowtime() -> None:
    problem = ps.SchedulingProblem(name="IndicatorFlowTime", horizon=2)
    t_1 = ps.FixedDurationTask(name="t1", duration=2)
    t_2 = ps.FixedDurationTask(name="t2", duration=2)

    i_1 = ps.IndicatorFromMathExpression(
        name="FlowTime", expression=t_1._end + t_2._end
    )

    solution = ps.SchedulingSolver(problem=problem, debug=True).solve()

    assert solution
    assert solution.indicators[i_1.name] == 4


#
# Tardiness
#
def test_indicator_tardiness_1() -> None:
    problem = ps.SchedulingProblem(name="IndicatorTardiness1")
    t_1 = ps.FixedDurationTask(
        name="T1", duration=5, due_date=2, due_date_is_deadline=False
    )
    ps.TaskStartAt(task=t_1, value=0)
    tard_1 = ps.IndicatorTardiness()
    solution = ps.SchedulingSolver(problem=problem).solve()
    assert solution
    assert solution.indicators[tard_1.name] == 3


def test_indicator_tardiness_2() -> None:
    problem = ps.SchedulingProblem(name="IndicatorTardiness2")
    t_1 = ps.FixedDurationTask(
        name="T1", duration=5, due_date=2, due_date_is_deadline=False
    )
    t_2 = ps.FixedDurationTask(
        name="T2", duration=7, due_date=5, due_date_is_deadline=False
    )
    ps.TaskStartAt(task=t_1, value=0)  # tardiness 3
    ps.TaskStartAt(task=t_2, value=0)  # tardiness 2
    tard_1 = ps.IndicatorTardiness()
    solution = ps.SchedulingSolver(problem=problem).solve()
    assert solution
    assert solution.indicators[tard_1.name] == 5


def test_indicator_tardiness_3() -> None:
    problem = ps.SchedulingProblem(name="IndicatorTardiness3")
    t_1 = ps.FixedDurationTask(
        name="T1", duration=5, due_date=20, due_date_is_deadline=False
    )
    t_2 = ps.FixedDurationTask(
        name="T2", duration=7, due_date=25, due_date_is_deadline=False
    )
    ps.TaskStartAt(task=t_1, value=0)  # tardiness 0
    ps.TaskStartAt(task=t_2, value=0)  # tardiness 0
    tard_1 = ps.IndicatorTardiness()
    solution = ps.SchedulingSolver(problem=problem).solve()
    assert solution
    assert solution.indicators[tard_1.name] == 0


def test_indicator_tardiness_4() -> None:
    """tardiness for a list of resources"""
    problem = ps.SchedulingProblem(name="IndicatorTardiness4")
    t_1 = ps.FixedDurationTask(
        name="T1", duration=5, due_date=20, due_date_is_deadline=False
    )
    t_2 = ps.FixedDurationTask(
        name="T2", duration=7, due_date=25, due_date_is_deadline=False
    )
    t_3 = ps.FixedDurationTask(
        name="T3", duration=11, due_date=5, due_date_is_deadline=False
    )

    ps.TaskStartAt(task=t_1, value=0)  # tardiness 0
    ps.TaskStartAt(task=t_2, value=0)  # tardiness 0
    ps.TaskStartAt(task=t_3, value=0)  # tardiness 6
    tard_1 = ps.IndicatorTardiness(list_of_tasks=[t_2, t_3])
    solution = ps.SchedulingSolver(problem=problem).solve()
    assert solution
    assert solution.indicators[tard_1.name] == 6


#
# Number of tardy tasks
#
def test_indicator_number_of_tardy_tasks_1() -> None:
    problem = ps.SchedulingProblem(name="IndicatorNumberOfTardyTasks1")
    t_1 = ps.FixedDurationTask(
        name="T1", duration=5, due_date=20, due_date_is_deadline=False
    )
    t_2 = ps.FixedDurationTask(
        name="T2", duration=7, due_date=25, due_date_is_deadline=False
    )
    t_3 = ps.FixedDurationTask(
        name="T3", duration=11, due_date=5, due_date_is_deadline=False
    )

    ps.TaskStartAt(task=t_1, value=0)  # tardiness 0  not tardy
    ps.TaskStartAt(task=t_2, value=0)  # tardiness 0, not tardy
    ps.TaskStartAt(task=t_3, value=0)  # tardiness 6, tardy
    tard_1 = ps.IndicatorNumberOfTardyTasks()
    solution = ps.SchedulingSolver(problem=problem).solve()
    assert solution
    assert solution.indicators[tard_1.name] == 1


def test_indicator_number_of_tardy_tasks_2() -> None:
    problem = ps.SchedulingProblem(name="IndicatorNumberOfTardyTasks2")
    n = 10  # 10 tardy tasks
    for i in range(n):
        t_i = ps.FixedDurationTask(
            name=f"T_{i}", duration=i + 2, due_date=i + 1, due_date_is_deadline=False
        )
        ps.TaskStartAt(task=t_i, value=0)  # tardiness 0  not tardy
    for i in range(n, n + 10):  # 10 untardy tasks
        t_i = ps.FixedDurationTask(
            name=f"T_{i}", duration=i + 1, due_date=i + 5, due_date_is_deadline=False
        )
        ps.TaskStartAt(task=t_i, value=0)  # tardiness 0  not tardy

    tard_1 = ps.IndicatorNumberOfTardyTasks()
    solution = ps.SchedulingSolver(problem=problem).solve()
    assert solution
    assert solution.indicators[tard_1.name] == 10


def test_indicator_number_of_tardy_tasks_3() -> None:
    problem = ps.SchedulingProblem(name="IndicatorNumberOfTardyTasks3")
    t_1 = ps.FixedDurationTask(
        name="T1", duration=5, due_date=5, due_date_is_deadline=False
    )
    t_2 = ps.FixedDurationTask(
        name="T2", duration=7, due_date=6, due_date_is_deadline=False
    )
    t_3 = ps.FixedDurationTask(
        name="T3", duration=11, due_date=5, due_date_is_deadline=False
    )

    ps.TaskStartAt(task=t_1, value=0)  # lateness 0
    ps.TaskStartAt(task=t_2, value=0)  # lateness 1
    ps.TaskStartAt(task=t_3, value=0)  # lateness 6
    tard_1 = ps.IndicatorNumberOfTardyTasks(list_of_tasks=[t_1, t_2])
    solution = ps.SchedulingSolver(problem=problem).solve()
    assert solution
    assert solution.indicators[tard_1.name] == 1


#
# Earlyness
#
def test_indicator_earliness_1() -> None:
    problem = ps.SchedulingProblem(name="IndicatorMaximumEarlyness1")

    task_1 = ps.FixedDurationTask(
        name="task1", duration=106, due_date=180, due_date_is_deadline=False
    )
    task_2 = ps.FixedDurationTask(
        name="task2", duration=100, due_date=180, due_date_is_deadline=False
    )
    task_3 = ps.FixedDurationTask(
        name="task3", duration=96, due_date=180, due_date_is_deadline=False
    )
    single_machine = ps.Worker(name="Worker1")

    for t in [
        task_1,
        task_2,
        task_3,
    ]:  # all the tasks are processed on the same machine
        t.add_required_resource(single_machine)

    total_earliness = ps.IndicatorEarliness(
        list_of_tasks=[task_1, task_2]
    )  # take all tasks by default

    solution = ps.SchedulingSolver(problem=problem).solve()
    assert solution


#
# Maximum lateness
#
def test_indicator_maximum_lateness_1() -> None:
    problem = ps.SchedulingProblem(name="IndicatorMaximumLateness1")
    t_1 = ps.FixedDurationTask(
        name="T1", duration=5, due_date=2, due_date_is_deadline=False
    )
    t_2 = ps.FixedDurationTask(
        name="T2", duration=7, due_date=5, due_date_is_deadline=False
    )
    ps.TaskStartAt(task=t_1, value=0)  # tardiness 3
    ps.TaskStartAt(task=t_2, value=0)  # tardiness 2
    tard_1 = ps.IndicatorMaximumLateness()
    solution = ps.SchedulingSolver(problem=problem).solve()
    assert solution
    assert solution.indicators[tard_1.name] == 3


def test_indicator_maximum_lateness_2() -> None:
    problem = ps.SchedulingProblem(name="IndicatorMaximumLateness2")
    t_1 = ps.FixedDurationTask(
        name="T1", duration=5, due_date=20, due_date_is_deadline=False
    )
    t_2 = ps.FixedDurationTask(
        name="T2", duration=7, due_date=50, due_date_is_deadline=False
    )
    ps.TaskStartAt(task=t_1, value=0)  # negative lateness: -15
    ps.TaskStartAt(task=t_2, value=0)  # negative lateness: -43
    tard_1 = ps.IndicatorMaximumLateness()
    solution = ps.SchedulingSolver(problem=problem).solve()
    assert solution
    assert solution.indicators[tard_1.name] == -15


def test_indicator_maximum_lateness_3() -> None:
    problem = ps.SchedulingProblem(name="IndicatorMaximumLateness3")
    t_1 = ps.FixedDurationTask(
        name="T1", duration=5, due_date=20, due_date_is_deadline=False
    )
    t_2 = ps.FixedDurationTask(
        name="T2", duration=7, due_date=50, due_date_is_deadline=False
    )
    t_3 = ps.FixedDurationTask(
        name="T3", duration=11, due_date=5, due_date_is_deadline=False
    )

    ps.TaskStartAt(task=t_1, value=0)  # negative lateness: -15
    ps.TaskStartAt(task=t_2, value=0)  # negative lateness: -43
    ps.TaskStartAt(task=t_3, value=0)
    tard_1 = ps.IndicatorMaximumLateness(list_of_tasks=[t_1, t_2])
    solution = ps.SchedulingSolver(problem=problem).solve()
    assert solution
    assert solution.indicators[tard_1.name] == -15


#
# Resource utilization
#
def test_resource_utilization_indicator_1() -> None:
    problem = ps.SchedulingProblem(name="IndicatorUtilization1", horizon=10)
    t_1 = ps.FixedDurationTask(name="T1", duration=5)
    worker_1 = ps.Worker(name="Worker1")
    t_1.add_required_resource(worker_1)

    utilization_ind = ps.IndicatorResourceUtilization(resource=worker_1)

    solution = ps.SchedulingSolver(problem=problem, debug=True).solve()

    assert solution
    assert solution.indicators[utilization_ind.name] == 50


def test_resource_utilization_indicator_2() -> None:
    """Two tasks, two workers."""
    problem = ps.SchedulingProblem(name="IndicatorUtilization2", horizon=10)

    t_1 = ps.FixedDurationTask(name="T1", duration=5)
    t_2 = ps.FixedDurationTask(name="T2", duration=5)

    worker_1 = ps.Worker(name="Worker1")
    worker_2 = ps.Worker(name="Worker2")

    t_1.add_required_resource(worker_1)
    t_2.add_required_resource(ps.SelectWorkers(list_of_workers=[worker_1, worker_2]))

    utilization_res_1 = ps.IndicatorResourceUtilization(resource=worker_1)
    utilization_res_2 = ps.IndicatorResourceUtilization(resource=worker_2)

    solution = ps.SchedulingSolver(problem=problem).solve()

    assert solution
    result_res_1 = solution.indicators[utilization_res_1.name]
    result_res_2 = solution.indicators[utilization_res_2.name]

    # sum should be 100
    assert result_res_1 + result_res_2 == 100


def test_resource_utilization_indicator_3() -> None:
    """Same as above, but both workers are selectable. Force one with resource
    utilization maximization objective."""
    problem = ps.SchedulingProblem(name="IndicatorUtilization3", horizon=10)

    t_1 = ps.FixedDurationTask(name="T1", duration=5)
    t_2 = ps.FixedDurationTask(name="T2", duration=5)

    worker_1 = ps.Worker(name="Worker1")
    worker_2 = ps.Worker(name="Worker2")

    t_1.add_required_resource(ps.SelectWorkers(list_of_workers=[worker_1, worker_2]))
    t_2.add_required_resource(ps.SelectWorkers(list_of_workers=[worker_1, worker_2]))

    utilization_res_1 = ps.IndicatorResourceUtilization(resource=worker_1)
    utilization_res_2 = ps.IndicatorResourceUtilization(resource=worker_2)

    ps.Objective(
        name="MaximizeResource1Utilization", target=utilization_res_1, kind="maximize"
    )

    solution = ps.SchedulingSolver(problem=problem).solve()

    assert solution
    assert solution.indicators[utilization_res_1.name] == 100
    assert solution.indicators[utilization_res_2.name] == 0


def test_resource_utilization_indicator_4() -> None:
    """20 optional tasks, one worker. Force resource utilization maximization objective."""
    problem = ps.SchedulingProblem(name="IndicatorUtilization4", horizon=20)

    worker = ps.Worker(name="Worker")

    for i in range(20):
        t = ps.FixedDurationTask(name=f"T{i+1}", duration=1, optional=True)
        t.add_required_resource(worker)

    utilization_res = ps.IndicatorResourceUtilization(resource=worker)

    ps.Objective(name="MaximizeUtilRes4", target=utilization_res, kind="maximize")

    solution = ps.SchedulingSolver(problem=problem).solve()

    assert solution
    assert solution.indicators[utilization_res.name] == 100


def test_resource_utilization_indicator_5() -> None:
    """Same input data than previous tests, but we dont use
    an optimisation solver, the objective of 100% is set by an
    additional constraint. This should be **much faster**."""
    problem = ps.SchedulingProblem(name="IndicatorUtilization5", horizon=20)

    worker = ps.Worker(name="Worker")

    for i in range(40):
        t = ps.FixedDurationTask(name=f"T{i+1}", duration=1, optional=True)
        t.add_required_resource(worker)

    utilization_res = ps.IndicatorResourceUtilization(resource=worker)

    ps.ConstraintFromExpression(expression=utilization_res._indicator_variable == 100)

    solution = ps.SchedulingSolver(problem=problem).solve()

    assert solution
    assert solution.indicators[utilization_res.name] == 100


#
# Resource idle
#
def test_indicator_resource_idle_1() -> None:
    problem = ps.SchedulingProblem(name="IndicatorResourceIdle1")
    task_1 = ps.FixedDurationTask(name="task1", duration=2)
    task_2 = ps.FixedDurationTask(name="task2", duration=5)
    task_3 = ps.FixedDurationTask(name="task3", duration=8)
    ps.TaskStartAt(task=task_1, value=3)
    ps.TaskStartAt(task=task_2, value=10)
    ps.TaskStartAt(task=task_3, value=30)
    worker = ps.Worker(name="AWorker")
    task_1.add_required_resource(worker)
    task_2.add_required_resource(worker)
    task_3.add_required_resource(worker)
    ind = ps.IndicatorResourceIdle(list_of_resources=[worker])
    solver = ps.SchedulingSolver(problem=problem)
    solution = solver.solve()
    assert solution
    assert solution.indicators[ind.name] == 20


def test_indicator_resource_idle_2() -> None:
    problem = ps.SchedulingProblem(name="IndicatorResourceIdle2")
    task_1 = ps.FixedDurationTask(name="task1", duration=2)
    task_2 = ps.FixedDurationTask(name="task2", duration=5)
    task_3 = ps.FixedDurationTask(name="task3", duration=8)
    task_4 = ps.FixedDurationTask(name="task4", duration=7)
    ps.TaskStartAt(task=task_1, value=3)
    ps.TaskStartAt(task=task_2, value=10)
    ps.TaskStartAt(task=task_3, value=30)
    ps.TaskStartAt(task=task_4, value=48)
    worker_1 = ps.Worker(name="Machine1")
    worker_2 = ps.Worker(name="Machine2")
    task_1.add_required_resource(worker_1)
    task_2.add_required_resource(worker_1)
    task_3.add_required_resource(worker_2)
    task_4.add_required_resource(worker_2)
    ind = ps.IndicatorResourceIdle(list_of_resources=[worker_1, worker_2])
    solver = ps.SchedulingSolver(problem=problem)
    solution = solver.solve()
    assert solution
    assert solution.indicators[ind.name] == 15


def test_indicator_resource_idle_3() -> None:
    """3 tasks, one is optional non scheduled"""
    problem = ps.SchedulingProblem(name="IndicatorResourceIdle3")
    task_1 = ps.FixedDurationTask(name="task1", duration=2)
    task_2 = ps.FixedDurationTask(name="task2", duration=5)
    task_3 = ps.FixedDurationTask(name="task3", duration=8, optional=True)
    ps.TaskStartAt(task=task_1, value=3)
    ps.TaskStartAt(task=task_2, value=11)
    ps.OptionalTaskForceSchedule(task=task_3, to_be_scheduled=False)
    worker_1 = ps.Worker(name="Machine1")
    task_1.add_required_resource(worker_1)
    task_2.add_required_resource(worker_1)
    task_3.add_required_resource(worker_1)
    ind = ps.IndicatorResourceIdle(list_of_resources=[worker_1])
    solver = ps.SchedulingSolver(problem=problem)
    solution = solver.solve()
    assert solution
    assert solution.indicators[ind.name] == 6


def test_optimize_indicator_multi_objective() -> None:
    problem = ps.SchedulingProblem(name="OptimizeIndicatorMultiObjective", horizon=10)
    task_1 = ps.FixedDurationTask(name="task1", duration=2, priority=1)
    task_2 = ps.FixedDurationTask(name="task2", duration=2, priority=10, optional=True)
    task_3 = ps.FixedDurationTask(name="task3", duration=2, priority=100, optional=True)

    worker = ps.Worker(name="AWorker")
    task_1.add_required_resource(worker)
    task_2.add_required_resource(worker)
    task_3.add_required_resource(worker)

    ps.ObjectiveMaximizeResourceUtilization(resource=worker)

    ps.ObjectivePriorities()

    solver = ps.SchedulingSolver(problem=problem)
    solution = solver.solve()
    assert solution


def test_incremental_optimizer_1() -> None:
    problem = ps.SchedulingProblem(name="IncrementalOptimizer1", horizon=100)
    task_1 = ps.FixedDurationTask(name="task1", duration=2)

    task_1_start_ind = ps.IndicatorFromMathExpression(
        name="Task1Start", expression=task_1._start
    )
    ps.Objective(target=task_1_start_ind, kind="maximize")

    solver = ps.SchedulingSolver(problem=problem)
    solution = solver.solve()

    assert solution
    assert solution.indicators[task_1_start_ind.name] == 98


#
# Total weighted completion time
#
def test_objective_total_weighted_completion_time_1() -> None:
    problem = ps.SchedulingProblem(name="ObjectiveTotalWeightedCompletionTime1")
    t_1 = ps.FixedDurationTask(name="T1", duration=8, priority=5)
    t_2 = ps.FixedDurationTask(name="T2", duration=7, priority=10)
    w_1 = ps.Worker(name="W1")
    t_1.add_required_resource(w_1)
    t_2.add_required_resource(w_1)
    ps.ObjectivePriorities()
    solution = ps.SchedulingSolver(problem=problem).solve()
    assert solution
    assert solution.tasks[t_1.name].end == 15
    assert solution.tasks[t_2.name].end == 7
    assert solution.indicators["TotalPriority"] == 7 * 10 + (7 + 8) * 5


def test_objective_total_weighted_completion_time_2() -> None:
    """use the default priority"""
    problem = ps.SchedulingProblem(name="ObjectiveTotalWeightedCompletionTime2")
    t_1 = ps.FixedDurationTask(name="T1", duration=8)
    t_2 = ps.FixedDurationTask(name="T2", duration=7)
    w_1 = ps.Worker(name="W1")
    t_1.add_required_resource(w_1)
    t_2.add_required_resource(w_1)
    ps.ObjectivePriorities()
    solution = ps.SchedulingSolver(problem=problem).solve()
    assert solution
    assert solution.tasks["T1"].end == 15
    assert solution.tasks["T2"].end == 7
    assert solution.indicators["TotalPriority"] == 7 * 1 + (7 + 8) * 1


# TODO: fix test
# def test_objective_total_weighted_completion_time_3() -> None:
#     """many different tasks, verify that tasks are scheduled in a decreasing order
#     of wj/pj"""
#     problem = ps.SchedulingProblem(name="ObjectiveTotalWeightedCompletionTime3")
#     n = 10
#     w_1 = ps.Worker(name="W1")
#     for i in range(1, n):
#         t_i = ps.FixedDurationTask(
#             name=f"T{i}",
#             duration=random.randint(10, 100),
#             priority=random.randint(10, 100),
#         )
#         t_i.add_required_resource(w_1)
#     ps.ObjectivePriorities()
#     solution = ps.SchedulingSolver(problem=problem).solve()
#     for i in range(1, n - 1):
#         task_i = solution.tasks[f"T{i}"]
#         task_i_plus_1 = solution.tasks[f"T{i+1}"]
#         if task_i.end <= task_i_plus_1.end:
#             assert (
#                 task_i.priority / task_i.duration
#                 >= task_i_plus_1.priority / task_i_plus_1.duration
#             )
#         else:
#             assert (
#                 task_i.priority / task_i.duration
#                 <= task_i_plus_1.priority / task_i_plus_1.duration
#             )


def test_resource_utilization_maximization_incremental_1() -> None:
    """Same as above, but both workers are selectable. Force one with resource
    utilization maximization objective."""
    problem = ps.SchedulingProblem(name="IndicatorMaximizeIncremental", horizon=10)

    t_1 = ps.FixedDurationTask(name="T1", duration=5)
    t_2 = ps.FixedDurationTask(name="T2", duration=5)

    worker_1 = ps.Worker(name="Worker1")
    worker_2 = ps.Worker(name="Worker2")

    t_1.add_required_resource(ps.SelectWorkers(list_of_workers=[worker_1, worker_2]))
    t_2.add_required_resource(ps.SelectWorkers(list_of_workers=[worker_1, worker_2]))

    utilization_res_1 = ps.IndicatorResourceUtilization(resource=worker_1)
    utilization_res_2 = ps.IndicatorResourceUtilization(resource=worker_2)

    ps.Objective(name="MaximizeUtilRes1", target=utilization_res_1, kind="maximize")
    solver = ps.SchedulingSolver(problem=problem)

    solution = solver.solve()

    assert solution
    assert solution.indicators[utilization_res_1.name] == 100
    assert solution.indicators[utilization_res_2.name] == 0


def get_single_resource_utilization_problem(problem_name):
    problem = ps.SchedulingProblem(name=problem_name, horizon=50)

    dur1 = 5
    dur2 = 5
    dur3 = 4
    dur4 = 3
    dur5 = 2

    t_1 = ps.FixedDurationTask(name="T1", duration=dur1)
    t_2 = ps.FixedDurationTask(name="T2", duration=dur2)
    t_3 = ps.FixedDurationTask(name="T3", duration=dur3)
    t_4 = ps.FixedDurationTask(name="T4", duration=dur4)
    t_5 = ps.FixedDurationTask(name="T5", duration=dur5)
    worker_1 = ps.Worker(name="Worker1")

    t_1.add_required_resource(worker_1)
    t_2.add_required_resource(worker_1)
    t_3.add_required_resource(worker_1)
    t_4.add_required_resource(worker_1)
    t_5.add_required_resource(worker_1)

    ps.TaskEndBefore(task=t_3, value=35)
    ps.TaskEndBefore(task=t_2, value=35)
    ps.TaskEndBefore(task=t_1, value=35)
    ps.TaskEndBefore(task=t_4, value=35)
    ps.TaskEndBefore(task=t_5, value=35)

    ps.TaskStartAfter(task=t_3, value=10)
    ps.TaskStartAfter(task=t_2, value=10)
    ps.TaskStartAfter(task=t_1, value=10)
    ps.TaskStartAfter(task=t_4, value=10)
    ps.TaskStartAfter(task=t_5, value=10)

    return problem, worker_1, dur1 + dur2 + dur3 + dur4 + dur5


def test_indicator_flowtime_single_resource_1() -> None:
    problem, worker_1, _ = get_single_resource_utilization_problem(
        "IndicatorFlowtimeSingleResource1"
    )
    # there should not be any task scheduled in this time period
    ps.ObjectiveMinimizeFlowtimeSingleResource(
        resource=worker_1, time_interval=[40, 50]
    )
    solver = ps.SchedulingSolver(problem=problem)

    solution = solver.solve()
    assert solution
    # the flowtime should be 0
    assert solution.indicators["FlowTimeSingleResource(Worker1:40:50)"] == 0


def test_indicator_flowtime_single_resource_2() -> None:
    # same as before, but the time interval contains all the tasks
    problem, worker_1, sum_durations = get_single_resource_utilization_problem(
        "IndicatorFlowtimeSingleResource2"
    )
    ps.ObjectiveMinimizeFlowtimeSingleResource(
        resource=worker_1, time_interval=[10, 40]
    )

    solver = ps.SchedulingSolver(problem=problem)

    solution = solver.solve()
    assert solution
    assert solution.indicators["FlowTimeSingleResource(Worker1:10:40)"] == sum_durations


def test_indicator_flowtime_single_resource_3() -> None:
    # same as before, but the time interval contains no task
    problem, worker_1, _ = get_single_resource_utilization_problem(
        "IndicatorFlowtimeSingleResource3"
    )
    ps.ObjectiveMinimizeFlowtimeSingleResource(resource=worker_1, time_interval=[5, 9])
    solver = ps.SchedulingSolver(problem=problem)

    solution = solver.solve()
    assert solution
    assert solution.indicators["FlowTimeSingleResource(Worker1:5:9)"] == 0


def test_indicator_flowtime_single_resource_4() -> None:
    # without any time_interval provided, should use the whole range [0, horizon]
    problem, worker_1, sum_durations = get_single_resource_utilization_problem(
        "IndicatorFlowtimeSingleResource4"
    )
    ps.ObjectiveMinimizeFlowtimeSingleResource(resource=worker_1)
    solver = ps.SchedulingSolver(problem=problem)

    solution = solver.solve()
    print(solution)
    assert solution
    assert solution.indicators[
        "FlowTimeSingleResource(Worker1:0:horizon)"
    ], sum_durations


def get_single_resource_utilization_problem_2(time_intervals, tst_name):
    horizon = time_intervals[-1][-1] + 3
    nb_tasks = [5 for interval in time_intervals if interval[1] - interval[0] > 3]
    problem = ps.SchedulingProblem(name=tst_name, horizon=horizon)
    worker_1 = ps.Worker(name="Worker1")

    tasks: list[ps.FixedDurationTask] = []
    for interval, nb_tasks_i in zip(time_intervals, nb_tasks):
        for _ in range(nb_tasks_i):
            tasks.append(ps.FixedDurationTask(name=f"T{len(tasks)}", duration=1))
            tasks[-1].add_required_resource(worker_1)
            ps.TaskStartAfter(task=tasks[-1], value=interval[0])
            ps.TaskEndBefore(task=tasks[-1], value=interval[1])
    return problem, worker_1, len(tasks)


def get_solution_sum_flowtime(solution) -> int:
    return sum(
        solution.indicators[indicator_id]
        for indicator_id in solution.indicators
        if "FlowTime" in indicator_id
    )


def test_indicator_flowtime_single_resource_5() -> None:
    # 2 time interval objectives
    time_intervals = [(11, 20), (21, 34)]
    (
        problem,
        worker_1,
        sum_durations,
    ) = get_single_resource_utilization_problem_2(
        time_intervals, "IndicatorFlowtimeSingleResource5"
    )
    for interval in time_intervals:
        ps.ObjectiveMinimizeFlowtimeSingleResource(
            resource=worker_1, time_interval=interval
        )

    solver = ps.SchedulingSolver(problem=problem)
    solution = solver.solve()

    assert solution
    assert sum_durations == get_solution_sum_flowtime(solution)


def test_indicator_flowtime_single_resource_6() -> None:
    # Multiple time intervals (Currently fails for nb_time_intervals > 2, gantt to check total_flowtime is correct)
    nb_time_intervals = 7
    time_interval_length = 13  # always > 5
    horizon = nb_time_intervals * time_interval_length
    time_intervals = [
        (i, i + time_interval_length) for i in range(0, horizon, time_interval_length)
    ]

    (
        problem,
        worker_1,
        sum_durations,
    ) = get_single_resource_utilization_problem_2(
        time_intervals, "IndicatorFlowtimeSingleResource6"
    )
    for interval in time_intervals:
        ps.ObjectiveMinimizeFlowtimeSingleResource(
            resource=worker_1, time_interval=interval
        )

    solver = ps.SchedulingSolver(problem=problem, optimizer="optimize")

    solution = solver.solve()

    assert solution
    assert sum_durations == get_solution_sum_flowtime(solution)


# number of tasks assigned to a resource
def test_indicator_nb_tasks_assigned_to_resource_1() -> None:
    n = 5
    problem = ps.SchedulingProblem(name="IndicatorUtilization5", horizon=n)
    worker = ps.Worker(name="Worker1")

    for i in range(n):
        t = ps.FixedDurationTask(name=f"T{i+1}", duration=1)
        t.add_required_resource(worker)

    ps.IndicatorNumberTasksAssigned(resource=worker)

    solver = ps.SchedulingSolver(problem=problem)
    solution = solver.solve()

    assert solution
    assert solution.indicators["Nb Tasks Assigned (Worker1)"] == n


#
# Indicator constraints
#
def test_indicator_constraint_1() -> None:
    # 4 tasks to be processed by three workers
    # assign the number of tasks to be processed
    problem = ps.SchedulingProblem(name="IndicatorConstraint1")
    t_1 = ps.FixedDurationTask(name="T1", duration=8)
    t_2 = ps.FixedDurationTask(name="T2", duration=7)
    t_3 = ps.FixedDurationTask(name="T3", duration=7)
    t_4 = ps.FixedDurationTask(name="T4", duration=7)
    w_1 = ps.Worker(name="W1")
    w_2 = ps.Worker(name="W2")
    w_3 = ps.Worker(name="W3")
    t_1.add_required_resource(ps.SelectWorkers(list_of_workers=[w_1, w_2, w_3]))
    t_2.add_required_resource(ps.SelectWorkers(list_of_workers=[w_1, w_2, w_3]))
    t_3.add_required_resource(ps.SelectWorkers(list_of_workers=[w_1, w_2, w_3]))
    t_4.add_required_resource(ps.SelectWorkers(list_of_workers=[w_1, w_2, w_3]))

    number_of_tasks_w_1 = ps.IndicatorNumberTasksAssigned(resource=w_1)
    number_of_tasks_w_2 = ps.IndicatorNumberTasksAssigned(resource=w_2)
    number_of_tasks_w_3 = ps.IndicatorNumberTasksAssigned(resource=w_3)

    ps.IndicatorTarget(indicator=number_of_tasks_w_1, value=1)
    ps.IndicatorTarget(indicator=number_of_tasks_w_2, value=1)
    ps.IndicatorTarget(indicator=number_of_tasks_w_3, value=2)

    solution = ps.SchedulingSolver(problem=problem).solve()
    assert solution


def test_indicator_constraint_2() -> None:
    # 4 tasks to be processed by three workers
    # set the minimum number of tasks to be assigned to each
    problem = ps.SchedulingProblem(name="IndicatorConstraint2")
    t_1 = ps.FixedDurationTask(name="T1", duration=8)
    t_2 = ps.FixedDurationTask(name="T2", duration=7)
    t_3 = ps.FixedDurationTask(name="T3", duration=7)
    t_4 = ps.FixedDurationTask(name="T4", duration=7)
    w_1 = ps.Worker(name="W1")
    w_2 = ps.Worker(name="W2")
    w_3 = ps.Worker(name="W3")
    t_1.add_required_resource(ps.SelectWorkers(list_of_workers=[w_1, w_2, w_3]))
    t_2.add_required_resource(ps.SelectWorkers(list_of_workers=[w_1, w_2, w_3]))
    t_3.add_required_resource(ps.SelectWorkers(list_of_workers=[w_1, w_2, w_3]))
    t_4.add_required_resource(ps.SelectWorkers(list_of_workers=[w_1, w_2, w_3]))

    number_of_tasks_w_1 = ps.IndicatorNumberTasksAssigned(resource=w_1)
    number_of_tasks_w_2 = ps.IndicatorNumberTasksAssigned(resource=w_2)
    number_of_tasks_w_3 = ps.IndicatorNumberTasksAssigned(resource=w_3)

    ps.IndicatorBounds(indicator=number_of_tasks_w_1, lower_bound=1, upper_bound=4)
    ps.IndicatorBounds(indicator=number_of_tasks_w_2, lower_bound=1, upper_bound=4)
    ps.IndicatorBounds(indicator=number_of_tasks_w_3, lower_bound=1, upper_bound=4)

    solution = ps.SchedulingSolver(problem=problem).solve()
    assert solution
