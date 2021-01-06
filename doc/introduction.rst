Introduction
============

About
-----

ProcessScheduler is a 100% pure python library to compute resource-constrained task schedules. It is distributed under the terms of the `GNU General Public License v3 <https://www.gnu.org/licenses/gpl-3.0.txt>`_ or later.

It is mostly intended to be used in an industrial context (manufacturing, building industry) but can be used for any related scheduling problem. It targets complex problems for which an obvious solution can not be found.

Features
--------

- f1

- f2

What's inside
-------------

ProcessScheduler processes a model written using the Python programming language. It produces a schedule compliant with the a of constraints over tasks and resources. The scheduling problem is solved using the Microsfot `Z3 Prover <https://github.com/Z3Prover/z3>`_ Z3 Prover, a MIT licensed SMT solver.

The solution of as scheduling problem can be rendered to a Gantt chart (using the `matplotlib <https://www.matplotlib.org>`_ library, and exported to any of the common jpg, png, pdf or svg formats.

.. image:: img/example.svg
