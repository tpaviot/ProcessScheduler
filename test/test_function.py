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


import processscheduler as ps


#
# Constant function
#
def test_constant_cost_function_1() -> None:
    c = ps.ConstantFunction(value=55)
    assert c(0) == 55
    assert c(10) == 55


#
# Linear function
#
def test_basic_linear_function_1() -> None:
    c = ps.LinearFunction(slope=1, intercept=1)
    assert c(0) == 1
    assert c(-1) == 0


def test_horizontal_linear_function_1() -> None:
    c = ps.LinearFunction(slope=0, intercept=3)
    assert c(0) == 3
    assert c(-1) == 3


#
# Polynomial function
#
def test_polynomial_function_1() -> None:
    c = ps.PolynomialFunction(coefficients=[1, 1])
    assert c(0) == 1
    assert c(-1) == 0


def test_polynomial_function_2() -> None:
    c = ps.PolynomialFunction(coefficients=[0, 4])
    assert c(0) == 4
    assert c(-1) == 4


def test_polynomial_function_3() -> None:
    c = ps.PolynomialFunction(coefficients=[1, 1, 1])
    assert c(0) == 1
    assert c(1) == 3
    assert c(2) == 7


def test_polynomial_function_4() -> None:
    c = ps.PolynomialFunction(coefficients=[2, 0, 0])
    assert c(0) == 0
    assert c(3) == 18


#
# Plots
#
def test_plot_constant_function():
    c = ps.ConstantFunction(value=55)
    ps.plot_function(c, interval=[0, 20], title="Constant function", show_plot=False)


def test_plot_linear_function():
    c = ps.LinearFunction(slope=1, intercept=2)
    ps.plot_function(c, interval=[0, 20], title="Linear function", show_plot=False)


def test_plot_polynomial_function():
    c = ps.PolynomialFunction(coefficients=[1, 2, 3, 4])
    ps.plot_function(c, interval=[0, 20], title="Polynomial function", show_plot=False)
