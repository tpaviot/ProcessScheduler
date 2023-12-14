# First order logic constraints

Builtin constraints may not be sufficient to cover the large number of use-cases user may encounter. Rather than extending more and more the builtin constraints, ProcessScheduler lets you build your own constraints using logical operators, implications and if-then-else statement between builtin constraints or class attributes.

## Boolean operators


The inheritance class diagram is the following:
``` mermaid
classDiagram
  Constraint <|-- And
  Constraint <|-- Or
  Constraint <|-- Xor
  Constraint <|-- Not
class And{
    +List[Constraint] list_of_constraints
  }
class Or{
    +List[Constraint] list_of_constraints
}
class Xor{
    +Constraint constraint_1
    +Constraint constraint_2
}
class Not{
    +Constraint constraint
}
```
Logical operators and ($\wedge$), or ($\lor$), xor ($\oplus$), not ($\lnot$) are provided through the `And`, `Or`, `Xor` and `Not` classes.

Using builtin task constraints in combination with logical operators enables a rich expressivity. For example, imagine that you need a task `t_1` to NOT start at time 3. At a first glance, you can expect a `TaskDontStartAt` to fit your needs, but it is not available from the builtin constraints library. The solution is to express this constraint in terms of first order logic, and state that you need the rule:

$$\lnot TaskStartAt(t_1, 3)$$

In python, this gives:

```
Not(constraint=TaskStartAt(task=t_1, value=3)
```

## Logical Implication


The logical implication ($\implies$) is wrapped by the `Implies` class. It takes two parameters: a condition, that has to be `True` or `False`, and a list of assertions that are to be implied if the condition is `True`.

``` mermaid
classDiagram
  Constraint <|-- Implies
class Implies{
    +bool condition
    +List[Constraint] list_of_constraints
  }
```
For example, the following logical implication:

$$t_2.start = 4 \implies TasksEndSynced(t_3, t_4)$$

is written in Python:

``` py
impl = Implies(condition=t_2._start == 4,
               list_of_constraints=[TasksEndSynced(task_1=t_3,task_2=t_4)]
```

## Conditionnal expression

``` mermaid
classDiagram
  Constraint <|-- Implies
class Implies{
    +bool condition
    +List[Constraint] then_list_of_constraints
    +List[Constraint] else_list_of_constraints
  }
```

Finally, an if/then/else statement is available through the class `IfThenElse` which takes 3 parameters: a condition and two lists of assertions that apply whether the condition is `True` or `False`.

``` py
IfThenElse(condition=t_2.start == 4,
           then_list_of_constraints=[TasksEndSynced(task_1=t_3, task_2=t_4)],
           else_list_of_constraints=[TasksStartSynced(task_1=t_3, task_2=t_4)])
```

## Nested first order logic operations

All of these statements can be nested to express an infinite variety of use cases. For example, if you do **not** want the task to start at 3, **and** also you do **not** want it to end at 9, then the rule to implement is:

$$\lnot TaskStartAt(t_1,3) \wedge \lnot TaskEndsAt(t_1, 9)$$

In python:

``` py
And(list_of_constraints=[Not(constraint=TaskStartAt(task=t_1, value=3)),
                         Not(constraint=TaskEndAt(task=t_1, value=9))])
```

In a more general cas, those logical functions can take both task constraints or tasks attributes. For example, the following assertion is possible :
