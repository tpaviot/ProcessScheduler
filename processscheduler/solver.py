""" ProcessScheduler, Copyright 2020 Thomas Paviot (tpaviot@gmail.com)

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.
"""

import time
from typing import Optional
import warnings

from z3 import (SolverFor, Sum, unsat,
                ArithRef, unknown, Optimize, set_option)

from processscheduler.objective import MaximizeObjective, MinimizeObjective

#
# Solver class definition
#
class SchedulingSolver:
    """ A solver class """
    def __init__(self, problem,
                 verbosity: Optional[bool] = False,
                 max_time: Optional[int] = 60,
                 parallel: Optional[bool] = False):
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
            self._solver = SolverFor('QF_LIA')  # SMT without optimization
            if verbosity:
                print("Solver without optimization enabled")

        if parallel:
            set_option("parallel.enable", True)  # enable parallel computation
            set_option("parallel.threads.max", 4)  #nbr of max tasks

        # add all tasks assertions to the solver
        for task in self.problem_context.tasks:
            self._solver.add(task.get_assertions())
            # bound start and end
            self._solver.add(task.end >= 0)
            if not task.lower_bounded:
                self._solver.add(task.start >= 0)
            if not task.upper_bounded:
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
                print("Maximze !")
                self._solver.maximize(obj.target)
            elif isinstance(obj, MinimizeObjective):
                print("Minimize")
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

    def solve(self) -> bool:
        """ call the solver and returns the solution, if ever """
        # first check satisfiability
        if not self.check_sat():
            return False

        solution = self._solver.model()

        if self._verbosity:
            print('Solver satistics:')
            for key, value in self._solver.statistics():
                print('\t%s: %s' % (key, value))
            print('Solution:')
            for decl in solution.decls():
                var_name = decl.name()
                var_value = solution[decl]
                print("\t%s=%s" %(var_name, var_value))
        ## propagate the result to the scenario
        self._problem.set_solution(solution)

        self.current_solution = solution

        return True

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
