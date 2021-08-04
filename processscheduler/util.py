"""This module utility functions share across the software."""

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

from z3 import And, FreshInt, If, Or

#
# Functions over python types (ints, strings, etc.)
#
def is_strict_positive_integer(value: int) -> bool:
    """Return True if the parameter value is an integer > 0"""
    return isinstance(value, int) and value > 0


def is_positive_integer(value: int) -> bool:
    """Return True if the parameter value is an integer >= 0"""
    return isinstance(value, int) and value >= 0


#
# Functions over python and z3 types
#

#
# Functions over z3 types only (ArithRef, BoolRef, etc.)
#
def calc_parabola_from_two_points(vector_x, vector_y):
    """Compute the parabola that fits 3 points A, B and C. (x,y) coordinates
    for these points are stored in two vectors.
    Return a, b, c such as points 1, 2, 3 satisfies
    y = ax**2+bx+c
    """
    x1, x2, x3 = vector_x
    y1, y2, y3 = vector_y
    denom = (x1 - x2) * (x1 - x3) * (x2 - x3)
    a = (x3 * (y2 - y1) + x2 * (y1 - y3) + x1 * (y3 - y2)) / denom
    b = (x3 * x3 * (y1 - y2) + x2 * x2 * (y3 - y1) + x1 * x1 * (y2 - y3)) / denom
    c = (
        x2 * x3 * (x2 - x3) * y1 + x3 * x1 * (x3 - x1) * y2 + x1 * x2 * (x1 - x2) * y3
    ) / denom
    return a, b, c


def sort_bubble(z3_int_list):
    """Take a list of int variables, return the list of new variables
    sorting using the bubble recursive sort"""
    sorted_list = z3_int_list.copy()
    glob_asst = []

    def bubble_up(ar):
        arr = ar.copy()
        local_asst = []
        for i in range(len(arr) - 1):
            x = arr[i]
            y = arr[i + 1]
            # compare and swap x and y
            x1, y1 = FreshInt(), FreshInt()
            c = If(x <= y, And(x1 == x, y1 == y), And(x1 == y, y1 == x))
            # store values
            arr[i] = x1
            arr[i + 1] = y1
            local_asst.append(c)
        return arr, local_asst

    for _ in range(len(sorted_list)):
        sorted_list, asst = bubble_up(sorted_list)
        glob_asst.extend(asst)

    return sorted_list, glob_asst


def sort_no_duplicates(z3_int_list):
    """Sort a list of integers that have distinct values"""
    n = len(z3_int_list)
    a = [FreshInt() for i in range(n)]
    constraints = [Or([a[i] == z3_int_list[j] for j in range(n)]) for i in range(n)]
    constraints.append(And([a[i] < a[i + 1] for i in range(n - 1)]))

    return a, constraints
