Resource Constraints
====================

ProcessScheduler provides a set of ready-to-use resource constraints. They allow expressing common rules such as "the resource A is available only from 8 am to 12" etc.

There are a set of builtin ready-to-use constraints, listed below.

- :class:`AllDifferentWorkers`

A :class:`AllDifferentWorkers` constraint applies to two :class:`SelectWorkers` instances. It constraints the solver to select different workers for each :class:`SelectWorkers`. For instance:

.. code-block:: python

    s1 = ps.SelectWorkers([worker_1, worker_2])
    s2 = ps.SelectWorkers([worker_1, worker_2])

could lead the solver to select worker_1 in both cases. Adding the following line:

.. code-block:: python

    cs = ps.AllDifferentWorkers(s1, s2)

let the solver selects the worker_1 for s1 and worker_2 for s2 or the opposite, worker_2 for s1 and worker_1 for s2. The cases where worker_1 is selected by both s1 and s2 or worker_2by selected by both s1 and s2 are impossible.

- :class:`AllSameWorkers`

A :class:`AllSameWorkers` constraint applies to two :class:`SelectWorkers` instances. It constraints the solver to ensure both different :class:`SelectWorkers` instances select the same worker. For example:

.. code-block:: python

    s1 = ps.SelectWorkers([worker_1, worker_2])
    s2 = ps.SelectWorkers([worker_1, worker_2])

could lead the solver to select worker_1 for s1 and worker_2 for s2. Adding the following line:

.. code-block:: python

    cs = ps.AllSametWorkers(s1, s2)

ensures either worker_1 is selected by both s1 and s2, or worker_2 is selected by both s1 and s2.

- :class:`ResourceUnavailable`

A :class:`ResourceUnavailable` applies to a resource and prevent the solver to schedule this resource if it is not available. This class takes a list of intervals:

.. code-block:: python

    worker_1 = ps.Worker('Sylvia')
    ca = ps.ResourceUnavailable(worker_1, [(1,2), (6,8)])

The :const:`ca` instance constraints the resource to be unavailable for 1 period between 1 and 2 instants, and for 2 periods between instants 6 and 8.

