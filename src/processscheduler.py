#!/usr/bin/env python
""" ProcessSchedule, Copyright 2020 Thomas Paviot (tpaviot@gmail.com)

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

from enum import IntEnum
import itertools
import time
from typing import Dict, List, Optional
import uuid
import warnings

try:
    from z3 import (SolverFor, Bool, If, Int, And, Or, Xor, Sum, unsat,
                    unknown, PbEq, Optimize, set_param, set_option,
                    ModelRef)
except ModuleNotFoundError:
    raise ImportError("z3 is a mandatory dependency")

#
# Base types
#
class ObjectiveType(IntEnum):
    MAKESPAN = 1
    FLOWTIME = 2
    EARLIEST = 3
    LATEST = 4

class PrecedenceType(IntEnum):
    LAX = 1
    STRICT = 2
    TIGHT = 3

#
# _NamedUIDObject, name and uid for hashing
#
class _NamedUIDObject:
    """ a base class common to all classes """
    def __init__(self, name) -> None:
        self.name = name
        self.uid = uuid.uuid4().int

    def __hash__(self) -> int:
        return self.uid

    def __repr__(self) -> str:
        return self.name

#
# Resources class definition
#
class _Resource(_NamedUIDObject):
    def __init__(self, name: str):
        super().__init__(name)

        # for each resource
        # we define a list that contains periods for which
        # the resource is busy
        # for instance:
        # self.busy_intervals=[(1,3), (5, 7)]
        self.busy_intervals = []

    def add_busy_interval(self, interval):
        # an interval is considered as a tuple (begin, end)
        self.busy_intervals.append(interval)

class Worker(_Resource):
    """ Class representing an atomic resource, e.g. a machine or a human being
    """
    def __init__(self, name: str) -> None:
        super().__init__(name)

class AlternativeWorkers(_Resource):
    """ Class representing n workers chosen among a list
    of n possible workers
    number_of_workers: 1 by default
    """
    def __init__(self, list_of_workers: List[_Resource], number_of_workers: Optional[int]=1):
        super().__init__('')
        self.list_of_workers = list_of_workers
        self.number_of_workers = number_of_workers

        # a dict that maps workers and selected boolean
        self.selection_dict = {}

        # create as many booleans as resources in the list
        selection_list = []
        for wrkr in list_of_workers:
            worker_is_selected = Bool('Selected_%i_%s' % (self.uid, wrkr.name))
            selection_list.append(worker_is_selected)
            self.selection_dict[wrkr] = worker_is_selected

        # create the assertion : exactly n boolean flags are allowed to be True,
        # the others must be False
        # see https://github.com/Z3Prover/z3/issues/694
        # and https://stackoverflow.com/questions/43081929/k-out-of-n-constraint-in-z3py
        self.selection_assertion = PbEq([(boolean, True) for boolean in selection_list], number_of_workers)

#
# Tasks class definition
#
class Task(_NamedUIDObject):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        # Following parameters are set after the solver was
        # successfully executed.
        # the _scheduled flag is set to True
        # if the solver schedules the task
        # by default set to False
        self.scheduled = False

        # scheduled start, end and duration set to 0 by default
        # be set after the solver is called
        self.scheduled_start = 0
        self.scheduled_end = 0
        self.scheduled_duration = 0

        # required resources to perform the task
        self._resources_required = []

        # assigned resource names, after the solver is ended
        self.resources_assigned = []

        # z3 Int variables
        self.start = Int('%s_start' % name)
        self.end = Int('%s_end' % name)
        self.duration = None  # defined for specialized tasks

        # SMT assertions
        # start and end integer values must be positive
        self._assertions = []

        # these two flags are set to True is there is a constraint
        # that set a lower or upper bound (e.g. a Precedence)
        # this is useful to reduce the number of assertions in z3
        # indeed if the task is lower_bounded by a precedence or
        # a StartAt, then there's no need to assert task.start >= 0
        self.lower_bounded = False
        # idem for the upper bound: no need to assert task.end <= horizon
        self.upper_bounded = False

    def add_assertion(self, z3_assertion):
        self._assertions.append(z3_assertion)

    def get_assertions(self):
        return self._assertions

    def add_required_resource(self, resource: _Resource) -> bool:
        if not isinstance(resource, _Resource):
            raise TypeError('you must pass a Resource instance')
        if isinstance(resource, AlternativeWorkers):
            # loop over each resource
            for worker in resource.list_of_workers:
                resource_maybe_busy_start = Int('%s_maybe_busy_%s_start' % (worker.name, self.name))
                resource_maybe_busy_end = Int('%s_maybe_busy_%s_end' % (worker.name, self.name))
                # create the busy interval for the resource
                worker.add_busy_interval((resource_maybe_busy_start, resource_maybe_busy_end))
                # add assertions. If worker is selected then sync the resource with the task
                selected_variable = resource.selection_dict[worker]
                # in the case the worker is selected
                # else: reject in the past !! (i.e. this resource will be scheduled in the past)
                # define the assertion ...
                assertion = If(selected_variable,
                               And(resource_maybe_busy_start + self.duration == resource_maybe_busy_end,
                                            resource_maybe_busy_start ==  self.start),
                               And(resource_maybe_busy_start < 0, resource_maybe_busy_end < 0))
                # ... and store it into the task assertions list
                self.add_assertion(assertion)
                # also, don't forget to add the AlternativeWorker assertion
                self.add_assertion(resource.selection_assertion)

                # finally, add each worker to the "required" resource list
                self._resources_required.append(worker)
        elif isinstance(resource, Worker):
            resource_busy_start = Int('%s_busy_%s_start' % (resource.name, self.name))
            resource_busy_end = Int('%s_busy_%s_end' % (resource.name, self.name))
            # create the busy interval for the resource
            resource.add_busy_interval((resource_busy_start, resource_busy_end))
            # set the busy resource to keep synced with the task
            self.add_assertion(resource_busy_start + self.duration == resource_busy_end)
            self.add_assertion(resource_busy_start ==  self.start)

            # finally, store this resource into the resource list
            self._resources_required.append(resource)
        return True

class FixedDurationTask(Task):
    def __init__(self, name: str, duration: int):
        super().__init__(name)
        self.duration = duration
        # add an assertion: end = start + duration
        self.add_assertion(self.start + self.duration == self.end)

class ZeroDurationTask(Task):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.duration = 0
        # add an assertion: end = start because the duration is zero
        self.add_assertion(self.start == self.end)

class VariableDurationTask(Task):
    def __init__(self, name: str,
                 length_at_least: Optional[int]=0, length_at_most: Optional[int]=None):
        super().__init__(name)
        self.duration = Int('%s_duration' % self.name)
        self.length_at_least = length_at_least
        self.length_at_most = length_at_most

        # set minimal duration
        self.add_assertion(self.duration >= length_at_least)

        if length_at_most is not None:
            self.add_assertion(self.duration <= length_at_most)

        # add an assertion: end = start + duration
        self.add_assertion(self.start + self.duration == self.end)
#
# Generic _Constraint class definition.
#
class _Constraint(_NamedUIDObject):
    """ abstract _Constraint class """
    def __init__(self):
        super().__init__(name='')

#
# Task constraints base class
#
class _TaskConstraint(_Constraint):
    def __init__(self):
        super().__init__()
        self.assertions = []

    def add_assertion(self, ass):
        self.assertions.append(ass)

    def get_assertions(self):
        return self.assertions

#
# Tasks constraints for two or more classes
#
class TaskPrecedence(_TaskConstraint):
    def __init__(self, task_before, task_after,
                 offset=0, kind=PrecedenceType.LAX):
        """ kind might be either LAX/STRICT/TIGHT
        Semantics : task after will start at least after offset periods
        task_before is finished.
        LAX constraint: task1_before_end + offset <= task_after_start
        STRICT constraint: task1_before_end + offset < task_after_start
        TIGHT constraint: task1_before_end + offset == task_after_start
        """
        super().__init__()

        if not isinstance(offset, int) or offset < 0:
            raise ValueError('offset must be a positive integer')

        self.task_before = task_before
        self.task_after = task_after
        self.offset = offset
        self.kind = kind

        if offset > 0:
            lower = task_before.end + offset
        else:
            lower = task_before.end
        upper = task_after.start

        if kind == PrecedenceType.LAX:
            self.add_assertion(lower <= upper)
        elif kind == PrecedenceType.STRICT:
            self.add_assertion(lower < upper)
        elif kind == PrecedenceType.TIGHT:
            self.add_assertion(lower == upper)
        else:
            raise ValueError("Unknown precedence type")

        task_after.lower_bounded = True
        task_before.upper_bounded = True

    def __repr__(self):
        comp_chars = {PrecedenceType.LAX:'<=',
                      PrecedenceType.STRICT:'<',
                      PrecedenceType.TIGHT: '==',
                     }
        return "Prcedence constraint: %s %s %s" % (self.task_before,
                                                   comp_chars[self.kind],
                                                   self.task_after)

class TasksStartSynced(_TaskConstraint):
    """ Two tasks that must start at the same time """
    def __init__(self, task_1: Task, task_2: Task) -> None:
        super().__init__()
        self.task_1 = task_1
        self.task_2 = task_2

        self.add_assertion(task_1.start == task_2.start)

class TasksEndSynced(_TaskConstraint):
    """ Two tasks that must complete at the same time """
    def __init__(self, task_1: Task, task_2: Task) -> None:
        super().__init__()
        self.task_1 = task_1
        self.task_2 = task_2

        self.add_assertion(task_1.end == task_2.end)


class TasksDontOverlap(_TaskConstraint):
    """ two tasks must not overlap, i.e. one needs to be completed before
    the other can be processed """
    def __init__(self, task_1: Task, task_2: Task) -> None:
        super().__init__()
        self.task_1 = task_1
        self.task_2 = task_2

        self.add_assertion(Xor(task_2.start >= task_1.end,
                               task_1.start >= task_2.end))

#
# Task constraints for one single task
#

class TaskStartAt(_TaskConstraint):
    """ One task must start at the desired time """
    def __init__(self, task: Task, value: int) -> None:
        super().__init__()
        self.task = task
        self.value = value

        self.add_assertion(task.start == value)

        task.lower_bounded = True

class TaskStartAfterStrict(_TaskConstraint):
    """ task.start > value """
    def __init__(self, task: Task, value: int) -> None:
        super().__init__()
        self.task = task
        self.value = value

        self.add_assertion(task.start > value)

        task.lower_bounded = True

class TaskStartAfterLax(_TaskConstraint):
    """  task.start >= value  """
    def __init__(self, task: Task, value: int) -> None:
        super().__init__()
        self.task = task
        self.value = value

        self.add_assertion(task.start >= value)

        task.lower_bounded = True

class TaskEndAt(_TaskConstraint):
    """ On task must complete at the desired time """
    def __init__(self, task: Task, value: int) -> None:
        super().__init__()
        self.task = task
        self.value = value

        self.add_assertion(task.end == value)

        task.upper_bounded = True

class TaskEndBeforeStrict(_TaskConstraint):
    """ task.end < value """
    def __init__(self, task: Task, value: int) -> None:
        super().__init__()
        self.task = task
        self.value = value

        self.add_assertion(task.end < value)

        task.upper_bounded = True

class TaskEndBeforeLax(_TaskConstraint):
    """ task.end <= value """
    def __init__(self, task: Task, value: int) -> None:
        super().__init__()
        self.task = task
        self.value = value

        self.add_assertion(task.end <= value)

        task.upper_bounded = True

# class TaskExclusive(_TaskConstraint):
#     """ TODO One task that needs to be processed alone, that is to say no other
#     task should be scheduled as soon as it started and until it is completed """
#     def __init__(self, task: Task) -> None:
#         super().__init__()
#         self.task = task

