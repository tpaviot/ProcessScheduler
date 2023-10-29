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

from typing import Dict, List, Optional, Tuple, Literal, Union

from z3 import ArithRef, Bool, PbEq, PbGe, PbLe

from processscheduler.base import _NamedUIDObject
from processscheduler.util import is_strict_positive_integer, is_positive_integer
from processscheduler.cost import _Cost, ConstantCostPerPeriod
import processscheduler.context as ps_context

from pydantic import Field, PositiveInt, ValidationError


#
# Utility functions
#
def _distribute_p_over_n(p, n):
    """Returns a list of integer p distributed over n values."""
    if p is None:
        return [p for _ in range(n)]
    if isinstance(p, int):
        int_div = p // n
        to_return = [int_div + p % n]
        to_return.extend(int_div for _ in range(n - 1))
        return to_return
    if isinstance(p, ConstantCostPerPeriod):
        int_div = p.value // n
        to_return = [ConstantCostPerPeriod(int_div + p.value % n)]
        to_return.extend(ConstantCostPerPeriod(int_div) for _ in range(n - 1))
        return to_return
    raise AssertionError("wrong type for parameter p")


#
# Resources class definition
#
class Resource(_NamedUIDObject):
    """base class for the representation of a resource"""

    def __init__(self, **data) -> None:
        super().__init__(**data)
        # for each resource, we define a dict that stores
        # all tasks and busy intervals of the resource.
        # busy intervals can be for example [(1,3), (5, 7)]
        self._busy_intervals = {}  # type: Dict[Task, Tuple[ArithRef, ArithRef]]

    def add_busy_interval(self, task, interval: Tuple[ArithRef, ArithRef]) -> None:
        """add an interval in which the resource is busy"""
        self._busy_intervals[task] = interval

    def get_busy_intervals(self) -> List[Tuple[ArithRef, ArithRef]]:
        """returns the list of all busy intervals"""
        return list(self._busy_intervals.values())


class Worker(Resource):
    """A worker is an atomic resource that cannot be split into smaller parts.
    Typical workers are human beings, machines etc."""

    productivity: PositiveInt = Field(default=1)
    cost: _Cost = Field(default=None)

    def __init__(self, **data) -> None:
        super().__init__(**data)
        # only worker are add to the main context, not SelectWorkers
        # add this resource to the current context
        if ps_context.main_context is None:
            raise AssertionError(
                "No context available. First create a SchedulingProblem"
            )
        ps_context.main_context.add_resource(self)


class CumulativeWorker(Resource):
    """A cumulative worker can process multiple tasks in parallel."""

    # size is 2 min, otherwise it should be a single worker
    size: int = Field(gt=2)
    productivity: PositiveInt = Field(default=1)
    cost: _Cost = Field(default=None)

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self.cost_defined_value = cost

        # productivity and cost_per_period are distributed over
        # individual workers
        # for example, a productivty of 7 for a size of 3 will be distributed
        # as 3 on worker 1, 2 on worker 2 and 2 on worker 3. Same for cost_per_periods
        productivities = _distribute_p_over_n(productivity, size)

        costs_per_period = _distribute_p_over_n(cost, size)

        # we create as much elementary workers as the cumulative size
        self.cumulative_workers = [
            Worker(
                name=f"{name}_CumulativeWorker_{i+1}",
                productivity=productivities[i],
                cost=costs_per_period[i],
            )
            for i in range(size)
        ]

        ps_context.main_context.add_resource_cumulative_worker(self)

    def get_select_workers(self):
        """Each time the cumulative resource is assigned to a task, a SelectWorker
        instance is assigned to the task."""
        return SelectWorkers(
            list_of_workers=self.cumulative_workers, nb_workers_to_select=1, kind="min"
        )


class SelectWorkers(Resource):
    """Class representing the selection of n workers chosen among a list
    of possible workers"""

    list_of_workers: List[Union[Worker, CumulativeWorker]] = Field(min_length=2)
    nb_workers_to_select: PositiveInt = Field(default=1)
    kind: Literal["exact", "min", "max"] = Field(default="exact")

    def __init__(self, **data) -> None:
        super().__init__(**data)

        problem_function = {"min": PbGe, "max": PbLe, "exact": PbEq}

        # TODO: in the validator
        if self.nb_workers_to_select > len(self.list_of_workers):
            raise ValueError(
                "nb_workers must be <= the number of workers provided in list_of_workers."
            )

        # build the list of workers that will be the base of the selection
        # instances from this list mght either be Workers or CumulativeWorkers. If
        # this is a cumulative, then we add the list of all workers from the cumulative
        # into this list.
        self._list_of_workers = []
        for worker in self.list_of_workers:
            if isinstance(worker, CumulativeWorker):
                self._list_of_workers.extend(worker.cumulative_workers)
            else:
                self._list_of_workers.append(worker)

        # a dict that maps workers and selected boolean
        self._selection_dict = {}

        # create as many booleans as resources in the list
        for worker in self.list_of_workers:
            worker_is_selected = Bool(f"Selected_{worker.name}_{self.uid}")
            self._selection_dict[worker] = worker_is_selected

        # create the assertion : exactly n boolean flags are allowed to be True,
        # the others must be False
        # see https://github.com/Z3Prover/z3/issues/694
        # and https://stackoverflow.com/questions/43081929/k-out-of-n-constraint-in-z3py
        selection_list = list(self._selection_dict.values())
        self._selection_assertion = problem_function[self.kind](
            [(selected, True) for selected in selection_list], self.nb_workers_to_select
        )
        ps_context.main_context.add_resource_select_workers(self)
