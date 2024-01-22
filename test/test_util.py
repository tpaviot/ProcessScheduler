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

import random

from processscheduler.util import (
    calc_parabola_from_three_points,
    sort_no_duplicates,
    sort_duplicates,
    clean_buffer_levels,
    get_minimum,
    get_maximum,
)

import z3


def test_calc_parabola_from_three_points():
    a, b, c = calc_parabola_from_three_points([0, 1, 2], [0, 2, 4])
    assert [a, b, c] == [0, 2, 0]
    d, e, f = calc_parabola_from_three_points([0, 1, 2], [0, 1, 4])
    assert [d, e, f] == [1, 0, 0]


def test_sort_no_duplicates():
    """sort an array of 20 different integers"""
    lst_to_sort = random.sample(range(-100, 100), 20)
    sorted_variables, assertions = sort_no_duplicates(lst_to_sort)
    s = z3.Solver()
    s.add(assertions)
    result = s.check()
    assert result == z3.sat
    solution = s.model()
    sorted_integers = [solution[v].as_long() for v in sorted_variables]
    assert sorted(lst_to_sort) == sorted_integers


def test_sort_duplicates():
    """sort an array of 20 integers with only 10 different"""
    lst_to_sort = random.sample(range(-100, 100), 10) * 2
    sorted_variables, assertions = sort_duplicates(lst_to_sort)
    s = z3.Solver()
    s.add(assertions)
    result = s.check()
    assert result == z3.sat
    solution = s.model()
    sorted_integers = [solution[v].as_long() for v in sorted_variables]
    assert sorted(lst_to_sort) == sorted_integers


def test_clean_buffer_levels():
    assert clean_buffer_levels([100, 21, 21, 21], [7, 7, 7]) == ([100, 21], [7])


def test_get_maximum():
    # 20 integers between 0 and 99
    lst = random.sample(range(100), k=20)
    # append 101, which must be the maximum
    lst.append(101)
    # build a list of z3 ints
    z3_lst = z3.Ints(" ".join([f"i{elem}" for elem in lst]))
    maxi = z3.Int("maxi")
    # find maximum
    assertions = get_maximum(maxi, z3_lst)
    # add assertions
    s = z3.Solver()
    s.add(assertions)
    s.add([a == b for a, b in zip(lst, z3_lst)])
    s.add(maxi == 101)
    assert s.check() == z3.sat


def test_get_minimum():
    # 20 integers between 10 and 99
    lst = random.sample(range(10, 100), k=20)
    # append 5, which must be the minimum
    lst.append(5)
    # build a list of z3 ints
    z3_lst = z3.Ints(" ".join([f"i{elem}" for elem in lst]))
    mini = z3.Int("mini")
    # find maximum
    assertions = get_minimum(mini, z3_lst)
    # add assertions
    s = z3.Solver()
    s.add(assertions)
    s.add([a == b for a, b in zip(lst, z3_lst)])
    s.add(mini == 5)
    assert s.check() == z3.sat
