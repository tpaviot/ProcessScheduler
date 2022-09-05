Resource assignment
===================

The solver decides which resource(s) should be assigned for a task to be processed. A :class:`Worker` instance can process only one task per time period whereas a :class:`CumulativeWorker` can process different tasks at the same time.

Single resource assignment
^^^^^^^^^^^^^^^^^^^^^^^^^^
Tell the task that it requires a set of resources to be processed

.. code-block:: python

    assemble_engine = FixedDurationTask('AssembleCarEngine', duration=10)
    john = Worker('JohnBenis')

    # the AssembleCarEngine can be processed by JohnBenis ONLY
    assemble_engine.add_required_resource(john)


Multiple resources assignment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To constraint different resources to process one single task.

.. code-block:: python

    paint_car = FixedDurationTask('PaintCar', duration=13)
    
    john = Worker('JohnBenis')
    alice = Worker('AliceParker')

    # the PaintCar task requires JohnBenis AND AliceParker
    paint_engine.add_required_resources([john, alice])

Alternative resource assignment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The :class:`SelectWorkers` class let the solver decide which resource(s) to assign to a task, among a collection of workers that have the ability to process the task. The solver can decide to assign exactly :math:`n` resources, **at most** :math:`n` or **at least** :math:`n`. For example, if 3 drillers are available, and if a drilling task can be processed by any of one of these 3 drillers, it is defined as:

.. code-block:: python

    drilling_hole = FixedDurationTask('DrillHolePhi10mm', duration=10)
    driller_1 = Worker('Driller1')
    driller_2 = Worker('Driller2')
    driller_3 = Worker('Driller3')
    # the DrillHolePhi10mm task can be processed by the Driller1 OR the Driller2 OR the Driller 3
    drilling_hole.add_required_resource(SelectWorkers([driller_1, driller_2, driller_3],
                                        nb_workers_to_select=1,
                                        kind='exact'))

This tells the solver to assign *exactly 1* resource among the list of the three workers able to process the task. The :attr:`kind` parameter can take either :const:`'exact'` (default value), :const:`'min'` or :const:`'max'` values.

:const:`nb_workers` can take any integer between 1 (default value) and the number of capable workers from the list.
