# Functions

The `Function` class and its derivatives allow representing a mathematical function that can be used for cost or penalty computation.

``` mermaid
classDiagram
  Function <|-- ConstantFunction
  Function <|-- LinearFunction
  Function <|-- PolynomialFunction
class ConstantFunction{
    +int value
}
class LinearFunction{
    +int slope
    +int intercept
}
class PolynomialFunction{
    +List[int] coefficients
}
```

## ConstantFunction

$$ f(x) = K, \forall x \in \mathbb{N}$$

in python

```py
my_function = ps.ConstantFunction(value=10)
```

## LinearFunction

$$ f(x) = s \times t + i, \forall x \in \mathbb{N}$$

in python

```py
my_function = ps.LinearFunction(slope=4, intercept=1)
```

## PolynomialFunction

$$f(x)={a_n}x^n + {a_{n-1}}x^{n-1} + ... + {a_i}x^i + ... + {a_1}x+{a_0}$$

```py
my_function = ps.PolynomialFunction(coefficients=[3, 6, 7])
```