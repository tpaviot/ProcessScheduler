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
from processscheduler.util import (
    calc_parabola_from_two_points,
    is_positive_integer,
    is_strict_positive_integer,
    sort_no_duplicates,
    sort_bubble,
)

from z3 import Solver, sat


class TestUtil(unittest.TestCase):
    def test_is_positive_integer(self):
        self.assertTrue(is_positive_integer(1))
        self.assertTrue(is_positive_integer(0))
        self.assertTrue(is_positive_integer(7))
        self.assertFalse(is_positive_integer(7.5))
        self.assertFalse(is_positive_integer(-1))
        self.assertFalse(is_positive_integer(-0.3))

    def test_is_strict_positive_integer(self):
        self.assertTrue(is_strict_positive_integer(1))
        self.assertFalse(is_strict_positive_integer(0))  # strict
        self.assertTrue(is_strict_positive_integer(7))
        self.assertFalse(is_strict_positive_integer(7.5))
        self.assertFalse(is_strict_positive_integer(-1))
        self.assertFalse(is_strict_positive_integer(-0.3))

    def test_calc_parabola_from_two_points(self):
        a, b, c = calc_parabola_from_two_points([0, 1, 2], [0, 2, 4])
        self.assertEqual([a, b, c], [0, 2, 0])
        d, e, f = calc_parabola_from_two_points([0, 1, 2], [0, 1, 4])
        self.assertEqual([d, e, f], [1, 0, 0])

    def test_sort_no_duplicates(self):
        lst_to_sort = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, -1, -2]
        sorted_variables, assertions = sort_no_duplicates(lst_to_sort)
        s = Solver()
        s.add(assertions)
        result = s.check()
        solution = s.model()
        sorted_integers = [solution[v].as_long() for v in sorted_variables]
        self.assertEqual(result, sat)
        self.assertEqual(sorted_integers, [-2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    def test_sort_duplicates(self):
        lst_to_sort = [10, 9, 8, 7, 6, 10, 9, 8, 7, 6, 1]
        sorted_variables, assertions = sort_bubble(lst_to_sort)
        s = Solver()
        s.add(assertions)
        result = s.check()
        solution = s.model()
        sorted_integers = [solution[v].as_long() for v in sorted_variables]
        self.assertEqual(result, sat)
        self.assertEqual(sorted_integers, [1, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10])


if __name__ == "__main__":
    unittest.main()
