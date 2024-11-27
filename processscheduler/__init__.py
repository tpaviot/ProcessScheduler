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

__VERSION__ = "2.1.0"

try:
    import z3
except ModuleNotFoundError as z3_not_found:
    raise ImportError("z3 not found. It is a mandatory dependency") from z3_not_found

# Expose everything useful
from processscheduler.first_order_logic import Not, Or, And, Xor, Implies, IfThenElse
from processscheduler.indicator import (
    Indicator,
    IndicatorFromMathExpression,
    IndicatorTardiness,
    IndicatorEarliness,
    IndicatorNumberOfTardyTasks,
    IndicatorMaximumLateness,
    IndicatorResourceUtilization,
    IndicatorResourceIdle,
    IndicatorNumberTasksAssigned,
    IndicatorResourceCost,
    IndicatorMaxBufferLevel,
    IndicatorMinBufferLevel,
)
from processscheduler.objective import (
    Objective,
    ObjectiveMaximizeIndicator,
    ObjectiveMinimizeIndicator,
    ObjectiveMinimizeMakespan,
    ObjectiveMaximizeResourceUtilization,
    ObjectiveMinimizeResourceCost,
    ObjectivePriorities,
    ObjectiveTasksStartLatest,
    ObjectiveTasksStartEarliest,
    ObjectiveMinimizeGreatestStartTime,
    ObjectiveMinimizeFlowtime,
    ObjectiveMinimizeFlowtimeSingleResource,
    ObjectiveMaximizeMaxBufferLevel,
    ObjectiveMinimizeMaxBufferLevel,
)
from processscheduler.task import (
    ZeroDurationTask,
    FixedDurationTask,
    VariableDurationTask,
    FixedDurationInterruptibleTask,
)
from processscheduler.constraint import *
from processscheduler.task_constraint import *
from processscheduler.resource_constraint import (
    SameWorkers,
    DistinctWorkers,
    ResourceUnavailable,
    ResourcePeriodicallyUnavailable,
    WorkLoad,
    ResourceTasksDistance,
    ResourceNonDelay,
    ResourceInterrupted,
    ResourcePeriodicallyInterrupted,
)
from processscheduler.indicator_constraint import IndicatorTarget, IndicatorBounds
from processscheduler.resource import Worker, CumulativeWorker, SelectWorkers
from processscheduler.function import (
    ConstantFunction,
    LinearFunction,
    PolynomialFunction,
    GeneralFunction,
)
from processscheduler.problem import SchedulingProblem
from processscheduler.solver import SchedulingSolver
from processscheduler.buffer import NonConcurrentBuffer, ConcurrentBuffer
from processscheduler.plotter import (
    plot_function,
    render_gantt_matplotlib,
    render_gantt_plotly,
)
