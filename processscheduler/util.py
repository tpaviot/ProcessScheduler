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

import z3


def calc_parabola_from_three_points(vector_x, vector_y):
    """
    Compute the coefficients a, b, c of the parabola that fits three points A, B, and C.

    Args:
        vector_x (list): List of x-coordinates for points A, B, and C.
        vector_y (list): List of y-coordinates for points A, B, and C.

    Returns:
        tuple: Coefficients a, b, c for the parabola equation y = ax^2 + bx + c.
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


def get_maximum(maxi, list_of_values):
    """
    Given a z3 variable and a list of z3 variables, return assertions and the maximum value.

    Args:
        maxi (z3.ArithRef): Z3 variable to represent the maximum value.
        list_of_values (list): List of z3 variables.

    Returns:
        list: Assertions to be passed to the solver.
    """
    if not list_of_values:
        raise AssertionError("Empty list")
    assertions = [z3.Or([maxi == elem for elem in list_of_values])]
    assertions.extend([maxi >= elem for elem in list_of_values])
    return assertions


def get_minimum(mini, list_of_values):
    """
    Given a z3 variable and a list of z3 variables, return assertions and the minimum value.

    Args:
        mini (z3.ArithRef): Z3 variable to represent the minimum value.
        list_of_values (list): List of z3 variables.

    Returns:
        list: Assertions to be passed to the solver.
    """
    if not list_of_values:
        raise AssertionError("Empty list")
    assertions = [z3.Or([mini == elem for elem in list_of_values])]
    assertions.extend([mini <= elem for elem in list_of_values])
    return assertions


def sort_duplicates(z3_int_list):
    """
    Sort a list of int variables using bubble sort and return the sorted list and associated assertions.

    Args:
        z3_int_list (list): List of z3 integer variables.

    Returns:
        tuple: Sorted list of z3 integer variables, and associated assertions.
    """
    sorted_list = z3_int_list.copy()
    glob_asst = []

    def bubble_up(ar):
        arr = ar.copy()
        local_asst = []
        for i in range(len(arr) - 1):
            x = arr[i]
            y = arr[i + 1]
            x1, y1 = z3.FreshInt(), z3.FreshInt()
            c = z3.If(x <= y, z3.And(x1 == x, y1 == y), z3.And(x1 == y, y1 == x))
            arr[i] = x1
            arr[i + 1] = y1
            local_asst.append(c)
        return arr, local_asst

    for _ in range(len(sorted_list)):
        sorted_list, asst = bubble_up(sorted_list)
        glob_asst.extend(asst)

    return sorted_list, glob_asst


def sort_no_duplicates(z3_int_list):
    """
    Sort a list of integers with distinct values and return the sorted list and constraints.

    Args:
        z3_int_list (list): List of z3 integer variables.

    Returns:
        tuple: Sorted list of z3 integer variables, and constraints for distinct values and ordering.
    """
    n = len(z3_int_list)
    a = [z3.FreshInt() for _ in range(n)]
    constraints = [z3.Or([a[i] == z3_int_list[j] for j in range(n)]) for i in range(n)]
    constraints.append(z3.And([a[i] < a[i + 1] for i in range(n - 1)]))
    return a, constraints


def clean_buffer_levels(buffer_levels, buffer_change_times):
    """
    Clean buffer levels and corresponding change times by removing duplicates.

    Args:
        buffer_levels (list): List of buffer levels.
        buffer_change_times (list): List of buffer change times.

    Returns:
        tuple: Cleaned buffer levels and corresponding change times.
    """
    if len(buffer_levels) != len(buffer_change_times) + 1:
        raise AssertionError(
            "Buffer levels list should have exactly one more element than buffer change times."
        )
    new_l1 = []  # Initial buffer level is always present
    new_l2 = []
    first_level = buffer_levels.pop(0)
    for a, b in zip(buffer_levels, buffer_change_times):
        if new_l2.count(b) < 1:
            new_l1.append(a)
            new_l2.append(b)
    new_l1 = [first_level] + new_l1
    return new_l1, new_l2
