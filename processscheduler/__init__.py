""" ProcessScheduler, Copyright 2020 Thomas Paviot (tpaviot@gmail.com)

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.
"""

__VERSION__ = '0.1-dev'

try:
    from z3 import BoolRef
except ModuleNotFoundError as z3_not_found:
    raise ImportError("z3 not found. It is a mandatory dependency") from z3_not_found

# Expose everything usefule
from processscheduler.boolean import not_, or_, and_, xor_
from processscheduler.task import ZeroDurationTask, FixedDurationTask, VariableDurationTask
from processscheduler.task_constraint import *
from processscheduler.resource import Worker, AlternativeWorkers
from processscheduler.problem import SchedulingProblem
from processscheduler.solver import SchedulingSolver