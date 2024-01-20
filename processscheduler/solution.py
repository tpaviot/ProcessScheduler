"""Solution definition and Gantt export."""

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

from datetime import timedelta, datetime
from typing import List, Tuple, Dict

from pydantic import Field

from processscheduler.base import BaseModelWithJson
from processscheduler.problem import SchedulingProblem
from processscheduler.excel_io import export_solution_to_excel_file

try:
    from pandas import DataFrame as df

    HAVE_PANDAS = True
except ImportError:
    HAVE_PANDAS = False


class TaskSolution(BaseModelWithJson):
    """Class to represent the solution for a scheduled Task."""

    name: str
    type: str = Field(default="")
    start: int = Field(default=0)
    end: int = Field(default=0)
    duration: int = Field(default=0)

    release_date: int = Field(default=None)
    due_date: int = Field(default=None)
    due_date_is_deadline: bool = Field(default=False)

    start_time: datetime = Field(default=None)
    end_time: datetime = Field(default=None)
    duration_time: timedelta = Field(default=None)

    optional: bool = Field(default=False)
    scheduled: bool = Field(default=False)

    work_amount: int = Field(default=0)
    priority: int = Field(default=None)

    # the name of assigned resources
    assigned_resources: List[str] = Field(default=[])


class ResourceSolution(BaseModelWithJson):
    """Class to represent the solution for the resource assignments."""

    name: str
    type: str = Field(default="")
    # an assignment is a list of tuples : [(Task_name, start, end), (task_2name, start2, end2) etc.]
    assignments: List[Tuple[str, int, int]] = Field(default=[])


class BufferSolution(BaseModelWithJson):
    """Class to represent the solution for a Buffer."""

    name: str
    # a collection of instants where the buffer state changes
    state_change_times: List[int] = Field(default=[])
    # a collection that represents the buffer state along the
    # whole schedule. Represented a integer values
    state: List[int] = Field(default=[])


class SchedulingSolution(BaseModelWithJson):
    """A class that represent the solution of a scheduling problem. Can be rendered
    to a matplotlib Gantt chart, or exported to json
    """

    problem: SchedulingProblem
    horizon: int = Field(default=0)
    tasks: Dict[str, TaskSolution] = Field(default={})
    resources: Dict[str, ResourceSolution] = Field(default={})
    buffers: Dict[str, BufferSolution] = Field(default={})
    indicators: Dict[str, int] = Field(default={})

    def __str__(self):
        """by default, return a panda dataframe, if panda available"""
        if HAVE_PANDAS:
            return str(self.to_df())
        else:
            return repr(self)

    def get_scheduled_tasks(self):
        return {
            task: self.tasks[task] for task in self.tasks if self.tasks[task].scheduled
        }

    def add_indicator_solution(self, indicator_name: str, indicator_value: int) -> None:
        """Add indicator solution."""
        self.indicators[indicator_name] = indicator_value

    def add_task_solution(self, task_solution: TaskSolution) -> None:
        """Add task solution."""
        self.tasks[task_solution.name] = task_solution

    def add_resource_solution(self, resource_solution: ResourceSolution) -> None:
        """Add resource solution."""
        self.resources[resource_solution.name] = resource_solution

    def add_buffer_solution(self, buffer_solution: BufferSolution) -> None:
        self.buffers[buffer_solution.name] = buffer_solution

    #
    # File export
    #
    def to_excel_file(self, excel_filename, colors=False):
        return export_solution_to_excel_file(self, excel_filename, colors)

    def to_df(self):
        """create and return a pandas dataframe representing"""
        if not HAVE_PANDAS:
            raise AssertionError("pandas is not installed")
        names = []
        starts = []
        ends = []
        durations = []
        resources = []
        scheduleds = []
        tardies = []
        for task_name in self.tasks:
            t = self.tasks[task_name]
            names.append(task_name)
            starts.append(t.start)
            ends.append(t.end)
            durations.append(t.duration)
            resources.append(t.assigned_resources)
            scheduleds.append(t.scheduled)
            # check tardies
            tardies.append(t.start - t.due_date if t.due_date is not None else False)

        tasks_df = df(
            {
                "Task name": names,
                "Allocated Resources": resources,
                "Start": starts,
                "End": ends,
                "Duration": durations,
                "Scheduled": scheduleds,
                "Tardy": tardies,
            }
        )
        return tasks_df
