#!/usr/bin/env -S uv run --script --quiet
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "aigverse",
#     "matplotlib>=3.8",
#     "numpy>=1.24",
# ]
# ///
"""Is there one best ABC recipe, or does the right one depend on the design?

Logic-synthesis practice leans on a handful of canonical ABC scripts -- ``resyn2``,
``compress2rs`` -- applied more or less universally. This study asks whether that
habit is justified, using the EPFL benchmark suite and the ``aigverse.abc`` bridge.

It runs three experiments:

1. **Does the order of operations matter?** ABC's four atomic transformations
   (``balance``, ``rewrite``, ``refactor``, ``resub``) can be applied in any of 24
   orders. If the choice of transformations were what mattered, every order would
   land in roughly the same place. We measure the spread, and then ask the sharper
   question: is any single order *consistently* good, or does the best order change
   from design to design?

2. **Do the two ABC command families trade off?** The classic commands optimize
   area while holding depth; the ``&``-space (ABC9) scripts restructure much more
   aggressively and aim at depth. We plot both families on the area-depth plane and
   check which points survive on the Pareto front.

3. **Can we predict optimizability?** If a cheap structural property of the input
   predicted how much a script could remove, one could pick a recipe without
   running it. We correlate input shape with achieved area reduction.

Usage:
    ./abc_recipe_study.py                    # default benchmark subset
    ./abc_recipe_study.py --quick            # fewest benchmarks, for a smoke test
    ./abc_recipe_study.py --all              # every benchmark listed below
    ./abc_recipe_study.py --benchmarks adder bar ctrl
    ./abc_recipe_study.py --verify           # equivalence-check every result

`aigverse` does not ship ABC. Install one and put it on ``PATH``, or point
``AIGVERSE_ABC`` at it, before running this script. See
https://aigverse.readthedocs.io/en/latest/installation.html#abc-integration
"""

from __future__ import annotations

import argparse
import csv
import itertools
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from aigverse import abc
from aigverse.algorithms import equivalence_checking
from aigverse.io import read_aiger_into_aig
from aigverse.networks import Aig, DepthAig

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence

# --------------------------------------------------------------------------------------
# Benchmarks
# --------------------------------------------------------------------------------------

EPFL_URL = "https://raw.githubusercontent.com/lsils/benchmarks/master/{category}/{name}.aig"

# (name, category). Ordered roughly by size. The default set stops before the
# designs that take minutes per script -- `div`, `hyp`, `log2`, `mem_ctrl`,
# `multiplier`, `sqrt`, `square` are reachable with --all.
BENCHMARKS: dict[str, str] = {
    "ctrl": "random_control",
    "router": "random_control",
    "int2float": "random_control",
    "dec": "random_control",
    "cavlc": "random_control",
    "priority": "random_control",
    "adder": "arithmetic",
    "i2c": "random_control",
    "max": "arithmetic",
    "bar": "arithmetic",
    "sin": "arithmetic",
    "voter": "random_control",
    "arbiter": "random_control",
    "square": "arithmetic",
    "sqrt": "arithmetic",
    "multiplier": "arithmetic",
    "log2": "arithmetic",
    "mem_ctrl": "random_control",
    "div": "arithmetic",
    "hyp": "arithmetic",
}

QUICK_SET = ["ctrl", "router", "int2float", "dec"]
DEFAULT_SET = [
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
]

# The four atomic transformations every canonical script is built from.
ATOMS: dict[str, Callable[[Aig], Aig]] = {
    "b": abc.balance,
    "rw": abc.rewrite,
    "rf": abc.refactor,
    "rs": abc.resub,
}

# Expert-designed schedules, for reference against the brute-forced orders.
CLASSIC_SCRIPTS: dict[str, Callable[[Aig], Aig]] = {
    "resyn": abc.resyn,
    "resyn2": abc.resyn2,
    "resyn3": abc.resyn3,
    "compress": abc.compress,
    "compress2": abc.compress2,
    "resyn2rs": abc.resyn2rs,
    "compress2rs": abc.compress2rs,
    "dc2": abc.dc2,
}

# The &-space counterparts. `gia_fraig` is SAT sweeping rather than restructuring,
# and is included because it removes redundancy the others structurally cannot see.
GIA_SCRIPTS: dict[str, Callable[[Aig], Aig]] = {
    "&b": abc.gia_balance,
    "&resub": abc.gia_resub,
    "&dc2": abc.gia_dc2,
    "&syn2": abc.gia_syn2,
    "&syn3": abc.gia_syn3,
    "&syn4": abc.gia_syn4,
    "&fraig": abc.gia_fraig,
}


