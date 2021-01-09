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
    problem.add_tasks(tasks)

    workers = [ps.Worker('task%i' % i) for i in range(n * 3)]
    problem.add_resources(workers)

    # for each task, add three single required workers
    for task in tasks:
        task.add_required_resource(random.choice(workers))
        task.add_required_resource(random.choice(workers))
        task.add_required_resource(random.choice(workers))
    return problem

def _solve_problem(problem, verbose=False):
    """ create a solver instance, return True if sat else False """
    solver = ps.SchedulingSolver(problem, verbosity=verbose)
    success = solver.solve()
    return success

class TestSolver(unittest.TestCase):
    def test_schedule_single_fixed_duration_task(self) -> None:
        problem = ps.SchedulingProblem('SingleFixedDurationTaskScheduling', horizon=2)
        task = ps.FixedDurationTask('task', duration=2)
        problem.add_task(task)
        self.assertTrue(_solve_problem(problem))
        # task should have been scheduled with start at 0
        # and end at 2
        self.assertEqual(task.scheduled_start, 0)
        self.assertEqual(task.scheduled_end, 2)

    def test_schedule_single_variable_duration_task(self) -> None:
        problem = ps.SchedulingProblem('SingleVariableDurationTaskScheduling')
        task = ps.VariableDurationTask('task')
        problem.add_task(task)

        # add two constraints to set start and end
        problem.add_constraint(ps.TaskStartAt(task, 1))
        problem.add_constraint(ps.TaskEndAt(task, 4))

        self.assertTrue(_solve_problem(problem, verbose=True))
        # task should have been scheduled with start at 0
        # and end at 2
        self.assertEqual(task.scheduled_start, 1)
        self.assertEqual(task.scheduled_duration, 3)
        self.assertEqual(task.scheduled_end, 4)

    def test_schedule_two_fixed_duration_task_with_precedence(self) -> None:
        problem = ps.SchedulingProblem('TwoFixedDurationTasksWithPrecedence', horizon=5)
        task_1 = ps.FixedDurationTask('task1', duration=2)
        task_2 = ps.FixedDurationTask('task2', duration=3)
        problem.add_tasks([task_1, task_2])

        # add two constraints to set start and end
        problem.add_constraint(ps.TaskStartAt(task_1, 0))
        prec_constraint = ps.TaskPrecedence(task_before=task_1,
                                            task_after=task_2)
        print(prec_constraint)
        problem.add_constraint(prec_constraint)

        self.assertTrue(_solve_problem(problem))
        self.assertEqual(task_1.scheduled_start, 0)
        self.assertEqual(task_1.scheduled_end, 2)
        self.assertEqual(task_2.scheduled_start, 2)
        self.assertEqual(task_2.scheduled_end, 5)

    def test_schedule_single_task_single_resource(self) -> None:
        problem = ps.SchedulingProblem('SingleTaskSingleResource', horizon=7)

        task = ps.FixedDurationTask('task', duration=7)
        problem.add_task(task)

        worker = ps.Worker('worker')
        problem.add_resource(worker)

        task.add_required_resource(worker)

        self.assertTrue(_solve_problem(problem))
        # task should have been scheduled with start at 0
        # and end at 2
        self.assertEqual(task.scheduled_start, 0)
        self.assertEqual(task.scheduled_end, 7)
        self.assertEqual(task.assigned_resources, [worker])

    def test_schedule_two_tasks_two_alternative_workers(self) -> None:
        problem = ps.SchedulingProblem('TwoTasksTwoAlternativeWorkers', horizon=4)
        # two tasks
        task_1 = ps.FixedDurationTask('task1', duration=3)
        task_2 = ps.FixedDurationTask('task2', duration=2)
        problem.add_tasks([task_1, task_2])
        # two workers
        worker_1 = ps.Worker('worker1')
        worker_2 = ps.Worker('worker2')
        problem.add_resources([worker_1, worker_2])

        task_1.add_required_resource(ps.AlternativeWorkers([worker_1, worker_2], 1))
        task_2.add_required_resource(ps.AlternativeWorkers([worker_1, worker_2], 1))

        self.assertTrue(_solve_problem(problem))
        # each task should have one worker assigned
        self.assertEqual(len(task_1.assigned_resources), 1)
        self.assertEqual(len(task_2.assigned_resources), 1)
        self.assertFalse(task_1.assigned_resources == task_2.assigned_resources)

    def test_unsat_1(self):
        problem = ps.SchedulingProblem('Unsat1')

        task = ps.FixedDurationTask('task', duration=7)
        problem.add_task(task)

        # add two constraints to set start and end
        # impossible to satisfy both
        problem.add_constraint(ps.TaskStartAt(task, 1))
        problem.add_constraint(ps.TaskEndAt(task, 4))

        self.assertFalse(_solve_problem(problem))

    def test_render_solution(self):
        """ take the single task/single resource and display output """
        problem = ps.SchedulingProblem('RenderSolution', horizon=7)
        task = ps.FixedDurationTask('task', duration=7)
        problem.add_task(task)
        worker = ps.Worker('worker')
        problem.add_resource(worker)
        task.add_required_resource(worker)
        self.assertTrue(_solve_problem(problem))
        # display solution, using both ascii or matplotlib
        problem.print_solution()
        problem.render_gantt_matplotlib(render_mode='Resources',
                                        show_plot=False,
                                        fig_filename='test_render_resources.svg')
        problem.render_gantt_matplotlib(render_mode='Tasks',
                                        show_plot=False,
                                        fig_filename='test_render_tasks.svg')
        self.assertTrue(os.path.isfile('test_render_resources.svg'))
        self.assertTrue(os.path.isfile('test_render_tasks.svg'))

    def test_solve_parallel(self):
        """ a stress test with parallel mode solving """
        problem = _get_big_random_problem('SolveParallel', 5000)
        parallel_solver = ps.SchedulingSolver(problem, parallel=True)
        success = parallel_solver.solve()
        self.assertTrue(success)

    def test_solve_max_time(self):
        """ a stress test which  """
        problem = _get_big_random_problem('SolveMaxTime', 10000)
        # 1s is not enough to solve this problem
        max_time_solver = ps.SchedulingSolver(problem, max_time=1)
        success = max_time_solver.solve()
        self.assertFalse(success)

    #
    # Objectives
    #
    def test_makespan_objective(self):
        problem = _get_big_random_problem('SolveMakeSpanObjective', 2000)
        # first look for a solution without optimization
        self.assertTrue(_solve_problem(problem))
        horizon_without_optimization = problem.scheduled_horizon
        # then add the objective and look for another solution
        problem.add_objective_makespan()
        # another solution
        self.assertTrue(_solve_problem(problem))
        horizon_with_optimization = problem.scheduled_horizon
        # horizon_with_optimization should be less than horizon_without_optimization
        self.assertLess(horizon_with_optimization, horizon_without_optimization)

    def test_flowtime_objective(self):
        problem = _get_big_random_problem('SolveFlowTimeObjective', 20)  # long to compute
        problem.add_objective_flowtime()
        self.assertTrue(_solve_problem(problem))

    def test_start_latest_objective(self):
        problem = _get_big_random_problem('SolveStartLatestObjective', 1000)
        problem.add_objective_start_latest()
        self.assertTrue(_solve_problem(problem))

    def test_start_earliest_objective(self):
        problem = _get_big_random_problem('SolveStartEarliestObjective', 1000)
        problem.add_objective_start_earliest()
        self.assertTrue(_solve_problem(problem))

    #
    # Logical Operators
    #
    def test_operator_not(self):
        problem = ps.SchedulingProblem('OperatorNot', horizon=4)
        # only one task, the solver should schedule a start time at 0
        task_1 = ps.FixedDurationTask('task1', duration=3)
        problem.add_task(task_1)
        problem.add_constraint(ps.not_(ps.TaskStartAt(task_1, 0)))
        self.assertTrue(_solve_problem(problem))
        # check that the task is not scheduled to start à 0
        # the only solution is 1
        self.assertTrue(task_1.scheduled_start == 1)

    def test_operator_not_and(self):
        problem = ps.SchedulingProblem('OperatorNotAnd', horizon=4)
        # only one task, the solver should schedule a start time at 0
        task_1 = ps.FixedDurationTask('task1', duration=2)
        problem.add_task(task_1)
        problem.add_constraint(ps.and_(ps.not_(ps.TaskStartAt(task_1, 0)),
                                       ps.not_(ps.TaskStartAt(task_1, 1))))
        self.assertTrue(_solve_problem(problem, verbose=True))
        # the only solution is to start at 2
        self.assertTrue(task_1.scheduled_start == 2)

    #
    # Implication
    #
    def test_implies(self):
        problem = ps.SchedulingProblem('Implies', horizon=6)
        # only one task, the solver should schedule a start time at 0
        task_1 = ps.FixedDurationTask('task1', duration=2)
        task_2 = ps.FixedDurationTask('task2', duration=2)
        problem.add_tasks([task_1, task_2])
        problem.add_constraint(ps.TaskStartAt(task_1, 1))
        problem.add_constraint(ps.implies(task_1.start == 1,
                                          ps.TaskStartAt(task_2, 4)))
        self.assertTrue(_solve_problem(problem))
        # the only solution is to start at 2
        self.assertTrue(task_1.scheduled_start == 1)
        self.assertTrue(task_2.scheduled_start == 4)
    #
    # If then else
    #
    def test_if_then_else(self):
        problem = ps.SchedulingProblem('IfThenElse', horizon=6)
        # only one task, the solver should schedule a start time at 0
        task_1 = ps.FixedDurationTask('task1', duration=2)
        task_2 = ps.FixedDurationTask('task2', duration=2)
        problem.add_tasks([task_1, task_2])
        problem.add_constraint(ps.TaskStartAt(task_1, 1))
        problem.add_constraint(ps.if_then_else(task_1.start == 0, # this condition is False
                                               ps.TaskStartAt(task_2, 4), # assertion not set
                                               ps.TaskStartAt(task_2, 2))) # this one
        self.assertTrue(_solve_problem(problem))
        # the only solution is to start at 2
        self.assertTrue(task_1.scheduled_start == 1)
        self.assertTrue(task_2.scheduled_start == 2)

    #
    # Find other solution
    #
    def test_find_another_solution(self):
        problem = ps.SchedulingProblem('FindAnotherSolution', horizon=6)
        solutions =[]
        # only one task, there are many diffrent solutions
        task_1 = ps.FixedDurationTask('task1', duration=2)
        problem.add_task(task_1)
        solver = ps.SchedulingSolver(problem)
        success = solver.solve()

        while success:
            solutions.append(task_1.scheduled_start)
            success = solver.find_another_solution(task_1.start)
        # there should be 5 solutions
        self.assertEqual(solutions, [0, 1, 2, 3, 4])

    #
    # Total work_amount, resource productivity
    #
    def test_work_amount_1(self):
        problem = ps.SchedulingProblem('WorkAmount')
        # only one task, there are many diffrent solutions
        task_1 = ps.VariableDurationTask('task1', work_amount=11)
        problem.add_task(task_1)
        # create one worker with a productivity of 2
        worker_1 = ps.Worker('Worker1', productivity=2)
        problem.add_resource(worker_1)
        task_1.add_required_resource(worker_1)
        # solve
        self.assertTrue(_solve_problem(problem))
        # the expected duration for task 1 is 6
        self.assertEqual(task_1.scheduled_duration, 6)

    def test_work_amount_2(self):
        # try the same problem than above, but with one more resource
        # check that the task duration is lower
        problem = ps.SchedulingProblem('WorkAmount', horizon=4)
        # only one task, there are many diffrent solutions
        task_1 = ps.VariableDurationTask('task1', work_amount=11)
        problem.add_task(task_1)
        # create two workers
        worker_1 = ps.Worker('Worker1', productivity=2)
        worker_2 = ps.Worker('Worker2', productivity=3)
        problem.add_resources([worker_1, worker_2])
        task_1.add_required_resources([worker_1, worker_2])
        # solve
        self.assertTrue(_solve_problem(problem))

    #
    # Import/export
    #
    def test_export_to_smt2(self):
        problem = _get_big_random_problem('SolveExportToSMT2', 5000)
        solver = ps.SchedulingSolver(problem)
        success = solver.solve()
        self.assertTrue(success)
        solver.export_to_smt2('big_random_problem.smt2')
        self.assertTrue(os.path.isfile('big_random_problem.smt2'))

if __name__ == "__main__":
    unittest.main()
