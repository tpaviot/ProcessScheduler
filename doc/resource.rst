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


Resource assignment
-------------------
Resources are assigned to tasks in two steps:

1. Tell the task that it requires a set of resources to be processed

.. code-block:: python

    assemble_engine = FixedDurationTask('AssembleCarEngine', 10)
    john = Worker('JohnBenis')
    assemble_engine.add_required_resource(john)

.. note::
   You can add any number of required resources to a task, but they all have to be different instances.

2. After the solver has found a solution, resources are assigned to tasks. In the former case, it is obvious that JohnBenis will actually be assigned to the task AssembleCarEngine. There can be cases where it is not possible to guess which resource will be assigned by the solver, especially if many different resources can be used to perform one specific task. In that case, we let the solver decides which resource(s) to assign by defining :ref:`alternative-workers` (see below).

.. _alternative-workers:

Alternative Workers
-------------------
:class:`AlternativeWorkers` is a collection of workers that have the ability to process a task. For example, if 3 drillers are available, and if a drilling task can be processed by any of one of these drillers, it is specified as following:
maybe performed either by:

.. code-block:: python

    drilling_hole = FixedDurationTask('DrillHolePhi10mm', 3)
    driller_1 = Worker('Driller1')
    driller_2 = Worker('Driller2')
    driller_3 = Worker('Driller3')
    drilling_hole.ad_required_resource(AlternativeWorkers([driller_1, driller_2, driller_3], 1))

The last 1 parameters tells the solver to choose 1 resource to perform the task. The number of workers is at least 1, and at most :math:`n`, under the condition that :math:`n` is smaller than the number of workers.
