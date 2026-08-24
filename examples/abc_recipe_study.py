#!/usr/bin/env -S uv run --script --quiet
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "aigverse>=0.1.4",
#     "matplotlib>=3.8",
#     # same floor as aigverse's own `adapters` extra, so `nox -s minimums`
#     # resolves one numpy for the whole repository
#     "numpy>=1.23.0",
# ]
# ///
"""Is there one best ABC recipe, or does the right one depend on the design?

Logic-synthesis practice leans on a handful of canonical ABC scripts -- ``resyn2``,
``compress2rs`` -- applied more or less universally. This study asks whether that
habit is justified, using the EPFL benchmark suite and the ``aigverse.abc`` bridge.

It runs two experiments and then analyses their output:

1. **Does the order of operations matter?** ABC's four atomic transformations
   (``balance``, ``rewrite``, ``refactor``, ``resub``) can be applied in any of 24
   orders. If the choice of transformations were what mattered, every order would
   land in roughly the same place. We measure the spread, and then ask the sharper
   question: is any single order *consistently* good, or does the best order change
   from design to design?

2. **Do the two ABC command families trade off?** The classic commands optimize
   area while holding depth; the ``&``-space (ABC9) scripts restructure much more
   aggressively and aim at depth. We plot both families on the area-depth plane and
   compare, per design, which family reaches the smallest result and which the
   shallowest.

The analysis then asks a third question of the data experiment 2 produced: **can we
predict optimizability?** If a cheap structural property of the input predicted how
much a script could remove, one could pick a recipe without running it. We correlate
input shape with achieved area reduction.

Benchmarks are fetched and cached by ``aigverse.benchmarks``, so nothing needs to
be downloaded by hand.

Every recipe goes to ABC as one parallel batch over the whole design set through
``aigverse.abc.run_many``, so the study runs on every core rather than one.
``--verify`` makes it SAT-bound instead, which hides most of that.

Usage:
    ./abc_recipe_study.py                    # default benchmark subset
    ./abc_recipe_study.py --quick            # fewest benchmarks, for a smoke test
    ./abc_recipe_study.py --all              # the whole EPFL suite (slow)
    ./abc_recipe_study.py --benchmarks adder bar ctrl
    ./abc_recipe_study.py --jobs 4           # cap the ABC processes run at once
    ./abc_recipe_study.py --verify           # equivalence-check every result

`aigverse` does not ship ABC. Install one and put it on ``PATH``, or point
``AIGVERSE_ABC`` at it, before running this script. See
https://aigverse.readthedocs.io/en/latest/installation.html#abc-integration
"""

from __future__ import annotations

import argparse
import csv
import itertools
import math
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

import matplotlib as mpl
import numpy as np

from aigverse import abc
from aigverse.algorithms import equivalence_checking
from aigverse.benchmarks import epfl, epfl_names
from aigverse.networks import DepthAig

# The figure is only ever written to a file, so pick the non-interactive backend
# before pyplot is imported and binds one -- otherwise this needs a display.
mpl.use("Agg")

from matplotlib import pyplot as plt

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from matplotlib.axes import Axes

    from aigverse.networks import Aig

# --------------------------------------------------------------------------------------
# Benchmarks
# --------------------------------------------------------------------------------------

# Curated subsets. These are ordered, so they are tuples rather than sets: the
# report prints designs in this order, smallest first, and a set would scramble
# that. The full list comes from `aigverse.benchmarks`.
QUICK_SET: tuple[str, ...] = ("ctrl", "router", "int2float", "dec")

# Stops before the designs that take minutes per script -- `div`, `hyp`, `log2`,
# `mem_ctrl`, `multiplier`, `sqrt` and `square` are reachable with --all.
DEFAULT_SET: tuple[str, ...] = (
    "ctrl",
    "router",
    "int2float",
    "dec",
    "cavlc",
    "priority",
    "adder",
    "i2c",
    "max",
    "bar",
)

# Labels for the two experiments and the two command families. They end up in the
# CSV and are matched on all over the report, so they are named once here.
ORDER: Final = "order"
FAMILY: Final = "family"
CLASSIC: Final = "classic"
GIA: Final = "&-space"

#: The expert script every brute-forced schedule is measured against.
REFERENCE_SCRIPT: Final = "resyn2"

#: SAT conflict budget for --verify. Unbounded checking can outlast the study
#: itself on designs like `bar` and `max`, so an exhausted budget is reported as
#: "undecided" rather than allowed to hang.
CONFLICT_LIMIT: Final = 100_000

# The recipe tables are read-only views: a typo assigning into one of them should
# fail rather than quietly reshape the experiment. Insertion order is meaningful
# here too -- it fixes the column order of the rank heatmap.

