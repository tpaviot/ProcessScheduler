Resource Constraints
====================

ProcessScheduler provides a set of ready-to-use resource constraints. They allow expressing common rules such as "the resource A is available only from 8 am to 12" etc.

There are a set of builtin ready-to-use constraints, listed below.

.. note::

	Naming convention: if the class name starts with *Task** then the constraint applies to one single task, if the class name starts with *Tasks** it applies to 2 or more task instances.

- :class:`AllDifferentWorkers`

- :class:`AllSameWorkers`

- :class:`ResourceUnavailable`
