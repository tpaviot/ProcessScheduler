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
def save_json(scheduling_problem, scheduling_solver, json_filename):
    pass

#
# Load a Problem/Solver from a json file
#
def load_json(json_filename):
    pass