#: The four atomic transformations every canonical script is built from, as the ABC
#: commands they issue. `abc.balance`, `abc.rewrite`, `abc.refactor` and `abc.resub`
#: are the same commands with default options, but calling them one at a time costs
#: one ABC process and one AIGER round-trip *each*; handing the whole schedule to
#: ABC runs it in a single process instead. One schedule then goes out across every
#: design at once through `abc.run_many`.
ATOMS: Mapping[str, str] = MappingProxyType({
    "b": "balance",
    "rw": "rewrite",
    "rf": "refactor",
    "rs": "resub",
})

#: The canonical `abc.rc` scripts, plus ABC's own `orchestrate`, for reference
#: against the brute-forced orders. Held as the commands they issue rather than as
#: the `abc.resyn2`-style wrappers, so a whole design set goes to `abc.run_many` in
#: one call; at default options every one of those wrappers issues exactly this.
CLASSIC_SCRIPTS: Mapping[str, tuple[str, ...]] = MappingProxyType({
    "resyn": abc.expand_script("resyn"),
    "resyn2": abc.expand_script("resyn2"),
    "resyn3": abc.expand_script("resyn3"),
    "compress": abc.expand_script("compress"),
    "compress2": abc.expand_script("compress2"),
    "resyn2rs": abc.expand_script("resyn2rs"),
    "compress2rs": abc.expand_script("compress2rs"),
    "dc2": abc.expand_script("dc2"),
    "orchestrate": ("orchestrate",),
})

#: The &-space counterparts. `&fraig` is SAT sweeping rather than restructuring, and
#: is included because it removes redundancy the others structurally cannot see.
GIA_SCRIPTS: Mapping[str, tuple[str, ...]] = MappingProxyType({
    "&b": ("&b",),
    "&resub": ("&resub",),
    "&dc2": ("&dc2",),
    "&syn2": ("&syn2",),
    "&syn3": ("&syn3",),
    "&syn4": ("&syn4",),
    "&fraig": ("&fraig",),
})


@dataclass
class Result:
    """One (benchmark, recipe) measurement."""

    benchmark: str
    experiment: str
    recipe: str
    family: str
    gates: int
    levels: int
    base_gates: int
    base_levels: int
    #: One of "unchecked", "equivalent" or "undecided". A plain `bool | None`
    #: cannot tell "we did not look" apart from "the solver gave up", and those
    #: mean very different things in the CSV. A "different" verdict never lands
    #: here: it aborts the study rather than being reported as a measurement.
    equivalence: str = "unchecked"

    @property
    def area_ratio(self) -> float:
        """Final AND count relative to the original.

        Returns:
            A value below 1.0 means the recipe removed gates.
        """
        return self.gates / self.base_gates

    @property
    def depth_ratio(self) -> float:
        """Final level count relative to the original.

        Returns:
            A value below 1.0 means the recipe removed levels.
        """
        return self.levels / self.base_levels


@dataclass
class Benchmark:
    """A loaded EPFL benchmark and its baseline measurements."""

    name: str
    aig: Aig
    gates: int
    levels: int
    results: list[Result] = field(default_factory=list)
    #: Cleared once an ordering fails here. Every order statistic is a "best and
    #: worst of all N orderings", which a partial sweep cannot answer without
    #: quietly biasing itself against the designs that ran completely.
    order_complete: bool = True

    def of(self, experiment: str, family: str | None = None) -> list[Result]:
        """Select this benchmark's results for one experiment.

        Args:
            experiment: Either :data:`ORDER` or :data:`FAMILY`.
            family: Restrict to one command family, or None for all of them.

        Returns:
            The matching results, in the order they were measured.
        """
        return [r for r in self.results if r.experiment == experiment and (family is None or r.family == family)]

    def reference(self) -> Result | None:
        """Find this benchmark's :data:`REFERENCE_SCRIPT` measurement.

        Returns:
            The result, or None if that script was not run or failed here.
        """
        return next((r for r in self.of(FAMILY) if r.recipe == REFERENCE_SCRIPT), None)

    @property
    def shape(self) -> float:
        """Levels per gate of the input.

        Returns:
            High means a long, thin design; low means wide and shallow.
        """
        return self.levels / self.gates


# --------------------------------------------------------------------------------------
# Plumbing
# --------------------------------------------------------------------------------------


def load(name: str, cache: Path | None) -> Aig:
    """Load an EPFL benchmark, downloading it on first use.

    All of the fetching, caching and error handling lives in
    `aigverse.benchmarks`; this only turns its errors into a clean exit.

    Args:
        name: Benchmark name, e.g. ``"adder"``.
        cache: Directory to cache downloads in, or None for the default.

    Returns:
        The benchmark network.

    Raises:
        SystemExit: If the benchmark is unknown, cannot be downloaded, or cannot
            be parsed.
    """
    try:
        return epfl(name, cache_dir=cache)
    except (ValueError, OSError, RuntimeError) as exc:
        # unknown benchmark, failed download, or an unparsable AIGER -- all three
        # are `epfl`'s documented failures and none is worth a traceback here
        msg = f"{name}: {exc}"
        raise SystemExit(msg) from exc


