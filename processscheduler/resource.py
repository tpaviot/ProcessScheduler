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

from typing import Dict, List, Tuple, Literal, Union

from z3 import ArithRef, Bool, PbEq, PbGe, PbLe

from pydantic import Field, PositiveInt

from processscheduler.base import NamedUIDObject
from processscheduler.cost import Cost, ConstantCostFunction

# import processscheduler.context as ps_context
import processscheduler.base


#
# Utility functions
#
def _distribute_p_over_n(p, n):
    """Returns a list of integer p distributed over n values."""
    if p is None:
        return [None for _ in range(n)]
    if isinstance(p, int):
        int_value = p
    elif isinstance(p, ConstantCostFunction):
        int_value = p.value
    else:
        raise AssertionError("wrong type for parameter p")
    to_return = [int_value // n + int_value % n]
    to_return.extend(int_value // n for _ in range(n - 1))
    # check that the list to return has the good length
    if len(to_return) != n:
        raise AssertionError("wrong length")
    if sum(to_return) != int_value:
        raise AssertionError("wrong sum")
    return to_return


#
# Resources class definition
#
class Resource(NamedUIDObject):
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

    productivity: int = Field(default=1, ge=0)  # productivity >= 0
    cost: Union[Cost, None] = Field(default=None)

    def __init__(self, **data) -> None:
        super().__init__(**data)
        # only worker are added to the main context, not SelectWorkers
        # add this resource to the current context
        if processscheduler.base.active_problem is None:
            raise AssertionError(
                "No context available. First create a SchedulingProblem"
            )
        processscheduler.base.active_problem.add_resource_worker(self)


class CumulativeWorker(Resource):
    """A cumulative worker can process multiple tasks in parallel."""

    # size is 2 min, otherwise it should be a single worker
    size: int = Field(gt=1)  # size strictly > 1
    productivity: PositiveInt = Field(default=1)
    cost: Union[Cost, None] = Field(default=None)

    def __init__(self, **data) -> None:
        super().__init__(**data)
        # productivity and cost_per_period are distributed over
        # individual workers
        # for example, a productivty of 7 for a size of 3 will be distributed
        # as 3 on worker 1, 2 on worker 2 and 2 on worker 3. Same for cost_per_periods
        productivities = _distribute_p_over_n(self.productivity, self.size)

        costs_per_period = _distribute_p_over_n(self.cost, self.size)
        # we create as much elementary workers as the cumulative size
        self._cumulative_workers = [
            Worker(
                name=f"{self.name}_CumulativeWorker_{i+1}",
                productivity=productivities[i],
                cost=ConstantCostFunction(value=costs_per_period[i])
                if costs_per_period[i] is not None
                else None,
            )
            for i in range(self.size)
        ]

        processscheduler.base.active_problem.add_resource_cumulative_worker(self)

    def get_select_workers(self):
        """Each time the cumulative resource is assigned to a task, a SelectWorker
        instance is assigned to the task."""
        return SelectWorkers(
            list_of_workers=self._cumulative_workers, nb_workers_to_select=1, kind="min"
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
                self._list_of_workers.extend(worker._cumulative_workers)
            else:
                self._list_of_workers.append(worker)

        # a dict that maps workers and selected boolean
        self._selection_dict = {}

        # create as many booleans as resources in the list
        for worker in self.list_of_workers:
            worker_is_selected = Bool(f"Selected_{worker.name}_{self._uid}")
            self._selection_dict[worker] = worker_is_selected
        # create the assertion : exactly n boolean flags are allowed to be True,
        # the others must be False
        # see https://github.com/Z3Prover/z3/issues/694
        # and https://stackoverflow.com/questions/43081929/k-out-of-n-constraint-in-z3py
        selection_list = list(self._selection_dict.values())
        self._selection_assertion = problem_function[self.kind](
            [(selected, True) for selected in selection_list], self.nb_workers_to_select
        )
        processscheduler.base.active_problem.add_resource_select_workers(self)
