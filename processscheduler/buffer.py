"""The buffers definition."""

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

from typing import Optional

from processscheduler.base import NamedUIDObject

# import processscheduler.context as ps_context
import processscheduler.base

from pydantic import Field


class Buffer(NamedUIDObject):
    initial_state: int = Field(default=None)
    final_state: int = Field(default=None)
    lower_bound: int = Field(default=None)
    upper_bound: int = Field(default=None)

    def __init__(self, **data) -> None:
        super().__init__(**data)
        # a dict that contains all tasks that consume this buffer
        # unloading tasks contribute to decrement the buffer state
        self._unloading_tasks = {}
        # a dict that contains all tasks that feed this buffer
        # loading tasks contribute to increment the buffer state
        self._loading_tasks = {}
        # a list that contains the instants where the buffer state changes
        self._state_changes_time = []
        # a list that stores the buffer state between each state change
        # the first item of this list is always the initial state
        self._buffer_states = []

        # add this task to the current context
        if processscheduler.base.active_problem is None:
            raise AssertionError(
                "No context available. First create a SchedulingProblem"
            )
        processscheduler.base.active_problem.add_buffer(self)

    def add_unloading_task(self, task, quantity) -> None:
        self._unloading_tasks[task] = quantity

    def add_loading_task(self, task, quantity) -> None:
        self._loading_tasks[task] = quantity


class NonConcurrentBuffer(Buffer):
    """A buffer that cannot be accessed by different tasks at the same time"""
