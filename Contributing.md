# Contribution guideline

In any contribution, please be as explicit as possible.

## Bug report

Use our [issue tracker](https://github.com/tpaviot/ProcessScheduler/issues) to report bugs.

A *bug* is either: an unexpected result or an unexpected exception raised by Python. It can't be anything else.

- choose an *explicit title*

- the title is not enough:: *always* insert a short and explicit description of what's going wrong

- the description *must* be followed by the shorted python script that reproduces the issue. The script must be self-contained, i.e. it can just be copied/pasted and be executed, no need for additional imports or tweaks

- use the correct markdown directives to insert the python formatted code.

- set the "bug" label to the issue so that it can quickly be identified as a bug.

## Feature request

Use our [issue tracker](https://github.com/tpaviot/ProcessScheduler/issues) to request new features.

- choose an *explicit title*

- insert a short/long/as you want/ description. Be as explicit as possible. Too general descriptions are difficult to read/understand

- you *may* insert a shot python snippet that demonstrates what you would like to achieve using the library, but you can't currently do.

- set the "enhancement" label to the issue.

## Contribute demos or use cases

You're welcome to contribute new jupyter notebooks.

## Contribute core library code

- follow the naming conventions (see below)

- each commit should be described by a short and explicit commit message

- submit a Pull Request (PR)


## Naming Conventions

- method names follow the ```undersocre_convention```

- class names follow the ```CamelCase``` naming convention

- Tasks constraints names start either by Task or Tasks (with an ending 's). If the constraint target one single tasks, use the first one. If it targets two or more tasks, use the second.
