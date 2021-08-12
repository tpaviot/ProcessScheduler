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
    problem_properties = {
        "name": scheduling_problem.name,
        "horizon": scheduling_problem.horizon_defined_value,
        "delta_time": scheduling_problem.delta_time,
        "start_time": scheduling_problem.start_time,
        "end_time": scheduling_problem.end_time,
    }

    d["ProblemParameters"] = problem_properties
    # Tasks
    tasks = {}
    for task in scheduling_problem.context.tasks:
        new_task_entry = {"type": type(task).__name__, "optional": task.optional}
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
        if "CumulativeWorker_" not in res.name
    ]

    for resource in all_workers_but_cumulative:  # Worker
        new_resource_entry = {
            "productivity": resource.productivity,
            "cost": resource.cost,
        }

        workers[resource.name] = new_resource_entry
    resources["Workers"] = workers
    # SelectWorkers
    select_workers = []
    for sw in scheduling_problem.context.select_workers:  # Worker
        new_sw = {
            "list_of_workers": [w.name for w in sw.list_of_workers],
            "nb_workers_to_select": sw.nb_workers_to_select,
            "kind": sw.kind,
        }

        select_workers.append(new_sw)
    resources["SelectWorkers"] = select_workers
    # CumulativeWorker
    cumulative_workers = {}
    for cw in scheduling_problem.context.cumulative_workers:  # Worker
        new_cw = {"size": cw.size, "productivity": cw.productivity, "cost": cw.cost}
        cumulative_workers[cw.name] = new_cw
    resources["CumulativeWorkers"] = cumulative_workers
    d["Resources"] = resources
    #
    # Buffers
    #
    buffers = {}
    for buffer in scheduling_problem.context.buffers:
        new_bffr = {
            'initial_state': buffer.initial_state,
            'final_state': buffer.final_state,
            'lower_bound': buffer.lower_bound,
            'upper_bound': buffer.upper_bound,
        }

        buffers[buffer.name] = new_bffr
    d["Buffers"] = buffers

    #
    # Constraints
    #
    task_constraints = []
    resource_constraints = {}

    workloads = []
    resource_unavailables = []
    resource_task_distances = []

    for constraint in scheduling_problem.context.constraints:
        new_cstr = {'type': type(constraint).__name__, 'optional': constraint.optional}
        # TaskConstraint
        if isinstance(constraint, ps.TaskConstraint):
            task_constraints.append(new_cstr)
        elif isinstance(constraint, ps.ResourceConstraint):
            # WorkLoad
            if isinstance(constraint, ps.WorkLoad):
                # expand the dictionary because json cannot
                # use tuple as keys.
                dd = []
                new_dict_entry = {'kind': constraint.kind}
                for k, v in constraint.dict_time_intervals_and_bound.items():

                    new_dict_entry["time_interval_lower_bound"] = k[0]
                    new_dict_entry["time_interval_upper_bound"] = k[1]
                    new_dict_entry["number_of_time_slots"] = v
                    dd.append(new_dict_entry)
                workloads.append(dd)
            elif isinstance(constraint, ps.ResourceUnavailable):
                dd = {
                    'list_of_time_intervals': constraint.list_of_time_intervals,
                    'resource': constraint.resource.name,
                }

                new_cstr["ResourceUnavailable"] = dd
                resource_unavailables.append(dd)
            elif isinstance(constraint, ps.ResourceTasksDistance):
                tt = {}
                resource_task_distances.append(tt)
    resource_constraints["WorkLoad"] = workloads
    resource_constraints["ResourceUnavailable"] = resource_unavailables
    resource_constraints["ResourceTasksDistance"] = resource_task_distances
    d["TaskConstraints"] = task_constraints
    d["ResourceConstraints"] = resource_constraints

    return json.dumps(d, indent=4, sort_keys=True)


#
# Load a Problem/Solver from a json file
#
def import_json(json_filename):
    pass