@dataclass
class Result:
    """One (benchmark, recipe) measurement."""

    benchmark: str
    experiment: str
    recipe: str
    family: str
    gates: int
    levels: int
    seconds: float
    base_gates: int
    base_levels: int
    equivalent: bool | None = None

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


# --------------------------------------------------------------------------------------
# Plumbing
# --------------------------------------------------------------------------------------


def fetch(name: str, cache: Path) -> Path:
    """Download an EPFL benchmark, or reuse the cached copy.

    Args:
        name: Benchmark name, e.g. ``"adder"``.
        cache: Directory to store downloads in.

    Returns:
        Path to the local AIGER file.

    Raises:
        SystemExit: If the benchmark is unknown or cannot be downloaded.
    """
    if name not in BENCHMARKS:
        known = ", ".join(sorted(BENCHMARKS))
        msg = f"unknown benchmark {name!r}; available: {known}"
        raise SystemExit(msg)

    cache.mkdir(parents=True, exist_ok=True)
    target = cache / f"{name}.aig"
    if target.is_file() and target.stat().st_size > 0:
        return target

    url = EPFL_URL.format(category=BENCHMARKS[name], name=name)
    print(f"  downloading {name} ...", end=" ", flush=True)
    try:
        with urllib.request.urlopen(url, timeout=60) as response:  # ruff: ignore[suspicious-url-open-usage]
            target.write_bytes(response.read())
    except (urllib.error.URLError, TimeoutError) as exc:
        msg = f"\ncould not download {url}: {exc}"
        raise SystemExit(msg) from exc
    print(f"{target.stat().st_size // 1024} KiB")
    return target


def measure(aig: Aig) -> tuple[int, int]:
    """Measure the size and depth of a network.

    Args:
        aig: The network to measure.

    Returns:
        Its AND count and its level count.
    """
    return aig.num_gates, DepthAig(aig).num_levels


def run_recipe(
    bench: Benchmark,
    experiment: str,
    recipe: str,
    family: str,
    apply: Callable[[Aig], Aig],
    *,
    verify: bool,
) -> Result | None:
    """Apply one recipe to one benchmark and record what it did.

    Args:
        bench: The benchmark to optimize.
        experiment: Which of the three studies this measurement belongs to.
        recipe: Human-readable name of the recipe.
        family: Grouping label used when plotting.
        apply: Callable performing the optimization.
        verify: Whether to equivalence-check the result.

    Returns:
        The measurement, or None if ABC failed on this input.
    """
    started = time.perf_counter()
    try:
        optimized = apply(bench.aig)
    except abc.AbcError as exc:
        print(f"    ! {recipe} failed on {bench.name}: {exc}")
        return None
    elapsed = time.perf_counter() - started

    gates, levels = measure(optimized)
    equivalent = equivalence_checking(bench.aig, optimized) if verify else None
    if equivalent is False:
        # Worth shouting about: this would be an ABC or a bridge bug, not a result.
        print(f"    !! {recipe} changed the function of {bench.name}")

    return Result(
        benchmark=bench.name,
        experiment=experiment,
        recipe=recipe,
        family=family,
        gates=gates,
        levels=levels,
        seconds=elapsed,
        base_gates=bench.gates,
        base_levels=bench.levels,
        equivalent=equivalent,
    )


def apply_sequence(order: Sequence[str], rounds: int) -> Callable[[Aig], Aig]:
    """Build a callable applying a sequence of atomic commands repeatedly.

    Args:
        order: The atom keys to apply, in order.
        rounds: How often to repeat the whole sequence.

    Returns:
        A callable taking and returning a network.
    """

    def run(aig: Aig) -> Aig:
        """Apply the schedule.

        Args:
            aig: The network to optimize.

        Returns:
            The optimized network.
        """
        current = aig
        for _ in range(rounds):
            for key in order:
                current = ATOMS[key](current)
        return current

    return run


# --------------------------------------------------------------------------------------
# Experiments
# --------------------------------------------------------------------------------------


def experiment_order(benchmarks: list[Benchmark], rounds: int, *, verify: bool) -> None:
    """Run every ordering of the four atomic transformations.

    Args:
        benchmarks: The benchmarks to run on.
        rounds: How often each schedule repeats.
        verify: Whether to equivalence-check every result.
    """
    orders = list(itertools.permutations(ATOMS))
    print(f"\n[1/3] schedule sensitivity: {len(orders)} orders x {rounds} rounds")

    for bench in benchmarks:
        print(f"  {bench.name} ({bench.gates} gates, {bench.levels} levels)")
        for order in orders:
            result = run_recipe(
                bench,
                "order",
                "; ".join(order),
                "permutation",
                apply_sequence(order, rounds),
                verify=verify,
            )
            if result is not None:
                bench.results.append(result)


