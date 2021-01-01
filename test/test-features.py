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

class TestFeatures(unittest.TestCase):
    def test_create_problem_with_horizon(self) -> None:
        """ Scenario creation
        """
        pb = ps.SchedulingProblem('ProblemWithHorizon', horizon=10)
        self.assertIsInstance(pb, ps.SchedulingProblem)

    def test_create_problem_without_horizon(self) -> None:
        """ Scenario creation
        """
        pb = ps.SchedulingProblem('ProblemWithoutHorizon')
        self.assertIsInstance(pb, ps.SchedulingProblem)

    def test_create_zero_length_(self) -> None:
        task = ps.ZeroDurationTask('zt')
        self.assertIsInstance(task, ps.ZeroDurationTask)

    def test_dont_overlap_task_constraint(self) -> None:
        # problem
        pb1 = ps.SchedulingProblem("DontOverlapExample", horizon=10)
        # tasks
        t1 = ps.FixedDurationTask('t1', duration=2)
        t2 = ps.FixedDurationTask('t2', duration=3)
        t3 = ps.FixedDurationTask('t3', duration=4)
        pb1.add_tasks([t1, t2,t3])
        # constraints
        c1 = ps.TaskStartAt(t2, 1)
        c2 = ps.TasksDontOverlap(t2, t3)
        pb1.add_constraints([c1, c2])
        # solve
        solver1 = ps.SchedulingSolver(pb1, verbosity=False)
        solver1.solve()
        # t3 should be scheduled last
        self.assertEqual(t3.scheduled_start, 4)

if __name__ == "__main__":
    unittest.main()
