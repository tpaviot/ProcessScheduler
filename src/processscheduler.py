# copyright Thomas Paviot

import uuid
import warnings

try:
    from z3 import Solver, Int, Or, unsat, unknown
except ModuleNotFoundError:
    raise ImportError("z3 is a madatory dependency")

class BaseObject:
    def __init__(self, name):
        self._name = name
        self._uid = uuid.uuid4().int

#
# Scenario class definition
#
class Scenario:
    def __init__(self, name):
        self._name = name
        self._tasks = []  # the list of tasks
        self._resources = []  # the list of resources

    def add_task(self, task):
        if not task in self._tasks:
            self._tasks.append(task)
        else:
            warnings.warn('task %s already part of the scenario' % task)

    def get_all_tasks(self):
        return self._tasks

    def get_zero_length_tasks(self):
        return [t for t in self._tasks if isinstance(t, ZeroLengthTask)]

    def get_fixed_length_tasks(self):
        return [t for t in self._tasks if isinstance(t, FixedLengthTask)]

    def get_variable_length_tasks(self):
        return [t for t in self._tasks if isinstance(t, VariableLengthTask)]

    def solve(self, verbosity=True):
        """ verbosity: output console is verbose
        """
        print("Solve the scenario")

#
# Tasks class definition
#
class Task:
    def __init__(self, name):
        self._name = name
        # no default value for task length,
        # must explicitely set by the user
        self._fixed_length = None
        self._fixed_length_value = None
        self._length = None
        self._variable_length = None

    def get_length(self):
        return self._length

    def set_fixed_length(self, length_value):
        if not isinstance(length_value, int):
            raise TypeError("Task fixed length must be an integer.")
        self._fixed_length = True
        self._variable_length = False
        self._length = length_value

    def set_variable_length(self):
        self._fixed_length = False
        self._variable_length = True

    def __repr__(self):
        return self._name

class FixedLengthTask(Task):
    def __init__(self, name, length):
        super().__init__(name)
        self.set_fixed_length(length)

class ZeroLengthTask(Task):
    def __init__(self, name):
        super().__init__(name)
        self.set_fixed_length(0)

class VariableLenghTask(Task):
    def __init__(self, name):
        super().__init__(name)
        self.set_variable_length()

if __name__ == "__main__":
    s = Scenario('essai')

    t1 = FixedLengthTask('t1', length=1)
    assert t1._fixed_length
    assert not t1._variable_length
    assert t1.get_length() == 1

    t2 = ZeroLengthTask('t2')
    assert t2._fixed_length
    assert not t2._variable_length
    t3 = VariableLenghTask('t3')
    assert not t3._fixed_length
    assert t3._variable_length == True

    s.add_task(t1)
    s.add_task(t1)
    s.add_task(t2)
    s.add_task(t3)

    assert s.get_zero_length_tasks() == [t2]