def measure(aig: Aig) -> tuple[int, int]:
    """Measure the size and depth of a network.

    Args:
        aig: The network to measure.

    Returns:
        Its AND count and its level count.
    """
    return aig.num_gates, DepthAig(aig).num_levels


def run_batch(
    benchmarks: list[Benchmark],
    experiment: str,
    recipe: str,
    family: str,
    commands: tuple[str, ...],
    *,
    gia: bool,
    jobs: int | None,
    verify: bool,
) -> list[Benchmark]:
    """Apply one recipe to every benchmark at once and record what it did.

    The whole design set goes to ABC as a single parallel batch, so the recipe
    costs one round of ABC time rather than one per design. Failures come back in
    place of their result, so a design ABC chokes on does not cost the sweep the
    rest of the row.

    Args:
        benchmarks: The benchmarks to optimize.
        experiment: Either :data:`ORDER` or :data:`FAMILY`.
        recipe: Human-readable name of the recipe.
        family: Grouping label used when plotting.
        commands: The ABC commands the recipe issues.
        gia: Whether the commands are `&`-space ones.
        jobs: How many ABC processes to run at once, or None for one per core.
        verify: Whether to equivalence-check every result.

    Returns:
        The benchmarks ABC failed on, which is empty in the normal case.
    """
    run = abc.gia.run_many if gia else abc.run_many
    optimized = run([bench.aig for bench in benchmarks], commands, jobs=jobs, return_exceptions=True)

    failed: list[Benchmark] = []
    for bench, result in zip(benchmarks, optimized, strict=True):
        if isinstance(result, abc.AbcError):
            print(f"    ! {recipe} failed on {bench.name}: {result}")
            failed.append(bench)
            continue
        bench.results.append(record(bench, experiment, recipe, family, result, verify=verify))
    return failed


def record(
    bench: Benchmark,
    experiment: str,
    recipe: str,
    family: str,
    optimized: Aig,
    *,
    verify: bool,
) -> Result:
    """Measure one optimized network and turn it into a row.

    Args:
        bench: The benchmark the result came from.
        experiment: Either :data:`ORDER` or :data:`FAMILY`.
        recipe: Human-readable name of the recipe.
        family: Grouping label used when plotting.
        optimized: What ABC produced.
        verify: Whether to equivalence-check the result.

    Returns:
        The measurement.

    Raises:
        SystemExit: If the optimization changed the function of the network.
    """
    gates, levels = measure(optimized)
    equivalence = check(bench, optimized, recipe) if verify else "unchecked"
    if equivalence == "different":
        # every number this study goes on to print assumes the optimizations
        # preserved the function, so there is nothing left worth measuring
        msg = f"aborting: '{recipe}' on {bench.name} is not equivalence-preserving, so the study data is invalid"
        raise SystemExit(msg)

    return Result(
        benchmark=bench.name,
        experiment=experiment,
        recipe=recipe,
        family=family,
        gates=gates,
        levels=levels,
        base_gates=bench.gates,
        base_levels=bench.levels,
        equivalence=equivalence,
    )


def check(bench: Benchmark, optimized: Aig, recipe: str) -> str:
    """Equivalence-check one optimization against its input.

    The SAT check runs under a conflict limit rather than unbounded: on the larger
    designs an exhaustive proof can outlast the whole study, and "we ran out of
    budget" is a perfectly reportable answer.

    Args:
        bench: The benchmark the result came from.
        optimized: The optimized network.
        recipe: Name of the recipe, for the message on a mismatch.

    Returns:
        One of "equivalent", "different" or "undecided".
    """
    equivalent = equivalence_checking(bench.aig, optimized, conflict_limit=CONFLICT_LIMIT)
    if equivalent is None:
        print(f"    ? {recipe} on {bench.name}: equivalence undecided within {CONFLICT_LIMIT} conflicts")
        return "undecided"
    if not equivalent:
        # Worth shouting about: this would be an ABC or a bridge bug, not a result.
        print(f"    !! {recipe} changed the function of {bench.name}")
        return "different"
    return "equivalent"


def commands_for(order: Sequence[str], rounds: int) -> tuple[str, ...]:
    """Expand a schedule of atomic transformations into ABC commands.

    The whole schedule goes to ABC as one script, so it costs a single process and
    a single AIGER round-trip no matter how long it is.

    Args:
        order: The atom keys to apply, in order.
        rounds: How often to repeat the whole sequence.

    Returns:
        The commands, in the order ABC runs them.
    """
    return tuple(ATOMS[key] for key in order) * rounds


# --------------------------------------------------------------------------------------
# Experiments
# --------------------------------------------------------------------------------------


