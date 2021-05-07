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

class TestCost(unittest.TestCase):
    def test_cost_basic(self) -> None:
        pb = ps.SchedulingProblem('CostBasic', horizon=12)
        ress_cost = ps.ConstantCostPerPeriod(5)
        ress = ps.Worker('ress1', cost=ress_cost)

    def test_cost_failure(self) -> None:
        pb = ps.SchedulingProblem('CostWrongType', horizon=12)
        with self.assertRaises(TypeError):
            ress = ps.Worker('ress1', cost = 5)


if __name__ == "__main__":
    unittest.main()
