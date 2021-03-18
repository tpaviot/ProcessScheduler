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

import unittest

import processscheduler as ps

class TestOptionalConstraint(unittest.TestCase):
    def test_optional_constraint_start_at_1(self) -> None:
        pb = ps.SchedulingProblem('OptionalTaskStartAt1', horizon=6)
        task_1 = ps.FixedDurationTask('task1', duration = 3)
        # the following tasks should conflict if they are mandatory
        pb.add_constraint(ps.TaskStartAt(task_1, 1, optional=True))
        pb.add_constraint(ps.TaskStartAt(task_1, 2, optional=True))
        pb.add_constraint(ps.TaskEndAt(task_1, 3, optional=True))

        solver = ps.SchedulingSolver(pb)
        solution = solver.solve()
        self.assertTrue(solution)

    def test_force_apply_n_optional_constraints(self) -> None:
        pb = ps.SchedulingProblem('OptionalTaskStartAt1', horizon=6)
        task_1 = ps.FixedDurationTask('task1', duration = 3)
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
