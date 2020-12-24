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
    from z3 import (Solver, Int, Or, Sum, unsat, unknown,
                    Optimize, set_param, set_option, ModelRef)
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
        self._name = name
        self._uid = uuid.uuid4().int

    def __hash__(self) -> int:
        return self._uid

    def __repr__(self) -> str:
        return self._name

#
# Resources class definition
#
class _Resource(_NamedUIDObject):
    def __init__(self, name: str):
        super().__init__(name)

class Worker(_Resource):
    """ Class representing an atomic resource, e.g. a machine or a human being
    """
    def __init__(self, name: str) -> None:
        super().__init__(name)

#
# Tasks class definition
#
class Task(_NamedUIDObject):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        # no default value for task length,
        # must explicitly set by the user
        self._fixed_length = None
        self._fixed_length_value = None
        self._length = None
        self._variable_length = None

        # these values will be filled by the solver
        self.start_value = None
        self.end_value = None

        # required resources to perform the task
        self._resources_required = []
        # assigned resource, after the solver is ended
        self._resources_assigned = []

    def add_required_resource(self, resource: _Resource) -> None:
        if not isinstance(resource, _Resource):
            raise TypeError('you must pass a Resource instance')
        self._resources_required.append(resource)

    def get_length(self) -> int:
        return self._length

    def set_fixed_length(self, length_value: int) -> None:
        if not isinstance(length_value, int):
            raise TypeError("Task fixed length must be an integer.")
        self._fixed_length = True
        self._variable_length = False
        self._length = length_value

    def set_variable_length(self) -> None:
        self._fixed_length = False
        self._variable_length = True

    def __repr__(self) -> str:
        return self._name

class FixedLengthTask(Task):
    def __init__(self, name: str, length: int):
        super().__init__(name)
        self.set_fixed_length(length)

class ZeroLengthTask(Task):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.set_fixed_length(0)

class VariableLengthTask(Task):
    def __init__(self, name: str,
                 length_at_least: Optional[int]=0, length_at_most: Optional[int]=None):
        super().__init__(name)
        self.set_variable_length()
        self._length_at_least = length_at_least
        self._length_at_most = length_at_most

#
# Generic _Constraint class definition.
#
class _Constraint(_NamedUIDObject):
    """ abstract _Constraint class """
    def __init__(self):
        super().__init__(name='')

#
# Task constraints
#
class _TaskConstraint(_Constraint):
    pass

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
        self._task_before = task_before
        self._task_after = task_after
        self._offset = offset
        self._kind = kind

    def __repr__(self):
        comp_chars = {PrecedenceType.LAX:'<=',
                      PrecedenceType.STRICT:'<',
                      PrecedenceType.TIGHT: '==',
                     }
        return "Prcedence constraint: %s %s %s" % (self._task_before,
                                                   comp_chars[self._kind],
                                                   self._task_after)

class TaskStartSynced(_TaskConstraint):
    """ Two task that must start at the same time """
    def __init__(self, task_1: Task, task_2: Task) -> None:
        super().__init__()
        self._task_1 = task_1
        self._task_2 = task_2

class TaskEndSynced(_TaskConstraint):
    """ Two tasks that must complete at the same time """
    def __init__(self, task_1: Task, task_2: Task) -> None:
        super().__init__()
        self._task_1 = task_1
        self._task_2 = task_2

class TaskStartAt(_TaskConstraint):
    """ One task must start at the desired time """
    def __init__(self, task: Task, value: int) -> None:
        super().__init__()
        self._task = task
        self._value = value

class TaskEndAt(_TaskConstraint):
    """ On task must complete at the desired time """
    def __init__(self, task: Task, value: int) -> None:
        super().__init__()
        self._task = task
        self._value = value

class TaskDontOverlap(_TaskConstraint):
    """ TODO two tasks must not overlap, i.e. one needs to be completed before
    the other can be processed """
    def __init__(self, task_1: Task, task_2: Task) -> None:
        super().__init__()
        self._task_1 = task_1
        self._task_2 = task_2

