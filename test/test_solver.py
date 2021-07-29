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

import os
import unittest

import processscheduler as ps


def build_complex_problem(name: str, n: int) -> ps.SchedulingProblem:
    """returns a problem with n tasks and n * 3 workers"""
    problem = ps.SchedulingProblem(name)

    nb_mandatory_tasks = 3 * n
    nb_optional_tasks = n
    nb_workers = 4 * n

    mandatory_tasks = [
        ps.FixedDurationTask("mand_task%i" % i, duration=i % 8 + 1)
        for i in range(nb_mandatory_tasks)
    ]

    # n/10 optional tasks
    optional_tasks = [
        ps.FixedDurationTask("opt_task%i" % i, duration=i % 8 + 1, optional=True)
        for i in range(nb_optional_tasks)
    ]

    all_tasks = mandatory_tasks + optional_tasks

    workers = [ps.Worker("task%i" % i) for i in range(nb_workers)]

    # for each task, add three single required workers
    for i, task in enumerate(all_tasks):
        j = i + 1  # an overlap
        task.add_required_resources(workers[j - 1 : i + 3])

    return problem


def _solve_problem(problem, debug=True):
    """create a solver instance, return True if sat else False"""
    solver = ps.SchedulingSolver(problem, debug)
    return solver.solve()


