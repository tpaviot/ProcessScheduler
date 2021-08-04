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

from processscheduler.base import _NamedUIDObject
import processscheduler.context as ps_context

#
# Buffer class definition
#
class NonConcurrentBuffer(_NamedUIDObject):
    """A buffer that cannot be accessed by different tasks at the same time"""

    def __init__(
        self,
        name: str,
        initial_state: Optional[int] = None,
        final_state: Optional[int] = None,
        lower_bound: Optional[int] = None,
        upper_bound: Optional[int] = None,
    ) -> None:
        super().__init__(name)
        # for each resource, we define a dict that stores
        # all tasks and busy intervals of the resource.
        # busy intervals can be for example [(1,3), (5, 7)]
        self.initial_state = initial_state
        self.final_state = final_state
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        # a dict that contains all tasks that consume this buffer
        # unloading tasks contribute to decrement the buffer state
        self.unloading_tasks = {}
        # a dict that contains all tasks that feed this buffer
        # loading tasks contribute to increment the buffer state
        self.loading_tasks = {}
        # a list that contains the instants where the buffer state changes
        self.state_changes_time = []
        # a list that contains the buffer state between each state change
        # the first item of this is always the initial state
        self.buffer_states = []

        # add this task to the current context
        if ps_context.main_context is None:
            raise AssertionError(
                "No context available. First create a SchedulingProblem"
            )
        ps_context.main_context.add_buffer(self)

    def add_unloading_task(self, task, quantity) -> None:
        self.unloading_tasks[task] = quantity

    def add_loading_task(self, task, quantity) -> None:
        self.loading_tasks[task] = quantity