class TaskExclusive(_TaskConstraint):
    """ TODO One task that needs to be processed alone, that is to say no other
    task should be scheduled as soon as it started until it is completed """
    def __init__(self, task: Task) -> None:
        super().__init__()
        self._task = task

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
        self._horizon = horizon
        # the list of tasks
        self._tasks = {} # type: Dict[str, Task]
        # the list of resources
        self._resources = [] # type: List[_Resource]
        # the constraints are defined in the scenario
        self._constraints = [] # type: List[_Constraint]
        # multiple objectives is possible
        self._objectives = [] # type: List[ObjectiveType]
        # the solution
        self._solution = None # type: ModelRef

    def set_solution(self, solution: ModelRef) -> None:
        """ for each tash, set the resource, start and length values """
        self._solution = solution

        for z3_variable in self._solution.decls():
            var_name = z3_variable.name()
            var_value = self._solution[z3_variable]

            # set the value
            if '_task_start' in var_name:
                task_name = var_name.split('_task_start')[0]
                self._tasks[task_name].start_value = var_value.as_long()
            if '_task_length' in var_name:
                task_name = var_name.split('_task_length')[0]
                self._tasks[task_name]._length = var_value.as_long()
            if var_name == 'horizon':
                self._horizon = var_value.as_long()

    def add_task(self, task: Task) -> bool:
        """ add a single task to the problem """
        task_name = task._name
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

    def get_tasks(self) -> List[Task]:
        """ return the list of tasks """
        return self._tasks.values()

    def get_zero_length_tasks(self)-> List[ZeroLengthTask]:
        return [t for t in self.get_tasks() if isinstance(t, ZeroLengthTask)]

    def get_fixed_length_tasks(self) -> List[FixedLengthTask]:
        return [t for t in self.get_tasks() if isinstance(t, FixedLengthTask)]

    def get_variable_length_tasks(self) -> List[VariableLengthTask]:
        return [t for t in self.get_tasks() if isinstance(t, VariableLengthTask)]

    def add_constraint(self, constraint: _Constraint) -> bool:
        if not constraint in self._constraints:
            self._constraints.append(constraint)
            return True
        warnings.warn("Resource already added.")
        return False

    def add_objective_makespan(self) -> None:
        """ makespan objective
        """
        self._objectives.append(ObjectiveType.MAKESPAN)

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
            warnings.warn("No solution.")
            return False
        for task in self._tasks.values():
            task_start = task.start_value
            task_end = task.start_value + task._length
            ress = task._resources_required
            print(task._name, ":", ress, task_start, task_end)
        return True

    def render_gantt_ascii(self) -> bool:
        """ displays an ascii gantt chart """
        if self._solution is None:
            warnings.warn("No solution.")
            return False
        print("Ascii Gantt solution")
        for task in self._tasks.values():
            task_line = '|' + task._name[:4] + '|' + ' ' * task.start_value + task._length * '#'
            print(task_line)
        print('-' * (self._horizon + 4))
        return True

    def render_gantt_matplotlib(self, figsize=(9,6), savefig=False) -> bool:
        """ generate a gantt diagram using matplotlib.
        Inspired by
        https://www.geeksforgeeks.org/python-basic-gantt-chart-using-matplotlib/
        """
        if self._solution is None:
            warnings.warn("No solution.")
            return False
        try:
            import matplotlib.pyplot as plt
            from matplotlib.colors import LinearSegmentedColormap
        except ImportError:
            warnings.warn('matplotlib not installed')
            return False
        fig, gantt = plt.subplots(1, 1, figsize=figsize)
        gantt.set_title("Task schedule - %s" % self._name)
        gantt.set_xlim(0, self._horizon)
        gantt.set_xticks(range(self._horizon + 1))
        # Setting labels for x-axis and y-axis
        gantt.set_xlabel('Periods', fontsize=12)
        gantt.set_ylabel('Tasks', fontsize=12)
        nbr_tasks = len(self.get_tasks())
        cmap = LinearSegmentedColormap.from_list('custom blue', ['#ffff00','#002266'], N=nbr_tasks * 2)
        gantt.set_ylim(0, 2 * nbr_tasks)
        gantt.set_yticks(range(1, 2 * nbr_tasks, 2))
        gantt.set_yticklabels(map(str, self.get_tasks()))
        # create a bar for each task
        for i, task in enumerate(self.get_tasks()):
            start = task.start_value
            length = task._length
            gantt.broken_barh([(start, length)], (i * 2, 2), facecolors=cmap(i))
            # build the bar text string
            text = "%s" % task
            if task._resources_required:
                text += "(" + "".join("%s" % c for c in task._resources_required) + ")"
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
    def __init__(self, problem, verbosity: Optional[bool]=True, max_time: Optional[int]=60):
        """ Scheduling Solver

        verbosity: True or False
        max_time: time in seconds
        """
        self._problem = problem

        self._verbosity = verbosity
        if verbosity:
            set_option("verbose", 2)

        # a dictionary to store all start, length and end variables for all tasks
        self._task_starts_IntVar = {} # type: Dict[Task, Int]
        self._task_ends_IntVar = {} # type: Dict[Task, Int]
        self._task_length_IntVar = {} # type: Dict[Task, Int]

        self._resource_busy_IntVar = {} # type: Dict[Task, Int]

        # by default, no optimization. This flag is set to True whenever any of the
        # add_objective_* is called
        self._optimization = False

        # define the horizon variable
        self._horizon = Int('horizon')

        # set timeout
        set_option("timeout", max_time * 1000)  # in ms

        # create the solver
        if self._problem._objectives:
            self.set_optimization()
        if not self._optimization:
            self._solver = Solver()  # SMT without optimization
            if self._problem._horizon is not None:
                self._solver.add(self._horizon == self._problem._horizon)
            else:
                if self._verbosity:
                    warnings.warn('Horizon not set')
        else:  # optimization enabled
            self._solver = Optimize()

        if self._verbosity:
            print("Solver:", type(self._solver))

    def prepare_model_before_resolution(self):
        """ the resolution worklow starts here. This method has to be called
        before solve is called. """
        self.set_random_seed_fixed()
        self.create_tasks_variables()
        # constraints
        self.process_task_constraints()
        self.process_resource_requirements()
        self.process_resource_contraints()
        # finally, the objectives
        self.create_objectives()

    def set_random_seed_fixed(self) -> None:
        """ set the random seed to a constant value, each time the
        solver is called, the solution will be the same
        """
        set_param("smt.random_seed", 1234)

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
        for obj in self._problem._objectives:
            if obj == ObjectiveType.MAKESPAN:
                # look for the minimum horizon, i.e. the shortest
                # time horizon to complete all tasks
                self._solver.minimize(self._horizon)
            elif obj == ObjectiveType.LATEST:
                # schedule all at the latest time according
                # to a given horizon
                mini = Int('SmallestStartTime')
                tasks_start = self._task_starts_IntVar.values()
                self._solver.add(Or([mini == tsk_st for tsk_st in tasks_start]))
                for tsk_st in tasks_start:
                    self._solver.add(mini <= tsk_st)
                self._solver.maximize(mini)
            elif obj == ObjectiveType.FLOWTIME:
                # minimum flowtime, i.e. minimize the sum of all end times
                flowtime = Int('FlowTime')
                self._solver.add(flowtime == Sum(list(self._task_ends_IntVar.values())))
                self._solver.minimize(flowtime)
            elif obj == ObjectiveType.EARLIEST:
                # minimize the greates start time
                maxi = Int('GreatestStartTime')
                tasks_start = self._task_starts_IntVar.values()
                self._solver.add(Or([maxi == tsk_st for tsk_st in tasks_start]))
                for tsk_st in tasks_start:
                    self._solver.add(maxi >= tsk_st)
                self._solver.minimize(maxi)

    def create_tasks_variables(self) -> None:
        """ for each task, create task_start (for all tasks) and task_length """
        for task in self._problem.get_tasks():
            task_name = "%s" % task
            # create a variable for the task start
            task_start = Int(task_name + "_task_start")
            task_end = Int(task_name + "_task_end")
            # add the constraint start >= 0
            self._solver.add(task_start >= 0)
            self._solver.add(task_end >= 0)
            if isinstance(task, ZeroLengthTask):
                self._solver.add(task_start == task_end)
            # for fixed length tasks only
            if isinstance(task, FixedLengthTask):
                self._solver.add(task_end == task_start + task._length)
                self._solver.add(task_end <= self._horizon)
            if isinstance(task, VariableLengthTask):
                task_length = Int(task_name + "_task_length")
                # task length should be positive
                self._solver.add(task_length >= 0)
                self._solver.add(task_end == task_start + task_length)
                self._solver.add(task_end <= self._horizon)
                self._solver.add(task_length >= task._length_at_least)
                if task._length_at_most is not None:
                    self._solver.add(task_length <= task._length_at_most)
                self._task_length_IntVar[task] = task_length
            # store the start and end variables in the related dictionary
            self._task_starts_IntVar[task] = task_start
            self._task_ends_IntVar[task] = task_end

    def process_task_constraints(self) -> None:
        """ process task constraints """
        for constraint in self._problem._constraints:
            # StartsSynced
            if isinstance(constraint, TaskStartSynced):
                # add the constraint that both start times must be equal
                task_1_start_variable = self._task_starts_IntVar[constraint._task_1]
                task_2_start_variable = self._task_starts_IntVar[constraint._task_2]
                self._solver.add(task_1_start_variable == task_2_start_variable)
            # TaskEndSynced
            elif isinstance(constraint, TaskEndSynced):
                task_1 = constraint._task_1
                task_2 = constraint._task_2
                task_1_start_variable = self._task_starts_IntVar[task_1]
                task_2_start_variable = self._task_starts_IntVar[task_2]
                if task_1 in self._task_length_IntVar:  # it's a VariableLengthTask
                    task_length_1 = self._task_length_IntVar[task_1]
                else:  # just an integer, FixedVariableLength
                    task_length_1 = task_1._length
                if task_2 in self._task_length_IntVar:  # it's a VariableLengthTask
                    task_length_2 = self._task_length_IntVar[task_2]
                else:  # just an integer, FixedVariableLength
                    task_length_2 = task_2._length
                task_1_end = task_1_start_variable + task_length_1
                task_2_end = task_2_start_variable + task_length_2
                self._solver.add(task_1_end == task_2_end)
            # TaskStartAt
            elif isinstance(constraint, TaskStartAt):
                task_start_variable = self._task_starts_IntVar[constraint._task]
                value = constraint._value
                self._solver.add(task_start_variable == value)
            # TaskEndAt
            elif isinstance(constraint, TaskEndAt):
                task = constraint._task
                task_start_variable = self._task_starts_IntVar[task]
                if task in self._task_length_IntVar:  # it's a VariableLengthTask
                    task_length = self._task_length_IntVar[task]
                else:  # just an integer, FixedVariableLength
                    task_length = task._length
                value = constraint._value
                self._solver.add(task_start_variable + task_length == value)
            # TaskPrecedence
            elif isinstance(constraint, TaskPrecedence):
                task_1 = constraint._task_before
                task_2 = constraint._task_after
                task_1_start_variable = self._task_starts_IntVar[task_1]
                task_2_start_variable = self._task_starts_IntVar[task_2]
                if task_1 in self._task_length_IntVar:  # it's a VariableLengthTask
                    task_1_length = self._task_length_IntVar[task_1]
                else:  # just an integer, FixedVariableLength
                    task_1_length = task_1._length
                if constraint._offset == 0:  # just to avoid constrains like x + 0 < y
                    task_1_end = task_1_start_variable + task_1_length
                else:
                    task_1_end = task_1_start_variable + task_1_length + constraint._offset
                if constraint._kind == PrecedenceType.LAX:
                    constraint_expr = task_1_end <= task_2_start_variable
                elif constraint._kind == PrecedenceType.STRICT:
                    constraint_expr = task_1_end < task_2_start_variable
                elif constraint._kind == PrecedenceType.TIGHT:
                    constraint_expr = task_1_end == task_2_start_variable
                self._solver.add(constraint_expr)

    def process_resource_contraints(self) -> None:
        """ process resource constraints """
        pass  # TODO

    def process_resource_requirements(self) -> None:
        # create variables for busy tasks
        for task in self._problem.get_tasks():
            task_name = task._name
            # the start variable for the task
            task_start = self._task_starts_IntVar[task]
            # the length variable (or int) for the task
            if task in self._task_length_IntVar:  # it's a VariableLengthTask
                task_length = self._task_length_IntVar[task]
            else:  # just an integer, FixedVariableLength
                task_length = task._length
            # then loop over required resources
            for resource in task._resources_required:
                resource_name = resource._name
                # create two variables for this resource
                resource_busy_start = Int('%s_busy_%s_start' % (resource_name, task_name))
                resource_busy_end = Int('%s_busy_%s_end' % (resource_name, task_name))
                # add a constraint about resource occupation
                #
                # These two constraints representthe fact that this resource
                # is actually used by the task
                #
                # the resource occupation
                self._solver.add(resource_busy_start + task_length == resource_busy_end)
                # sync task and resource occupation
                self._solver.add(resource_busy_start ==  task_start)

                # store the resource variables
                # Note that a resource may be busy due to several different tasks
                if resource not in self._resource_busy_IntVar:
                    self._resource_busy_IntVar[resource] = [(resource_busy_start, resource_busy_end)]
                else:
                    self._resource_busy_IntVar[resource].append((resource_busy_start, resource_busy_end))
        # when done, tell that these intervals cannot overlap
        # We just tell that, when we take two tasks of busy resource, one may be before
        # or after the other.
        # let's take an example:
        # lets T1=(start1, end1) and T2 =(start2, end2)
        # then start2 >= end1 OR start1 >= end2
        # we must do that for each combination of two tasks in the resource_IntVar list.
        # for that, use the itertools.combination class
        # example of use
        # list(itertools.combinations(['T1', 'T2', 'T3'], r=2))
        for res in self._resource_busy_IntVar:
            tasks = self._resource_busy_IntVar[res]
            number_of_tasks = len(tasks)
            if number_of_tasks <= 1:  # no possible overlap, nothing to do
                continue
            # get all pairs combination
            combinations = list(itertools.combinations(range(number_of_tasks), r=2))
            for comb in combinations:
                i, j = comb
                start_task_i, end_task_i = tasks[i]
                start_task_j, end_task_j = tasks[j]
                # add the Or constraint
                self._solver.add(Or(start_task_i >= end_task_j, start_task_j >= end_task_i))

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
        self.prepare_model_before_resolution()
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

        # propagate the result to the scenario
        self._problem.set_solution(solution)

        return True

