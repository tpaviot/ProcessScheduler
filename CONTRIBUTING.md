# Contribution guideline

In any contribution, please be as explicit as possible.

## Bug report

Use our [issue tracker](https://github.com/tpaviot/ProcessScheduler/issues) to report bugs.

A *bug* is either: an unexpected result or an unexpected exception raised by Python. It can't be anything else.

*   choose an *explicit title* that starts with "Bug: " or "Error: "
*   the title is not enough: *always* insert a short and explicit description of what's going wrong,
*   the description *must* be followed by the short python script that reproduces the issue. The script must be self-contained, i.e. it can just be copied/pasted in a text editor and be executed, no need for additional imports or tweaks,
*   use the correct [markdown directives](https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet#code) to insert your syntax highlighted python code,
*   set the "bug" label to the issue, so that the ticket can quickly be identified as a bug.

## Feature request

Use our [issue tracker](https://github.com/tpaviot/ProcessScheduler/issues) to request new features.

A *request feature* has to be understood as "something I would like ProcessScheduler to be able at, but I think it cant't currently do". If you think wrong, or if there is a way to do it in a straightforward manner, then the Feature request entry will be closed after you got an answer 

*   choose an *explicit title* that starts with "Feature request: "
*   insert a short/long/as you want/ description. Be as explicit as possible. Generally speaking, too general descriptions are difficult to read/understand,
*   you *may* insert a shot python snippet that demonstrates what you would like to achieve using the library, and how,
*   set the "enhancement" label to the issue.

## Contribute demos or use cases

You're welcome to contribute new jupyter notebooks.

## Contribute core library code

*   follow the naming conventions (see below),
*   each commit should be described by a short and explicit commit message,
*   use [pylint](https://pypi.org/project/pylint/) to check the code quality and remove common warnings: remove trailing whitespaces, unused imports, unuser variables etc. However, no need to reach a 10/10 mark,
*   submit a Pull Request (PR)

## Naming Conventions

*   function and method names follow the ```lowercase_separated_by_underscores``` convention
*   class names follow the ```UpperCamelCase``` naming convention
*   Tasks constraints names start either by Task or Tasks (with an ending 's). If the constraint target one single tasks, use the first one. If it targets two or more tasks, use the second.
