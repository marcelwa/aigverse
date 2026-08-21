# `aigverse` examples

Standalone, runnable scripts that show what `aigverse` can do. Each one declares its own
dependencies inline using [PEP 723](https://peps.python.org/pep-0723/), so
[`uv`](https://docs.astral.sh/uv/) runs it with no setup at all:

```console
uv run examples/abc_recipe_study.py
```

That resolves `aigverse` from PyPI; `uv run --with-editable . examples/abc_recipe_study.py`
runs against the checkout you are sitting in instead.

These scripts are not part of the `aigverse` package and are not shipped in the wheel or
the source distribution.

## `abc_recipe_study.py`

> **Is there one best ABC recipe, or does the right one depend on the design?**

Runs all 24 orderings of rewriting, refactoring, resubstitution and balancing over part of
the EPFL benchmark suite, and weighs ABC's classic command family against its `&`-space
counterpart. Requires an ABC executable — `aigverse` does not ship one.

[ABC Integration → A worked study](https://aigverse.readthedocs.io/en/latest/abc.html#a-worked-study)
describes the experiment, its options, and its outputs.
