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

from datetime import time, timedelta, datetime
import json

import processscheduler as ps

#
# Solution Export to JSON
#
class SolutionJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, time, timedelta)):
            return "%s" % obj
        return obj.__dict__


def solution_to_json_string(solution):
    """Export the solution to a json string."""
    d = {}
    # problem properties
    problem_properties = {}
    d["horizon"] = solution.horizon
    # time data
    problem_properties["problem_timedelta"] = solution.problem.delta_time
    if solution.problem.delta_time is None:
        problem_properties["problem_start_time"] = None
        problem_properties["problem_end_time"] = None
    elif solution.problem.start_time is not None:
        problem_properties["problem_start_time"] = solution.problem.start_time
        problem_properties["problem_end_time"] = (
            solution.problem.start_time + solution.horizon * solution.problem.delta_time
        )
    else:
        problem_properties["problem_start_time"] = time(0)
        problem_properties["problem_end_time"] = (
            solution.horizon * solution.problem.delta_time
        )
    d["problem_properties"] = problem_properties

    d["tasks"] = solution.tasks
    d["resources"] = solution.resources
    d["buffers"] = solution.buffers
    d["indicators"] = solution.indicators
    return json.dumps(d, indent=4, sort_keys=True, cls=SolutionJSONEncoder)


#
# Problem and Solver export to json
#
def export_json_to_file(scheduling_problem, scheduling_solver, json_filename):
    json_string = export_json_to_string(scheduling_problem, scheduling_solver)
    with open(json_filename, "w") as outfile:
        outfile.write(json_string)


def export_json_to_string(scheduling_problem, scheduling_solver) -> str:
    d = {}
    # SchedulingProblem general properties
    problem_properties = {}
    problem_properties["name"] = scheduling_problem.name
    problem_properties["horizon"] = scheduling_problem.horizon_defined_value
    problem_properties["delta_time"] = scheduling_problem.delta_time
    problem_properties["start_time"] = scheduling_problem.start_time
    problem_properties["end_time"] = scheduling_problem.end_time
    d["ProblemParameters"] = problem_properties
    # Tasks
    tasks = {}
    for task in scheduling_problem.context.tasks:
        new_task_entry = {}
        new_task_entry["type"] = type(task).__name__
        new_task_entry["optional"] = task.optional
        if isinstance(task, ps.FixedDurationTask):
            new_task_entry["duration"] = task.duration_defined_value
        if isinstance(task, (ps.FixedDurationTask, ps.VariableDurationTask)):
            new_task_entry["work_amount"] = task.work_amount
            new_task_entry["priority"] = task.priority
        if isinstance(task, ps.VariableDurationTask):
            new_task_entry["min_duration"] = task.min_duration
            new_task_entry["max_duration"] = task.max_duration
        tasks[task.name] = new_task_entry
    d["Tasks"] = tasks
    # Resources
    resources = {}
    # Workers
    workers = {}
    # we dont export workers created by cumulative resource
    all_workers_but_cumulative = [
        res
        for res in scheduling_problem.context.resources
        if not "CumulativeWorker_" in res.name
    ]
    for resource in all_workers_but_cumulative:  # Worker
        new_resource_entry = {}
        new_resource_entry["productivity"] = resource.productivity
        new_resource_entry["cost"] = resource.cost
        workers[resource.name] = new_resource_entry
    resources["Workers"] = workers
    # SelectWorkers
    select_workers = []
    for sw in scheduling_problem.context.select_workers:  # Worker
        new_sw = {}
        new_sw["list_of_workers"] = [w.name for w in sw.list_of_workers]
        new_sw["nb_workers_to_select"] = sw.nb_workers_to_select
        new_sw["kind"] = sw.kind
        select_workers.append(new_sw)
    resources["SelectWorkers"] = select_workers
    # CumulativeWorker
    cumulative_workers = {}
    for cw in scheduling_problem.context.cumulative_workers:  # Worker
        new_cw = {}
        new_cw["size"] = cw.size
        new_cw["productivity"] = cw.productivity
        new_cw["cost"] = cw.cost
        cumulative_workers[cw.name] = new_cw
    resources["CumulativeWorkers"] = cumulative_workers
    d["Resources"] = resources
    #
    # Constraints
    #
    constraints = []
    for constraint in scheduling_problem.context.constraints:
        new_cstr = {}
        new_cstr["type"] = type(constraint).__name__
        constraints.append(new_cstr)
    d["Constraints"] = constraints

    return json.dumps(d, indent=4, sort_keys=True)


#
# Load a Problem/Solver from a json file
#
def import_json(json_filename):
    pass
