---
title: About
---

# What's inside?

ProcessScheduler operates on models written in the Python programming language, offering the flexibility to accommodate a wide range of scheduling requirements for tasks and resources.

To tackle scheduling challenges, ProcessScheduler leverages the power of the Microsoft SMT [Z3 Prover](https://github.com/Z3Prover/z3), an MIT licensed [SMT solver](https://en.wikipedia.org/wiki/Satisfiability_modulo_theories). For those eager to delve deeper into the optimization aspects of the solver, a comprehensive reference can be found in the paper:

Bjørner, N., Phan, AD., Fleckenstein, L. (2015). νZ - An Optimizing SMT Solver. In: Baier, C., Tinelli, C. (eds) Tools and Algorithms for the Construction and Analysis of Systems. TACAS 2015. Lecture Notes in Computer Science, vol 9035. Springer, Berlin, Heidelberg. https://doi.org/10.1007/978-3-662-46681-0_14

Additionally, an introductory guide to programming with Z3 in Python is available at [z3-py-tutorial](https://ericpony.github.io/z3py-tutorial/guide-examples.htm). 

It's worth noting that Z3 and pydantic are the **only mandatory dependencies** for ProcessScheduler.

Furthermore, the tool offers the flexibility to visualize scheduling solutions by rendering them into Gantt charts, which can be exported in common formats such as JPG, PNG, PDF, or SVG. Please note that the optional libraries, matplotlib and plotly, are not pre-installed but can be easily integrated based on your preferences and needs.
