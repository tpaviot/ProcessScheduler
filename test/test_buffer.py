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
        pb = ps.SchedulingProblem("BufferBasic", horizon=12)
        buffer = ps.Buffer("Buffer1", initial_state=10)

    def test_instanciate_buffer_error(self) -> None:
        pb = ps.SchedulingProblem("BufferError", horizon=12)
        buffer = ps.Buffer("Buffer1", initial_state=10)
        # a buffer with that name already exist, adding a new
        # one with the same name should raise an ValueError exception
        with self.assertRaises(ValueError):
            buffer = ps.Buffer("Buffer1", initial_state=10)

    def test_consume_buffer_1(self) -> None:
        # only one buffer and one task
        pb = ps.SchedulingProblem("ConsumeBuffer1")

        task_1 = ps.FixedDurationTask("task1", duration=3)
        buffer = ps.Buffer("Buffer1", initial_state=10)

        pb.add_constraint(ps.TaskStartAt(task_1, 5))
        c1 = ps.TaskConsumeBuffer(task_1, buffer, quantity=3)
        pb.add_constraint(c1)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertEqual(solution.buffers[buffer.name].state, [10, 7])
        self.assertEqual(solution.buffers[buffer.name].state_change_times, [5])

    def test_consume_buffer_2(self) -> None:
        pb = ps.SchedulingProblem("ConsumeBuffer2")

        task_1 = ps.FixedDurationTask("task1", duration=3)
        task_2 = ps.FixedDurationTask("task2", duration=3)
        task_3 = ps.FixedDurationTask("task3", duration=3)
        buffer = ps.Buffer("Buffer1", initial_state=10)

        pb.add_constraint(ps.TaskStartAt(task_1, 5))
        pb.add_constraint(ps.TaskStartAt(task_2, 10))
        pb.add_constraint(ps.TaskStartAt(task_3, 15))
        c1 = ps.TaskConsumeBuffer(task_1, buffer, quantity=3)
        pb.add_constraint(c1)

        c2 = ps.TaskConsumeBuffer(task_2, buffer, quantity=2)
        pb.add_constraint(c2)

        c3 = ps.TaskConsumeBuffer(task_3, buffer, quantity=1)
        pb.add_constraint(c3)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertEqual(solution.buffers[buffer.name].state, [10, 7, 5, 4])
        self.assertEqual(solution.buffers[buffer.name].state_change_times, [5, 10, 15])

    def test_feed_buffer_1(self) -> None:
        # only one buffer and one task
        pb = ps.SchedulingProblem("FeedBuffer1")

        task_1 = ps.FixedDurationTask("task1", duration=3)
        buffer = ps.Buffer("Buffer1", initial_state=10)

        pb.add_constraint(ps.TaskStartAt(task_1, 5))
        c1 = ps.TaskFeedBuffer(task_1, buffer, quantity=3)
        pb.add_constraint(c1)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertEqual(solution.buffers[buffer.name].state, [10, 13])
        self.assertEqual(solution.buffers[buffer.name].state_change_times, [8])

    def test_feed_buffer_2(self) -> None:
        pb = ps.SchedulingProblem("FeedBuffer2")

        task_1 = ps.FixedDurationTask("task1", duration=3)
        task_2 = ps.FixedDurationTask("task2", duration=3)
        task_3 = ps.FixedDurationTask("task3", duration=3)
        buffer = ps.Buffer("Buffer1", initial_state=10)

        pb.add_constraint(ps.TaskStartAt(task_1, 5))
        pb.add_constraint(ps.TaskStartAt(task_2, 10))
        pb.add_constraint(ps.TaskStartAt(task_3, 15))
        c1 = ps.TaskFeedBuffer(task_1, buffer, quantity=3)
        pb.add_constraint(c1)

        c2 = ps.TaskFeedBuffer(task_2, buffer, quantity=2)
        pb.add_constraint(c2)

        c3 = ps.TaskFeedBuffer(task_3, buffer, quantity=1)
        pb.add_constraint(c3)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertEqual(solution.buffers[buffer.name].state, [10, 13, 15, 16])
        self.assertEqual(solution.buffers[buffer.name].state_change_times, [8, 13, 18])

    def test_consume_feed_buffers_1(self) -> None:
        # one task that consumes and feed two different buffers
        pb = ps.SchedulingProblem("ConsumeFeedBuffer1")

        task_1 = ps.FixedDurationTask("task1", duration=3)
        buffer_1 = ps.Buffer("Buffer1", initial_state=10)
        buffer_2 = ps.Buffer("Buffer2", initial_state=0)

        pb.add_constraint(ps.TaskStartAt(task_1, 5))
        c1 = ps.TaskConsumeBuffer(task_1, buffer_1, quantity=3)
        pb.add_constraint(c1)

        c2 = ps.TaskFeedBuffer(task_1, buffer_2, quantity=2)
        pb.add_constraint(c2)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertEqual(solution.buffers[buffer_1.name].state, [10, 7])
        self.assertEqual(solution.buffers[buffer_1.name].state_change_times, [5])
        self.assertEqual(solution.buffers[buffer_2.name].state, [0, 2])
        self.assertEqual(solution.buffers[buffer_2.name].state_change_times, [8])

        # plot buffers
        solution.render_gantt_matplotlib(show_plot=False)


if __name__ == "__main__":
    unittest.main()