class TestSolver(unittest.TestCase):
    def test_schedule_single_fixed_duration_task(self) -> None:
        problem = ps.SchedulingProblem("SingleFixedDurationTaskScheduling", horizon=2)
        task = ps.FixedDurationTask("task", duration=2)

        solution = _solve_problem(problem)
        self.assertTrue(solution)
        # task should have been scheduled with start at 0
        # and end at 2
        task_solution = solution.tasks[task.name]
        self.assertEqual(task_solution.start, 0)
        self.assertEqual(task_solution.end, 2)

    def test_schedule_single_variable_duration_task(self) -> None:
        problem = ps.SchedulingProblem("SingleVariableDurationTaskScheduling")
        task = ps.VariableDurationTask("task")

        # add two constraints to set start and end
        problem.add_constraint(ps.TaskStartAt(task, 1))
        problem.add_constraint(ps.TaskEndAt(task, 4))

        solution = _solve_problem(problem)
        self.assertTrue(solution)
        # task should have been scheduled with start at 0
        # and end at 2
        task_solution = solution.tasks[task.name]
        self.assertEqual(task_solution.start, 1)
        self.assertEqual(task_solution.duration, 3)
        self.assertEqual(task_solution.end, 4)

    def test_schedule_two_fixed_duration_task_with_precedence(self) -> None:
        problem = ps.SchedulingProblem("TwoFixedDurationTasksWithPrecedence", horizon=5)
        task_1 = ps.FixedDurationTask("task1", duration=2)
        task_2 = ps.FixedDurationTask("task2", duration=3)

        # add two constraints to set start and end
        problem.add_constraint(ps.TaskStartAt(task_1, 0))
        problem.add_constraint(ps.TaskPrecedence(task_before=task_1, task_after=task_2))
        solution = _solve_problem(problem)
        self.assertTrue(solution)

        task_1_solution = solution.tasks[task_1.name]
        task_2_solution = solution.tasks[task_2.name]

        self.assertEqual(task_1_solution.start, 0)
        self.assertEqual(task_1_solution.end, 2)
        self.assertEqual(task_2_solution.start, 2)
        self.assertEqual(task_2_solution.end, 5)

    def test_schedule_single_task_single_resource(self) -> None:
        problem = ps.SchedulingProblem("SingleTaskSingleResource", horizon=7)

        task = ps.FixedDurationTask("task", duration=7)

        worker = ps.Worker("worker")

        task.add_required_resource(worker)

        solution = _solve_problem(problem)
        self.assertTrue(solution)
        # task should have been scheduled with start at 0
        # and end at 2
        task_solution = solution.tasks[task.name]

        self.assertEqual(task_solution.start, 0)
        self.assertEqual(task_solution.end, 7)
        self.assertEqual(task_solution.assigned_resources, ["worker"])

    def test_schedule_two_tasks_two_alternative_workers(self) -> None:
        problem = ps.SchedulingProblem("TwoTasksTwoSelectWorkers", horizon=4)
        # two tasks
        task_1 = ps.FixedDurationTask("task1", duration=3)
        task_2 = ps.FixedDurationTask("task2", duration=2)
        # two workers
        worker_1 = ps.Worker("worker1")
        worker_2 = ps.Worker("worker2")

        task_1.add_required_resource(ps.SelectWorkers([worker_1, worker_2], 1))
        task_2.add_required_resource(ps.SelectWorkers([worker_1, worker_2], 1))

        solution = _solve_problem(problem)
        self.assertTrue(solution)
        # each task should have one worker assigned
        task_1_solution = solution.tasks[task_1.name]
        task_2_solution = solution.tasks[task_2.name]
        self.assertEqual(len(task_1_solution.assigned_resources), 1)
        self.assertEqual(len(task_1_solution.assigned_resources), 1)
        self.assertFalse(
            task_1_solution.assigned_resources == task_2_solution.assigned_resources
        )

    def test_schedule_three_tasks_three_alternative_workers(self) -> None:
        problem = ps.SchedulingProblem("ThreeTasksThreeSelectWorkers")
        # two tasks
        task_1 = ps.FixedDurationTask("task1", duration=3)
        task_2 = ps.FixedDurationTask("task2", duration=2)
        task_3 = ps.FixedDurationTask("task3", duration=2)

        # three workers
        worker_1 = ps.Worker("worker1")
        worker_2 = ps.Worker("worker2")
        worker_3 = ps.Worker("worker3")

        all_workers = [worker_1, worker_2, worker_3]
        task_1.add_required_resource(ps.SelectWorkers(all_workers, 1))
        task_2.add_required_resource(ps.SelectWorkers(all_workers, 2))
        task_3.add_required_resource(ps.SelectWorkers(all_workers, 3))

        solution = _solve_problem(problem)
        self.assertTrue(solution)
        # each task should have one worker assigned
        self.assertEqual(len(solution.tasks[task_1.name].assigned_resources), 1)
        self.assertEqual(len(solution.tasks[task_2.name].assigned_resources), 2)
        self.assertEqual(len(solution.tasks[task_3.name].assigned_resources), 3)

    def test_alternative_workers_2(self) -> None:
        # problem
        pb_alt = ps.SchedulingProblem("AlternativeWorkerExample")

        # tasks
        t1 = ps.FixedDurationTask("t1", duration=3)
        t2 = ps.FixedDurationTask("t2", duration=2)
        t3 = ps.FixedDurationTask("t3", duration=2)
        t4 = ps.FixedDurationTask("t4", duration=2)
        t5 = ps.FixedDurationTask("t5", duration=2)

        # resource requirements
        w1 = ps.Worker("W1")
        w2 = ps.Worker("W2")
        w3 = ps.Worker("W3")
        w4 = ps.SelectWorkers([w1, w2, w3], nb_workers_to_select=1, kind="exact")
        w5 = ps.SelectWorkers([w1, w2, w3], nb_workers_to_select=2, kind="max")
        w6 = ps.SelectWorkers([w1, w2, w3], nb_workers_to_select=3, kind="min")

        # resource assignment
        t1.add_required_resource(w1)  # t1 only needs w1
        t2.add_required_resource(w2)  # t2 only needs w2
        t3.add_required_resource(w4)  # t3 needs one of w1, 2 or 3
        t4.add_required_resource(w5)  # t4 needs at most 2 of w1, w2 or 3
        t5.add_required_resource(w6)  # t5 needs at least 3 of w1, w2 or w3

        # add a makespan objective
        pb_alt.add_objective_makespan()

        # solve
        solver1 = ps.SchedulingSolver(pb_alt, debug=False)
        solution = solver1.solve()

        self.assertEqual(solution.horizon, 5)

    def test_unsat_1(self):
        problem = ps.SchedulingProblem("Unsat1")

        task = ps.FixedDurationTask("task", duration=7)

        # add two constraints to set start and end
        # impossible to satisfy both
        problem.add_constraint(ps.TaskStartAt(task, 1))
        problem.add_constraint(ps.TaskEndAt(task, 4))

        self.assertFalse(_solve_problem(problem))

    def test_solve_parallel(self):
        """a stress test with parallel mode solving"""
        problem = build_complex_problem("SolveParallel", 50)
        parallel_solver = ps.SchedulingSolver(problem, parallel=True)
        solution = parallel_solver.solve()
        self.assertTrue(solution)

    # TODO: failing test on some azure instances
    # def test_solve_max_time(self):
    #     """ a stress test which  """
    #     problem = build_complex_problem('SolveMaxTime', 1000)
    #     problem.add_objective_makespan()
    #     # 1s is not enough to solve this problem
    #     max_time_solver = ps.SchedulingSolver(problem, max_time=1)
    #     solution = max_time_solver.solve()
    #     self.assertFalse(solution)

    def test_solve_non_integer_max_time(self):
        """a stress test which"""
        problem = build_complex_problem("SolveMaxTime", 1000)
        problem.add_objective_makespan()
        # 0.5s is not enough to solve this problem
        max_time_solver = ps.SchedulingSolver(problem, max_time=0.05)
        solution = max_time_solver.solve()
        self.assertFalse(solution)

    #
    # Objectives
    #
    def test_makespan_objective(self):
        problem = build_complex_problem("SolveMakeSpanObjective", 20)
        # first look for a solution without optimization
        solution_1 = _solve_problem(problem)
        self.assertTrue(solution_1)

        horizon_without_optimization = solution_1.horizon
        # then add the objective and look for another solution
        problem.add_objective_makespan()
        # another solution
        solution_2 = _solve_problem(problem)
        self.assertTrue(solution_2)

        horizon_with_optimization = solution_2.horizon
        # horizon_with_optimization should be less than horizon_without_optimization
        self.assertLess(horizon_with_optimization, horizon_without_optimization)

    def test_flowtime_objective_big_problem(self):
        problem = build_complex_problem("SolveFlowTimeObjective", 5)  # long to compute
        problem.add_objective_flowtime()
        self.assertTrue(_solve_problem(problem))

    def test_start_latest_objective_big_problem(self):
        problem = build_complex_problem("SolveStartLatestObjective", 10)
        problem.add_objective_start_latest()
        self.assertTrue(_solve_problem(problem))

    def test_start_earliest_objective_big_problem(self):
        problem = build_complex_problem("SolveStartEarliestObjective", 10)
        problem.add_objective_start_earliest()
        self.assertTrue(_solve_problem(problem))

    def test_start_latest(self):
        problem = ps.SchedulingProblem("SolveStartLatest", horizon=51)
        # only one task, the solver should schedule a start time at 0
        task_1 = ps.FixedDurationTask("task1", duration=2)
        task_2 = ps.FixedDurationTask("task2", duration=3)

        problem.add_constraint(ps.TaskPrecedence(task_1, task_2))

        problem.add_objective_start_latest()
        solution = _solve_problem(problem)
        self.assertTrue(solution)
        # check that the task is not scheduled to start à 0
        # the only solution is 1
        self.assertEqual(solution.tasks[task_1.name].start, 51 - (3 + 2))
        self.assertEqual(solution.tasks[task_2.name].start, 51 - 3)

    def test_priorities(self):
        problem = ps.SchedulingProblem("SolvePriorities")
        task_1 = ps.FixedDurationTask("task1", duration=2, priority=1)
        task_2 = ps.FixedDurationTask("task2", duration=2, priority=10)
        task_3 = ps.FixedDurationTask("task3", duration=2, priority=100)

        problem.add_constraint(ps.TasksDontOverlap(task_1, task_2))
        problem.add_constraint(ps.TasksDontOverlap(task_2, task_3))
        problem.add_constraint(ps.TasksDontOverlap(task_1, task_3))

        problem.add_objective_priorities()

        # set debug to False because assert_and_track
        # does not properly handles optimization
        solution = _solve_problem(problem, debug=False)
        self.assertTrue(solution)
        # check that the task is not scheduled to start à 0
        # the only solution is 1
        self.assertLess(
            solution.tasks[task_3.name].start, solution.tasks[task_2.name].start
        )
        self.assertLess(
            solution.tasks[task_2.name].start, solution.tasks[task_1.name].start
        )

    #
    # Logical Operators
    #
    def test_operator_not(self):
        problem = ps.SchedulingProblem("OperatorNot", horizon=4)
        # only one task, the solver should schedule a start time at 0
        task_1 = ps.FixedDurationTask("task1", duration=3)

        problem.add_constraint(ps.not_(ps.TaskStartAt(task_1, 0)))
        solution = _solve_problem(problem)
        self.assertTrue(solution)
        # check that the task is not scheduled to start à 0
        # the only solution is 1
        self.assertTrue(solution.tasks[task_1.name].start == 1)

    def test_operator_not_and(self):
        problem = ps.SchedulingProblem("OperatorNotAnd", horizon=4)
        # only one task, the solver should schedule a start time at 0
        task_1 = ps.FixedDurationTask("task1", duration=2)
        # problem.add_task(task_1)
        problem.add_constraint(
            ps.and_(
                [ps.not_(ps.TaskStartAt(task_1, 0)), ps.not_(ps.TaskStartAt(task_1, 1))]
            )
        )
        solution = _solve_problem(problem)
        self.assertTrue(solution)
        # the only solution is to start at 2
        self.assertTrue(solution.tasks[task_1.name].start == 2)

    #
    # Implication
    #
    def test_implies(self):
        problem = ps.SchedulingProblem("Implies", horizon=6)
        # only one task, the solver should schedule a start time at 0
        task_1 = ps.FixedDurationTask("task1", duration=2)
        task_2 = ps.FixedDurationTask("task2", duration=2)
        problem.add_constraint(ps.TaskStartAt(task_1, 1))
        problem.add_constraint(
            ps.implies(task_1.start == 1, [ps.TaskStartAt(task_2, 4)])
        )
        solution = _solve_problem(problem)
        self.assertTrue(solution)
        # the only solution is to start at 2
        self.assertTrue(solution.tasks[task_1.name].start == 1)
        self.assertTrue(solution.tasks[task_2.name].start == 4)

    #
    # If then else
    #
    def test_if_then_else(self):
        problem = ps.SchedulingProblem("IfThenElse", horizon=6)
        # only one task, the solver should schedule a start time at 0
        task_1 = ps.FixedDurationTask("task1", duration=2)
        task_2 = ps.FixedDurationTask("task2", duration=2)
        problem.add_constraint(ps.TaskStartAt(task_1, 1))
        problem.add_constraint(
            ps.if_then_else(
                task_1.start == 0,  # this condition is False
                [ps.TaskStartAt(task_2, 4)],  # assertion not set
                [ps.TaskStartAt(task_2, 2)],
            )
        )  # this one
        solution = _solve_problem(problem)
        self.assertTrue(solution)
        # the only solution is to start at 2
        self.assertTrue(solution.tasks[task_1.name].start == 1)
        self.assertTrue(solution.tasks[task_2.name].start == 2)

    #
    # Find other solution
    #
    def test_find_another_solution(self):
        problem = ps.SchedulingProblem("FindAnotherSolution", horizon=6)
        solutions = []

        task_1 = ps.FixedDurationTask("task1", duration=2)
        solver = ps.SchedulingSolver(problem)
        solution = solver.solve()

        while solution:
            solutions.append(solution.tasks[task_1.name].start)
            solution = solver.find_another_solution(task_1.start)
        # there should be 5 solutions
        self.assertEqual(solutions, [0, 1, 2, 3, 4])

    def test_find_another_solution_solve_before(self):
        problem = ps.SchedulingProblem("FindAnotherSolutionSolveBefore", horizon=6)

        task_1 = ps.FixedDurationTask("task1", duration=2)
        solver = ps.SchedulingSolver(problem)
        result = solver.find_another_solution(
            task_1.start
        )  # error, first have to solve
        self.assertFalse(result)

    #
    # Total work_amount, resource productivity
    #
    def test_work_amount_1(self):
        problem = ps.SchedulingProblem("WorkAmount")

        task_1 = ps.VariableDurationTask("task1", work_amount=11)
        # create one worker with a productivity of 2
        worker_1 = ps.Worker("Worker1", productivity=2)
        task_1.add_required_resource(worker_1)
        # solve
        solution = _solve_problem(problem)
        self.assertTrue(solution)
        # the expected duration for task 1 is 6
        self.assertEqual(solution.tasks[task_1.name].duration, 6)

    def test_work_amount_2(self):
        # try the same problem than above, but with one more resource
        # check that the task duration is lower
        problem = ps.SchedulingProblem("WorkAmount", horizon=4)

        task_1 = ps.VariableDurationTask("task1", work_amount=11)
        # create two workers
        worker_1 = ps.Worker("Worker1", productivity=2)
        worker_2 = ps.Worker("Worker2", productivity=3)
        task_1.add_required_resources([worker_1, worker_2])
        # solve
        self.assertTrue(_solve_problem(problem))

    #
    # Import/export
    #
    def test_export_to_smt2(self):
        problem = build_complex_problem("SolveExportToSMT2", 50)
        solver = ps.SchedulingSolver(problem)
        solution = _solve_problem(problem)
        self.assertTrue(solution)
        solver.export_to_smt2("complex_problem.smt2")
        self.assertTrue(os.path.isfile("complex_problem.smt2"))

    def test_export_solution_to_json(self):
        problem = build_complex_problem("SolutionExportToJson", 50)
        solution = _solve_problem(problem)
        self.assertTrue(solution)
        solution.to_json_string()

    #
    # Resource constraints
    #
    def test_all_same_distinct_workers(self):
        pb = ps.SchedulingProblem("AllSameDistinctWorkers")

        task_1 = ps.FixedDurationTask("task1", duration=2)
        task_2 = ps.FixedDurationTask("task2", duration=2)
        task_3 = ps.FixedDurationTask("task3", duration=2)
        task_4 = ps.FixedDurationTask("task4", duration=2)

        worker_1 = ps.Worker("John")
        worker_2 = ps.Worker("Bob")

        res_for_t1 = ps.SelectWorkers([worker_1, worker_2], 1)
        res_for_t2 = ps.SelectWorkers([worker_1, worker_2], 1)
        res_for_t3 = ps.SelectWorkers([worker_1, worker_2], 1)
        res_for_t4 = ps.SelectWorkers([worker_1, worker_2], 1)

        task_1.add_required_resource(res_for_t1)
        task_2.add_required_resource(res_for_t2)
        task_3.add_required_resource(res_for_t3)
        task_4.add_required_resource(res_for_t4)

        c = ps.SameWorkers(res_for_t1, res_for_t2)
        d = ps.SameWorkers(res_for_t3, res_for_t4)
        e = ps.DistinctWorkers(res_for_t2, res_for_t4)
        pb.add_constraints([c, d, e])

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertEqual(solution.horizon, 4)


if __name__ == "__main__":
    unittest.main()
