Introduction
============

ProcessScheduler is intended to be used in an industrial context (manufacturing, building industry, healthcare), and can be used for any related scheduling problem. It targets complex problems for which an obvious solution can not be found.

The following features are provided:

- Task definition with zero, fixed or variable length, work_amount, 

- Resource definition including productivity and cost, assignment of resource(s) to tasks,

- Temporal tasks constraints (precedence, fixed start, fixed end etc.),

- Resource constraints: resource availability,

- First order logic operation between tasks/resources constraints: and/or/xor/not boolean operators, implication, if/then/else

- Gantt chart rendering using matplotlib,

- Export solution to json, SMT problem to SMTLIB.

This document explains how to write the model, run the solver, and finally analyze the solution(s).


.. note::

	ProcessScheduler was inspired by the fantastic `pyschdedule <https://github.com/timnon/pyschedule>`_ library by Tim Nonner. By choosing to rely on an SMT solver rather than a MIP solver such as CBC/Gurobi/SCIP, ProcessScheduler strongly diverges from its predecessor.

What's inside
-------------

ProcessScheduler processes a model written using the Python programming language. It produces a schedule compliant with a set of constraints over tasks and/or resources.

The scheduling problem is solved using the Microsfot `Z3 Prover <https://github.com/Z3Prover/z3>`_, a MIT licensed `SMT solver <https://en.wikipedia.org/wiki/Satisfiability_modulo_theories>`_. A good introduction to programming Z3 with Python can be read at `z3-py-tutorial <https://ericpony.github.io/z3py-tutorial/guide-examples.htm>`_. Z3 is the only mandatory dependency of ProcessScheduler.

The solution of a scheduling problem can be rendered to a Gantt chart using the `matplotlib <https://www.matplotlib.org>`_ library, and exported to any of the common jpg, png, pdf or svg formats. matplotlib is an optional dependency of ProcessScheduler.

Download/install
----------------
Use ``pip`` to install the package on your machine:

.. code-block:: bash

	pip install processscheduler

and check the installation from a python3 prompt:

.. code-block:: bash

	>>> import processscheduler as ps

