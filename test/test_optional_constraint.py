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


class TestOptionalConstraint(unittest.TestCase):
    def test_optional_constraint_start_at_1(self) -> None:
        pb = ps.SchedulingProblem("OptionalTaskStartAt1", horizon=6)
        task_1 = ps.FixedDurationTask("task1", duration=3)
        # the following tasks should conflict if they are mandatory
        pb.add_constraint(ps.TaskStartAt(task_1, 1, optional=True))
        pb.add_constraint(ps.TaskStartAt(task_1, 2, optional=True))
        pb.add_constraint(ps.TaskEndAt(task_1, 3, optional=True))

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)

    def test_force_apply_n_optional_constraints(self) -> None:
        pb = ps.SchedulingProblem("OptionalTaskStartAt1", horizon=6)
        task_1 = ps.FixedDurationTask("task1", duration=3)
        # the following tasks should conflict if they are mandatory
        cstr1 = ps.TaskStartAt(task_1, 1, optional=True)
        cstr2 = ps.TaskStartAt(task_1, 2, optional=True)
        cstr3 = ps.TaskEndAt(task_1, 3, optional=True)
        # force to apply exactly one constraint
        cstr4 = ps.ForceApplyNOptionalConstraints([cstr1, cstr2, cstr3], 1)
        # if we force 2 constraints, there should not be any solution

        pb.add_constraints([cstr1, cstr2, cstr3, cstr4])

        solver = ps.SchedulingSolver(pb)

        solution = solver.solve()
        self.assertTrue(solution)


if __name__ == "__main__":
    unittest.main()