def experiment_order(benchmarks: list[Benchmark], rounds: int, *, jobs: int | None, verify: bool) -> None:
    """Run every ordering of the four atomic transformations.

    One ordering at a time, across every design at once: the designs are what the
    batch parallelizes over, and keeping the orders sequential keeps the progress
    line meaningful.

    Args:
        benchmarks: The benchmarks to run on.
        rounds: How often each schedule repeats.
        jobs: How many ABC processes to run at once, or None for one per core.
        verify: Whether to equivalence-check every result.
    """
    orders = list(itertools.permutations(ATOMS))
    print(f"\n[1/2] schedule sensitivity: {len(orders)} orders x {rounds} rounds ({len(ATOMS) * rounds} commands)")

    for order in orders:
        recipe = "; ".join(order)
        failed = run_batch(
            benchmarks,
            ORDER,
            recipe,
            "permutation",
            commands_for(order, rounds),
            gia=False,
            jobs=jobs,
            verify=verify,
        )
        print(f"  {recipe:<20} {len(benchmarks) - len(failed)}/{len(benchmarks)} designs")
        for bench in failed:
            bench.order_complete = False


def experiment_families(benchmarks: list[Benchmark], *, jobs: int | None, verify: bool) -> None:
    """Run the canonical classic scripts and their `&`-space counterparts.

    Args:
        benchmarks: The benchmarks to run on.
        jobs: How many ABC processes to run at once, or None for one per core.
        verify: Whether to equivalence-check every result.
    """
    print(f"\n[2/2] family comparison: {len(CLASSIC_SCRIPTS)} classic + {len(GIA_SCRIPTS)} &-space scripts")

    for family, scripts in ((CLASSIC, CLASSIC_SCRIPTS), (GIA, GIA_SCRIPTS)):
        for name, commands in scripts.items():
            failed = run_batch(
                benchmarks,
                FAMILY,
                name,
                family,
                commands,
                gia=family == GIA,
                jobs=jobs,
                verify=verify,
            )
            print(f"  {name:<20} {len(benchmarks) - len(failed)}/{len(benchmarks)} designs")


# --------------------------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------------------------


def spearman(xs: Sequence[float], ys: Sequence[float]) -> float:
    """Compute Spearman's rank correlation coefficient.

    Implemented here rather than pulled from SciPy to keep the dependency list of
    this script to matplotlib and numpy.

    Args:
        xs: First sample.
        ys: Second sample.

    Returns:
        The correlation in [-1, 1], or NaN if either sample is constant.
    """
    if len(xs) < 2:
        return float("nan")
    rank_x = _rank(np.asarray(xs, dtype=float))
    rank_y = _rank(np.asarray(ys, dtype=float))
    if rank_x.std() == 0 or rank_y.std() == 0:
        return float("nan")
    return float(np.corrcoef(rank_x, rank_y)[0, 1])


def _rank(values: np.ndarray) -> np.ndarray:
    """Rank values, averaging ties.

    Args:
        values: The sample to rank.

    Returns:
        The ranks, in the order of the input.
    """
    order = values.argsort()
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(len(values), dtype=float)
    # average tied ranks so that a plateau does not create a spurious ordering
    for value in np.unique(values):
        mask = values == value
        if mask.sum() > 1:
            ranks[mask] = ranks[mask].mean()
    return ranks


@dataclass
class ShapeVsGain:
    """Input shape against achieved area reduction, for the predictability question."""

    names: list[str] = field(default_factory=list)
    shapes: list[float] = field(default_factory=list)
    gains: list[float] = field(default_factory=list)

    @property
    def rho(self) -> float:
        """Spearman correlation between the two.

        Returns:
            The correlation in [-1, 1], or NaN if it is not defined.
        """
        return spearman(self.shapes, self.gains)


def complete_orders(benchmarks: list[Benchmark]) -> list[Benchmark]:
    """Select the benchmarks whose order sweep produced every ordering.

    Args:
        benchmarks: The benchmarks, with their results attached.

    Returns:
        Those safe to compare orderings on.
    """
    return [bench for bench in benchmarks if bench.order_complete]


def shape_vs_gain(benchmarks: list[Benchmark]) -> ShapeVsGain:
    """Pair each benchmark's input shape with the best reduction a classic script hit.

    Args:
        benchmarks: The benchmarks, with their results attached.

    Returns:
        The paired samples, covering only benchmarks that have classic results.
    """
    paired = ShapeVsGain()
    for bench in benchmarks:
        rows = bench.of(FAMILY, CLASSIC)
        if not rows:
            continue
        paired.names.append(bench.name)
        paired.shapes.append(bench.shape)
        paired.gains.append(1.0 - min(r.area_ratio for r in rows))
    return paired


