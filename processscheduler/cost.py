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

from processscheduler.base import _NamedUIDObject, is_positive_integer

class _Cost(_NamedUIDObject):
    """ The base class for cost definition, to be assigned to a resource instance"""
    def __init__(self):
        super().__init__('')

class ConstantCostPerPeriod(_Cost):
    def __init__(self, value: int) -> None:
        super().__init__()
        if not is_positive_integer(value):
            raise ValueError('the cost per period must be a positive integer')
        self.value = value

class PolynomialCostFunction(_Cost):
    def __init__(self, function: callable) -> None:
        super().__init__()
        if not callable(function):
            raise TypeError('function must be a callable')
        self.f = function

    def __call__(self, value):
        """ compute the value of the cost function for a given value"""
        return self.f(value)