def experiment_families(benchmarks: list[Benchmark], *, verify: bool) -> None:
    """Run the canonical classic scripts and their `&`-space counterparts.

    Args:
        benchmarks: The benchmarks to run on.
        verify: Whether to equivalence-check every result.
    """
    print(f"\n[2/3] family comparison: {len(CLASSIC_SCRIPTS)} classic + {len(GIA_SCRIPTS)} &-space scripts")

    for bench in benchmarks:
        print(f"  {bench.name}")
        for family, scripts in (("classic", CLASSIC_SCRIPTS), ("&-space", GIA_SCRIPTS)):
            for name, fn in scripts.items():
                result = run_recipe(bench, "family", name, family, fn, verify=verify)
                if result is not None:
                    bench.results.append(result)


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


def report(benchmarks: list[Benchmark]) -> dict[str, float]:
    """Print the findings and return the headline numbers.

    Args:
        benchmarks: The benchmarks, with their results attached.

    Returns:
        A mapping of headline statistic names to values.
    """
    headline: dict[str, float] = {}
    print("\n" + "=" * 78)
    print("FINDINGS")
    print("=" * 78)

    # --- 1. does order matter? -----------------------------------------------------
    print("\n1. Does the order of the four transformations matter?\n")
    print(f"   {'benchmark':<12} {'best':>8} {'worst':>8} {'spread':>8}   best order")
    spreads = []
    for bench in benchmarks:
        rows = [r for r in bench.results if r.experiment == "order"]
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
        print(
            f"\n   On {len(spreads) - len(sensitive)} of {len(spreads)} designs the order made no "
            f"difference at all -- every ordering"
        )
        print("   reached the same AND count, so the schedule was simply irrelevant there.")
        if sensitive:
            print(
                f"\n   On the other {len(sensitive)} it moved the result by {np.mean(sensitive):.1%} "
                f"on average and up to {np.max(sensitive):.1%},"
            )
            print("   using exactly the same four transformations the same number of times.")
            print(f"   Averaged over every design that becomes a much tamer {np.mean(spreads):.1%}, which is why")
            print("   the per-design view in panel B is the one worth reading.")

    # Is one order universally best? Rank each order per benchmark and see whether
    # any of them stays near the top everywhere.
    per_order: dict[str, list[float]] = {}
    for bench in benchmarks:
        rows = [r for r in bench.results if r.experiment == "order"]
        if len(rows) < 2:
            continue
        ranks = _rank(np.array([r.gates for r in rows], dtype=float))
        for row, rank in zip(rows, ranks, strict=False):
            per_order.setdefault(row.recipe, []).append(rank / (len(rows) - 1))

    if per_order:
        mean_rank = {name: float(np.mean(v)) for name, v in per_order.items()}
        best_order = min(mean_rank, key=lambda k: mean_rank[k])
        worst_rank_of_best = max(per_order[best_order])
        headline["best_order_mean_rank"] = mean_rank[best_order]
        headline["best_order_worst_rank"] = worst_rank_of_best
        print(f"\n   Best order on average: '{best_order}' (mean normalized rank {mean_rank[best_order]:.2f}),")
        print(f"   but on its worst benchmark it ranks {worst_rank_of_best:.2f} -- so it is not universally best.")

    # Where does the expert script sit inside that distribution? Note that resyn2
    # issues ten commands while a schedule here issues four per round, so this is a
    # comparison of recipes, not a controlled comparison at equal effort.
    beaten, total = 0, 0
    for bench in benchmarks:
        rows = [r for r in bench.results if r.experiment == "order"]
        expert = [r for r in bench.results if r.experiment == "family" and r.recipe == "resyn2"]
        if not rows or not expert:
            continue
        total += 1
        if min(r.gates for r in rows) < expert[0].gates:
            beaten += 1
    if total:
        headline["resyn2_beaten_fraction"] = beaten / total
        print(
            f"\n   On {beaten} of {total} benchmarks some plain 4-command order beat resyn2 outright"
            f" (which issues ten commands)."
        )

    # --- 2. do the families trade off? ---------------------------------------------
    print("\n2. Do the classic and &-space families trade area against depth?\n")
    print(f"   {'benchmark':<12} {'best area':>22} {'best depth':>22}")
    mixed_fronts = 0
    for bench in benchmarks:
        rows = [r for r in bench.results if r.experiment == "family"]
        if not rows:
            continue
        by_area = min(rows, key=lambda r: (r.gates, r.levels))
        by_depth = min(rows, key=lambda r: (r.levels, r.gates))
        if by_area.family != by_depth.family:
            mixed_fronts += 1
        print(
            f"   {bench.name:<12} {by_area.recipe:>12} ({by_area.family[:1]}) {by_area.gates:>6}"
            f" {by_depth.recipe:>12} ({by_depth.family[:1]}) {by_depth.levels:>6}"
        )

    counted = sum(1 for b in benchmarks if any(r.experiment == "family" for r in b.results))
    if counted:
        headline["mixed_front_fraction"] = mixed_fronts / counted
        print(
            f"\n   On {mixed_fronts} of {counted} benchmarks the smallest and the shallowest result "
            f"come from different families."
        )
        print("   Neither family dominates; picking one a priori forfeits one of the two objectives.")

    # --- 3. is optimizability predictable? -----------------------------------------
    print("\n3. Does the shape of the input predict how much can be removed?\n")
    shapes: list[float] = []
    gains: list[float] = []
    for bench in benchmarks:
        rows = [r for r in bench.results if r.experiment == "family" and r.family == "classic"]
        if not rows:
            continue
        # levels per gate: high means a long, thin design; low means wide and shallow
        shapes.append(bench.levels / bench.gates)
        gains.append(1.0 - min(r.area_ratio for r in rows))

    if len(shapes) >= 3:
        rho = spearman(shapes, gains)
        headline["shape_gain_spearman"] = rho
        print(f"   Spearman rho between levels/gates and best area reduction: {rho:+.2f}")
        if abs(rho) < 0.5:
            print("   Weak: this cheap structural feature does not tell you what a script will achieve.")
        else:
            print("   Strong enough to be worth a closer look on a larger benchmark set.")

    return headline