#
# Resource constraints
#
class _ResourceConstraint(_Constraint):
    pass

#
# SchedulingProblem class definition
#
class SchedulingProblem:
    def __init__(self, name: str, horizon: Optional[int]=None):
        self._name = name

        # define the horizon variable if no horizon defined
        if horizon is None:
            self._horizon = Int('horizon')
        else:  # an integer horizon is defined, no need to create a z3 variable
            self._horizon = horizon

        self._scheduled_horizon = 0  # set after the solver is finished
        # the list of tasks to be scheduled in this scenario
        self._tasks = {} # type: Dict[str, Task]
        # the list of resources available in this scenario
        self._resources = {} # type: Dict[str, _Resource]
        # the constraints are defined in the scenario
        self._constraints = [] # type: List[_Constraint]
        # multiple objectives is possible
        self._objectives = [] # type: List[ObjectiveType]
        # the solution
        self._solution = None # type: ModelRef

    def set_solution(self, solution: ModelRef) -> None:
        """ for each task, set the resource, start and length values """
        self._solution = solution

        for task in self._tasks.values():
            task.scheduled_start = solution[task.start].as_long()
            task.scheduled_end = solution[task.end].as_long()
            if isinstance(task, VariableDurationTask):
                task.scheduled_duration = solution[task.duration].as_long()
            else:
                task.scheduled_duration = task.duration
            # set task to "Scheduled" status
            task.schedule = True

        # set the resource assignement
        task.resources_assigned = ['bilou']
        # set the horizon
        if isinstance(self._horizon, int):
            self._scheduled_horizon = self._horizon
        else:
            self._scheduled_horizon = solution[self._horizon].as_long()

    def add_task(self, task: Task) -> bool:
        """ add a single task to the problem """
        task_name = task.name
        if not task_name in self._tasks:
            self._tasks[task_name] = task
        else:
            warnings.warn('task %s already part of the problem' % task)
            return False
        return True

    def add_tasks(self, list_of_tasks: List[Task]) -> None:
        """ adds tasks to the problem """
        for task in list_of_tasks:
            self.add_task(task)

    def add_resource(self, resource: _Resource) -> bool:
        """ add a single resource to the problem """
        resource_name = resource.name
        if not resource_name in self._resources:
            self._resources[resource_name] = resource
        else:
            warnings.warn('resource %s already part of the problem' % resource)
            return False
        return True

    def add_resources(self, list_of_resources: List[_Resource]) -> None:
        for resource in list_of_resources:
            self.add_resource(resource)

    def get_tasks(self) -> List[Task]:
        """ return the list of tasks """
        return self._tasks.values()

    def get_zero_length_tasks(self)-> List[ZeroDurationTask]:
        return [t for t in self.get_tasks() if isinstance(t, ZeroDurationTask)]

    def get_fixed_length_tasks(self) -> List[FixedDurationTask]:
        return [t for t in self.get_tasks() if isinstance(t, FixedDurationTask)]

    def get_variable_length_tasks(self) -> List[VariableDurationTask]:
        return [t for t in self.get_tasks() if isinstance(t, VariableDurationTask)]

    def add_constraint(self, constraint: _Constraint) -> bool:
        if not isinstance(constraint, _Constraint):
            raise TypeError("add_constraint takes a _Constraint instance")
        if not constraint in self._constraints:
            self._constraints.append(constraint)
            return True
        warnings.warn("Resource already added.")
        return False

    def add_constraints(self, list_of_constraints: List[_Constraint]) -> None:
        """ adds constraints to the problem """
        for constraint in list_of_constraints:
            self.add_constraint(constraint)

    def add_objective_makespan(self) -> bool:
        """ makespan objective
        """
        if isinstance(self._horizon, int):
            warnings.warn('Horizon set to fixed value %i, cannot be optimized' % self._horizon)
            return False
        self._objectives.append(ObjectiveType.MAKESPAN)
        return True

    def add_objective_start_latest(self) -> None:
        """ maximize the minimu start time, i.e. all the tasks
        are scheduled as late as possible """
        self._objectives.append(ObjectiveType.LATEST)

    def add_objective_start_earliest(self) -> None:
        """ minimize the greatest start time, i.e. tasks are schedules
        as early as possible """
        self._objectives.append(ObjectiveType.EARLIEST)

    def add_objective_flowtime(self) -> None:
        """ the flowtime is the sum of all ends, minimize. Be carful that
        it is contradictory with makespan """
        self._objectives.append(ObjectiveType.FLOWTIME)

    def print_solution(self) -> bool:
        """ print solution to console """
        if self._solution is None:
            warnings.warn("No solution to display.")
            return False
        for task in self._tasks.values():
            ress = task._resources_required
            print(task.name, ":", ress, task.scheduled_start, task.scheduled_end)
        return True

    def render_gantt_ascii(self) -> bool:
        """ displays an ascii gantt chart """
        if self._solution is None:
            warnings.warn("No solution to display.")
            return False
        print("Ascii Gantt solution")
        for task in self._tasks.values():
            task_line = '|' + task.name[:4] + '|' + \
                        ' ' * task.scheduled_start + task.scheduled_duration * '#'
            print(task_line)
        print('-' * (self._scheduled_horizon + 4))
        return True

    def render_gantt_matplotlib(self, figsize=(9,6), savefig=False) -> bool:
        """ generate a gantt diagram using matplotlib.
        Inspired by
        https://www.geeksforgeeks.org/python-basic-gantt-chart-using-matplotlib/
        """
        if self._solution is None:
            warnings.warn("No solution to plot.")
            return False
        try:
            import matplotlib.pyplot as plt
            from matplotlib.colors import LinearSegmentedColormap
        except ImportError:
            warnings.warn('matplotlib not installed')
            return False
        fig, gantt = plt.subplots(1, 1, figsize=figsize)
        gantt.set_title("Task schedule - %s" % self._name)
        gantt.set_xlim(0, self._scheduled_horizon)
        gantt.set_xticks(range(self._scheduled_horizon + 1))
        # Setting labels for x-axis and y-axis
        gantt.set_xlabel('Periods', fontsize=12)
        gantt.set_ylabel('Tasks', fontsize=12)
        nbr_tasks = len(self.get_tasks())
        nbr_of_colors = nbr_tasks * 2
        cmap = LinearSegmentedColormap.from_list('custom blue',
                                                 ['#ffff00','#002266'],
                                                 N = nbr_of_colors)
        # the task color is defined from the task name, this way the task has
        # already the same color, even if it is defined after
        gantt.set_ylim(0, 2 * nbr_tasks)
        gantt.set_yticks(range(1, 2 * nbr_tasks, 2))
        gantt.set_yticklabels(map(str, self.get_tasks()))
        # create a bar for each task
        for i, task in enumerate(self.get_tasks()):
            start = task.scheduled_start
            length = task.scheduled_duration
            if length == 0:  # zero duration tasks, to be visible
                gantt.broken_barh([(start - 0.05, 0.1)], (i * 2, 2), facecolors=cmap(i))
            else:
                gantt.broken_barh([(start, length)], (i * 2, 2), facecolors=cmap(i))
            # build the bar text string
            text = "%s" % task
            if task._resources_required:
                resources_names = ["%s" % c for c in task._resources_required]
                resources_names.sort()  # alphabetical sort
                text += "(" + ",".join(resources_names) + ")"
            else:
                text += "(no resource)"
            gantt.text(x=start + length / 2, y=i * 2 + 1,
                       s=text, ha='center', va='center', color='black')
        plt.grid(axis='x')
        if savefig:
            plt.savefig('scr.png')
        plt.show()
        return True