if __name__ == "__main__":
    s = SchedulingProblem('tst-problem')#, horizon=30)

    t1 = FixedLengthTask('t1', length=1)
    assert t1._fixed_length
    assert not t1._variable_length
    assert t1.get_length() == 1

    t2 = ZeroLengthTask('t2')
    assert t2._fixed_length
    assert not t2._variable_length

    t3 = VariableLengthTask('t3')
    assert not t3._fixed_length
    assert t3._variable_length

    t4 = FixedLengthTask('t4', length=2)
    t5 = FixedLengthTask('t5', length=3)
    t6 = FixedLengthTask('t6', length=2)
    t7 = FixedLengthTask('t7', length=2)
    t8 = FixedLengthTask('t8', length=2)

    s.add_task(t1)
    s.add_task(t1)
    s.add_tasks([t2, t3, t4, t5, t6, t7, t8])

    assert s.get_zero_length_tasks() == [t2]

    r1 = Worker('R1')
    r2 = Worker('R2')

    # resources required
    t1.add_required_resource(r1)
    t2.add_required_resource(r2)

    # constraints
    s.add_constraint(TaskStartSynced(t1, t2))
    s.add_constraint(TaskStartAt(t4, 4))
    s.add_constraint(TaskEndAt(t5, 9))
    s.add_constraint(TaskEndSynced(t5, t6))

    # precedence
    s.add_constraint(TaskStartAt(t7, 4))
    c1 = TaskPrecedence(t7, t8, offset=1, kind=PrecedenceType.LAX)
    s.add_constraint(c1)

    # set optimization
    #s.add_objective_makespan()
    #s.add_objective_start_latest()
    #s.add_objective_start_earliest()
    #s.add_objective_flowtime()

    solver = SchedulingSolver(s, verbosity=False)
    solver.solve()

    s.print_solution()
    s.render_gantt_ascii()
    s.render_gantt_matplotlib()
