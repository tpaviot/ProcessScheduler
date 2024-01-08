# Indicator Constraints

The Indicator Constraints applies to an indicator.

``` mermaid
classDiagram
  Constraint <|-- IndicatorConstraint
  IndicatorConstraint <|-- IndicatorTarget
  IndicatorConstraint <|-- IndicatorBounds
```

## IndicatorTarget

The `IndicatorTarget` constraint is designed to direct the solver to find a specific value for the indicator. 

``` py
 c1 = ps.IndicatorTarget(indicator=ind_1,
                         value=10)
```

## IndicatorBounds

The `IndicatorBounds` constraint restricts the value of an indicator within a specified range, defined by lower_bound and upper_bound. This constraint is useful for keeping indicator values within acceptable or feasible limits.

``` py
 c1 = ps.IndicatorBounds(indicator=ind_1,
                         lower_bound = 5,
                         upper_bound = 10)
```

`lower_bound` and `upper_bound` are optional parameters that can be set to `None`.

!!! note

    Note: At least one of `lower_bound` or `upper_bound` must be provided.