# Solver class definition
#
class SchedulingSolver:
    def __init__(self, problem,
                 verbosity: Optional[bool]=False,
                 max_time: Optional[int]=60,
                 parallel: Optional[bool]=False):
        """ Scheduling Solver

        verbosity: True or False, False by default
        max_time: time in seconds, 60 by default
        parallel: True to enable mutlthreading, False by default
        """
        self._problem = problem

        self._verbosity = verbosity
        if verbosity:
            set_option("verbose", 2)

        # by default, no optimization. This flag is set to True whenever any of the
        # add_objective_* is called
        self._optimization = False

        # set timeout
        set_option("timeout", max_time * 1000)  # in ms

        # by default, set the random seed to a fixed value
        set_param("smt.random_seed", 1234)

        # create the solver
        if self._problem._objectives:
            self.set_optimization()
        if not self._optimization:
            self._solver = SolverFor('QF_LIA')  # SMT without optimization
            #if self._problem._horizon is not None:
            #    self._solver.add(self._horizon == self._problem._horizon)
            #else:
            if self._verbosity:
                warnings.warn('Horizon not set')
        else:  # optimization enabled
            self._solver = Optimize()

        if parallel:
            set_option("parallel.enable", True)
            set_option("parallel.threads.max", 4)  #nbr of max tasks

        if self._verbosity:
            print("Solver:", type(self._solver))

        # add all tasks assertions to the solver
        for task in self._problem.get_tasks():
            self._solver.add(task.get_assertions())
            # bound start and end
            self._solver.add(task.end >= 0)
            if not task.lower_bounded:
                self._solver.add(task.start >= 0)
            if not task.upper_bounded:
                self._solver.add(task.end <= self._problem._horizon)

        # then process tasks constraints
        for constraint in self._problem._constraints:
            self._solver.add(constraint.get_assertions())

        self.process_resource_requirements()
        self.create_objectives()

    def set_random_seed_variable(self) -> None:
        """ each time the solver is called, the result may be different
        """
        set_param("smt.random_seed", int(time.time()))

    def set_optimization(self) -> None:
        """" set the optimization flag to True """
        if not self._optimization:
            print("Add least one optimization objective. Optimization set to True.")
        self._optimization = True

    def create_objectives(self) -> None:
        """ create optimization objectives """
        tasks = self._problem.get_tasks()

        for obj in self._problem._objectives:
            if obj == ObjectiveType.MAKESPAN:
                # look for the minimum horizon, i.e. the shortest
                # time horizon to complete all tasks
                self._solver.minimize(self._problem._horizon)
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
        for resource in self._problem._resources.values():  # loop over resources
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

    def check_sat(self) -> bool:
        """ check satisfiability """
        init_time = time.perf_counter()
        sat_result  = self._solver.check()
        final_time = time.perf_counter()
        print('Satisfiability checked in %.2fs' % (final_time - init_time))

        if self._verbosity:
            for assertion in self._solver.assertions():
                print("\t", assertion)

        if sat_result == unsat:
            print("No solution exists.")
            return False

        if sat_result == unknown:
            print("No solution can be found.")
            return False

        return True

    def solve(self) -> bool:
        """ call the solver and returns the solution, if ever """
        # check satisfiability
        if not self.check_sat():
            warnings.warn("The problem doesn't have any solution")
            return False

        solution = self._solver.model()

        if self._verbosity:
            print("Solver satistics:")
            for key, value in self._solver.statistics():
                print("\t%s : %s" % (key, value))
            print("### Solution found ###")
            for decl in solution.decls():
                var_name = decl.name()
                var_value = solution[decl]
                print("%s=%s" %(var_name, var_value))

        ## propagate the result to the scenario
        self._problem.set_solution(solution)

        return True

