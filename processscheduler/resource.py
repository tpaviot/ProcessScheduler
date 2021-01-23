"""The resources definition."""

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

from typing import Dict, List, Optional, Tuple
import warnings

from z3 import ArithRef, Bool, PbEq, PbGe, PbLe, Xor

from processscheduler.base import (_NamedUIDObject, is_positive_integer,
                                   is_strict_positive_integer)
import processscheduler.context as ps_context

#
# Resources class definition
#
class _Resource(_NamedUIDObject):
    """ base class for the representation of a resource """
    def __init__(self, name: str):
        super().__init__(name)

        # for each resource, we define a dict that stores
        # all tasks and busy intervals of the resource.
        # busy intervals can be for example [(1,3), (5, 7)]
        self.busy_intervals = {} # type: Dict[Task, Tuple[ArithRef, ArithRef]]

    def add_busy_interval(self, task, interval: Tuple[ArithRef, ArithRef]) -> None:
        """ add an interval in which the resource is busy """
        if task in self.busy_intervals:
            warnings.warn('%s is already defined as a required resource for task %s' % (self.name,
                                                                                        task.name))
            return False
        # add the assertions: this new interval must not overlap with all the
        # intervals already defined
        start, end = interval
        for start_task_i, end_task_i in self.get_busy_intervals():
            self.add_assertion(Xor(start_task_i >= end, start >= end_task_i))

        # finally add this interval to the dict
        self.busy_intervals[task] = interval

        return True

    def get_busy_intervals(self) -> List[Tuple[ArithRef, ArithRef]]:
        """ returns the list of all busy intervals """
        return list(self.busy_intervals.values())

class Worker(_Resource):
    """ A worker is an atomic resource that cannot be split into smaller parts.
    Typical workers are human beings, machines etc. """
    def __init__(self,
                 name: str,
                 productivity: Optional[int] = 1,
                 cost_per_period: Optional[int] = 0) -> None:
        super().__init__(name)
        if not is_positive_integer(productivity):
            raise TypeError('productivity must be an integer >= 0')
        self.productivity = productivity
        self.cost_per_period = cost_per_period
        # only worker are add to the main context, not SelectWorkers
        ps_context.main_context.add_resource(self)

class SelectWorkers(_Resource):
    """ Class representing the selection of n workers chosen among a list
    of possible workers """
    def __init__(self,
                 list_of_workers: List[_Resource],
                 nb_workers: Optional[int] = 1,
                 kind: Optional[str] = 'exact'):
        """ create an instance of the SelectWorkers class. """
        super().__init__('')

        problem_function = {'atleast': PbGe, 'atmost': PbLe, 'exact': PbEq}

        if kind not in problem_function:
            raise ValueError("kind must be either 'exact', 'atleast' or 'atmost'")

        if not is_strict_positive_integer(nb_workers):
            raise TypeError('nb_workers must be an integer > 0')

        if nb_workers > len(list_of_workers):
            raise ValueError('nb_workers must be <= the number of workers provided in list_of_workers.')

        if len(list_of_workers) < 1:
            raise ValueError('At least 2 workers should be in the list_of_workers.')

        self.list_of_workers = list_of_workers
        self.nb_workers = nb_workers

        # a dict that maps workers and selected boolean
        self.selection_dict = {}

        # create as many booleans as resources in the list
        for worker in list_of_workers:
            worker_is_selected = Bool('Selected_%s_%i' % (worker.name, self.uid))
            self.selection_dict[worker] = worker_is_selected

        # create the assertion : exactly n boolean flags are allowed to be True,
        # the others must be False
        # see https://github.com/Z3Prover/z3/issues/694
        # and https://stackoverflow.com/questions/43081929/k-out-of-n-constraint-in-z3py
        selection_list = list(self.selection_dict.values())
        self.selection_assertion = problem_function[kind]([(selected, True) for selected in selection_list],
                                                          nb_workers)
