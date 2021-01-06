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

import itertools
import time
from typing import Optional

from z3 import (SolverFor,Int, Or, Xor, Sum, unsat,
                    unknown, Optimize, set_option)

from processscheduler.base import ObjectiveType

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

        self._verbosity = verbosity
        if verbosity:
            set_option("verbose", 2)

        # set timeout
        set_option("timeout", max_time * 1000)  # in ms

        # create the solver
        if self._problem.objectives:
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
        for task in self._problem.get_tasks():
            self._solver.add(task.get_assertions())
            # bound start and end
            self._solver.add(task.end >= 0)
            if not task.lower_bounded:
                self._solver.add(task.start >= 0)
            if not task.upper_bounded:
                self._solver.add(task.end <= self._problem.horizon)

        # then process tasks constraints
        for constraint in self._problem._constraints:
            self._solver.add(constraint)

        self.process_resource_requirements()
        self.process_work_amount()
        self.create_objectives()

    def create_objectives(self) -> None:
        """ create optimization objectives """
        tasks = self._problem.get_tasks()

        for obj in self._problem.objectives:
            if obj == ObjectiveType.MAKESPAN:
                # look for the minimum horizon, i.e. the shortest
                # time horizon to complete all tasks
                self._solver.minimize(self._problem.horizon)
            elif obj == ObjectiveType.LATEST:
                # schedule all at the latest time according
                # to a given horizon
                mini = Int('SmallestStartTime')
                self._solver.add(Or([mini == task.start for task in tasks]))
                for tsk in tasks:
                    self._solver.add(mini <= tsk.start)
                self._solver.maximize(mini)
            elif obj == ObjectiveType.FLOWTIME:
                # minimum flowtime, i.e. minimize the sum of all end times
                flowtime = Int('FlowTime')
                self._solver.add(flowtime == Sum([task.end for task in tasks]))
                self._solver.minimize(flowtime)
            elif obj == ObjectiveType.EARLIEST:
                # minimize the greatest start time
                maxi = Int('GreatestStartTime')
                self._solver.add(Or([maxi == task.start for task in tasks]))
                for tsk in tasks:
                    self._solver.add(maxi >= tsk.start)
                self._solver.minimize(maxi)

    def process_resource_requirements(self) -> None:
        """ force non overlapping of resources busy intervals """
        for resource in self._problem.resources.values():  # loop over resources
            intervals = resource.busy_intervals
            if len(intervals) <= 1:  # no need to carry about overlapping, only one task
                continue
            # get all pairs combination
            all_pairs = list(itertools.combinations(range(len(intervals)), r=2))

            for pair in all_pairs:
                i, j = pair
                start_task_i, end_task_i = intervals[i]
                start_task_j, end_task_j = intervals[j]
                # add the Xor constraint
                self._solver.add(Xor(start_task_i >= end_task_j, start_task_j >= end_task_i))

    def process_work_amount(self) -> None:
        """ for each task, compute the total work for all required resources """
        for task in self._problem.get_tasks():
            if task.work_amount > 0.:
                work_total_for_all_resources = []
                for required_resource in task.required_resources:
                    # look for start and end busy intervals
                    for interv_low, interv_up in required_resource.busy_intervals:
                        task_name = task.name
                        if task_name in interv_low.__repr__():
                            work_contribution = required_resource.productivity * (interv_up - interv_low)
                            work_total_for_all_resources.append(work_contribution)
                self._solver.add(Sum(work_total_for_all_resources) >= task.work_amount)

    def check_sat(self) -> bool:
        """ check satisfiability """
        init_time = time.perf_counter()
        sat_result  = self._solver.check()
        final_time = time.perf_counter()
        print('%s Satisfiability checked in %.2fs' % (self._problem._name, final_time - init_time))

        if self._verbosity:
            for assertion in self._solver.assertions():
                print("\t", assertion)

        if sat_result == unsat:
            print("No solution exists for problem %s." % self._problem._name)
            return False

        if sat_result == unknown:
            print("No solution can be found for problem %s." % self._problem._name)
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

        return True
