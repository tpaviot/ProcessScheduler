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

Worker productivity
^^^^^^^^^^^^^^^^^^^
The worker :attr:`productivity` is the quantity of work the worker can produce per period. The default productivity for a worker is :const:`0`.

For example, if two drillers are available, the first one with a producvity of 3 holes per period, the second one with a productivity of 9 holes per period, then will be defined as:

.. code-block:: python

    driller_1 = Worker('Driller1', productivity=3)
    driller_2 = Worker('Driller1', productivity=9)

.. note::

  The workers :const:`productivity` is used by the solver to satisfy the targeted task :attr:`work_amount`.

Worker cost per period
^^^^^^^^^^^^^^^^^^^^^^
The worker :attr:`cost_per_period` is set to :const:`0` by default, and can bet set at the Worker instantiation.

In the case where a Senior developer is charged 750$/hour and a junior dev 250$/hour, then if one period is mapped to one hour:

.. code-block:: python

    dev_1 = Worker('SeniorDeveloper', cost_per_period=750)
    dev_2 = Worker('JuniorDeveloper', cost_per_period=250)

.. note::

  The worker :attr:`cost_per_period` is useful to measure the total cost of a resource/a set of resources/a schedule, or to find the schedule that minimizes the total cost of a resource/a set of resources/ a schedule.

CumulativeWorker
----------------
A cumulative worker can process several tasks in parallel. The maximal number of simultaneous tasks the worker can process is defined by the :attr:`size` parameter.

.. code-block:: python

    # the machine A can process up to 4 tasks at the same time
    machine_A = CumulativeWorker('MachineA', size=4)

Resource assignment
^^^^^^^^^^^^^^^^^^^
Resources are assigned to tasks in two steps:

1. Tell the task that it requires a set of resources to be processed

.. code-block:: python

    assemble_engine = FixedDurationTask('AssembleCarEngine', 10)
    paint_engine = FixedDurationTask('PaintCarEngine', 10)
    
    john = Worker('JohnBenis')
    alice = Worker('AliceParker')
    
    assemble_engine.add_required_resource(john)
    paint_engine.add_required_resources([john, alice])

2. After the solver has found a solution, resources are assigned to tasks. In the case above, it is obvious that JohnBenis will actually be assigned to the task :const:`AssembleCarEngine`. There can be cases where it is not possible to guess which resource will be assigned by the solver, especially if many different resources can be used to perform one specific task. In that case, let the solver decides which resource(s) to assign by defining :ref:`alternative-workers` (see below).

.. _alternative-workers:

Workers selection
-----------------
The :class:`SelectWorkers` class let the solver decide which resource(s) to assign to a task, among a collection of workers that have the ability to process the task. :class:`SelectWorkers` can decide to assign exactly :math:`n` resources, **at most** :math:`n` or **at least** :math:`n`. For example, if 3 drillers are available, and if a drilling task can be processed by any of one of these 3 drillers, it is defined as:

.. code-block:: python

    drilling_hole = FixedDurationTask('DrillHolePhi10mm', duration=10)
    driller_1 = Worker('Driller1')
    driller_2 = Worker('Driller2')
    driller_3 = Worker('Driller3')
    drilling_hole.add_required_resource(SelectWorkers([driller_1, driller_2, driller_3],
                                        nb_workers=1,
                                        kind='exact'))

This tells the solver to select *exactly 1* resource among the list of three workers able to process the task. The :attr:`kind` parameter can take either :const:`'exact'` (default value), :const:`'min'` or :const:`'max'` values.

:const:`nb_workers` can take any integer between 1 (default value) and the number of capable workers in the list. Passing a value out of these bounds will raise an exception.