def report(benchmarks: list[Benchmark], rounds: int) -> dict[str, float]:
    """Print the findings and return the headline numbers.

    Args:
        benchmarks: The benchmarks, with their results attached.
        rounds: How often each schedule repeated, for the effort comparison.

    Returns:
        A mapping of headline statistic names to values.
    """
    print("\n" + "=" * 78)
    print("FINDINGS")
    print("=" * 78)
    return {
        **_report_order(benchmarks, rounds),
        **_report_families(benchmarks),
        **_report_predictability(benchmarks),
    }


def _report_order(benchmarks: list[Benchmark], rounds: int) -> dict[str, float]:
    """Report on how much the schedule alone moves the result.

    Args:
        benchmarks: The benchmarks, with their results attached.
        rounds: How often each schedule repeated, for the effort comparison.

    Returns:
        This section's headline statistics.
    """
    headline: dict[str, float] = {}
    print("\n1. Does the order of the four transformations matter?\n")
    complete = complete_orders(benchmarks)
    dropped = [bench.name for bench in benchmarks if not bench.order_complete]
    if dropped:
        print(f"   Excluded, an ordering failed there and a partial sweep is not comparable: {', '.join(dropped)}\n")
        headline["order_designs_excluded"] = float(len(dropped))
    print(f"   {'benchmark':<12} {'best':>8} {'worst':>8} {'spread':>8}   best order")
    spreads = []
    for bench in complete:
        rows = bench.of(ORDER)
        if not rows:
            continue
        best = min(rows, key=lambda r: r.gates)
        worst = max(rows, key=lambda r: r.gates)
        spread = (worst.gates - best.gates) / best.gates
        spreads.append(spread)
        print(f"   {bench.name:<12} {best.gates:>8} {worst.gates:>8} {spread:>7.1%}   {best.recipe}")

    if spreads:
        sensitive = [s for s in spreads if s > 0]
        headline["mean_order_spread"] = float(np.mean(spreads))
        headline["max_order_spread"] = float(np.max(spreads))
        headline["order_insensitive_fraction"] = 1.0 - len(sensitive) / len(spreads)
        insensitive = len(spreads) - len(sensitive)
        if insensitive:
            print(
                f"\n   On {insensitive} of {len(spreads)} designs the order made no difference at all -- every ordering"
            )
            print("   reached the same AND count, so the schedule was simply irrelevant there.")
        if sensitive:
            where = f"On the other {len(sensitive)}" if insensitive else f"On all {len(sensitive)} of them"
            print(
                f"\n   {where} it moved the result by {np.mean(sensitive):.1%} "
                f"on average and up to {np.max(sensitive):.1%},"
            )
            print("   using exactly the same four transformations the same number of times.")
            if insensitive:
                print(f"   Averaged over every design that becomes a much tamer {np.mean(spreads):.1%}, which is why")
                print("   the per-design view in panel B is the one worth reading.")
            else:
                print("   The per-design view in panel B is the one worth reading.")

    headline.update(_report_order_stability(complete))
    headline.update(_report_reference(complete, rounds))
    return headline


def _report_order_stability(benchmarks: list[Benchmark]) -> dict[str, float]:
    """Report whether any single order is good everywhere.

    Args:
        benchmarks: The benchmarks whose order sweep ran to completion.

    Returns:
        This section's headline statistics.
    """
    # Rank each order per benchmark and see whether any of them stays near the top.
    per_order: dict[str, list[float]] = {}
    for bench in benchmarks:
        rows = bench.of(ORDER)
        if len(rows) < 2:
            continue
        ranks = _rank(np.array([r.gates for r in rows], dtype=float))
        for row, rank in zip(rows, ranks, strict=True):
            per_order.setdefault(row.recipe, []).append(rank / (len(rows) - 1))

    if not per_order:
        return {}

    mean_rank = {name: float(np.mean(v)) for name, v in per_order.items()}
    best_order = min(mean_rank, key=lambda k: mean_rank[k])
    worst_rank_of_best = max(per_order[best_order])
    print(f"\n   Best order on average: '{best_order}' (mean normalized rank {mean_rank[best_order]:.2f}),")
    print(f"   but on its worst benchmark it ranks {worst_rank_of_best:.2f} -- so it is not universally best.")
    return {
        "best_order_mean_rank": mean_rank[best_order],
        "best_order_worst_rank": worst_rank_of_best,
    }


