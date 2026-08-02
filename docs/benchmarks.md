---
file_format: mystnb
kernelspec:
  name: python3
---

# Benchmarks

Experiments need circuits. `aigverse` can fetch standard benchmark suites on demand and
cache them locally, so a script names a benchmark instead of carrying a downloader and a
checked-in copy of the data.

Nothing is bundled with `aigverse` and nothing is downloaded at import time — the first
call that needs a file fetches it.

## The EPFL suite

The [EPFL combinational benchmark suite](https://github.com/lsils/benchmarks) is the
standard yardstick for logic synthesis: twenty circuits split into ten _arithmetic_ and
ten _random/control_ designs.

```{code-cell} ipython3
from aigverse.benchmarks import epfl, epfl_names

print(epfl_names("arithmetic"))
print(epfl_names("random_control"))
```

Loading one gives a {py:class}`~aigverse.networks.NamedAig`, which is an
{py:class}`~aigverse.networks.Aig` that kept the input and output names from the AIGER
symbol table, so the names come along at no cost:

```python
from aigverse.networks import DepthAig

aig = epfl("ctrl")
print(f"{aig.num_pis} inputs, {aig.num_pos} outputs")
print(f"{aig.num_gates} AND gates, {DepthAig(aig).num_levels} levels")
```

```text
7 inputs, 26 outputs
174 AND gates, 10 levels
```

Sweeping part of the suite is then a loop:

```python
for name in epfl_names("random_control"):
    design = epfl(name)
    print(
        f"{name:12s} {design.num_gates:6d} gates  {DepthAig(design).num_levels:4d} levels"
    )
```

:::{note}
Unusually for these docs, the examples that load a circuit are **not** executed at build
time. Everything else here is, and normally that is what keeps the examples honest — but
an executed `epfl(...)` would make every documentation build depend on `github.com` being
reachable and prompt, and a stalled download of a one-kilobyte file is enough to fail the
build outright.

The API these examples show is covered end-to-end by the test suite instead, including a
job that performs real downloads, which is the right place for that guarantee.
:::

:::{warning}
The suite spans four orders of magnitude. `ctrl` has 174 AND gates; `hyp` has over
214,000 and is a several-hundred-megabyte proposition once loaded and optimized. Start
small.
:::

If only the AIGER file is wanted — to hand to another tool, say — use
{py:func}`~aigverse.benchmarks.epfl_path`, which downloads and returns the path without
parsing.

## Revisions

The benchmark repository is versioned by commit rather than by release, and its circuits
do change. The loader therefore defaults to a **pinned commit** rather than to `master`,
so that two people running the same code get the same circuits.

That is not only about reproducibility across machines. A moving default would not even be
self-consistent: whoever already had a warm cache would keep the old circuit forever, while
a newcomer downloaded the new one, and the two would silently disagree.

Ask for something else when you want it:

```python
aig = epfl("adder", revision="master")  # whatever is current
aig = epfl("adder", revision="9e5d0ec")  # some other commit
```

Each revision is cached separately, so switching between them does not re-download
anything you already have. The pin itself is kept current by Renovate.

## Where downloads are cached

By default, benchmarks land in a per-user cache directory — `~/.cache/aigverse/benchmarks`
on Linux, `~/Library/Caches/aigverse/benchmarks` on macOS, and `%LOCALAPPDATA%` on
Windows. Notably _not_ the working directory, so a sweep run inside a repository checkout
does not scatter circuits through it.

Override it in whichever way suits:

```python
from aigverse.benchmarks import set_benchmark_cache

set_benchmark_cache("/scratch/benchmarks")  # process-wide
aig = epfl("adder", cache_dir="/tmp/here")  # this call only
```

or set `AIGVERSE_BENCHMARK_CACHE` in the environment. The precedence is
{py:func}`~aigverse.benchmarks.set_benchmark_cache`, then the environment variable, then
the platform default.
