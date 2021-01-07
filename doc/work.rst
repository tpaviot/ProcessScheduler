Task work - resources productivty
=================================

task.work_amount
----------------
Each :class:`Task` instance has a :attr:`work_amount` attribute. It represents the amount of work required by the task to be processed. The attribute type is a positive integer. It is dimensionless but should not be mapped to a duration or any other time dimension parameter.

For example a work_amount can be: for a drilling task, the number of holes to drill; for a maintenance task, the number of screws to remove; for a sotfware testing development task, the number of tests to write etc.

resource.productivity
---------------------
Eache :class:`Worker` assigned to the :class:`Task` has a :attr:`producivity` attribute: it represents the quantity of work the resource can produce per period.

For example, a driller can drill 8 holes per period; a maintenance operator can remove 16 screws per period; a software developer can write 7 tests per period.

The solver ensures that the schedule can fullfil the work_amount requirements, that is to say each task has all the required resources able to produce the total work.
