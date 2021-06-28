Resource
========

According to the APICS dictionary, a resource is anything that adds value to a product or service in its creation, production, or delivery.

In the context of ProcessScheduler, a resource is anything that is needed by a task to be successfully processed. In a scheduling problem, resources can be human beings, machines, inventories, rooms or beds in an hotel or an hospital, elevator etc.

ProcessScheduler provides the following classes to deal with resources.

Worker
------

A worker is an atomic countable resource. *Atomic* means it cannot be divided into smaller parts. *Countable* means it is discrete and available in a finite number, in a finite time. The :class:`Worker` class can be used to represent machines or humans. A Worker has the ability to process a task, alone or together with other workers/resources.

A Worker is created as follows:

.. code-block:: python

    john = Worker('JohnBenis')

Productivity
------------
The worker :attr:`productivity` is the quantity of work the worker can produce per period. The default productivity for a worker is :const:`0`.

For example, if two drillers are available, the first one with a producvity of 3 holes per period, the second one with a productivity of 9 holes per period, then will be defined as:

.. code-block:: python

    driller_1 = Worker('Driller1', productivity=3)
    driller_2 = Worker('Driller1', productivity=9)

.. note::

  The workers :const:`productivity` is used by the solver to satisfy the targeted task :attr:`work_amount` parameter value.

Cost
----

A cost information can be added to any resource. ProcessScheduler can use this information to compute the total cost of a schedule, the cost for a resource, or optimize the schedule so that the cost is the lowest (minimiation, see the Objective section). There are currently two different ways to define a resource cost:

* the class :class:`ConstantCostPerPeriod`: the cost of the resource is constant over time.

.. code-block:: python

    dev_1 = Worker('SeniorDeveloper', cost=ConstantCostPerPeriod(750))

* the class :class:`PolynomialCostFunction`: the cost of the resource evolves as a polynomial function of time. It is useful to represent, for example, energy cost that is known to be unstable (oil) or time dependent (electricity). The :attr:`cost` parameter takes any python function (i.e. a :attr:`callable` object).

.. code-block:: python

    def quadratic_time_function(t):
        return (t-20)**2 + 154

    cost_function = PolynomialCostFunction(quadratic_time_function)
    dev_1 = Worker('AWorker', cost=cost_function)

The worker :attr:`cost` is set to :const:`None` by default.

The cost function can be plotted using matplotlib, just for information. Just give the plotter the range to be plotted:

.. code-block:: python

    cost_function.plot([0, 200])

.. image:: img/CostQuadraticFunction.svg

.. warning::

    Currently, ProcessScheduler can handle integer numbers only. Then, all the coefficients of the polynomial must be integer numbers. If ever there are floating point numbers, no exception will be raised, but you might face strange results in the cost computation.

.. note::

  The worker :attr:`cost_per_period` is useful to measure the total cost of a resource/a set of resources/a schedule, or to find the schedule that minimizes the total cost of a resource/a set of resources/ a schedule.

CumulativeWorker
----------------
A cumulative worker can process several tasks in parallel. The maximal number of simultaneous tasks the worker can process is defined by the :attr:`size` parameter.

.. code-block:: python

    # the machine A can process up to 4 tasks at the same time
    machine_A = CumulativeWorker('MachineA', size=4)
