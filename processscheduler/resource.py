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

from typing import List, Optional, Tuple

from z3 import ArithRef, Bool, PbLe

from processscheduler.base import _NamedUIDObject, is_positive_integer

#
# Resources class definition
#
class _Resource(_NamedUIDObject):
    """ base class for the representation of a resource """
    def __init__(self, name: str):
        super().__init__(name)

        # for each resource, we define a list that contains periods for which
        # the resource is busy, for instance busy_intervals can be [(1,3), (5, 7)]
        self.busy_intervals = [] # type: List[Tuple[ArithRef, ArithRef]]

    def add_busy_interval(self, interval: Tuple[ArithRef, ArithRef]):
        """ add an interval in which the resource is busy """
        # an interval is considered as a tuple (begin, end)
        self.busy_intervals.append(interval)

class Worker(_Resource):
    """ A worker is an atomic resource that cannot be split into smaller parts.
    Typical workers are human beings, machines etc. """
    def __init__(self, name: str, productivity: Optional[int] = 0) -> None:
        super().__init__(name)
        if not is_positive_integer(productivity):
            raise TypeError('productivity must be an integer >= 0')
        self.productivity = productivity

    # Necessary to define _eq__ and __hash__ because of lgtm warnings of kind
    def __hash__(self) -> int:
        return self.uid

    def __eq__(self, other) -> Bool:
        return self.uid == other.uid


class AlternativeWorkers(_Resource):
    """ Class representing the selection of n workers chosen among a list
    of possible workers """
    def __init__(self, list_of_workers: List[_Resource], number_of_workers: Optional[int] = 1):
        """ create an instance of the AlternativeWorkers class. """
        super().__init__('')
        self.list_of_workers = list_of_workers
        self.number_of_workers = number_of_workers

        # a dict that maps workers and selected boolean
        self.selection_dict = {}

        # create as many booleans as resources in the list
        selection_list = []
        for wrkr in list_of_workers:
            worker_is_selected = Bool('Selected_%i_%s' % (self.uid, wrkr.name))
            selection_list.append(worker_is_selected)
            self.selection_dict[wrkr] = worker_is_selected

        # create the assertion : exactly n boolean flags are allowed to be True,
        # the others must be False
        # see https://github.com/Z3Prover/z3/issues/694
        # and https://stackoverflow.com/questions/43081929/k-out-of-n-constraint-in-z3py
        self.selection_assertion = PbLe([(boolean, True) for boolean in selection_list],
                                        number_of_workers)
