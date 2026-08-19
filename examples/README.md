# `aigverse` examples

Standalone, runnable scripts that show what `aigverse` can do. Each one declares its own
dependencies inline using [PEP 723](https://peps.python.org/pep-0723/), so
[`uv`](https://docs.astral.sh/uv/) can run it with no setup at all — from this directory:

```console
./abc_recipe_study.py
```

or, equivalently, from the repository root:

```console
uv run examples/abc_recipe_study.py
```

Either form installs `aigverse` from PyPI. To run a script against the checkout you are
sitting in instead — which is what you want when the script uses something not yet
released:

```console
uv run --with-editable . examples/abc_recipe_study.py
```

These scripts are not part of the `aigverse` package and are not shipped in the wheel or
the source distribution.

## `abc_recipe_study.py`

> **Is there one best ABC recipe, or does the right one depend on the design?**

Loads part of the [EPFL benchmark suite](https://github.com/lsils/benchmarks) through
`aigverse.benchmarks` and uses the `aigverse.abc` bridge to ask three questions of it:

1. **Does the order of operations matter?** All 24 orderings of ABC's four atomic
   transformations — `balance`, `rewrite`, `refactor`, `resub` — are run on each design.
   Using the same transformations the same number of times, the order alone moves the
   final AND count by several percent, and the best order is not the same one twice.
2. **Do the two command families trade off?** The classic commands are plotted against
   their `&`-space (ABC9) counterparts on the area–depth plane. On many designs the
   smallest and the shallowest results come from _different_ families, so committing to
   one up front gives up an objective.
3. **Is optimizability predictable?** A cheap structural feature of the input is
   correlated against how much the best script managed to remove. This one is an analysis
   of the data question 2 produced rather than a third run over ABC.

It writes `abc_recipe_study.png`, an `abc_recipe_study.csv` with every raw measurement, and an
`abc_recipe_study_headline.csv` with the summary statistics, and prints its findings as it goes.

Requires an ABC executable — `aigverse` does not ship one. See
[Installation → ABC Integration](https://aigverse.readthedocs.io/en/latest/installation.html#abc-integration).

```console
./abc_recipe_study.py --quick        # four small designs, for a smoke test
./abc_recipe_study.py                # the default ten-design set
./abc_recipe_study.py --all          # the whole EPFL suite, hyp and div included (slow)
./abc_recipe_study.py --verify       # equivalence-check every single result
```

`--verify` aborts the study if any optimization turns out not to be
equivalence-preserving: that would be a bug in ABC or in the bridge, and every number
the study prints rests on it not happening.
