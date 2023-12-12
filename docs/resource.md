********
Resource
********

According to the APICS dictionary, a resource is anything that adds value to a product or service in its creation, production, or delivery.

In the context of ProcessScheduler, a resource is anything that is needed by a task to be successfully processed. In a scheduling problem, resources can be human beings, machines, inventories, rooms or beds in an hotel or an hospital, elevator etc.

ProcessScheduler provides the following classes to deal with resources: `Worker`, `CumulativeWorker` 

Worker
======
A Worker is an atomic, countable resource. Being atomic implies that it cannot be further divided into smaller parts, and being countable means it exists in a finite number, available during specific time intervals. The :class:`Worker` class is ideal for representing entities like machines or humans. A :class:`Worker` possesses the capacity to process tasks either individually or in collaboration with other workers or resources.

To create a Worker, you can use the following syntax:

.. code-block:: python

    john = Worker('JohnBenis')

CumulativeWorker
================
On the other hand, a :class:`CumulativeWorker` can simultaneously handle multiple tasks in parallel. The maximum number of tasks that a :class:`CumulativeWorker` can process concurrently is determined by the :attr:`size` parameter.

For example, you can define a CumulativeWorker like this:

.. code-block:: python

    # the machine A can process up to 4 tasks at the same time
    machine_A = CumulativeWorker('MachineA', size=4)

Advanced parameters
===================
Productivity
------------
The :attr:`productivity` attribute of a worker represents the amount of work the worker can complete per period. By default, a worker's :attr:`productivity` is set to 0.

For instance, if you have two drillers, with the first one capable of drilling 3 holes per period and the second one drilling 9 holes per period, you can define them as follows:

.. code-block:: python

    driller_1 = Worker('Driller1', productivity=3)
    driller_2 = Worker('Driller1', productivity=9)

.. note::

  The workers :const:`productivity` is used by the solver to satisfy the targeted task :attr:`work_amount` parameter value.

Cost
----
You can associate cost information with any resource, enabling ProcessScheduler to compute the total cost of a schedule, the cost per resource, or optimize the schedule to minimize costs (see the Objective section for details). There are two ways to define resource costs:

1. Constant Cost Per Period: In this approach, the resource's cost remains constant over time.

.. code-block:: python

    dev_1 = Worker('SeniorDeveloper', cost=ConstantCostPerPeriod(750))

2. Polynomial Cost Function: This method allows you to represent resource costs as a polynomial function of time. It's particularly useful for modeling costs that are volatile (e.g., oil prices) or time-dependent (e.g., electricity costs). The cost parameter accepts any Python callable object.

.. code-block:: python

    def quadratic_time_function(t):
        return (t-20)**2 + 154

    cost_function = PolynomialCostFunction(quadratic_time_function)
    dev_1 = Worker('AWorker', cost=cost_function)

The worker :attr:`cost` is set to :const:`None` by default.

You can visualize the cost function using Matplotlib, which provides insights into how the cost evolves over time:

.. code-block:: python

    cost_function.plot([0, 200])

.. image:: img/CostQuadraticFunction.svg

.. warning::

    Currently, ProcessScheduler can handle integer numbers only. Then, all the coefficients of the polynomial must be integer numbers. If ever there are floating point numbers, no exception will be raised, but you might face strange results in the cost computation.

.. note::

  The worker :attr:`cost_per_period` is useful to measure the total cost of a resource/a set of resources/a schedule, or to find the schedule that minimizes the total cost of a resource/a set of resources/ a schedule.
