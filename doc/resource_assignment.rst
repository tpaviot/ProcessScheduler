*******************
Resource assignment
*******************

In the context of scheduling, resource assignment is the process of determining which resource or resources should be assigned to a task for its successful processing. ProcessScheduler provides flexible ways to specify resource assignments for tasks, depending on your scheduling needs. A :class:`Worker` instance can process only one task per time period whereas a :class:`CumulativeWorker` can process multiple tasks at the same time.

Single resource assignment
==========================
For assigning a single resource to a task, you can use the following syntax:

.. code-block:: python

    assemble_engine = FixedDurationTask('AssembleCarEngine', duration=10)
    john = Worker('JohnBenis')

    # the AssembleCarEngine can be processed by JohnBenis ONLY
    assemble_engine.add_required_resource(john)


Multiple resources assignment
============================
To assign multiple resources to a single task, you can use the following approach:

.. code-block:: python

    paint_car = FixedDurationTask('PaintCar', duration=13)
    
    john = Worker('JohnBenis')
    alice = Worker('AliceParker')

    # the PaintCar task requires JohnBenis AND AliceParker
    paint_engine.add_required_resources([john, alice])

Alternative resource assignment
===============================
ProcessScheduler introduces the :class:`SelectWorkers` class, which allows the solver to decide which resource or resources to assign to a task from a collection of capable workers. You can specify whether the solver should assign exactly n resources, at most n resources, or at least n resources. Let's consider the following example: 3 drillers are available, a drilling task can be processed by any of one of these 3 drillers. This can be represented as:

.. code-block:: python

    drilling_hole = FixedDurationTask('DrillHolePhi10mm', duration=10)
    driller_1 = Worker('Driller1')
    driller_2 = Worker('Driller2')
    driller_3 = Worker('Driller3')
    # the DrillHolePhi10mm task can be processed by the Driller1 OR the Driller2 OR the Driller 3
    drilling_hole.add_required_resource(SelectWorkers([driller_1,
                                                       driller_2,
                                                       driller_3],
                                        nb_workers_to_select=1,
                                        kind='exact'))

In this case, the solver is instructed to assign exactly one resource from the list of three workers capable of performing the task. The ``kind`` parameter can be set to :const:`'exact'` (default), :const:`'min'`, or :const:`'max'`, depending on your requirements. Additionally, you can specify the number of workers to select with ``nb_workers_to_select``, which can be any integer between 1 (default) and the total number of eligible workers in the list.

These resource assignment options provide flexibility and control over how tasks are allocated to available resources, ensuring efficient scheduling in various use cases.