def _report_reference(benchmarks: list[Benchmark], rounds: int) -> dict[str, float]:
    """Report how the brute-forced orders fare against the expert script.

    Args:
        benchmarks: The benchmarks whose order sweep ran to completion.
        rounds: How often each schedule repeated, for the effort comparison.

    Returns:
        This section's headline statistics.
    """
    beaten, total = 0, 0
    for bench in benchmarks:
        rows = bench.of(ORDER)
        expert = bench.reference()
        if not rows or expert is None:
            continue
        total += 1
        if min(r.gates for r in rows) < expert.gates:
            beaten += 1
    if not total:
        return {}

    # State the effort honestly: a schedule here issues len(ATOMS) commands per
    # round, which at the default two rounds is close to what resyn2 spends.
    issued = len(ATOMS) * rounds
    reference_length = len(abc.SCRIPTS[REFERENCE_SCRIPT])
    print(
        f"\n   On {beaten} of {total} benchmarks some plain {issued}-command order beat"
        f" {REFERENCE_SCRIPT} outright (which issues {reference_length})."
    )
    return {"reference_beaten_fraction": beaten / total}


def _report_families(benchmarks: list[Benchmark]) -> dict[str, float]:
    """Report whether the two command families trade area against depth.

    Args:
        benchmarks: The benchmarks, with their results attached.

    Returns:
        This section's headline statistics.
    """
    print("\n2. Do the classic and &-space families trade area against depth?\n")
    print(f"   {'benchmark':<12} {'best area':>22} {'best depth':>22}")
    mixed_fronts, counted = 0, 0
    for bench in benchmarks:
        rows = bench.of(FAMILY)
        if not rows:
            continue
        counted += 1
        by_area = min(rows, key=lambda r: (r.gates, r.levels))
        by_depth = min(rows, key=lambda r: (r.levels, r.gates))
        if by_area.family != by_depth.family:
            mixed_fronts += 1
        print(
            f"   {bench.name:<12} {by_area.recipe:>12} ({by_area.family[:1]}) {by_area.gates:>6}"
            f" {by_depth.recipe:>12} ({by_depth.family[:1]}) {by_depth.levels:>6}"
        )

    if not counted:
        return {}

    print(
        f"\n   On {mixed_fronts} of {counted} benchmarks the smallest and the shallowest result "
        f"come from different families."
    )
    print("   Neither family dominates; picking one a priori forfeits one of the two objectives.")
    return {"mixed_front_fraction": mixed_fronts / counted}


def _report_predictability(benchmarks: list[Benchmark]) -> dict[str, float]:
    """Report whether input shape predicts how much a script can remove.

    Args:
        benchmarks: The benchmarks, with their results attached.

    Returns:
        This section's headline statistics.
    """
    print("\n3. Does the shape of the input predict how much can be removed?\n")
    paired = shape_vs_gain(benchmarks)
    if len(paired.shapes) < 3:
        print("   Too few benchmarks with classic results to say anything.")
        return {}

    rho = paired.rho
    print(f"   Spearman rho between levels/gates and best area reduction: {rho:+.2f}")
    if abs(rho) < 0.5:
        print("   Weak: this cheap structural feature does not tell you what a script will achieve.")
    else:
        print("   Strong enough to be worth a closer look on a larger benchmark set.")
    return {"shape_gain_spearman": rho}


# --------------------------------------------------------------------------------------
# Plotting
# --------------------------------------------------------------------------------------


def plot(benchmarks: list[Benchmark], rounds: int, output: Path) -> None:
    """Render the four-panel summary figure.

    Args:
        benchmarks: The benchmarks, with their results attached.
        rounds: How often each schedule repeated, for the effort comparison.
        output: Path of the PNG to write.
    """
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    fig.suptitle(
        "Is there one best ABC recipe? Evidence from the EPFL suite via aigverse.abc",
        fontsize=14,
        fontweight="bold",
    )

    # panels A and B rank orderings against each other, so a design that is
    # missing one of them belongs in neither
    complete = complete_orders(benchmarks)
    _plot_order_spread(axes[0][0], complete, rounds)
    _plot_order_stability(axes[0][1], complete)
    _plot_area_depth(axes[1][0], benchmarks)
    _plot_predictability(axes[1][1], benchmarks)

    fig.tight_layout(rect=(0, 0.02, 1, 0.97))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150)
    print(f"\nwrote {output}")


