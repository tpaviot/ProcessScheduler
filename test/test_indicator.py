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

import unittest

import processscheduler as ps


class TestIndicator(unittest.TestCase):
    def test_indicator_flowtime(self) -> None:
        problem = ps.SchedulingProblem("IndicatorFlowTime", horizon=2)
        t_1 = ps.FixedDurationTask("t1", 2)
        t_2 = ps.FixedDurationTask("t2", 2)

        i_1 = ps.Indicator("FlowTime", t_1.end + t_2.end)

        solution = ps.SchedulingSolver(problem).solve()

        self.assertTrue(solution)
        self.assertEqual(solution.indicators[i_1.name], 4)

    def test_resource_utilization_indicator_1(self) -> None:
        problem = ps.SchedulingProblem("IndicatorUtilization1", horizon=10)
        t_1 = ps.FixedDurationTask("T1", duration=5)
        worker_1 = ps.Worker("Worker1")
        t_1.add_required_resource(worker_1)
        utilization_ind = problem.add_indicator_resource_utilization(worker_1)

        solution = ps.SchedulingSolver(problem).solve()

        self.assertTrue(solution)
        self.assertEqual(solution.indicators[utilization_ind.name], 50)

    def test_resource_utilization_indicator_2(self) -> None:
        """Two tasks, two workers."""
        problem = ps.SchedulingProblem("IndicatorUtilization2", horizon=10)

        t_1 = ps.FixedDurationTask("T1", duration=5)
        t_2 = ps.FixedDurationTask("T2", duration=5)

        worker_1 = ps.Worker("Worker1")
        worker_2 = ps.Worker("Worker2")

        t_1.add_required_resource(worker_1)
        t_2.add_required_resource(ps.SelectWorkers([worker_1, worker_2]))

        utilization_res_1 = problem.add_indicator_resource_utilization(worker_1)
        utilization_res_2 = problem.add_indicator_resource_utilization(worker_2)

        solution = ps.SchedulingSolver(problem).solve()

        self.assertTrue(solution)
        result_res_1 = solution.indicators[utilization_res_1.name]
        result_res_2 = solution.indicators[utilization_res_2.name]

        # sum should be 100
        self.assertEqual(result_res_1 + result_res_2, 100)

    def test_resource_utilization_indicator_3(self) -> None:
        """Same as above, but both workers are selectable. Force one with resource
        utilization maximization objective."""
        problem = ps.SchedulingProblem("IndicatorUtilization3", horizon=10)

        t_1 = ps.FixedDurationTask("T1", duration=5)
        t_2 = ps.FixedDurationTask("T2", duration=5)

        worker_1 = ps.Worker("Worker1")
        worker_2 = ps.Worker("Worker2")

        t_1.add_required_resource(ps.SelectWorkers([worker_1, worker_2]))
        t_2.add_required_resource(ps.SelectWorkers([worker_1, worker_2]))

        utilization_res_1 = problem.add_indicator_resource_utilization(worker_1)
        utilization_res_2 = problem.add_indicator_resource_utilization(worker_2)

        ps.MaximizeObjective("MaximieResource1Utilization", utilization_res_1)

        solution = ps.SchedulingSolver(problem).solve()

        self.assertTrue(solution)
        self.assertEqual(solution.indicators[utilization_res_1.name], 100)
        self.assertEqual(solution.indicators[utilization_res_2.name], 0)

    def test_resource_utilization_indicator_4(self) -> None:
        """20 optional tasks, one worker. Force resource utilization maximization objective."""
        problem = ps.SchedulingProblem("IndicatorUtilization4", horizon=20)

        worker = ps.Worker("Worker")

        for i in range(20):
            t = ps.FixedDurationTask(f"T{i+1}", duration=1, optional=True)
            t.add_required_resource(worker)

        utilization_res = problem.add_indicator_resource_utilization(worker)
        problem.maximize_indicator(utilization_res)

        solution = ps.SchedulingSolver(problem).solve()

        self.assertTrue(solution)
        self.assertEqual(solution.indicators[utilization_res.name], 100)

    # TODO: test commented out because it sometimes fails on Azure cloud
    # def test_resource_utilization_indicator_5(self) -> None:
    #     """Same input data than previous tests, but we dont use
    #     an optimisation solver, the objective of 100% is set by an
    #     additional constraint. This should be **much faster**."""
    #     problem = ps.SchedulingProblem('IndicatorUtilization5', horizon = 20)

    #     worker = ps.Worker('Worker')

    #     for i in range(40):
    #         t = ps.FixedDurationTask(f'T{i+1}', duration = 1, optional = True)
    #         t.add_required_resource(worker)

    #     utilization_res = problem.add_indicator_resource_utilization(worker)

    #     problem.add_constraint(utilization_res.indicator_variable == 100)

    #     solution = ps.SchedulingSolver(problem).solve()

    #     self.assertTrue(solution)
    #     self.assertEqual(solution.indicators[utilization_res.name], 100)

    def test_optimize_indicator(self) -> None:
        problem = ps.SchedulingProblem("SolvePriorities", horizon=10)
        task_1 = ps.FixedDurationTask("task1", duration=2, priority=1)
        task_2 = ps.FixedDurationTask("task2", duration=2, priority=10, optional=True)
        task_3 = ps.FixedDurationTask("task3", duration=2, priority=100, optional=True)

        worker = ps.Worker("AWorker")
        task_1.add_required_resource(worker)
        task_2.add_required_resource(worker)
        task_3.add_required_resource(worker)

        problem.add_objective_resource_utilization(worker)
        problem.add_objective_priorities()

        solver = ps.SchedulingSolver(problem)
        solution = solver.solve()
        self.assertTrue(solution)

    def test_incremental_optimizer_1(self) -> None:
        problem = ps.SchedulingProblem("IncrementalOptimizer1", horizon=100)
        task_1 = ps.FixedDurationTask("task1", duration=2)

        task_1_start_ind = ps.Indicator("Task1Start", task_1.start)
        problem.maximize_indicator(task_1_start_ind)

        solver = ps.SchedulingSolver(problem)
        solution = solver.solve()

        self.assertTrue(solution)
        self.assertEqual(solution.indicators[task_1_start_ind.name], 98)

    def test_resource_utilization_maximization_incremental_1(self) -> None:
        """Same as above, but both workers are selectable. Force one with resource
        utilization maximization objective."""
        problem = ps.SchedulingProblem("IndicatorMaximizeIncremental", horizon=10)

        t_1 = ps.FixedDurationTask("T1", duration=5)
        t_2 = ps.FixedDurationTask("T2", duration=5)

        worker_1 = ps.Worker("Worker1")
        worker_2 = ps.Worker("Worker2")

        t_1.add_required_resource(ps.SelectWorkers([worker_1, worker_2]))
        t_2.add_required_resource(ps.SelectWorkers([worker_1, worker_2]))

        utilization_res_1 = problem.add_indicator_resource_utilization(worker_1)
        utilization_res_2 = problem.add_indicator_resource_utilization(worker_2)

        problem.maximize_indicator(utilization_res_1)
        solver = ps.SchedulingSolver(problem)

        solution = solver.solve()

        self.assertTrue(solution)
        self.assertEqual(solution.indicators[utilization_res_1.name], 100)
        self.assertEqual(solution.indicators[utilization_res_2.name], 0)

    def get_single_resource_utilization_problem(self, problem_name):
        problem = ps.SchedulingProblem("IndicatorFlowtimeSingleResource1", horizon=50)

        dur1 = 5
        dur2 = 5
        dur3 = 4
        dur4 = 3
        dur5 = 2

        t_1 = ps.FixedDurationTask("T1", duration=dur1)
        t_2 = ps.FixedDurationTask("T2", duration=dur2)
        t_3 = ps.FixedDurationTask("T3", duration=dur3)
        t_4 = ps.FixedDurationTask("T4", duration=dur4)
        t_5 = ps.FixedDurationTask("T5", duration=dur5)
        worker_1 = ps.Worker("Worker1")

        t_1.add_required_resource(worker_1)
        t_2.add_required_resource(worker_1)
        t_3.add_required_resource(worker_1)
        t_4.add_required_resource(worker_1)
        t_5.add_required_resource(worker_1)

        problem.add_constraint(ps.TaskEndBeforeLax(t_3, 35))
        problem.add_constraint(ps.TaskEndBeforeLax(t_2, 35))
        problem.add_constraint(ps.TaskEndBeforeLax(t_1, 35))
        problem.add_constraint(ps.TaskEndBeforeLax(t_4, 35))
        problem.add_constraint(ps.TaskEndBeforeLax(t_5, 35))

        problem.add_constraint(ps.TaskStartAfterLax(t_3, 10))
        problem.add_constraint(ps.TaskStartAfterLax(t_2, 10))
        problem.add_constraint(ps.TaskStartAfterLax(t_1, 10))
        problem.add_constraint(ps.TaskStartAfterLax(t_4, 10))
        problem.add_constraint(ps.TaskStartAfterLax(t_5, 10))

        return problem, worker_1, dur1 + dur2 + dur3 + dur4 + dur5

    def test_indicator_flowtime_single_resource_1(self) -> None:
        problem, worker_1, _ = self.get_single_resource_utilization_problem(
            "IndicatorFlowtimeSingleResource1"
        )
        # there should not be any task scheduled in this time period
        problem.add_objective_flowtime_single_resource(worker_1, time_interval=[40, 50])
        solver = ps.SchedulingSolver(problem)

        solution = solver.solve()
        self.assertTrue(solution)
        # the flowtime should be 0
        self.assertEqual(solution.indicators["FlowTime(Worker1:40:50)"], 0)

    def test_indicator_flowtime_single_resource_2(self) -> None:
        # same as before, but the time interval contains all the tasks
        problem, worker_1, sum_durations = self.get_single_resource_utilization_problem(
            "IndicatorFlowtimeSingleResource2"
        )
        problem.add_objective_flowtime_single_resource(worker_1, time_interval=[10, 40])
        solver = ps.SchedulingSolver(problem)

        solution = solver.solve()
        self.assertTrue(solution)
        self.assertEqual(solution.indicators["FlowTime(Worker1:10:40)"], sum_durations)

    def test_indicator_flowtime_single_resource_3(self) -> None:
        # same as before, but the time interval contains no task
        problem, worker_1, _ = self.get_single_resource_utilization_problem(
            "IndicatorFlowtimeSingleResource3"
        )
        problem.add_objective_flowtime_single_resource(worker_1, time_interval=[5, 9])
        solver = ps.SchedulingSolver(problem)

        solution = solver.solve()
        self.assertTrue(solution)
        print(solution)
        self.assertEqual(solution.indicators["FlowTime(Worker1:5:9)"], 0)

    def test_indicator_flowtime_single_resource_4(self) -> None:
        # without any time_interval provided, should use the whole range [0, horizon]
        problem, worker_1, sum_durations = self.get_single_resource_utilization_problem(
            "IndicatorFlowtimeSingleResource4"
        )
        problem.add_objective_flowtime_single_resource(worker_1)
        solver = ps.SchedulingSolver(problem)

        solution = solver.solve()
        print(solution)
        self.assertTrue(solution)
        self.assertEqual(
            solution.indicators["FlowTime(Worker1:0:horizon)"], sum_durations
        )

    @staticmethod
    def get_single_resource_utilization_problem_2(time_intervals):
        horizon = time_intervals[-1][-1] + 3
        nb_tasks = [5 for interval in time_intervals if interval[1] - interval[0] > 3]
        problem = ps.SchedulingProblem(
            "IndicatorFlowtimeSingleResource", horizon=horizon
        )
        worker_1 = ps.Worker("Worker1")

        tasks: list[ps.FixedDurationTask] = []
        for interval, nb_tasks_i in zip(time_intervals, nb_tasks):
            for _ in range(nb_tasks_i):
                tasks.append(ps.FixedDurationTask("T%s" % len(tasks), duration=1))
                tasks[-1].add_required_resource(worker_1)
                problem.add_constraint(ps.TaskStartAfterLax(tasks[-1], interval[0]))
                problem.add_constraint(ps.TaskEndBeforeLax(tasks[-1], interval[1]))
        return problem, worker_1, len(tasks)

    @staticmethod
    def get_sum_flowtime(solution) -> int:
        return sum(
            solution.indicators[indicator_id]
            for indicator_id in solution.indicators
            if "FlowTime" in indicator_id
        )

    def test_indicator_flowtime_single_resource_5(self) -> None:
        # 2 time interval objectives
        time_intervals = [(11, 20), (21, 34)]
        (
            problem,
            worker_1,
            sum_durations,
        ) = self.get_single_resource_utilization_problem_2(time_intervals)
        for interval in time_intervals:
            problem.add_objective_flowtime_single_resource(
                worker_1, time_interval=interval
            )

        solver = ps.SchedulingSolver(problem)
        solution = solver.solve()

        self.assertTrue(solution)
        self.assertEqual(sum_durations, self.get_sum_flowtime(solution))

    def test_indicator_flowtime_single_resource_6(self) -> None:
        # Mutliple time intervals (Currently fails for nb_time_intervals > 2, gantt to check total_flowtime is correct)
        nb_time_intervals = 7
        time_interval_length = 13  # always > 5
        horizon = nb_time_intervals * time_interval_length
        time_intervals = [
            (i, i + time_interval_length)
            for i in range(0, horizon, time_interval_length)
        ]

        (
            problem,
            worker_1,
            sum_durations,
        ) = self.get_single_resource_utilization_problem_2(time_intervals)
        for interval in time_intervals:
            problem.add_objective_flowtime_single_resource(
                worker_1, time_interval=interval
            )

        solver = ps.SchedulingSolver(problem)

        solution = solver.solve()

        self.assertTrue(solution)
        self.assertEqual(sum_durations, self.get_sum_flowtime(solution))

    # number of tasks assigned to a resource
    def test_indicator_nb_tasks_assigned_to_resource_1(self) -> None:
        n = 5
        problem = ps.SchedulingProblem("IndicatorUtilization5", horizon=n)
        worker = ps.Worker("Worker1")

        for i in range(n):
            t = ps.FixedDurationTask(f"T{i+1}", duration=1)
            t.add_required_resource(worker)

        problem.add_indicator_number_tasks_assigned(worker)

        solver = ps.SchedulingSolver(problem)
        solution = solver.solve()

        self.assertTrue(solution)
        self.assertEqual(solution.indicators["Nb Tasks Assigned (Worker1)"], n)


if __name__ == "__main__":
    unittest.main()
