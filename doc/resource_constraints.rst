Resource Constraints
====================

ProcessScheduler provides a set of ready-to-use resource constraints. They allow expressing common rules such as "the resource A is available only from 8 am to 12" etc. There are a set of builtin ready-to-use constraints, listed below.

Capacity
--------
The :class:`ResourceCapacity` constraint can be used to restrict the number of tasks which are executed during  certain time periods.

This constraint applies to one resource, whether it is a single worker or a cumulative worker. It takes the time periods as a python dictionary composed of time intervals (the keys) and an integer number (the capacity). The :attr:`kind` parameter allows to define which kind of restriction applies to the resource: exact, atmost (default value) or at least.

.. highlight:: python

.. code-block:: python

    c1 = ps.ResourceCapacity(worker_1, {(0, 6): 2})

In the previous example, the resource :attr:`worker_1` cannot be scheduled into more than 2 timeslots between instants 0 and 6.

Any number of time intervals can be passed to this class, just extend the timeslots dictionary, e.g.:

.. code-block:: python

    c1 = ps.ResourceCapacity(worker_1, {(0, 6): 2,
                                        (19, 21): 6})

The **restriction** of the :class:`CapacityConstraint` is not necessarily a *limitation*. Indeed you can specify that the integer number is actually an exact of minimal value to target. For example, if we need the resource :attr:`worker_1` to be scheduled **at least** into three time slots between instants 0 and 10, then:

.. code-block:: python

    c1 = ps.ResourceCapacity(worker_1, {(0, 10): 3, kind='atleast'}

ResourceUnavailable
-------------------

A :class:`ResourceUnavailable` applies to a resource and prevent the solver to schedule this resource during certain time periods. This class takes a list of intervals:

.. code-block:: python

    worker_1 = ps.Worker('Sylvia')
    ca = ps.ResourceUnavailable(worker_1, [(1,2), (6,8)])

The :const:`ca` instance constraints the resource to be unavailable for 1 period between 1 and 2 instants, and for 2 periods between instants 6 and 8.

.. note::

    This constrint is a special case for the :class:`ResourceCapacity`. The same could be achieved using

AllDifferentWorkers
-------------------

A :class:`AllDifferentWorkers` constraint applies to two :class:`SelectWorkers` instances. It constraints the solver to select different workers for each :class:`SelectWorkers`. For instance:

.. code-block:: python

    s1 = ps.SelectWorkers([worker_1, worker_2])
    s2 = ps.SelectWorkers([worker_1, worker_2])

could lead the solver to select worker_1 in both cases. Adding the following line:

.. code-block:: python

    cs = ps.AllDifferentWorkers(s1, s2)

let the solver selects the worker_1 for s1 and worker_2 for s2 or the opposite, worker_2 for s1 and worker_1 for s2. The cases where worker_1 is selected by both s1 and s2 or worker_2by selected by both s1 and s2 are impossible.

AllSameWorkers
--------------

A :class:`AllSameWorkers` constraint applies to two :class:`SelectWorkers` instances. It constraints the solver to ensure both different :class:`SelectWorkers` instances select the same worker. For example:

.. code-block:: python

    s1 = ps.SelectWorkers([worker_1, worker_2])
    s2 = ps.SelectWorkers([worker_1, worker_2])

could lead the solver to select worker_1 for s1 and worker_2 for s2. Adding the following line:

.. code-block:: python

    cs = ps.AllSametWorkers(s1, s2)

ensures either worker_1 is selected by both s1 and s2, or worker_2 is selected by both s1 and s2.
