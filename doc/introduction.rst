Introduction
============

ProcessScheduler is a 100% pure python library to compute resource-constrained task schedules. It is distributed under the terms of the `GNU General Public License v3 <https://www.gnu.org/licenses/gpl-3.0.txt>`_ or later.

It is mostly intended to be used in an industrial context (manufacturing, building industry) but can be used for any related scheduling problem. It targets complex problems for which an obvious solution can not be found.

Features
--------

- Task with fixed or variable length, work_amount

- Resource, worker, productivity and cost

- First order logic operators (and/or/xor/not), implication and if/then/else

- Gantt chart rendering using matplotlib

What's inside
-------------

ProcessScheduler processes a model written using the Python programming language. It produces a schedule compliant with a set of constraints over tasks and/or resources. The scheduling problem is solved using the Microsfot `Z3 Prover <https://github.com/Z3Prover/z3>`_, a MIT licensed `SMT solver <https://en.wikipedia.org/wiki/Satisfiability_modulo_theories>`_. A good introduction to programming Z3 with Python can be read at https://ericpony.github.io/z3py-tutorial/guide-examples.htm

Z3 is the only mandatory dependency of ProcessScheduler.

The solution of a scheduling problem can be rendered to a Gantt chart (using the `matplotlib <https://www.matplotlib.org>`_ library, and exported to any of the common jpg, png, pdf or svg formats.

matplotlib is an optional dependency of ProcessScheduler.

Gantt chart examples
--------------------

.. image:: img/example_1.svg
