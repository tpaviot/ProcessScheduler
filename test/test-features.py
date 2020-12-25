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
import warnings

import processscheduler as ps

class TestFeatures(unittest.TestCase):
    def test_create_problem(self) -> None:
        """ Scenario creation
        """
        pb = ps.SchedulingProblem('pb1', horizon=10)
        self.assertIsInstance(pb, ps.SchedulingProblem)

    def test_create_zero_length_(self) -> None:
        task = ps.ZeroLengthTask('zt')
        self.assertTrue(task._fixed_length)
        self.assertFalse(task._variable_length)

    def test_dont_overlap_task_constraint(self) -> None:
        # problem
        pb1 = ps.SchedulingProblem("DontOverlapExample", horizon=10)
        # tasks
        t1 = ps.FixedLengthTask('t1', length=2)
        t2 = ps.FixedLengthTask('t2', length=2)
        t3 = ps.FixedLengthTask('t3', length=2)
        pb1.add_tasks([t1, t2,t3])
        # constraints
        c1 = ps.TaskStartAt(t2, 1)
        c2 = ps.TaskDontOverlap(t2, t3)
        pb1.add_constraints([c1, c2])
        # solve
        solver1 = ps.SchedulingSolver(pb1, verbosity=False)
        solver1.solve()
        # t3 should be scheduled last
        self.assertEqual(t3.start_value, 3)

if __name__ == "__main__":
    unittest.main()