def _plot_order_spread(ax: Axes, benchmarks: list[Benchmark], rounds: int) -> None:
    """Panel A: how much the schedule alone changes the outcome.

    Args:
        ax: The axes to draw on.
        benchmarks: The benchmarks whose order sweep ran to completion.
        rounds: How often each schedule repeated, for the effort comparison.
    """
    # one pass, so the columns and the benchmarks they came from cannot drift apart
    columns = [(bench, [r.area_ratio for r in bench.of(ORDER)]) for bench in benchmarks if bench.of(ORDER)]
    if not columns:
        ax.set_visible(False)
        return

    parts = ax.violinplot([ratios for _, ratios in columns], showextrema=False)
    # matplotlib types this entry as a single Collection artist; at runtime it is a
    # list of them, one per violin.
    for body in parts["bodies"]:  # ty: ignore[not-iterable]
        body.set_facecolor("#4C72B0")
        body.set_alpha(0.45)

    rng = np.random.default_rng(0)
    for index, (bench, ratios) in enumerate(columns, start=1):
        # the individual orders, jittered: a design where every order lands on the
        # same value produces no violin at all, and that is itself a finding
        ax.scatter(
            index + rng.uniform(-0.06, 0.06, len(ratios)),
            ratios,
            s=9,
            color="#2C3E60",
            alpha=0.6,
            zorder=4,
        )
        expert = bench.reference()
        if expert is not None:
            ax.plot(index, expert.area_ratio, marker="*", markersize=15, color="#C44E52", zorder=5)

    ax.set_xticks(range(1, len(columns) + 1))
    ax.set_xticklabels([bench.name for bench, _ in columns], rotation=45, ha="right")
    ax.axhline(1.0, color="grey", linewidth=0.8, linestyle=":")
    ax.set_ylabel("AND count relative to original")
    issued = len(ATOMS) * rounds
    reference_length = len(abc.SCRIPTS[REFERENCE_SCRIPT])
    # label both marks with their own budget: the star is not drawn at the same
    # effort as the dots, and a reader comparing them needs to be told so
    ax.set_title(
        f"A  All {math.factorial(len(ATOMS))} orders of {'/'.join(ATOMS.values())}, "
        f"{rounds} round{'' if rounds == 1 else 's'}\n"
        f"dot = one ordering ({issued} commands) \u00b7 "
        f"red star = {REFERENCE_SCRIPT} ({reference_length} commands)",
        fontsize=10,
    )
    ax.grid(axis="y", alpha=0.3)


def _plot_order_stability(ax: Axes, benchmarks: list[Benchmark]) -> None:
    """Panel B: whether a good order stays good across designs.

    Args:
        ax: The axes to draw on.
        benchmarks: The benchmarks whose order sweep ran to completion.
    """
    matrix: list[np.ndarray] = []
    names: list[str] = []
    orders: list[str] | None = None
    for bench in benchmarks:
        rows = sorted(bench.of(ORDER), key=lambda r: r.recipe)
        if len(rows) < 2:
            continue
        recipes = [r.recipe for r in rows]
        if orders is None:
            orders = recipes
        elif recipes != orders:
            # `plot` already drops incomplete sweeps; this keeps the function
            # honest for any other caller, since ragged rows would not line up
            continue
        names.append(bench.name)
        ranks = _rank(np.array([r.gates for r in rows], dtype=float))
        matrix.append(ranks / (len(rows) - 1))

    if not matrix or orders is None:
        ax.set_visible(False)
        return

    image = ax.imshow(np.array(matrix), aspect="auto", cmap="RdYlGn_r", vmin=0, vmax=1)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=8)
    ax.set_xticks(range(len(orders)))
    ax.set_xticklabels(orders, rotation=90, fontsize=6)
    ax.set_title("B  Rank of each order per benchmark\ngreen = best here, red = worst here", fontsize=10)
    ax.figure.colorbar(image, ax=ax, label="normalized rank")


def _plot_area_depth(ax: Axes, benchmarks: list[Benchmark]) -> None:
    """Panel C: the area-depth plane, by command family.

    Args:
        ax: The axes to draw on.
        benchmarks: The benchmarks, with their results attached.
    """
    drawn = False
    for family, color in ((CLASSIC, "#4C72B0"), (GIA, "#DD8452")):
        # one call per family rather than one per point: same picture, two artists
        points = [r for bench in benchmarks for r in bench.of(FAMILY, family)]
        if not points:
            continue
        drawn = True
        ax.scatter(
            [r.area_ratio for r in points],
            [r.depth_ratio for r in points],
            color=color,
            alpha=0.65,
            s=28,
            label=family,
        )

    ax.axhline(1.0, color="grey", linewidth=0.8, linestyle=":")
    ax.axvline(1.0, color="grey", linewidth=0.8, linestyle=":")
    ax.set_xlabel("AND count relative to original")
    ax.set_ylabel("levels relative to original")
    ax.set_title("C  Where each family lands\nlower-left is better on both axes", fontsize=10)
    if drawn:
        ax.legend(loc="best", fontsize=9)
    ax.grid(alpha=0.3)


def _plot_predictability(ax: Axes, benchmarks: list[Benchmark]) -> None:
    """Panel D: input shape against achieved reduction.

    Args:
        ax: The axes to draw on.
        benchmarks: The benchmarks, with their results attached.
    """
    paired = shape_vs_gain(benchmarks)
    # same floor as the report: two points always correlate perfectly, and the
    # title would present that artifact as a finding
    if len(paired.shapes) < 3:
        ax.set_visible(False)
        return

    ax.scatter(paired.shapes, paired.gains, color="#55A868", s=55)
    for x, y, name in zip(paired.shapes, paired.gains, paired.names, strict=True):
        ax.annotate(name, (x, y), textcoords="offset points", xytext=(5, 4), fontsize=7)

    ax.set_xscale("log")
    ax.set_xlabel("levels / gates of the input  (log scale)")
    ax.set_ylabel("best area reduction achieved")
    ax.set_title(f"D  Is optimizability predictable from shape?\nSpearman rho = {paired.rho:+.2f}", fontsize=10)
    ax.grid(alpha=0.3)


