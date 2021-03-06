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

import time
from typing import Optional
import uuid
import warnings

from z3 import Solver, Sum, unsat, ArithRef, unknown, Optimize, set_option

from processscheduler.objective import MaximizeObjective, MinimizeObjective
from processscheduler.solution import SchedulingSolution, TaskSolution, ResourceSolution

#
# Solver class definition
#
class SchedulingSolver:
    """ A solver class """
    def __init__(self, problem,
                 debug: Optional[bool] = False,
                 max_time: Optional[int] = 60,
                 optimize_priority = 'lex',
                 parallel: Optional[bool] = False):
        """ Scheduling Solver

        debug: True or False, False by default
        max_time: time in seconds, 60 by default
        optimize_priority: one of 'lex', 'box', 'pareto'
        parallel: True to enable mutlthreading, False by default
        """
        self._problem = problem
        self.problem_context = problem.context
        self.debug = debug
        # objectives list
        self.optimize_priority = optimize_priority
        self.objectives = []  # the list of all objectives defined in this problem

        if debug:
            set_option("verbose", 2)

        # set timeout
        set_option("timeout", max_time * 1000)  # in ms

        # create the solver
        print('Solver type:\n===========')
        if self.problem_context.objectives:
            self._solver = Optimize()  # Solver with optimization
            self._solver.set(priority=self.optimize_priority)
            print("\t-> Solver with optimization enabled")
        else:
            # see this url for a documentation about logics
            # http://smtlib.cs.uiowa.edu/logics.shtml
            self._solver = Solver()
            print("\t-> Standard SAT/SMT solver")
            if debug:
                set_option(unsat_core=True)

        if parallel:
            set_option("parallel.enable", True)  # enable parallel computation

        # add all tasks assertions to the solver
        for task in self.problem_context.tasks:
            self.add_constraint(task.get_assertions())
            self.add_constraint(task.end <= self._problem.horizon)

        # then process tasks constraints
        for constraint in self.problem_context.constraints:
            self.add_constraint(constraint)
        # process resources requirements
        for ress in self.problem_context.resources:
            self.add_constraint(ress.get_assertions())

        # process indicators
        for indic in self.problem_context.indicators:
            self.add_constraint(indic.get_assertions())

        self.process_work_amount()

        self.create_objectives()

        # each time the solver is called, the current_solution is stored
        self.current_solution = None

    def add_constraint(self, cstr) -> bool:
        # set the method to use to add constraints
        # in debug mode this is assert_and_track, to be able to trace
        # unsat core, in regular mode this is the add function
        if self.debug:
            if isinstance(cstr, list):
                for c in cstr:
                    self._solver.assert_and_track(c, 'asst_%s' % uuid.uuid4().hex[:8])
            else:
                self._solver.assert_and_track(cstr, 'asst_%s' % uuid.uuid4().hex[:8])
        else:
            self._solver.add(cstr)

    def create_objectives(self) -> None:
        """ create optimization objectives """
        for obj in self.problem_context.objectives:
            if isinstance(obj, MaximizeObjective):
                # look for the minimum horizon, i.e. the shortest
                # time horizon to complete all tasks
                new_max = self._solver.maximize(obj.target)
                self.objectives.append(['%s(max objective)' % obj.target, new_max])
            elif isinstance(obj, MinimizeObjective):
                new_min = self._solver.minimize(obj.target)
                self.objectives.append(['%s(min objective)' % obj.target, new_min])

    def process_work_amount(self) -> None:
        """ for each task, compute the total work for all required resources """
        for task in self.problem_context.tasks:
            if task.work_amount > 0.:
                work_total_for_all_resources = []
                for required_resource in task.required_resources:
                    # work contribution for the resource
                    interv_low, interv_up = required_resource.busy_intervals[task]
                    work_contribution = required_resource.productivity * (interv_up - interv_low)
                    work_total_for_all_resources.append(work_contribution)
                self.add_constraint(Sum(work_total_for_all_resources) >= task.work_amount)

    def check_sat(self) -> bool:
        """ check satisfiability """
        init_time = time.perf_counter()
        sat_result  = self._solver.check()
        final_time = time.perf_counter()

        if self.debug:
            self.print_assertions()
            if isinstance(self._solver, Optimize):
                print('\tObjectives:\n\t======')
                for obj in self._solver.objectives():
                    print('\t', obj)
        print('SAT computation time:\n=====================')
        print('\t%s satisfiability checked in %.2fs' % (self._problem.name, final_time - init_time))

        if sat_result == unsat:
            print("SAT result:\n===========")
            print("\tNo solution exists for problem %s." % self._problem.name)
            if self.debug:
                unsat_core = self._solver.unsat_core()
                print('\t%i unsatisfied assertion(s) (probable conflict):' % len(unsat_core))
                for c in unsat_core:
                    print('\t->%s' % c)
            return False

        if sat_result == unknown:
            reason = self._solver.reason_unknown()
            print("\tNo solution can be found for problem %s because: %s" % (self._problem.name,
                                                                             reason))
            return False

        return True

    def build_solution(self, z3_sol):
        """ create a SchedulingSolution instance, and return it """
        solution = SchedulingSolution(self._problem)

        # set the horizon solution
        solution.horizon = z3_sol[self._problem.horizon].as_long()

        # process tasks
        for task in self._problem.context.tasks:
            # for each task, create a TaskSolution instance
            new_task_solution = TaskSolution(task.name)
            new_task_solution.type = type(task).__name__
            new_task_solution.start = z3_sol[task.start].as_long()
            new_task_solution.end = z3_sol[task.end].as_long()
            new_task_solution.duration = z3_sol[task.duration].as_long()
            new_task_solution.optional = task.optional

            # times, if ever delta_time and start_time are defined
            if self._problem.delta_time is not None:
                new_task_solution.duration_time = new_task_solution.duration * self._problem.delta_time
                if self._problem.start_time is not None:
                    new_task_solution.start_time = self._problem.start_time + new_task_solution.start * self._problem.delta_time
                    new_task_solution.end_time = new_task_solution.start_time + new_task_solution.duration_time
                else:
                    new_task_solution.start_time = new_task_solution.start * self._problem.delta_time
                    new_task_solution.end_time = new_task_solution.start_time + new_task_solution.duration_time

            if task.optional:
                # ugly hack, necessary because there's no as_bool()
                # method for Bool objects
                new_task_solution.scheduled = ("%s" % z3_sol[task.scheduled] == 'True')
            else:
                new_task_solution.scheduled = True

            # process resource assignments
            for req_res in task.required_resources:
                # by default, resource_should_be_assigned is set to True
                # if will be set to False if the resource is an alternative worker
                resource_is_assigned = True
                # among those workers, some of them
                # are busy "in the past", that is to say they
                # should not be assigned to the related task
                # for each interval
                lower_bound, _ = req_res.busy_intervals[task]
                if z3_sol[lower_bound].as_long() < 0:
                    # should not be scheduled
                    resource_is_assigned = False
                # add this resource to assigned resources, anytime
                if resource_is_assigned and (req_res.name not in new_task_solution.assigned_resources):
                    # if it is a cumulative resource, then we transform the resource name
                    resource_name = req_res.name.split('_CumulativeWorker_')[0]
                    if resource_name not in new_task_solution.assigned_resources:
                        new_task_solution.assigned_resources.append(resource_name)

            solution.add_task_solution(new_task_solution)

        # process resources
        for resource in self._problem.context.resources:
            # for each task, create a TaskSolution instance
            # for cumulative workers, we append the current work
            if '_CumulativeWorker_' in resource.name:
                cumulative_worker_name = resource.name.split('_CumulativeWorker_')[0]
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
                if start >= 0 and end >= 0 and (task_name, start, end) not in new_resource_solution.assignments:
                    new_resource_solution.assignments.append((task_name, start, end))

            if '_CumulativeWorker_' in resource.name:
                cumulative_worker_name = resource.name.split('_CumulativeWorker_')[0]
                if cumulative_worker_name not in solution.resources:
                    solution.add_resource_solution(new_resource_solution)
            else:
                solution.add_resource_solution(new_resource_solution)

        # process indicators
        for indicator in self._problem.context.indicators:
            indicator_name = indicator.name
            indicator_value = z3_sol[indicator.indicator_variable].as_long()
            solution.add_indicator_solution(indicator_name, indicator_value)

        return solution

    def solve(self) -> bool:
        """ call the solver and returns the solution, if ever """
        # first check satisfiability
        if not self.check_sat():
            return False

        solution = self._solver.model()
        self.current_solution = solution

        if self.objectives:
            print('Optimization results:\n=====================')
            print('\t->Objective priority specification: %s' % self.optimize_priority)
            print('\t->Objective values:')
            for objective_name, objective_value in self.objectives:  # if ever no objectives, this line will do nothing
                print('\t\t->%s: %s' % (objective_name, objective_value.value()))

        if self.debug:
            self.print_statistics()
            self.print_solution()

        sol = self.build_solution(solution)

        return sol

    def print_assertions(self):
        """A utility method to display solver assertions"""
        print('Assertions:\n===========')
        for assertion in self._solver.assertions():
            print('\t->', assertion)

    def print_statistics(self):
        """A utility method that displays solver statistics"""
        print('Solver satistics:')
        for key, value in self._solver.statistics():
            print('\t%s: %s' % (key, value))

    def print_solution(self):
        """A utility method that displays all internal variables for the current solution"""
        print('Solution:')
        for decl in self.current_solution.decls():
            var_name = decl.name()
            var_value = self.current_solution[decl]
            print("\t-> %s=%s" %(var_name, var_value))

    def find_another_solution(self, variable: ArithRef) -> bool:
        """ let the solver find another solution for the variable """
        if self.current_solution is None:
            warnings.warn('No current solution. First call the solve() method.')
            return False
        current_variable_value = self.current_solution[variable].as_long()
        self.add_constraint(variable != current_variable_value)
        return self.solve()

    def export_to_smt2(self, smt_filename):
        """ export the model to a smt file to be processed by another SMT solver """
        with open(smt_filename, 'w') as outfile:
            outfile.write(self._solver.to_smt2())
