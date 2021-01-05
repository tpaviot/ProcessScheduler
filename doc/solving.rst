Scheduling problem solving
==========================

Solving a scheduling problem involves the :class:`SchedulingSolver` class.

A :class:`SchedulingSolver` instance takes a :class:`SchedulingProblem` instance

SchedulingProblem
-----------------

For many users, the data provided by the simple API is enough. In some advanced
cases you may find it necessary to use this more customizable parsing mechanism.

First, define a visitor that implements the :class:`CxxVisitor` protocol. Then
you can create an instance of it and pass it to the :class:`CxxParser`.

.. code-block:: python

    visitor = MyVisitor()
    parser = CxxParser(filename, content, visitor)
    parser.parse()

    # do something with the data collected by the visitor

Your visitor should do something with the data as the various callbacks are
called. See the :class:`SimpleCxxVisitor` for inspiration.

Tasks
-----
The Task object.

Workers
-------
The Worker class.

Constraints
-----------
Constrinas on Tasks and Resources.


