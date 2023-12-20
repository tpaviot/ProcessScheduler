# Customized constraints

If no builtin constraint fit your needs, you can define your own constraint from an assertion expressed in term of [z3-solver](https://github.com/Z3Prover/z3) objects.

This is achieved by using the `ConstraintFromExpression` object. For example:

``` py
ps.ConstraintFromExpression(expression=t1.start == t_2.end + t_4.duration)
```

!!! warning

	A z3 ArithRef relation involved the "==" operator, used for assignement, not comparison. Your linter may complain about this syntax.

You can combine the following variables:

| Object | Variable name | Type | Description |
| ------ | --------- | ---- | ----------- |
| Task | _start | int | task start |
| Task | _end | int | task end |
| Task | _duration | int | can be modified only for VariableDurationTask |
| Task | _scheduled | bool | can be modified only if task as been set as optional |

Please refer to the [z3 solver python API](https://ericpony.github.io/z3py-tutorial/guide-examples.htm) to learn how to create ArithRef objects.