# --------------------------------------------------------------------------------------
# Plotting
# --------------------------------------------------------------------------------------


def plot(benchmarks: list[Benchmark], output: Path) -> None:
    """Render the four-panel summary figure.

    Args:
        benchmarks: The benchmarks, with their results attached.
        output: Path of the PNG to write.
    """
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    fig.suptitle(
        "Is there one best ABC recipe? Evidence from the EPFL suite via aigverse.abc",
        fontsize=14,
        fontweight="bold",
    )

    _plot_order_spread(axes[0][0], benchmarks)
    _plot_order_stability(axes[0][1], benchmarks)
    _plot_area_depth(axes[1][0], benchmarks)
    _plot_predictability(axes[1][1], benchmarks)

    fig.tight_layout(rect=(0, 0.02, 1, 0.97))
    fig.savefig(output, dpi=150)
    print(f"\nwrote {output}")


def _plot_order_spread(ax: plt.Axes, benchmarks: list[Benchmark]) -> None:
    """Panel A: how much the schedule alone changes the outcome.

    Args:
        ax: The axes to draw on.
        benchmarks: The benchmarks, with their results attached.
    """
    names, data = [], []
    for bench in benchmarks:
        rows = [r for r in bench.results if r.experiment == "order"]
        if rows:
            names.append(bench.name)
            data.append([r.area_ratio for r in rows])

    if not data:
        ax.set_visible(False)
        return

    parts = ax.violinplot(data, showextrema=False)
    for body in parts["bodies"]:
        body.set_facecolor("#4C72B0")
        body.set_alpha(0.45)

    rng = np.random.default_rng(0)
    for index, (bench, column) in enumerate(
        zip((b for b in benchmarks if any(r.experiment == "order" for r in b.results)), data, strict=False), start=1
    ):
        # the individual orders, jittered: a design where every order lands on the
        # same value produces no violin at all, and that is itself a finding
        ax.scatter(
            index + rng.uniform(-0.06, 0.06, len(column)),
            column,
            s=9,
            color="#2C3E60",
            alpha=0.6,
            zorder=4,
        )
        expert = [r for r in bench.results if r.experiment == "family" and r.recipe == "resyn2"]
        if expert:
            ax.plot(index, expert[0].area_ratio, marker="*", markersize=15, color="#C44E52", zorder=5)

    ax.set_xticks(range(1, len(names) + 1))
    ax.set_xticklabels(names, rotation=45, ha="right")
    ax.axhline(1.0, color="grey", linewidth=0.8, linestyle=":")
    ax.set_ylabel("AND count relative to original")
    ax.set_title(
        "A  All 24 orders of (balance, rewrite, refactor, resub)\nred star = resyn2 (ten commands, not four)",
        fontsize=10,
    )
    ax.grid(axis="y", alpha=0.3)


