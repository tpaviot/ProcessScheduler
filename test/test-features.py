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

if __name__ == "__main__":
    unittest.main()