if __name__ == "__main__":
    pb = SchedulingProblem('tst-problem', horizon=30)

    t1 = FixedDurationTask('t1', duration=1)
    print(t1)
    assert t1.duration == 1

    t2 = ZeroDurationTask('t2')
    assert t2.duration == 0

    t3 = VariableDurationTask('t3')

    t4 = FixedDurationTask('t4', duration=2)
    t5 = FixedDurationTask('t5', duration=3)
    t6 = FixedDurationTask('t6', duration=2)
    t7 = FixedDurationTask('t7', duration=2)
    t8 = FixedDurationTask('t8', duration=2)
    t9 = FixedDurationTask('t9', duration=3)

    pb.add_task(t1)
    pb.add_task(t1)
    pb.add_tasks([t2, t3, t4, t5, t6, t7, t8, t9])

    assert pb.get_zero_length_tasks() == [t2]

    r1 = Worker('W1')
    r2 = Worker('W2')
    r3 = Worker('W3')
    r4 = AlternativeWorkers([r1, r2, r3], 1)
    t9.add_required_resource(r4)
    pb.add_resources([r1, r2, r3])
    # resources required
    t1.add_required_resource(r1)
    t1.add_required_resource(r2)
    #print(t1.get_assertions())
    for res in pb._resources.values():
        print(res.busy_intervals)
    # constraints
    pb.add_constraint(TasksStartSynced(t1, t2))
    pb.add_constraint(TaskStartAt(t4, 4))
    pb.add_constraint(TaskEndAt(t5, 9))
    pb.add_constraint(TasksEndSynced(t5, t6))

    # precedence
    pb.add_constraint(TaskStartAt(t7, 4))
    #s.add_constraint(TaskDontOverlap(t4, t7))
    c1 = TaskPrecedence(t7, t8, offset=1, kind=PrecedenceType.LAX)
    pb.add_constraint(c1)

    # set optimization
    #pb.add_objective_makespan()
    #pb.add_objective_start_latest()
    #pb.add_objective_start_earliest()
    #pb.add_objective_flowtime()

    solver = SchedulingSolver(pb, verbosity=True)
    solver.solve()

    pb.print_solution()
    pb.render_gantt_ascii()
    pb.render_gantt_matplotlib()
