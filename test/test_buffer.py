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


class TestBuffer(unittest.TestCase):
    def test_instanciate_buffer(self) -> None:
        ps.SchedulingProblem(name="BufferBasic", horizon=12)
        ps.NonConcurrentBuffer(name="Buffer1", initial_state=10)

    def test_instanciate_buffer_error(self) -> None:
        ps.SchedulingProblem(name="BufferError", horizon=12)
        ps.NonConcurrentBuffer(name="Buffer1", initial_state=10)
        # a buffer with that name already exist, adding a new
        # one with the same name should raise an ValueError exception
        with self.assertRaises(ValueError):
            ps.NonConcurrentBuffer(name="Buffer1", initial_state=10)

    def test_unload_buffer_1(self) -> None:
        # only one buffer and one task
        pb = ps.SchedulingProblem(name="UnloadBuffer1")

        task_1 = ps.FixedDurationTask(name="task1", duration=3)
        buffer = ps.NonConcurrentBuffer(name="Buffer1", initial_state=10)

        ps.TaskStartAt(task=task_1, value=5)
        ps.TaskUnloadBuffer(task=task_1, buffer=buffer, quantity=3)

        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertEqual(solution.buffers[buffer.name].state, [10, 7])
        self.assertEqual(solution.buffers[buffer.name].state_change_times, [5])

    def test_unload_buffer_2(self) -> None:
        pb = ps.SchedulingProblem(name="UnloadBuffer2")

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
        self.assertTrue(solution)
        self.assertEqual(solution.buffers[buffer.name].state, [10, 7, 5, 4])
        self.assertEqual(solution.buffers[buffer.name].state_change_times, [5, 10, 15])

    def test_load_buffer_1(self) -> None:
        # only one buffer and one task
        pb = ps.SchedulingProblem(name="LoadBuffer1")

        task_1 = ps.FixedDurationTask(name="task1", duration=3)
        buffer = ps.NonConcurrentBuffer(name="Buffer1", initial_state=10)

        ps.TaskStartAt(task=task_1, value=5)
        ps.TaskLoadBuffer(task=task_1, buffer=buffer, quantity=3)

        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertEqual(solution.buffers[buffer.name].state, [10, 13])
        self.assertEqual(solution.buffers[buffer.name].state_change_times, [8])

    def test_load_buffer_2(self) -> None:
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
        self.assertTrue(solution)
        self.assertEqual(solution.buffers[buffer.name].state, [10, 13, 15, 16])
        self.assertEqual(solution.buffers[buffer.name].state_change_times, [8, 13, 18])

    def test_load_unload_feed_buffers_1(self) -> None:
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
        self.assertTrue(solution)
        self.assertEqual(solution.buffers[buffer_1.name].state, [10, 7])
        self.assertEqual(solution.buffers[buffer_1.name].state_change_times, [5])
        self.assertEqual(solution.buffers[buffer_2.name].state, [0, 2])
        self.assertEqual(solution.buffers[buffer_2.name].state_change_times, [8])

        # plot buffers
        solution.render_gantt_matplotlib(show_plot=False)

    def test_buffer_bounds_1(self) -> None:
        # n tasks take 1, n tasks feed one. Bounds 0 to 1
        pb = ps.SchedulingProblem(name="BufferBounds1")

        n = 3
        unloading_tasks = [
            ps.FixedDurationTask(name="LoadTask_%i" % i, duration=3) for i in range(n)
        ]
        loading_tasks = [
            ps.FixedDurationTask(name="UnloadTask_%i" % i, duration=3) for i in range(n)
        ]
        # create buffer
        buffer = ps.NonConcurrentBuffer(name="Buffer1", lower_bound=0, upper_bound=1)

        for t in unloading_tasks:
            ps.TaskUnloadBuffer(task=t, buffer=buffer, quantity=1)

        for t in loading_tasks:
            ps.TaskLoadBuffer(task=t, buffer=buffer, quantity=1)

        pb.add_objective_makespan()

        solver = ps.SchedulingSolver(
            problem=pb, max_time=300, parallel=True
        )  # , debug=True)#, logics="QF_UFIDL")
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertEqual(solution.horizon, 9)


if __name__ == "__main__":
    unittest.main()
