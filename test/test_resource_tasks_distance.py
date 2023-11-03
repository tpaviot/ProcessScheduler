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


class TestResourceTasksDistance(unittest.TestCase):
    def test_resource_tasks_distance_raise_1(self) -> None:
        # if no task is assigned to the worker, a issue is raised
        ps.SchedulingProblem(name="ResourceTasksDistanceNoTaskRaiseAssertionError")
        worker = ps.Worker(name="Worker")
        with self.assertRaises(AssertionError):
            ps.ResourceTasksDistance(
                resource=worker, distance=0, list_of_time_intervals=[(0, 5)]
            )

    def test_resource_tasks_distance_raise_2(self) -> None:
        # if only one task is assigned to the worker, a issue is raised
        ps.SchedulingProblem(name="ResourceTasksDistanceOneTaskRaiseAssertionError")
        worker = ps.Worker(name="worker")
        task = ps.FixedDurationTask(name="Task", duration=1)
        task.add_required_resource(worker)
        with self.assertRaises(AssertionError):
            ps.ResourceTasksDistance(
                resource=worker, distance=0, list_of_time_intervals=[(0, 5)]
            )

    def test_resource_tasks_distance_1(self) -> None:
        pb = ps.SchedulingProblem(name="ResourceTasksDistance1", horizon=20)
        task_1 = ps.FixedDurationTask(name="task1", duration=8)
        task_2 = ps.FixedDurationTask(name="task2", duration=4)
        worker_1 = ps.Worker(name="Worker1")
        task_1.add_required_resource(worker_1)
        task_2.add_required_resource(worker_1)

        ps.ResourceTasksDistance(resource=worker_1, distance=4, mode="exact")
        ps.TaskStartAt(task=task_1, value=1)

        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)

        t1_start = solution.tasks[task_1.name].start
        t2_start = solution.tasks[task_2.name].start
        t1_end = solution.tasks[task_1.name].end
        t2_end = solution.tasks[task_2.name].end
        self.assertEqual(t1_start, 1)
        self.assertEqual(t1_end, 9)
        self.assertEqual(t2_start, 13)
        self.assertEqual(t2_end, 17)

    def test_resource_tasks_distance_2(self) -> None:
        pb = ps.SchedulingProblem(name="ResourceTasksDistance2")
        task_1 = ps.FixedDurationTask(name="task1", duration=8)
        task_2 = ps.FixedDurationTask(name="task2", duration=4)
        worker_1 = ps.Worker(name="Worker1")
        task_1.add_required_resource(worker_1)
        task_2.add_required_resource(worker_1)

        ps.ResourceTasksDistance(resource=worker_1, distance=4, mode="max")
        ps.TaskStartAt(task=task_1, value=1)

        pb.add_objective_makespan()

        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)

        t1_start = solution.tasks[task_1.name].start
        t2_start = solution.tasks[task_2.name].start
        t1_end = solution.tasks[task_1.name].end
        t2_end = solution.tasks[task_2.name].end
        self.assertEqual(t1_start, 1)
        self.assertEqual(t1_end, 9)
        self.assertEqual(t2_start, 9)
        self.assertEqual(t2_end, 13)

    def test_resource_tasks_distance_3(self) -> None:
        pb = ps.SchedulingProblem(name="ResourceTasksDistanceContiguous3")
        task_1 = ps.FixedDurationTask(name="task1", duration=8)
        task_2 = ps.FixedDurationTask(name="task2", duration=4)
        task_3 = ps.FixedDurationTask(name="task3", duration=5)
        worker_1 = ps.Worker(name="Worker1")
        task_1.add_required_resource(worker_1)
        task_2.add_required_resource(worker_1)
        task_3.add_required_resource(worker_1)

        # a constraint to tell tasks are contiguous
        ps.ResourceTasksDistance(resource=worker_1, distance=0, mode="exact")
        ps.TaskStartAt(task=task_1, value=2)

        pb.add_objective_makespan()

        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)

        t1_start = solution.tasks[task_1.name].start
        t2_start = solution.tasks[task_2.name].start
        t3_start = solution.tasks[task_3.name].start
        t1_end = solution.tasks[task_1.name].end

        self.assertEqual(t1_start, 2)
        self.assertEqual(t1_end, 10)
        self.assertTrue(t3_start in [10, 14])
        self.assertTrue(t2_start in [10, 15])

    def test_resource_tasks_distance_4(self) -> None:
        """Adding one or more non scheduled optional tasks should not change anything"""
        pb = ps.SchedulingProblem(
            name="ResourceTasksDistance4OptionalTasks", horizon=20
        )
        task_1 = ps.FixedDurationTask(name="task1", duration=8)
        task_2 = ps.FixedDurationTask(name="task2", duration=4)
        task_3 = ps.FixedDurationTask(name="task3", duration=3, optional=True)
        task_4 = ps.FixedDurationTask(name="task4", duration=2, optional=True)
        task_5 = ps.FixedDurationTask(name="task5", duration=1, optional=True)
        worker_1 = ps.Worker(name="Worker1")
        task_1.add_required_resource(worker_1)
        task_2.add_required_resource(worker_1)

        ps.ResourceTasksDistance(resource=worker_1, distance=4, mode="exact")
        ps.TaskStartAt(task=task_1, value=1)

        solver = ps.SchedulingSolver(problem=pb)

        # for optional tasks to not be scheduled
        solver.initialize()  # required before appending any z3 assertion
        solver.append_z3_assertion(task_3._scheduled == False)
        solver.append_z3_assertion(task_4._scheduled == False)
        solver.append_z3_assertion(task_5._scheduled == False)

        solution = solver.solve()

        self.assertTrue(solution)

        t1_start = solution.tasks[task_1.name].start
        t2_start = solution.tasks[task_2.name].start
        t1_end = solution.tasks[task_1.name].end
        t2_end = solution.tasks[task_2.name].end
        self.assertEqual(t1_start, 1)
        self.assertEqual(t1_end, 9)
        self.assertEqual(t2_start, 13)
        self.assertEqual(t2_end, 17)

    def test_resource_tasks_distance_single_time_period_1(self) -> None:
        """Adding one or more non scheduled optional tasks should not change anything"""
        pb = ps.SchedulingProblem(name="ResourceTasksDistanceSingleTimePeriod1")
        task_1 = ps.FixedDurationTask(name="task1", duration=1)
        task_2 = ps.FixedDurationTask(name="task2", duration=1)

        worker_1 = ps.Worker(name="Worker1")
        task_1.add_required_resource(worker_1)
        task_2.add_required_resource(worker_1)

        ps.ResourceTasksDistance(
            resource=worker_1,
            distance=4,
            mode="exact",
            list_of_time_intervals=[[10, 18]],
        )
        ps.TaskPrecedence(task_before=task_1, task_after=task_2)
        # we add a makespan objective: the two tasks should be scheduled with an horizon of 2
        # because they are outside the time period
        pb.add_objective_makespan()

        solver = ps.SchedulingSolver(problem=pb)

        solution = solver.solve()

        self.assertTrue(solution)
        t1_start = solution.tasks[task_1.name].start
        t2_start = solution.tasks[task_2.name].start
        t1_end = solution.tasks[task_1.name].end
        t2_end = solution.tasks[task_2.name].end
        self.assertEqual(t1_start, 0)
        self.assertEqual(t1_end, 1)
        self.assertEqual(t2_start, 1)
        self.assertEqual(t2_end, 2)

    def test_resource_tasks_distance_single_time_period_2(self) -> None:
        """The same as above, except that we force the tasks to be scheduled
        in the time period so that the distance applies"""
        pb = ps.SchedulingProblem(name="ResourceTasksDistanceSingleTimePeriod2")
        task_1 = ps.FixedDurationTask(name="task1", duration=1)
        task_2 = ps.FixedDurationTask(name="task2", duration=1)

        worker_1 = ps.Worker(name="Worker1")
        task_1.add_required_resource(worker_1)
        task_2.add_required_resource(worker_1)

        ps.ResourceTasksDistance(
            resource=worker_1,
            distance=4,
            mode="exact",
            list_of_time_intervals=[[10, 18]],
        )
        # force task 1 to start at 10 (in the time period intervak)
        ps.TaskStartAt(task=task_1, value=10)
        # task_2 must be scheduled after task_1
        ps.TaskPrecedence(task_before=task_1, task_after=task_2)

        # add a makespan objective, to be sure, to schedule task_2 in the time interal
        pb.add_objective_makespan()

        # as a consequence, task2 should be scheduled 4 periods after and start at 15
        solver = ps.SchedulingSolver(problem=pb)

        solution = solver.solve()

        self.assertTrue(solution)
        self.assertEqual(solution.tasks[task_2.name].start, 15)
        self.assertEqual(solution.tasks[task_2.name].end, 16)

    def test_resource_tasks_distance_double_time_period_1(self) -> None:
        """1 resource, 4 tasks, two time intervals for the ResourceTaskDistance"""
        pb = ps.SchedulingProblem(name="ResourceTasksDistanceMultiTimePeriod1")
        tasks = [ps.FixedDurationTask(name="task%i" % i, duration=1) for i in range(4)]

        worker_1 = ps.Worker(name="Worker1")
        for t in tasks:
            t.add_required_resource(worker_1)

        ps.ResourceTasksDistance(
            resource=worker_1,
            distance=4,
            mode="exact",
            list_of_time_intervals=[(10, 20), (30, 40)],
        )

        # add a makespan objective, all tasks should be scheduled from 0 to 4
        pb.add_objective_makespan()

        # as a consequence, task2 should be scheduled 4 periods after and start at 15
        solver = ps.SchedulingSolver(problem=pb)

        solution = solver.solve()

        self.assertTrue(solution)
        self.assertEqual(solution.horizon, 4)

    def test_resource_tasks_distance_double_time_period_2(self) -> None:
        """Same as above, but force the tasks to be scheduled within the time intervals"""
        pb = ps.SchedulingProblem(name="ResourceTasksDistanceMultiTimePeriod2")
        tasks = [ps.FixedDurationTask(name="task%i" % i, duration=1) for i in range(4)]

        worker_1 = ps.Worker(name="Worker1")
        for t in tasks:
            t.add_required_resource(worker_1)

        ps.ResourceTasksDistance(
            resource=worker_1,
            distance=4,
            mode="exact",
            list_of_time_intervals=[(10, 20), (30, 40)],
        )
        ps.TaskStartAt(task=tasks[0], value=10)
        ps.TaskStartAfter(task=tasks[1], value=10)
        ps.TaskEndBefore(task=tasks[1], value=20)
        ps.TaskStartAt(task=tasks[2], value=30)
        ps.TaskStartAfter(task=tasks[3], value=30)
        ps.TaskEndBefore(task=tasks[3], value=40)
        # as a consequence, task2 should be scheduled 4 periods after and start at 15
        solver = ps.SchedulingSolver(problem=pb)

        solution = solver.solve()

        self.assertTrue(solution)
        self.assertEqual(solution.horizon, 36)
        t0_start = solution.tasks[tasks[0].name].start
        t1_start = solution.tasks[tasks[1].name].start
        t2_start = solution.tasks[tasks[2].name].start
        t3_start = solution.tasks[tasks[3].name].start
        t0_end = solution.tasks[tasks[0].name].end
        t1_end = solution.tasks[tasks[1].name].end
        t2_end = solution.tasks[tasks[2].name].end
        t3_end = solution.tasks[tasks[3].name].end
        self.assertEqual(t0_start, 10)
        self.assertEqual(t0_end, 11)
        self.assertEqual(t1_start, 15)
        self.assertEqual(t1_end, 16)
        self.assertEqual(t2_start, 30)
        self.assertEqual(t2_end, 31)
        self.assertEqual(t3_start, 35)
        self.assertEqual(t3_end, 36)


if __name__ == "__main__":
    unittest.main()
