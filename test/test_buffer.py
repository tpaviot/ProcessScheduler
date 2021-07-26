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

    def test_consume_buffer(self) -> None:
        pb = ps.SchedulingProblem("ConsumeBuffer")

        task_1 = ps.FixedDurationTask("task1", duration=3)
        buffer = ps.Buffer("Buffer1", initial_state=10)

        c = ps.TaskConsumeBuffer(task_1, buffer, quantity=3)
        pb.add_constraint(c)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)

    def test_feed_buffer(self) -> None:
        pb = ps.SchedulingProblem("FeedBuffer")

        task_1 = ps.FixedDurationTask("task1", duration=3)
        buffer = ps.Buffer("Buffer1", initial_state=10)

        c = ps.TaskFeedBuffer(task_1, buffer, quantity=8)
        pb.add_constraint(c)

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)

if __name__ == "__main__":
    unittest.main()
