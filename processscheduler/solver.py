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

from typing import Literal

import z3

from pydantic import Field, PositiveFloat, Extra, ConfigDict

from processscheduler.base import BaseModelWithJson
from processscheduler.indicator import Indicator, IndicatorFromMathExpression
from processscheduler.objective import Objective
from processscheduler.solution import (
    SchedulingSolution,
    TaskSolution,
    ResourceSolution,
    BufferSolution,
)
from processscheduler.buffer import NonConcurrentBuffer, ConcurrentBuffer
from processscheduler.problem import SchedulingProblem

from processscheduler.util import (
    calc_parabola_from_three_points,
    sort_no_duplicates,
    sort_duplicates,
    clean_buffer_states,
)


#
# Solver class definition
#
class SchedulingSolver(BaseModelWithJson):
    """A solver class"""

    model_config = ConfigDict(extra="forbid")

    problem: SchedulingProblem
    debug: bool = Field(default=False)
    max_time: PositiveFloat = Field(default=10)
    parallel: bool = Field(default=False)
    random_values: bool = Field(default=False)
    logics: Literal[
        "QF_LRA",
        "HORN",
        "QF_LIA",
        "QF_RDL",
        "QF_IDL",
        "QF_AUFLIA",
        "QF_ALIA",
        "QF_AUFLIRA",
        "QF_AUFNIA",
        "QF_AUFNIRA",
        "QF_ANIA",
        "QF_LIRA",
        "QF_UFLIA",
        "QF_UFLRA",
        "QF_UFIDL",
        "QF_UFRDL",
        "QF_NIRA",
        "QF_UFNRA",
        "QF_UFNIA",
        "QF_UFNIRA",
        "QF_S",
        "QF_SLIA",
        "UFIDL",
        "HORN",
        "QF_FPLRA",
    ] = Field(default=None)
    verbosity: int = Field(default=0)
    optimizer: Literal["incremental", "optimize"] = Field(default="incremental")
    optimize_priority: Literal["pareto", "lex", "box", "weight"] = Field(
        default="pareto"
    )

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self._objective = None  # the list of all objectives defined in this problem
        self._current_solution = None  # no solution until the problem is solved
        self._map_boolrefs_to_geometric_constraints = {}
        self._initialized = False

        if self.debug:
            z3.set_option("verbose", 2)
            z3.set_option(unsat_core=True)
        else:
            z3.set_option("verbose", self.verbosity)
            z3.set_option(unsat_core=False)

        z3.set_option("parallel.enable", self.parallel)
        if self.random_values:
            z3.set_option("sat.random_seed", random.randint(1, 1000))
            z3.set_option("smt.random_seed", random.randint(1, 1000))
            z3.set_option("smt.arith.random_initial_value", True)
        else:
            z3.set_option("sat.random_seed", 0)
            z3.set_option("smt.random_seed", 0)
            z3.set_option("smt.arith.random_initial_value", False)

        # set timeout
        if self.max_time != "inf":
            z3.set_option("timeout", int(self.max_time * 1000))  # in milliseconds

        # some flags that will be used after
        self._is_not_optimization_problem = False
        self._is_optimization_problem = False
        self._is_multi_objective_optimization_problem = False

    def get_parameters_description(self):
        """return the solver parameter names and values as a dict"""
        if not self._initialized:
            raise AssertionError(
                "please initialize solver before requesting for param name/values."
            )

        parameters_description = {}

        types = {
            0: "uint",
            1: "bool",
            2: "double",
            3: "str",
            4: "symbol",
            5: "invalid",
            6: "other",
        }

        descr = self._solver.param_descrs()
        for i in range(1, descr.size()):
            param_name = descr.get_name(i)
            param_type = types[descr.get_kind(param_name)]
            param_documentation = descr.get_documentation(param_name)
            try:
                param_value = z3.get_param(param_name)
            except:
                param_value = "unknown"
            parameters_description[param_name] = {
                "type": param_type,
                "value": param_value,
                "documentation": param_documentation,
            }

        return parameters_description

    def initialize(self):
        # create the solver
        print("Solver type:\n===========")

        # check if the problem is an optimization problem
        self._is_not_optimization_problem = len(self.problem.objectives) == 0
        self._is_optimization_problem = len(self.problem.objectives) > 0
        self._is_multi_objective_optimization_problem = len(self.problem.objectives) > 1
        # use the z3 z3.Optimize solver if requested
        if not self._is_not_optimization_problem and self.optimizer == "optimize":
            self._solver = z3.Optimize()
            self._solver.set(priority=self.optimize_priority)
            print("\t-> Builtin z3 z3.Optimize solver")
        elif self.logics is None:
            self._solver = z3.Solver()
            print("\t-> Standard SAT/SMT solver")
        else:
            self._solver = z3.SolverFor(self.logics)
            print("\t-> SMT solver using logics", self.logics)

        # add all tasks z3 assertions to the solver
        for task in self.problem.tasks.values():
            self.append_z3_assertion(task.get_z3_assertions())
            self.append_z3_assertion(task._end <= self.problem._horizon)

        # process resources assertions
        for ress in self.problem.workers.values():
            self.append_z3_assertion(ress.get_z3_assertions())

        # process resource intervals
        for ress in self.problem.workers.values():
            busy_intervals = ress.get_busy_intervals()
            nb_intervals = len(busy_intervals)
            for i in range(nb_intervals):
                start_task_i, end_task_i = busy_intervals[i]
                for k in range(i + 1, nb_intervals):
                    start_task_k, end_task_k = busy_intervals[k]
                    self.append_z3_assertion(
                        z3.Or(start_task_k >= end_task_i, start_task_i >= end_task_k)
                    )

        # add z3 assertions for constraints
        # that are *NOT* defined from an assertion
        constraints_not_from_assertion = [
            c
            for c in self.problem.constraints.values()
            if not c._created_from_assertion
        ]
        for constraint in constraints_not_from_assertion:
            self.append_z3_assertion(constraint.get_z3_assertions(), constraint.name)

        # process indicators
        for indic in self.problem.indicators.values():
            self.append_z3_assertion(indic.get_z3_assertions())

        # work amounts
        # for each task, compute the total work for all required resources"""
        for task in self.problem.tasks.values():
            if task.work_amount > 0.0:
                work_total_for_all_resources = []
                for required_resource in task._required_resources:
                    # work contribution for the resource
                    interv_low, interv_up = required_resource._busy_intervals[task]
                    work_contribution = required_resource.productivity * (
                        interv_up - interv_low
                    )
                    work_total_for_all_resources.append(work_contribution)
                self.append_z3_assertion(
                    z3.Sum(work_total_for_all_resources) >= task.work_amount
                )

        # process buffers
        for buffer in self.problem.buffers:
            # first add all buffer assertions
            self.append_z3_assertion(buffer.get_z3_assertions())
            # and after, additional assertions
            # sort consume/feed times in asc order
            tasks_start_unload = [t._start for t in buffer._unloading_tasks]
            number_of_unloading_tasks = len(tasks_start_unload)

            tasks_end_load = [t._end for t in buffer._loading_tasks]
            number_of_loading_tasks = len(tasks_end_load)

            # sort_no_duplicates seems to be better in terms of performance
            # but not suitable for concurrent access to a buffer.
            if isinstance(buffer, NonConcurrentBuffer):
                sorted_times, sort_assertions = sort_no_duplicates(
                    tasks_start_unload + tasks_end_load
                )
            else:  # ConcurrentBuffer
                sorted_times, sort_assertions = sort_duplicates(
                    tasks_start_unload + tasks_end_load
                )
            self.append_z3_assertion(sort_assertions)

            # add the constraints that give the buffer state change times
            for st, bfst in zip(sorted_times, buffer._state_changes_time):
                self.append_z3_assertion(st == bfst)

            # the final state of the list is constrained by the final_state value
            if buffer.final_state is not None:
                self.append_z3_assertion(
                    buffer._buffer_states[-1] == buffer.final_state
                )
            # lower and upper bounds
            if buffer.lower_bound is not None:
                for st in buffer._buffer_states:
                    self.append_z3_assertion(st >= buffer.lower_bound)
            if buffer.upper_bound is not None:
                for st in buffer._buffer_states:
                    self.append_z3_assertion(st <= buffer.upper_bound)
            #
            # Concurrent buffers
            #
            if isinstance(buffer, ConcurrentBuffer):
                functions = []
                x = z3.Int(f"t_{buffer.name}_variable")

                # unloading tasks
                for t in buffer._unloading_tasks:
                    f = z3.Function(
                        f"{buffer.name}_{t.name}_quantity_unloading",
                        z3.IntSort(),
                        z3.IntSort(),
                    )
                    asst = z3.ForAll(
                        x,
                        z3.If(
                            x == t._start,
                            f(x) == -buffer._unloading_tasks[t],
                            f(x) == 0,
                        ),
                    )
                    self.append_z3_assertion(asst)
                    functions.append(f)

                # loading tasks
                for t in buffer._loading_tasks:
                    f = z3.Function(
                        f"{buffer.name}_{t.name}_quantity_loading",
                        z3.IntSort(),
                        z3.IntSort(),
                    )
                    asst = z3.ForAll(
                        x,
                        z3.If(
                            x == t._end, f(x) == +buffer._loading_tasks[t], f(x) == 0
                        ),
                    )
                    self.append_z3_assertion(asst)
                    functions.append(f)
                for i in range(len(buffer._buffer_states) - 1):
                    if i == 0:
                        asst = buffer._buffer_states[1] == buffer._buffer_states[
                            0
                        ] + z3.Sum(
                            [f(buffer._state_changes_time[0]) for f in functions]
                        )
                        self.append_z3_assertion(asst)
                    else:  # if two consecutives state change times are the same, then only count them
                        asst = z3.If(
                            buffer._state_changes_time[i]
                            == buffer._state_changes_time[i - 1],
                            buffer._buffer_states[i + 1] == buffer._buffer_states[i],
                            buffer._buffer_states[i + 1]
                            == buffer._buffer_states[i]
                            + z3.Sum(
                                [f(buffer._state_changes_time[i]) for f in functions]
                            ),
                        )
                        self.append_z3_assertion(asst)
            #
            # Non concurrent buffers
            #
            elif isinstance(buffer, NonConcurrentBuffer):
                buffer_mapping = z3.Array(
                    f"Buffer_{buffer.name}_mapping", z3.IntSort(), z3.IntSort()
                )
                for t in buffer._unloading_tasks:
                    self.append_z3_assertion(
                        buffer_mapping
                        == z3.Store(
                            buffer_mapping, t._start, -buffer._unloading_tasks[t]
                        )
                    )
                for t in buffer._loading_tasks:
                    self.append_z3_assertion(
                        buffer_mapping
                        == z3.Store(buffer_mapping, t._end, +buffer._loading_tasks[t])
                    )
                # and, for the other, the buffer state i+1 is the buffer state i +/- the buffer change
                for i in range(len(buffer._buffer_states) - 1):
                    self.append_z3_assertion(
                        buffer._buffer_states[i + 1]
                        == buffer._buffer_states[i]
                        + buffer_mapping[buffer._state_changes_time[i]]
                    )

        # Finally add other assertions (FOL, user defined)
        for z3_assertion in self.problem.get_z3_assertions():
            self.append_z3_assertion(z3_assertion)

        # optimization
        if self._is_optimization_problem:
            self.create_objective()

        self._initialized = True

    def append_z3_assertion(self, assts, higher_constraint_name=None) -> bool:
        # set the method to use to add constraints
        # in debug mode this is assert_and_track, to be able to trace
        # z3.unsat core, in regular mode this is the add function
        if self.debug:
            if not isinstance(assts, list):
                assts = [assts]
            for asst in assts:
                asst_identifier = f"asst_{uuid.uuid4().hex[:8]}"
                self._solver.assert_and_track(asst, asst_identifier)
                # if the higher_contraint_name is defined, fill in the map_boolrefs_to_geometric_constraints dict
                # to track the constraint that causes the conflict
                if higher_constraint_name is not None:
                    self._map_boolrefs_to_geometric_constraints[
                        asst_identifier
                    ] = higher_constraint_name
        else:
            self._solver.add(assts)

    def build_equivalent_weighted_objective(self) -> bool:
        # Replace objectives O_i, O_j, O_k with
        # O = WiOi+WjOj+WkOk etc.
        equivalent_single_objective = z3.Int("EquivalentSingleObjective")
        weighted_objectives = []
        for obj in self.problem.objectives.values():
            variable_to_optimize = obj._target
            weight = obj.weight
            if obj.kind == "maximize":
                weighted_objectives.append(-weight * variable_to_optimize)
            elif obj.kind == "minimize":
                weighted_objectives.append(weight * variable_to_optimize)
        self.append_z3_assertion(
            equivalent_single_objective == z3.Sum(weighted_objectives)
        )
        # create an indicator
        equivalent_indicator = IndicatorFromMathExpression(
            name="EquivalentIndicator", expression=equivalent_single_objective
        )
        equivalent_objective = Objective(
            name="MinimizeEquivalentObjective",
            target=equivalent_indicator,
            kind="minimize",
        )
        self._objective = equivalent_objective
        self.append_z3_assertion(equivalent_indicator.get_z3_assertions())
        return equivalent_objective, equivalent_indicator

    def create_objective(self) -> bool:
        """create optimization objectives"""
        # in case of a single value to optimize
        if self._is_multi_objective_optimization_problem:
            if self.optimizer == "incremental" or self.optimize_priority == "weight":
                eq_obj, _ = self.build_equivalent_weighted_objective()
                if self.optimizer == "optimize":
                    self._solver.minimize(eq_obj._target)
            else:
                for obj in self.problem.objectives.values():
                    variable_to_optimize = obj._target
                    if obj.kind == "maximize":
                        self._solver.maximize(variable_to_optimize)
                    elif obj.kind == "minimize":
                        self._solver.minimize(variable_to_optimize)
        else:
            self._objective = list(self.problem.objectives.values())[0]
            if self.optimizer == "optimize":
                variable_to_optimize = self._objective._target
                if self._objective.kind == "maximize":
                    self._solver.maximize(variable_to_optimize)
                elif self._objective.kind == "minimize":
                    self._solver.minimize(variable_to_optimize)

    def check_sat(self, find_better_value: Optional[bool] = False):
        """check satisfiability.
        find_beter_value: the check_sat method is called from the incremental solver. Then we
        should not prompt that no solution can be found, but that no better solution can be found.
        Return
        * result as True (sat) or False (z3.unsat, z3.unknown).
        * the computation time.
        """
        init_time = time.perf_counter()
        sat_result = self._solver.check()
        check_sat_time = time.perf_counter() - init_time

        if sat_result == z3.unsat:
            if not find_better_value:
                print(
                    f"\tNo solution can be found for problem {self.problem.name}.\n\tReason: Unsatisfiable problem: no solution exists"
                )
            else:
                print(
                    f"\tCan't find a better solution for problem {self.problem.name}.\n"
                )

        if sat_result == z3.unknown:
            reason = self._solver.reason_unknown()
            print(
                f"\tNo solution can be found for problem {self.problem.name}.\n\tReason: {reason}"
            )

        return sat_result, check_sat_time

    def build_solution(self, z3_sol):
        """create and return a SchedulingSolution instance"""
        solution = SchedulingSolution(problem=self.problem)
        # horizon
        if self.problem.horizon is not None:
            solution.horizon = self.problem.horizon
        else:
            solution.horizon = z3_sol[self.problem._horizon].as_long()

        # process tasks
        for task in self.problem.tasks.values():
            # for each task, create a TaskSolution instance
            new_task_solution = TaskSolution(name=task.name)
            new_task_solution.type = type(task).__name__
            new_task_solution.start = z3_sol[task._start].as_long()
            new_task_solution.end = z3_sol[task._end].as_long()
            new_task_solution.duration = z3_sol[task._duration].as_long()
            new_task_solution.optional = task.optional

            new_task_solution.release_date = task.release_date
            new_task_solution.due_date = task.due_date
            new_task_solution.due_date_is_deadline = task.due_date_is_deadline

            new_task_solution.work_amount = task.work_amount
            new_task_solution.priority = task.priority

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
                new_task_solution.scheduled = f"{z3_sol[task._scheduled]}" == "True"
            else:
                new_task_solution.scheduled = True

            # process resource assignments
            for req_res in task._required_resources:
                # among those workers, some of them
                # are busy "in the past", that is to say they
                # should not be assigned to the related task
                # for each interval
                lower_bound, _ = req_res._busy_intervals[task]
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
        for resource in self.problem.workers.values():
            # for each task, create a TaskSolution instance
            # for cumulative workers, we append the current work
            if "_CumulativeWorker_" in resource.name:
                cumulative_worker_name = resource.name.split("_CumulativeWorker_")[0]
                if cumulative_worker_name not in solution.resources:
                    new_resource_solution = ResourceSolution(
                        name=cumulative_worker_name
                    )
                else:
                    new_resource_solution = solution.resources[cumulative_worker_name]
            else:
                new_resource_solution = ResourceSolution(name=resource.name)
            new_resource_solution.type = type(resource).__name__
            # check for task processed by this resource
            for task in resource._busy_intervals.keys():
                task_name = task.name
                st_var, end_var = resource._busy_intervals[task]
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
        for buffer in self.problem.buffers:
            buffer_name = buffer.name
            new_buffer_solution = BufferSolution(name=buffer_name)
            # buffer state values
            state_values = [
                z3_sol[sv_z3_var].as_long() for sv_z3_var in buffer._buffer_states
            ]
            # change_state_times
            change_state_times = [
                z3_sol[sct_z3_var].as_long()
                for sct_z3_var in buffer._state_changes_time
            ]
            # need to fix the results if ever the buffer
            # has been loaded/unloaded by concurrent tasks
            (
                new_buffer_solution.state,
                new_buffer_solution.state_change_times,
            ) = clean_buffer_states(state_values, change_state_times)

            solution.add_buffer_solution(new_buffer_solution)
        # process indicators
        for indicator in self.problem.indicators.values():
            indicator_name = indicator.name
            indicator_value = z3_sol[indicator._indicator_variable].as_long()
            solution.add_indicator_solution(indicator_name, indicator_value)

        return solution

    def solve(self) -> Union[bool, SchedulingSolution]:
        """call the solver and returns the solution, if ever"""
        if not self._initialized:
            self.initialize()

        # for all cases
        if self.debug:
            self.print_assertions()

        if self._is_optimization_problem and self.optimizer == "incremental":
            if self._is_multi_objective_optimization_problem:
                print("\tObjectives:\n\t======")
                for obj_name in self.problem.objectives:
                    print(f"\t{obj_name}")
            solution = self.solve_optimize_incremental(
                self._objective._target,
                kind="min" if self._objective.kind == "minimize" else "max",
            )
            if not solution:
                return False
        else:
            # first check satisfiability
            sat_result, sat_computation_time = self.check_sat()

            print("Total computation time:\n=====================")
            print(
                f"\t{self.problem.name} satisfiability checked in {sat_computation_time:.2f}s"
            )

            if sat_result == z3.unsat:
                if self.debug:
                    # extract z3.unsat core
                    unsat_core = self._solver.unsat_core()

                    conflicting_contraits = []
                    unknown_asst_origins = []
                    for asst in unsat_core:
                        # look for an entry in the map dict
                        if f"{asst}" in self._map_boolrefs_to_geometric_constraints:
                            constraint = self._map_boolrefs_to_geometric_constraints[
                                f"{asst}"
                            ]
                            conflicting_contraits.append(constraint)
                        else:
                            unknown_asst_origins.append(f"{asst}")
                    print(
                        f"\tUnsatisfied assertions - conflict between {len(conflicting_contraits)} constraints:"
                    )
                    for c in conflicting_contraits:
                        print(f"\t\t-> {c}")
                    print(
                        f"\tUnknown assertion origins ({len(unknown_asst_origins)} conflicts):"
                    )
                    for a in unknown_asst_origins:
                        print(f"\t\t-> {a}")
                    # look the entry
                return False

            if sat_result == z3.unknown:
                return False

            # then get the solution
            solution = self._solver.model()

            # print objectives values if optimizer
            if self.optimizer == "optimize":
                for obj in self.problem.objectives.values():
                    print(obj.name, "Value : ", solution[obj._target].as_long())

        self._current_solution = solution

        sol = self.build_solution(solution)

        if self.debug:
            self.print_statistics()
            self.print_solution()

        return sol

    def solve_optimize_incremental(
        self,
        variable: z3.ArithRef,
        max_iter: Optional[int] = None,
        kind: Optional[str] = "min",
    ) -> int:
        """target a min or max for a variable, without the z3.Optimize solver.
        The loop continues ever and ever until the next value is more than 90%"""
        if not self._initialized:
            self.initialize()

        if kind not in ["min", "max"]:
            raise ValueError("choose either 'min' or 'max'")
        num_iter = 0
        solution = False
        total_time = 0
        current_variable_value = None
        print("Incremental optimizer:\n======================")
        three_last_times = []

        if self._objective._bounds is None:
            bound = None
        else:
            bound = (
                self._objective._bounds[0]
                if kind == "min"
                else self._objective._bounds[1]
            )

        while True:  # infinite loop, break if z3.unsat or max_num_iter
            num_iter += 1
            if max_iter is not None and num_iter > max_iter:
                warnings.warn(
                    f"""maximum number of iteration {max_iter} exceeded, stop computation but there might be a
                    better solution. Increase the max_iter parameter and rerun the incremental optimizer."""
                )
                break

            incremental_solver_is_computing_a_better_value = (
                current_variable_value is not None
            )
            is_sat, sat_computation_time = self.check_sat(
                incremental_solver_is_computing_a_better_value
            )

            if is_sat == z3.unsat and current_variable_value is not None:
                print(f"\tFound optimum {current_variable_value}. Stopping iteration.")
                break
            if is_sat == z3.unsat:
                print("\tNo solution found. Stopping iteration.")
                break
            if is_sat == z3.unknown:
                break
            # at this stage, is_sat should be sat
            solution = self._solver.model()
            current_variable_value = solution[variable].as_long()
            total_time += sat_computation_time
            print(
                f"\tFound value: {current_variable_value} elapsed time:{total_time:.3f}s"
            )
            if self.max_time != "inf" and total_time > self.max_time:
                print("Max time exceeded. Stop incremental solver.")
                break

            if bound is not None and current_variable_value == bound:
                print(
                    f"\tFound optimum {current_variable_value}. Stop incremental solver."
                )
                break

            # prevent the solver to start a new round if we expect it to be
            # very long. The idea is the following: store the last 3 computation
            # times, compute and extrapolate a quadratic using a quadratic function.
            # Break the loop if ever the expected
            # time is too big.
            if len(three_last_times) < 3:
                three_last_times.append(total_time)
            else:
                three_last_times.pop(0)
                three_last_times.append(total_time)
                # Compute the expected value
                a, b, c = calc_parabola_from_three_points([0, 1, 2], three_last_times)
                expected_next_time = a * 9 + 3 * b + c
                if self.max_time != "inf" and expected_next_time > self.max_time:
                    print(
                        "Max time expected on the next iteration. Stop incremental solver."
                    )
                    break
            self._solver.push()
            if kind == "min":
                self.append_z3_assertion(variable < current_variable_value)
                print(f"\tChecking better value < {current_variable_value}")
            else:
                self.append_z3_assertion(variable > current_variable_value)
                print(f"\tChecking better value > {current_variable_value}")

        print(f"\ttotal number of iterations: {num_iter}")
        if current_variable_value is not None:
            print(f"\tvalue: {current_variable_value}")
        print(f"\t{self.problem.name} satisfiability checked in {total_time:.2f}s")

        return solution

    def print_assertions(self):
        """A utility method to display solver assertions"""
        print("Assertions:\n===========")
        for assertion in self._solver.assertions():
            print("\t->", assertion)

    def print_statistics(self):
        """A utility method that displays solver statistics"""
        print("Solver statistics:")
        for key, value in self._solver.statistics():
            print(f"\t{key}: {value}")

    def print_solution(self):
        """A utility method that displays all internal variables for the current solution"""
        print("Solution:")
        for decl in self._current_solution.decls():
            var_name = decl.name()
            var_value = self._current_solution[decl]
            print(f"\t-> {var_name}={var_value}")

    def find_another_solution(self, variable: z3.ArithRef) -> bool:
        """let the solver find another solution for the variable"""
        if self._current_solution is None:
            raise AssertionError("No current solution. First call the solve() method.")
        current_variable_value = self._current_solution[variable].as_long()
        self.append_z3_assertion(variable != current_variable_value)
        return self.solve()

    def export_to_smt2(self, smt_filename: str):
        """export the model to a smt file to be processed by another SMT solver"""
        with open(smt_filename, "w", encoding="utf-8") as outfile:
            outfile.write(self._solver.to_smt2())
