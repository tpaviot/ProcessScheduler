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
import warnings

from z3 import (SolverFor, Sum, unsat,
                ArithRef, unknown, Optimize, set_option)

from processscheduler.objective import MaximizeObjective, MinimizeObjective
from processscheduler.solution import SchedulingSolution, TaskSolution, ResourceSolution

#
# Solver class definition
#
class SchedulingSolver:
    """ A solver class """
    def __init__(self, problem,
                 verbosity: Optional[bool] = False,
                 max_time: Optional[int] = 60,
                 parallel: Optional[bool] = False,
                 logic: Optional[str] = 'QF_LIA'):
        """ Scheduling Solver

        verbosity: True or False, False by default
        max_time: time in seconds, 60 by default
        parallel: True to enable mutlthreading, False by default
        """
        self._problem = problem
        self.problem_context = problem.context

        self._verbosity = verbosity
        if verbosity:
            set_option("verbose", 2)

        # set timeout
        set_option("timeout", max_time * 1000)  # in ms

        # create the solver
        if self.problem_context.objectives:
            self._solver = Optimize()  # Solver with optimization
            if verbosity:
                print("Solver with optimization enabled")
        else:
            # see this url for a documentation about logics
            # http://smtlib.cs.uiowa.edu/logics.shtml
            self._solver = SolverFor(logic)  # SMT without optimization
            if verbosity:
                print("Solver without optimization enabled")

        if parallel:
            set_option("parallel.enable", True)  # enable parallel computation
            set_option("parallel.threads.max", 4)  #nbr of max tasks

        # add all tasks assertions to the solver
        for task in self.problem_context.tasks:
            self._solver.add(task.get_assertions())
            self._solver.add(task.end <= self._problem.horizon)

        # then process tasks constraints
        for constraint in self.problem_context.constraints:
            self._solver.add(constraint)

        # process resources requirements
        for ress in self.problem_context.resources:
            self._solver.add(ress.get_assertions())

        # process indicators
        for indic in self.problem_context.indicators:
            self._solver.add(indic.get_assertions())

        self.process_work_amount()

        self.create_objectives()

        # each time the solver is called, the current_solution is stored
        self.current_solution = None

    def create_objectives(self) -> None:
        """ create optimization objectives """
        for obj in self.problem_context.objectives:
            if isinstance(obj, MaximizeObjective):
                # look for the minimum horizon, i.e. the shortest
                # time horizon to complete all tasks
                self._solver.maximize(obj.target)
            elif isinstance(obj, MinimizeObjective):
                self._solver.minimize(obj.target)

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
                self._solver.add(Sum(work_total_for_all_resources) >= task.work_amount)

    def check_sat(self) -> bool:
        """ check satisfiability """
        init_time = time.perf_counter()
        sat_result  = self._solver.check()
        final_time = time.perf_counter()
        print('%s Satisfiability checked in %.2fs' % (self._problem.name, final_time - init_time))

        if self._verbosity:
            print("\tAssertions:\n\t======")
            for assertion in self._solver.assertions():
                print("\t", assertion)
            print("\tObjectives:\n\t======")
            if isinstance(self._solver, Optimize):
                for obj in self._solver.objectives():
                    print('\t', obj)
        if sat_result == unsat:
            print("No solution exists for problem %s." % self._problem.name)
            return False

        if sat_result == unknown:
            reason = self._solver.reason_unknown()
            print("No solution can be found for problem %s because: %s" % (self._problem.name,
                                                                           reason))
            return False

        return True

    def build_solution(self, z3_sol):
        """ create a SchedulingSolution instance, and return it """
        solution = SchedulingSolution(self._problem.name)

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
            if task.optional:
                new_task_solution.scheduled = ("%s" % z3_sol[task.scheduled] == 'True')  # ugly hack
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
                    new_task_solution.assigned_resources.append(req_res.name)

            solution.add_task_solution(new_task_solution)

        # process resources
        for resource in self._problem.context.resources:
            # for each task, create a TaskSolution instance
            new_resource_solution = ResourceSolution(resource.name)
            new_resource_solution.type = type(resource).__name__
            # check for task processed by this resource
            for task in resource.busy_intervals.keys():
                task_name = task.name
                st_var, end_var = resource.busy_intervals[task]
                start = z3_sol[st_var].as_long()
                end = z3_sol[end_var].as_long()
                if start >= 0 and end >= 0:
                    new_resource_solution.assignments.append((task_name, start, end))

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

        if self._verbosity:
            print('Solver satistics:')
            for key, value in self._solver.statistics():
                print('\t%s: %s' % (key, value))
            print('Solution:')
            for decl in solution.decls():
                var_name = decl.name()
                var_value = solution[decl]
                print("\t%s=%s" %(var_name, var_value))

        sol = self.build_solution(solution)

        return sol

    def find_another_solution(self, variable: ArithRef) -> bool:
        """ let the solver find another solution for the variable """
        if self.current_solution is None:
            warnings.warn('No current solution. First call the solve() method.')
            return False
        current_variable_value = self.current_solution[variable].as_long()
        self._solver.add(variable != current_variable_value)
        return self.solve()

    def export_to_smt2(self, smt_filename):
        """ export the model to a smt file to be processed by another SMT solver """
        with open(smt_filename, 'w') as outfile:
            outfile.write(self._solver.to_smt2())