# --------------------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------------------


def write_csv(benchmarks: Iterable[Benchmark], path: Path) -> None:
    """Write every measurement to CSV so the study can be re-analysed.

    Args:
        benchmarks: The benchmarks, with their results attached.
        path: Path of the CSV to write.
    """
    fields = [
        "benchmark",
        "experiment",
        "recipe",
        "family",
        "gates",
        "levels",
        "base_gates",
        "base_levels",
        "equivalence",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for bench in benchmarks:
            for row in bench.results:
                writer.writerow({name: getattr(row, name) for name in fields})
    print(f"wrote {path}")


def write_headline(headline: Mapping[str, float], path: Path) -> None:
    """Write the headline statistics to CSV so runs can be compared.

    Args:
        headline: The headline statistics, as returned by :func:`report`.
        path: Path of the CSV to write.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["statistic", "value"])
        writer.writerows(headline.items())
    print(f"wrote {path}")


def positive(value: str) -> int:
    """Parse a strictly positive integer, for argparse.

    Args:
        value: The raw command-line token.

    Returns:
        The parsed value.

    Raises:
        ArgumentTypeError: If it is not an integer of at least 1. Zero rounds would
            measure nothing at all, which is never what the caller meant.
    """
    parsed = int(value)
    if parsed < 1:
        msg = f"expected a positive integer, got {value}"
        raise argparse.ArgumentTypeError(msg)
    return parsed


def parse_args() -> argparse.Namespace:
    """Parse the command line.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--quick", action="store_true", help="use the four smallest benchmarks")
    group.add_argument("--all", action="store_true", help="use every benchmark, including the very large ones")
    group.add_argument("--benchmarks", nargs="+", metavar="NAME", help="explicit benchmark list")
    parser.add_argument("--rounds", type=positive, default=2, help="repetitions of each schedule (default: 2)")
    parser.add_argument("--verify", action="store_true", help="equivalence-check every result (slow)")
    parser.add_argument("--jobs", type=positive, help="ABC processes to run at once (default: one per core)")
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="where to cache downloads (default: the aigverse benchmark cache)",
    )
    parser.add_argument("--output", type=Path, default=Path("abc_recipe_study.png"), help="figure to write")
    parser.add_argument("--csv", type=Path, default=Path("abc_recipe_study.csv"), help="raw measurements to write")
    return parser.parse_args()


def main() -> int:
    """Run the study.

    Returns:
        A process exit code.
    """
    args = parse_args()

    if not abc.is_available():
        print("No ABC executable found.", file=sys.stderr)
        print(
            "aigverse does not ship ABC. Install it and put it on PATH, or set AIGVERSE_ABC.\n"
            "See https://aigverse.readthedocs.io/en/latest/installation.html#abc-integration",
            file=sys.stderr,
        )
        return 1

    print(f"ABC: {abc.abc_binary()}")
    print(f"     {abc.abc_version()}")

    selected: tuple[str, ...]
    if args.benchmarks:
        selected = tuple(args.benchmarks)
    elif args.quick:
        selected = QUICK_SET
    elif args.all:
        selected = epfl_names()
    else:
        selected = DEFAULT_SET

    print(f"\nloading {len(selected)} benchmarks")
    benchmarks: list[Benchmark] = []
    for name in selected:
        aig = load(name, args.cache_dir)
        gates, levels = measure(aig)
        print(f"  {name:12s} {gates:6d} gates  {levels:4d} levels")
        benchmarks.append(Benchmark(name=name, aig=aig, gates=gates, levels=levels))

    started = time.perf_counter()
    experiment_order(benchmarks, args.rounds, jobs=args.jobs, verify=args.verify)
    experiment_families(benchmarks, jobs=args.jobs, verify=args.verify)
    elapsed = time.perf_counter() - started

    # Wall clock rather than summed ABC time: the runs overlap now, so the two are
    # no longer the same number and only this one bounds how long the study takes.
    runs = len(benchmarks) * (math.factorial(len(ATOMS)) + len(CLASSIC_SCRIPTS) + len(GIA_SCRIPTS))
    print(f"\nanalysis  ({runs} ABC runs in {elapsed:.1f}s of wall clock)")

    headline = report(benchmarks, args.rounds)
    write_csv(benchmarks, args.csv)
    write_headline(headline, args.csv.with_name(f"{args.csv.stem}_headline{args.csv.suffix}"))
    plot(benchmarks, args.rounds, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
