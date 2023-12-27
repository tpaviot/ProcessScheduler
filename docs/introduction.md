---
title: Introduction
---

# About

ProcessScheduler operates on models written in the Python programming language, offering the flexibility to accommodate a wide range of scheduling requirements for tasks and resources.

To tackle scheduling challenges, ProcessScheduler leverages the power of the Microsoft SMT [Z3 Prover](https://github.com/Z3Prover/z3), an MIT licensed [SMT solver](https://en.wikipedia.org/wiki/Satisfiability_modulo_theories). For those eager to delve deeper into the optimization aspects of the solver, a comprehensive reference can be found in the paper "Bjorner et al. νZ - An Optimizing SMT Solver (2016)." Additionally, an introductory guide to programming with Z3 in Python is available at [z3-py-tutorial](https://ericpony.github.io/z3py-tutorial/guide-examples.htm). It's worth noting that Z3 is the only mandatory dependency for ProcessScheduler.

Furthermore, the tool offers the flexibility to visualize scheduling solutions by rendering them into Gantt charts, which can be exported in common formats such as JPG, PNG, PDF, or SVG. Please note that the optional libraries, matplotlib and plotly, are not pre-installed but can be easily integrated based on your preferences and needs.

# Download/install

Use ``pip`` to install the package and the required dependencies (Z3) on your machine:

``` bash
pip install ProcessScheduler
```
and check the installation from a python3 prompt:


``` py
>>> import processscheduler as ps
```

# Development version

Create a local copy of the `github <https://github.com/tpaviot/ProcessScheduler>`_ repository:

``` bash
git clone https://github.com/tpaviot/ProcessScheduler
```

Then install the development version:

``` bash
cd ProcessScheduler
pip install -e .
```
