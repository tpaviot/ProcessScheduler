#Copyright 2020 Thomas Paviot (tpaviot@gmail.com)
#
#Licensed to the Apache Software Foundation (ASF) under one
#or more contributor license agreements.  See the NOTICE file
#distributed with this work for additional information
#regarding copyright ownership.  The ASF licenses this file
#to you under the Apache License, Version 2.0 (the
#"License"); you may not use this file except in compliance
#with the License.  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing,
#software distributed under the License is distributed on an
#"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#KIND, either express or implied.  See the License for the
#specific language governing permissions and limitations
#under the License.

import os
import random
import unittest

import processscheduler as ps

def _get_big_random_problem(name:str, n: int) -> ps.SchedulingProblem:
    """ returns a problem with n tasks and n * 3 workers. Workers are random assigned. """
    problem = ps.SchedulingProblem(name)

    tasks = [ps.FixedDurationTask('task%i' % i,
                                  duration=random.randint(1, n // 10)) for i in range(n)]

    workers = [ps.Worker('task%i' % i) for i in range(n * 3)]

    # for each task, add three single required workers
    for task in tasks:
        random_workers = random.sample(workers, 3)
        task.add_required_resources(random_workers)

    return problem

def _solve_problem(problem, verbose=False):
    """ create a solver instance, return True if sat else False """
    solver = ps.SchedulingSolver(problem, verbosity=verbose)
    solution = solver.solve()
    return solution

class TestSolver(unittest.TestCase):
    def test_schedule_single_fixed_duration_task(self) -> None:
        problem = ps.SchedulingProblem('SingleFixedDurationTaskScheduling', horizon=2)
        task = ps.FixedDurationTask('task', duration=2)

        solution = _solve_problem(problem)
        self.assertTrue(solution)
        # task should have been scheduled with start at 0
        # and end at 2
        task_solution = solution.tasks[task.name]
        self.assertEqual(task_solution.start, 0)
        self.assertEqual(task_solution.end, 2)

    def test_schedule_single_variable_duration_task(self) -> None:
        problem = ps.SchedulingProblem('SingleVariableDurationTaskScheduling')
        task = ps.VariableDurationTask('task')

        # add two constraints to set start and end
        problem.add_constraint(ps.TaskStartAt(task, 1))
        problem.add_constraint(ps.TaskEndAt(task, 4))

        solution = _solve_problem(problem, verbose=True)
        self.assertTrue(solution)
        # task should have been scheduled with start at 0
        # and end at 2
        task_solution = solution.tasks[task.name]
        self.assertEqual(task_solution.start, 1)
        self.assertEqual(task_solution.duration, 3)
        self.assertEqual(task_solution.end, 4)

    def test_schedule_two_fixed_duration_task_with_precedence(self) -> None:
        problem = ps.SchedulingProblem('TwoFixedDurationTasksWithPrecedence', horizon=5)
        task_1 = ps.FixedDurationTask('task1', duration=2)
        task_2 = ps.FixedDurationTask('task2', duration=3)

        # add two constraints to set start and end
        problem.add_constraint(ps.TaskStartAt(task_1, 0))
        problem.add_constraint(ps.TaskPrecedence(task_before=task_1,
                                                 task_after=task_2))
        solution = _solve_problem(problem)
        self.assertTrue(solution)

        task_1_solution = solution.tasks[task_1.name]
        task_2_solution = solution.tasks[task_2.name]

        self.assertEqual(task_1_solution.start, 0)
        self.assertEqual(task_1_solution.end, 2)
        self.assertEqual(task_2_solution.start, 2)
        self.assertEqual(task_2_solution.end, 5)

    def test_schedule_single_task_single_resource(self) -> None:
        problem = ps.SchedulingProblem('SingleTaskSingleResource', horizon=7)

        task = ps.FixedDurationTask('task', duration=7)

        worker = ps.Worker('worker')

        task.add_required_resource(worker)

        solution = _solve_problem(problem)
        self.assertTrue(solution)
        # task should have been scheduled with start at 0
        # and end at 2
        task_solution = solution.tasks[task.name]

        self.assertEqual(task_solution.start, 0)
        self.assertEqual(task_solution.end, 7)
        self.assertEqual(task_solution.assigned_resources, ['worker'])

    def test_schedule_two_tasks_two_alternative_workers(self) -> None:
        problem = ps.SchedulingProblem('TwoTasksTwoSelectWorkers', horizon=4)
        # two tasks
        task_1 = ps.FixedDurationTask('task1', duration=3)
        task_2 = ps.FixedDurationTask('task2', duration=2)
        # two workers
        worker_1 = ps.Worker('worker1')
        worker_2 = ps.Worker('worker2')

        task_1.add_required_resource(ps.SelectWorkers([worker_1, worker_2], 1))
        task_2.add_required_resource(ps.SelectWorkers([worker_1, worker_2], 1))

        solution = _solve_problem(problem)
        self.assertTrue(solution)
        # each task should have one worker assigned
        task_1_solution = solution.tasks[task_1.name]
        task_2_solution = solution.tasks[task_2.name]
        self.assertEqual(len(task_1_solution.assigned_resources), 1)
        self.assertEqual(len(task_1_solution.assigned_resources), 1)
        self.assertFalse(task_1_solution.assigned_resources == task_2_solution.assigned_resources)

    def test_schedule_three_tasks_three_alternative_workers(self) -> None:
        problem = ps.SchedulingProblem('ThreeTasksThreeSelectWorkers')
        # two tasks
        task_1 = ps.FixedDurationTask('task1', duration=3)
        task_2 = ps.FixedDurationTask('task2', duration=2)
        task_3 = ps.FixedDurationTask('task3', duration=2)

        # three workers
        worker_1 = ps.Worker('worker1')
        worker_2 = ps.Worker('worker2')
        worker_3 = ps.Worker('worker3')

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
        t1 = ps.FixedDurationTask('t1', duration=3)
        t2 = ps.FixedDurationTask('t2', duration=2)
        t3 = ps.FixedDurationTask('t3', duration=2)
        t4 = ps.FixedDurationTask('t4', duration=2)
        t5 = ps.FixedDurationTask('t5', duration=2)

        # resource requirements
        w1 = ps.Worker('W1')
        w2 = ps.Worker('W2')
        w3 = ps.Worker('W3')
        w4 = ps.SelectWorkers([w1, w2, w3], nb_workers=1, kind='exact')
        w5 = ps.SelectWorkers([w1, w2, w3], nb_workers=2, kind='atmost')
        w6 = ps.SelectWorkers([w1, w2, w3], nb_workers=3, kind='atleast')

        # resource assignement
        t1.add_required_resource(w1)  # t1 only needs w1
        t2.add_required_resource(w2)  # t2 only needs w2
        t3.add_required_resource(w4)  # t3 needs one of w1, 2 or 3
        t4.add_required_resource(w5)  # t4 needs at most 2 of w1, w2 or 3
        t5.add_required_resource(w6)  # t5 needs at least 3 of w1, w2 or w3

        # add a makespan objective
        pb_alt.add_objective_makespan()

        # solve
        solver1 = ps.SchedulingSolver(pb_alt, verbosity=False)
        solution = solver1.solve()

        self.assertEqual(solution.horizon, 5)

    def test_unsat_1(self):
        problem = ps.SchedulingProblem('Unsat1')

        task = ps.FixedDurationTask('task', duration=7)

        # add two constraints to set start and end
        # impossible to satisfy both
        problem.add_constraint(ps.TaskStartAt(task, 1))
        problem.add_constraint(ps.TaskEndAt(task, 4))

        self.assertFalse(_solve_problem(problem))

    def test_render_solution(self):
        """ take the single task/single resource and display output """
        problem = ps.SchedulingProblem('RenderSolution', horizon=7)
        task = ps.FixedDurationTask('task', duration=7)
        #problem.add_task(task)
        worker = ps.Worker('worker')
        #problem.add_resource(worker)
        task.add_required_resource(worker)
        solution = _solve_problem(problem)
        self.assertTrue(solution)
        # display solution, using both ascii or matplotlib
        solution.render_gantt_matplotlib(render_mode='Resources',
                                        show_plot=False,
                                        fig_filename='test_render_resources.svg')
        solution.render_gantt_matplotlib(render_mode='Tasks',
                                        show_plot=False,
                                        fig_filename='test_render_tasks.svg')
        self.assertTrue(os.path.isfile('test_render_resources.svg'))
        self.assertTrue(os.path.isfile('test_render_tasks.svg'))

    def test_solve_parallel(self):
        """ a stress test with parallel mode solving """
        problem = _get_big_random_problem('SolveParallel', 5000)
        parallel_solver = ps.SchedulingSolver(problem, parallel=True)
        solution = parallel_solver.solve()
        self.assertTrue(solution)

    def test_solve_max_time(self):
        """ a stress test which  """
        problem = _get_big_random_problem('SolveMaxTime', 10000)
        # 1s is not enough to solve this problem
        max_time_solver = ps.SchedulingSolver(problem, max_time=1)
        solution = max_time_solver.solve()
        self.assertFalse(solution)

    #
    # Objectives
    #
    def test_makespan_objective(self):
        problem = _get_big_random_problem('SolveMakeSpanObjective', 2000)
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
        problem = _get_big_random_problem('SolveFlowTimeObjective', 20)  # long to compute
        problem.add_objective_flowtime()
        self.assertTrue(_solve_problem(problem))

    def test_start_latest_objective_big_problem(self):
        problem = _get_big_random_problem('SolveStartLatestObjective', 1000)
        problem.add_objective_start_latest()
        self.assertTrue(_solve_problem(problem))

    def test_start_earliest_objective_big_problem(self):
        problem = _get_big_random_problem('SolveStartEarliestObjective', 1000)
        problem.add_objective_start_earliest()
        self.assertTrue(_solve_problem(problem))

    def test_start_latest(self):
        problem = ps.SchedulingProblem('SolveStartLatest', horizon=51)
        # only one task, the solver should schedule a start time at 0
        task_1 = ps.FixedDurationTask('task1', duration=2)
        task_2 = ps.FixedDurationTask('task2', duration=3)

        problem.add_constraint(ps.TaskPrecedence(task_1, task_2))

        problem.add_objective_start_latest()
        solution = _solve_problem(problem)
        self.assertTrue(solution)
        # check that the task is not scheduled to start à 0
        # the only solution is 1
        self.assertEqual(solution.tasks[task_1.name].start, 51 - (3 + 2))
        self.assertEqual(solution.tasks[task_2.name].start, 51 - 3)

    def test_priorities(self):
        problem = ps.SchedulingProblem('SolvePriorities')
        task_1 = ps.FixedDurationTask('task1', duration=2, priority=1)
        task_2 = ps.FixedDurationTask('task2', duration=2, priority=10)
        task_3 = ps.FixedDurationTask('task3', duration=2, priority=100)

        problem.add_constraint(ps.TasksDontOverlap(task_1, task_2))
        problem.add_constraint(ps.TasksDontOverlap(task_2, task_3))
        problem.add_constraint(ps.TasksDontOverlap(task_1, task_3))

        problem.add_objective_priorities()

        solution = _solve_problem(problem)
        self.assertTrue(solution)
        # check that the task is not scheduled to start à 0
        # the only solution is 1
        self.assertLess(solution.tasks[task_3.name].start,
                        solution.tasks[task_2.name].start)
        self.assertLess(solution.tasks[task_2.name].start,
                        solution.tasks[task_1.name].start)

    #
    # Logical Operators
    #
    def test_operator_not(self):
        problem = ps.SchedulingProblem('OperatorNot', horizon=4)
        # only one task, the solver should schedule a start time at 0
        task_1 = ps.FixedDurationTask('task1', duration=3)

        problem.add_constraint(ps.not_(ps.TaskStartAt(task_1, 0)))
        solution = _solve_problem(problem)
        self.assertTrue(solution)
        # check that the task is not scheduled to start à 0
        # the only solution is 1
        self.assertTrue(solution.tasks[task_1.name].start == 1)

    def test_operator_not_and(self):
        problem = ps.SchedulingProblem('OperatorNotAnd', horizon=4)
        # only one task, the solver should schedule a start time at 0
        task_1 = ps.FixedDurationTask('task1', duration=2)
        #problem.add_task(task_1)
        problem.add_constraint(ps.and_([ps.not_(ps.TaskStartAt(task_1, 0)),
                                        ps.not_(ps.TaskStartAt(task_1, 1))]))
        solution = _solve_problem(problem)
        self.assertTrue(solution)
        # the only solution is to start at 2
        self.assertTrue(solution.tasks[task_1.name].start == 2)

    #
    # Implication
    #
    def test_implies(self):
        problem = ps.SchedulingProblem('Implies', horizon=6)
        # only one task, the solver should schedule a start time at 0
        task_1 = ps.FixedDurationTask('task1', duration=2)
        task_2 = ps.FixedDurationTask('task2', duration=2)
        problem.add_constraint(ps.TaskStartAt(task_1, 1))
        problem.add_constraint(ps.implies(task_1.start == 1,
                                          [ps.TaskStartAt(task_2, 4)]))
        solution = _solve_problem(problem)
        self.assertTrue(solution)
        # the only solution is to start at 2
        self.assertTrue(solution.tasks[task_1.name].start == 1)
        self.assertTrue(solution.tasks[task_2.name].start == 4)
    #
    # If then else
    #
    def test_if_then_else(self):
        problem = ps.SchedulingProblem('IfThenElse', horizon=6)
        # only one task, the solver should schedule a start time at 0
        task_1 = ps.FixedDurationTask('task1', duration=2)
        task_2 = ps.FixedDurationTask('task2', duration=2)
        problem.add_constraint(ps.TaskStartAt(task_1, 1))
        problem.add_constraint(ps.if_then_else(task_1.start == 0, # this condition is False
                                               [ps.TaskStartAt(task_2, 4)], # assertion not set
                                               [ps.TaskStartAt(task_2, 2)])) # this one
        solution = _solve_problem(problem)
        self.assertTrue(solution)
        # the only solution is to start at 2
        self.assertTrue(solution.tasks[task_1.name].start == 1)
        self.assertTrue(solution.tasks[task_2.name].start == 2)

    #
    # Find other solution
    #
    def test_find_another_solution(self):
        problem = ps.SchedulingProblem('FindAnotherSolution', horizon=6)
        solutions =[]
        # only one task, there are many diffrent solutions
        task_1 = ps.FixedDurationTask('task1', duration=2)
        solver = ps.SchedulingSolver(problem)
        solution = solver.solve()

        while solution:
            solutions.append(solution.tasks[task_1.name].start)
            solution = solver.find_another_solution(task_1.start)
        # there should be 5 solutions
        self.assertEqual(solutions, [0, 1, 2, 3, 4])

    def test_find_another_solution_solve_before(self):
        problem = ps.SchedulingProblem('FindAnotherSolutionSolveBefore', horizon=6)
        # only one task, there are many diffrent solutions
        task_1 = ps.FixedDurationTask('task1', duration=2)
        solver = ps.SchedulingSolver(problem)
        result = solver.find_another_solution(task_1.start) # error, first have to solve
        self.assertFalse(result)

    #
    # Total work_amount, resource productivity
    #
    def test_work_amount_1(self):
        problem = ps.SchedulingProblem('WorkAmount')
        # only one task, there are many diffrent solutions
        task_1 = ps.VariableDurationTask('task1', work_amount=11)
        # create one worker with a productivity of 2
        worker_1 = ps.Worker('Worker1', productivity=2)
        task_1.add_required_resource(worker_1)
        # solve
        solution = _solve_problem(problem, verbose=True)
        self.assertTrue(solution)
        # the expected duration for task 1 is 6
        self.assertEqual(solution.tasks[task_1.name].duration, 6)

    def test_work_amount_2(self):
        # try the same problem than above, but with one more resource
        # check that the task duration is lower
        problem = ps.SchedulingProblem('WorkAmount', horizon=4)
        # only one task, there are many diffrent solutions
        task_1 = ps.VariableDurationTask('task1', work_amount=11)
        # create two workers
        worker_1 = ps.Worker('Worker1', productivity=2)
        worker_2 = ps.Worker('Worker2', productivity=3)
        task_1.add_required_resources([worker_1, worker_2])
        # solve
        self.assertTrue(_solve_problem(problem))

    #
    # Import/export
    #
    def test_export_to_smt2(self):
        problem = _get_big_random_problem('SolveExportToSMT2', 5000)
        solver = ps.SchedulingSolver(problem)
        solution = _solve_problem(problem)
        self.assertTrue(solution)
        solver.export_to_smt2('big_random_problem.smt2')
        self.assertTrue(os.path.isfile('big_random_problem.smt2'))

    def test_export_solution_to_json(self):
        problem = _get_big_random_problem('SolutionExportToJson', 5000)
        solution = _solve_problem(problem)
        self.assertTrue(solution)
        solution.to_json_string()

    #
    # Resource constraints
    #
    def test_all_same_different_workers(self):
        pb = ps.SchedulingProblem('AllSameDifferentWorkers')

        task_1 = ps.FixedDurationTask('task1', duration = 2)
        task_2 = ps.FixedDurationTask('task2', duration = 2)
        task_3 = ps.FixedDurationTask('task3', duration = 2)
        task_4 = ps.FixedDurationTask('task4', duration = 2)

        worker_1 = ps.Worker('John')
        worker_2 = ps.Worker('Bob')

        res_for_t1 = ps.SelectWorkers([worker_1, worker_2], 1)
        res_for_t2 = ps.SelectWorkers([worker_1, worker_2], 1)
        res_for_t3 = ps.SelectWorkers([worker_1, worker_2], 1)
        res_for_t4 = ps.SelectWorkers([worker_1, worker_2], 1)

        task_1.add_required_resource(res_for_t1)
        task_2.add_required_resource(res_for_t2)
        task_3.add_required_resource(res_for_t3)
        task_4.add_required_resource(res_for_t4)

        c = ps.AllSameSelected(res_for_t1, res_for_t2)
        d = ps.AllSameSelected(res_for_t3, res_for_t4)
        e = ps.AllDifferentSelected(res_for_t2, res_for_t4)
        pb.add_constraints([c, d, e])

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertEqual(solution.horizon, 4)

    def test_resource_unavailable(self) -> None:
        pb = ps.SchedulingProblem('ResourceUnavailable', horizon=10)
        task_1 = ps.FixedDurationTask('task1', duration = 3)
        worker_1 = ps.Worker('Worker1')
        task_1.add_required_resource(worker_1)
        c1 = ps.ResourceUnavailable(worker_1, [(1, 3), (6, 8)])
        pb.add_constraint(c1)
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertEqual(solution.tasks[task_1.name].start, 3)
        self.assertEqual(solution.tasks[task_1.name].end, 6)

    def test_resource_unavailable_2(self) -> None:
        pb = ps.SchedulingProblem('ResourceUnavailable2', horizon=10)
        task_1 = ps.FixedDurationTask('task1', duration = 3)
        worker_1 = ps.Worker('Worker1')
        task_1.add_required_resource(worker_1)
        # difference with the first one: build 2 constraints
        # merged using a and_
        c1 = ps.ResourceUnavailable(worker_1, [(1, 3)])
        c2 = ps.ResourceUnavailable(worker_1, [(6, 8)])
        pb.add_constraint(ps.and_([c1, c2]))
        # that should not change the problem solution
        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertEqual(solution.tasks[task_1.name].start, 3)
        self.assertEqual(solution.tasks[task_1.name].end, 6)


if __name__ == "__main__":
    unittest.main()
