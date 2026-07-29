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

```{code-cell} ipython3
from aigverse.networks import DepthAig

aig = epfl("ctrl")
print(f"{aig.num_pis} inputs, {aig.num_pos} outputs")
print(f"{aig.num_gates} AND gates, {DepthAig(aig).num_levels} levels")
```

Sweeping the small end of the suite is then a loop:

```{code-cell} ipython3
for name in ("ctrl", "router", "int2float", "dec"):
    design = epfl(name)
    print(f"{name:12s} {design.num_gates:5d} gates  {DepthAig(design).num_levels:3d} levels")
```

:::{warning}
The suite spans four orders of magnitude. `ctrl` has 174 AND gates; `hyp` has over
214,000 and is a several-hundred-megabyte proposition once loaded and optimized. Start
small.
:::

If only the AIGER file is wanted — to hand to another tool, say — use
{py:func}`~aigverse.benchmarks.epfl_path`, which downloads and returns the path without
parsing.

## Pinning a revision

The benchmark repository is versioned by commit rather than by release, and its circuits
do change. By default the loader tracks `master`; pass an explicit `revision` to make a
result reproducible:

```python
aig = epfl("adder", revision="9e5d0ec")
```

Each revision is cached separately, so switching between them does not re-download
anything you already have.

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
