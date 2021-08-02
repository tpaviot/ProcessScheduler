"""Solver definition and related classes/functions."""

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

import random
import time
from typing import Optional, Union
import uuid
import warnings

from z3 import (
    ArithRef,
    Array,
    Int,
    IntSort,
    Or,
    Solver,
    SolverFor,
    Store,
    Sum,
    unsat,
    unknown,
    set_option,
)

from processscheduler.objective import MaximizeObjective, MinimizeObjective, Indicator
from processscheduler.solution import (
    SchedulingSolution,
    TaskSolution,
    ResourceSolution,
    BufferSolution,
)
from processscheduler.util import calc_parabola_from_two_points, sort_no_duplicates

#
# Solver class definition
#
class SchedulingSolver:
    """A solver class"""

    def __init__(
        self,
        problem,
        debug: Optional[bool] = False,
        max_time: Optional[int] = 10,
        parallel: Optional[bool] = False,
        random_values: Optional[bool] = False,
        logics: Optional[str] = None,
        verbosity: Optional[int] = 0,
    ):
        """Scheduling Solver

        debug: True or False, False by default
        max_time: time in seconds, 60 by default
        parallel: True to enable mutlthreading, False by default
        """
        self.problem = problem
        self.problem_context = problem.context
        self.debug = debug
        # objectives list
        self.objective = None  # the list of all objectives defined in this problem
        self.current_solution = None  # no solution until the problem is solved

        # set_option('smt.arith.auto_config_simplex', True)
        if debug:
            set_option("verbose", 2)
        else:
            set_option("verbose", verbosity)

        if random_values:
            set_option("sat.random_seed", random.randint(1, 1e3))
            set_option("smt.random_seed", random.randint(1, 1e3))
            set_option("smt.arith.random_initial_value", True)
        else:
            set_option("sat.random_seed", 0)
            set_option("smt.random_seed", 0)
            set_option("smt.arith.random_initial_value", False)

        # set timeout
        self.max_time = max_time  # in seconds
        set_option("timeout", int(self.max_time * 1000))  # in milliseconds

        # create the solver
        print("Solver type:\n===========")

        # check if the problem is an optimization problem
        self.is_not_optimization_problem = len(self.problem_context.objectives) == 0
        self.is_optimization_problem = len(self.problem_context.objectives) > 0
        self.is_multi_objective_optimization_problem = (
            len(self.problem_context.objectives) > 1
        )
        # the Optimize() solver is used only in the case of a mutli-optimization
        # problem. This enables to choose the priority method.
        # in the case of a single objective optimization, the Optimize() solver
        # apperas to be less robust than the basic Solver(). The
        # incremental solver is then used.

        # see this url for a documentation about logics
        # http://smtlib.cs.uiowa.edu/logics.shtml
        if logics is None:
            self._solver = Solver()
            print("\t-> Standard SAT/SMT solver")
        else:
            self._solver = SolverFor(logics)
            print("\t-> SMT solver using logics", logics)
        if debug:
            set_option(unsat_core=True)

        if parallel:
            set_option("parallel.enable", True)  # enable parallel computation

        # add all tasks assertions to the solver
        for task in self.problem_context.tasks:
            self.add_constraint(task.get_assertions())
            self.add_constraint(task.end <= self.problem.horizon)

        # then process tasks constraints
        for constraint in self.problem_context.constraints:
            self.add_constraint(constraint)

        # process resources requirements
        for ress in self.problem_context.resources:
            self.add_constraint(ress.get_assertions())

        # process resource intervals
        for ress in self.problem_context.resources:
            busy_intervals = ress.get_busy_intervals()
            nb_intervals = len(busy_intervals)
            for i in range(nb_intervals):
                start_task_i, end_task_i = busy_intervals[i]
                for k in range(i + 1, nb_intervals):
                    start_task_k, end_task_k = busy_intervals[k]
                    self.add_constraint(
                        Or(start_task_k >= end_task_i, start_task_i >= end_task_k)
                    )

        # process indicators
        for indic in self.problem_context.indicators:
            self.add_constraint(indic.get_assertions())

        # work amounts
        # for each task, compute the total work for all required resources"""
        for task in self.problem_context.tasks:
            if task.work_amount > 0.0:
                work_total_for_all_resources = []
                for required_resource in task.required_resources:
                    # work contribution for the resource
                    interv_low, interv_up = required_resource.busy_intervals[task]
                    work_contribution = required_resource.productivity * (
                        interv_up - interv_low
                    )
                    work_total_for_all_resources.append(work_contribution)
                self.add_constraint(
                    Sum(work_total_for_all_resources) >= task.work_amount
                )

        # process buffers
        for buffer in self.problem_context.buffers:
            #
            # create an array that stores the mapping between start times and
            # quantities. For example, if a start T1 starts at 2 and consumes
            # 8, and T3 ends at 6 and consumes 5 then the mapping array
            # will look like : A[2]=8 and A[6]=-5
            # SO far, no way to have the same start time at different inst
            buffer_mapping = Array(
                "Buffer_%s_mapping" % buffer.name, IntSort(), IntSort()
            )
            for t in buffer.unloading_tasks:
                self.add_constraint(
                    buffer_mapping
                    == Store(buffer_mapping, t.start, -buffer.unloading_tasks[t])
                )
            for t in buffer.loading_tasks:
                self.add_constraint(
                    buffer_mapping
                    == Store(buffer_mapping, t.end, +buffer.loading_tasks[t])
                )
            # sort consume/feed times in asc order
            tasks_start_unload = [t.start for t in buffer.unloading_tasks]
            tasks_end_load = [t.end for t in buffer.loading_tasks]

            sorted_times, sort_assertions = sort_no_duplicates(
                tasks_start_unload + tasks_end_load
            )
            self.add_constraint(sort_assertions)
            # create as many buffer state changes as sorted_times
            buffer.state_changes_time = [
                Int("%s_sc_time_%i" % (buffer.name, k))
                for k in range(len(sorted_times))
            ]

            # add the constraints that give the buffer state change times
            for st, bfst in zip(sorted_times, buffer.state_changes_time):
                self.add_constraint(st == bfst)

            # compute the different buffer states according to state changes
            buffer.buffer_states = [
                Int("%s_state_%i" % (buffer.name, k))
                for k in range(len(buffer.state_changes_time) + 1)
            ]
            # add constraints for buffer states
            # the first buffer state is equal to the buffer initial level
            if buffer.initial_state is not None:
                self.add_constraint(buffer.buffer_states[0] == buffer.initial_state)
            if buffer.final_state is not None:
                self.add_constraint(buffer.buffer_states[-1] == buffer.final_state)
            if buffer.lower_bound is not None:
                for st in buffer.buffer_states:
                    self.add_constraint(st >= buffer.lower_bound)
            if buffer.upper_bound is not None:
                for st in buffer.buffer_states:
                    self.add_constraint(st <= buffer.upper_bound)
            # and, for the other, the buffer state i+1 is the buffer state i +/- the buffer change
            for i in range(len(buffer.buffer_states) - 1):
                self.add_constraint(
                    buffer.buffer_states[i + 1]
                    == buffer.buffer_states[i]
                    + buffer_mapping[buffer.state_changes_time[i]]
                )

        # optimization
        if self.is_optimization_problem:
            self.create_objective()

    def add_constraint(self, cstr) -> bool:
        # set the method to use to add constraints
        # in debug mode this is assert_and_track, to be able to trace
        # unsat core, in regular mode this is the add function
        if self.debug:
            if isinstance(cstr, list):
                for c in cstr:
                    self._solver.assert_and_track(c, "asst_%s" % uuid.uuid4().hex[:8])
            else:
                self._solver.assert_and_track(cstr, "asst_%s" % uuid.uuid4().hex[:8])
        else:
            self._solver.add(cstr)

    def create_objective(self) -> bool:
        """create optimization objectives"""
        # in case of a single value to optimize
        if self.is_multi_objective_optimization_problem:
            # Replace objectives O_i, O_j, O_k with
            # O = WiOi+WjOj+WkOk etc.
            equivalent_single_objective = Int("EquivalentSingleObjective")
            weighted_objectives = []
            for obj in self.problem_context.objectives:
                variable_to_optimize = obj.target
                weight = obj.weight
                if isinstance(obj, MaximizeObjective):
                    weighted_objectives.append(-weight * variable_to_optimize)
                else:
                    weighted_objectives.append(weight * variable_to_optimize)
            self.add_constraint(equivalent_single_objective == Sum(weighted_objectives))
            # create an indicator
            equivalent_indicator = Indicator(
                "EquivalentIndicator", equivalent_single_objective
            )
            self.objective = MinimizeObjective(
                "EquivalentObjective", equivalent_indicator
            )
            self.add_constraint(equivalent_indicator.get_assertions())
        else:
            self.objective = self.problem.context.objectives[0]

    def check_sat(self):
        """check satisfiability. Returns resulta as True (sat) or False (unsat, unknown).
        The computation time.
        """
        init_time = time.perf_counter()
        sat_result = self._solver.check()
        check_sat_time = time.perf_counter() - init_time

        if sat_result == unsat:
            print(
                "\tNo solution can be found for problem %s.\n\tReason: Unsatisfiable problem: no solution exists"
                % self.problem.name
            )

        if sat_result == unknown:
            reason = self._solver.reason_unknown()
            print(
                "\tNo solution can be found for problem %s.\n\tReason: %s"
                % (self.problem.name, reason)
            )

        return sat_result, check_sat_time

    def build_solution(self, z3_sol):
        """create and return a SchedulingSolution instance"""
        solution = SchedulingSolution(self.problem)

        # set the horizon solution
        solution.horizon = z3_sol[self.problem.horizon].as_long()

        # process tasks
        for task in self.problem.context.tasks:
            # for each task, create a TaskSolution instance
            new_task_solution = TaskSolution(task.name)
            new_task_solution.type = type(task).__name__
            new_task_solution.start = z3_sol[task.start].as_long()
            new_task_solution.end = z3_sol[task.end].as_long()
            new_task_solution.duration = z3_sol[task.duration].as_long()
            new_task_solution.optional = task.optional

            # times, if ever delta_time and start_time are defined
            if self.problem.delta_time is not None:
                new_task_solution.duration_time = (
                    new_task_solution.duration * self.problem.delta_time
                )
                if self.problem.start_time is not None:
                    new_task_solution.start_time = (
                        self.problem.start_time
                        + new_task_solution.start * self.problem.delta_time
                    )
                else:
                    new_task_solution.start_time = (
                        new_task_solution.start * self.problem.delta_time
                    )
                new_task_solution.end_time = (
                    new_task_solution.start_time + new_task_solution.duration_time
                )
            if task.optional:
                # ugly hack, necessary because there's no as_bool()
                # method for Bool objects
                new_task_solution.scheduled = "%s" % z3_sol[task.scheduled] == "True"
            else:
                new_task_solution.scheduled = True

            # process resource assignments
            for req_res in task.required_resources:
                # among those workers, some of them
                # are busy "in the past", that is to say they
                # should not be assigned to the related task
                # for each interval
                lower_bound, _ = req_res.busy_intervals[task]
                resource_is_assigned = z3_sol[lower_bound].as_long() >= 0
                # add this resource to assigned resources, anytime
                if resource_is_assigned and (
                    req_res.name not in new_task_solution.assigned_resources
                ):
                    # if it is a cumulative resource, then we transform the resource name
                    resource_name = req_res.name.split("_CumulativeWorker_")[0]
                    if resource_name not in new_task_solution.assigned_resources:
                        new_task_solution.assigned_resources.append(resource_name)

            solution.add_task_solution(new_task_solution)

        # process resources
        for resource in self.problem.context.resources:
            # for each task, create a TaskSolution instance
            # for cumulative workers, we append the current work
            if "_CumulativeWorker_" in resource.name:
                cumulative_worker_name = resource.name.split("_CumulativeWorker_")[0]
                if cumulative_worker_name not in solution.resources:
                    new_resource_solution = ResourceSolution(cumulative_worker_name)
                else:
                    new_resource_solution = solution.resources[cumulative_worker_name]
            else:
                new_resource_solution = ResourceSolution(resource.name)
            new_resource_solution.type = type(resource).__name__
            # check for task processed by this resource
            for task in resource.busy_intervals.keys():
                task_name = task.name
                st_var, end_var = resource.busy_intervals[task]
                start = z3_sol[st_var].as_long()
                end = z3_sol[end_var].as_long()
                if (
                    start >= 0
                    and end >= 0
                    and (task_name, start, end) not in new_resource_solution.assignments
                ):
                    new_resource_solution.assignments.append((task_name, start, end))

            if "_CumulativeWorker_" in resource.name:
                cumulative_worker_name = resource.name.split("_CumulativeWorker_")[0]
                if cumulative_worker_name not in solution.resources:
                    solution.add_resource_solution(new_resource_solution)
            else:
                solution.add_resource_solution(new_resource_solution)

        # process buffers
        for buffer in self.problem.context.buffers:
            buffer_name = buffer.name
            new_buffer_solution = BufferSolution(buffer_name)
            # change_state_times
            cst_lst = [
                z3_sol[sct_z3_var].as_long() for sct_z3_var in buffer.state_changes_time
            ]

            new_buffer_solution.state_change_times = cst_lst
            # state values
            sv_lst = [z3_sol[sv_z3_var].as_long() for sv_z3_var in buffer.buffer_states]
            new_buffer_solution.state = sv_lst

            solution.add_buffer_solution(new_buffer_solution)
        # process indicators
        for indicator in self.problem.context.indicators:
            indicator_name = indicator.name
            indicator_value = z3_sol[indicator.indicator_variable].as_long()
            solution.add_indicator_solution(indicator_name, indicator_value)

        return solution

    def solve(self) -> Union[bool, SchedulingSolution]:
        """call the solver and returns the solution, if ever"""
        # for all cases
        if self.debug:
            self.print_assertions()

        if self.is_optimization_problem:
            if self.is_multi_objective_optimization_problem:
                print("\tObjectives:\n\t======")
                for obj in self.problem.context.objectives:
                    print("\t%s" % obj)
            # in this case, use the incremental solver
            if isinstance(self.objective, MinimizeObjective):
                dd = "min"
            elif isinstance(self.objective, MaximizeObjective):
                dd = "max"
            # print(dir(objective))
            # print(objective.target)
            solution = self.solve_optimize_incremental(self.objective.target, kind=dd)
            if not solution:
                return False
        else:
            # first check satisfiability
            sat_result, sat_computation_time = self.check_sat()

            print("Total computation time:\n=====================")
            print(
                "\t%s satisfiability checked in %.2fs"
                % (self.problem.name, sat_computation_time)
            )

            if sat_result == unsat:
                if self.debug:
                    unsat_core = self._solver.unsat_core()
                    print(
                        "\t%i unsatisfied assertion(s) (probable conflict):"
                        % len(unsat_core)
                    )
                    for c in unsat_core:
                        print("\t->%s" % c)
                return False

            if sat_result == unknown:
                return False

            # then get the solution
            solution = self._solver.model()

        self.current_solution = solution
        sol = self.build_solution(solution)

        if self.debug:
            self.print_statistics()
            self.print_solution()

        return sol

    def solve_optimize_incremental(
        self,
        variable: ArithRef,
        max_recursion_depth: Optional[int] = None,
        kind: Optional[str] = "min",
    ) -> int:
        """target a min or max for a variable, without the Optimize solver.
        The loop continues ever and ever until the next value is more than 90%"""
        if kind not in ["min", "max"]:
            raise ValueError("choose either 'min' or 'max'")
        depth = 0
        solution = False
        total_time = 0
        current_variable_value = None
        print("Incremental optimizer:\n======================")
        three_last_times = []

        if self.objective.bounds is None:
            bound = None
        else:
            bound = (
                self.objective.bounds[0] if kind == "min" else self.objective.bounds[1]
            )

        while True:  # infinite loop, break if unsat of max_depth
            depth += 1
            if max_recursion_depth is not None and depth > max_recursion_depth:
                warnings.warn(
                    "maximum recursion depth exceeded. There might be a better solution."
                )
                break

            is_sat, sat_computation_time = self.check_sat()

            if is_sat == unsat and current_variable_value is not None:
                print(
                    "\tFound optimum %i. Stopping iteration." % current_variable_value
                )
                break
            elif is_sat == unsat:
                print("\tNo solution found. Stopping iteration.")
                break
            elif is_sat == unknown:
                break
            # at this stage, is_sat should be sat
            solution = self._solver.model()

            current_variable_value = solution[variable].as_long()
            print(
                "\tFound value:",
                current_variable_value,
                "elapsed time:%.3fs" % total_time,
            )
            total_time += sat_computation_time
            if total_time > self.max_time:
                warnings.warn("max time exceeded")
                break

            if bound is not None and current_variable_value == bound:
                print(
                    "\tFound optimum %i. Stopping iteration." % current_variable_value
                )
                break

            # prevent the solver to start a new round if we expect it to be
            # very long. The idea is the following: store the laste 3 computation
            # times, compute and extrapolation. Break the loop if ever the expected
            # time is too important.
            if len(three_last_times) < 3:
                three_last_times.append(total_time)
            else:
                three_last_times.pop(0)
                three_last_times.append(total_time)
                # Compute the expected value
                a, b, c = calc_parabola_from_two_points([0, 1, 2], three_last_times)
                expected_next_time = a * 9 + 3 * b + c
                if expected_next_time > self.max_time:
                    warnings.warn("time may exceed max time. Stopping iteration.")
                    break
            self._solver.push()
            if kind == "min":
                self.add_constraint(variable < current_variable_value)
                print("\tChecking better value <%s" % current_variable_value)
            else:
                self.add_constraint(variable > current_variable_value)
                print("\tChecking better value >%s" % current_variable_value)

        print("\ttotal number of iterations: %i" % depth)
        if current_variable_value is not None:
            print("\tvalue: %i" % current_variable_value)
        print("\t%s satisfiability checked in %.2fs" % (self.problem.name, total_time))

        return solution

    def print_assertions(self):
        """A utility method to display solver assertions"""
        print("Assertions:\n===========")
        for assertion in self._solver.assertions():
            print("\t->", assertion)

    def print_statistics(self):
        """A utility method that displays solver statistics"""
        print("Solver satistics:")
        for key, value in self._solver.statistics():
            print("\t%s: %s" % (key, value))

    def print_solution(self):
        """A utility method that displays all internal variables for the current solution"""
        print("Solution:")
        for decl in self.current_solution.decls():
            var_name = decl.name()
            var_value = self.current_solution[decl]
            print("\t-> %s=%s" % (var_name, var_value))

    def find_another_solution(self, variable: ArithRef) -> bool:
        """let the solver find another solution for the variable"""
        if self.current_solution is None:
            warnings.warn("No current solution. First call the solve() method.")
            return False
        current_variable_value = self.current_solution[variable].as_long()
        self.add_constraint(variable != current_variable_value)
        return self.solve()

    def export_to_smt2(self, smt_filename: str):
        """export the model to a smt file to be processed by another SMT solver"""
        with open(smt_filename, "w") as outfile:
            outfile.write(self._solver.to_smt2())