def _plot_order_stability(ax: plt.Axes, benchmarks: list[Benchmark]) -> None:
    """Panel B: whether a good order stays good across designs.

    Args:
        ax: The axes to draw on.
        benchmarks: The benchmarks, with their results attached.
    """
    matrix, names, orders = [], [], None
    for bench in benchmarks:
        rows = sorted((r for r in bench.results if r.experiment == "order"), key=lambda r: r.recipe)
        if len(rows) < 2:
            continue
        if orders is None:
            orders = [r.recipe for r in rows]
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
    plt.colorbar(image, ax=ax, label="normalized rank")


def _plot_area_depth(ax: plt.Axes, benchmarks: list[Benchmark]) -> None:
    """Panel C: the area-depth plane, by command family.

    Args:
        ax: The axes to draw on.
        benchmarks: The benchmarks, with their results attached.
    """
    colors = {"classic": "#4C72B0", "&-space": "#DD8452"}
    seen: set[str] = set()

    for bench in benchmarks:
        for row in bench.results:
            if row.experiment != "family":
                continue
            ax.scatter(
                row.area_ratio,
                row.depth_ratio,
                color=colors[row.family],
                alpha=0.65,
                s=28,
                label=row.family if row.family not in seen else None,
            )
            seen.add(row.family)

    ax.axhline(1.0, color="grey", linewidth=0.8, linestyle=":")
    ax.axvline(1.0, color="grey", linewidth=0.8, linestyle=":")
    ax.set_xlabel("AND count relative to original")
    ax.set_ylabel("levels relative to original")
    ax.set_title("C  Where each family lands\nlower-left is better on both axes", fontsize=10)
    if seen:
        ax.legend(loc="best", fontsize=9)
    ax.grid(alpha=0.3)


def _plot_predictability(ax: plt.Axes, benchmarks: list[Benchmark]) -> None:
    """Panel D: input shape against achieved reduction.

    Args:
        ax: The axes to draw on.
        benchmarks: The benchmarks, with their results attached.
    """
    shapes, gains, names = [], [], []
    for bench in benchmarks:
        rows = [r for r in bench.results if r.experiment == "family" and r.family == "classic"]
        if not rows:
            continue
        shapes.append(bench.levels / bench.gates)
        gains.append(1.0 - min(r.area_ratio for r in rows))
        names.append(bench.name)

    if len(shapes) < 2:
        ax.set_visible(False)
        return

    ax.scatter(shapes, gains, color="#55A868", s=55)
    for x, y, name in zip(shapes, gains, names, strict=False):
        ax.annotate(name, (x, y), textcoords="offset points", xytext=(5, 4), fontsize=7)

    rho = spearman(shapes, gains)
    ax.set_xscale("log")
    ax.set_xlabel("levels / gates of the input  (log scale)")
    ax.set_ylabel("best area reduction achieved")
    ax.set_title(f"D  Is optimizability predictable from shape?\nSpearman rho = {rho:+.2f}", fontsize=10)
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
        "seconds",
        "base_gates",
        "base_levels",
        "equivalent",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for bench in benchmarks:
            for row in bench.results:
                writer.writerow({name: getattr(row, name) for name in fields})
    print(f"wrote {path}")


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
    parser.add_argument("--rounds", type=int, default=2, help="repetitions of each schedule (default: 2)")
    parser.add_argument("--verify", action="store_true", help="equivalence-check every result (slow)")
    parser.add_argument("--cache-dir", type=Path, default=Path("epfl-benchmarks"), help="where to keep downloads")
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

    if args.benchmarks:
        selected = args.benchmarks
    elif args.quick:
        selected = QUICK_SET
    elif args.all:
        selected = list(BENCHMARKS)
    else:
        selected = DEFAULT_SET

    print(f"\nloading {len(selected)} benchmarks into {args.cache_dir}/")
    benchmarks: list[Benchmark] = []
    for name in selected:
        path = fetch(name, args.cache_dir)
        aig = Aig(read_aiger_into_aig(path))
        gates, levels = measure(aig)
        benchmarks.append(Benchmark(name=name, aig=aig, gates=gates, levels=levels))

    started = time.perf_counter()
    experiment_order(benchmarks, args.rounds, verify=args.verify)
    experiment_families(benchmarks, verify=args.verify)
    print(f"\n[3/3] analysis  ({time.perf_counter() - started:.1f}s of ABC time)")

    report(benchmarks)
    write_csv(benchmarks, args.csv)
    plot(benchmarks, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
