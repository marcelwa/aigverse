"""Standard benchmark suites for logic synthesis.

Fetches well-known benchmark circuits on demand and caches them locally, so a
script or an experiment can name a benchmark rather than shipping a downloader
and a copy of the data.

Nothing is downloaded at import time and no benchmark is bundled with
`aigverse`; the first call that needs a file fetches it.

Example:
    >>> from aigverse.benchmarks import epfl
    >>> aig = epfl("ctrl")  # doctest: +SKIP
    >>> aig.num_gates  # doctest: +SKIP
    174
"""

from __future__ import annotations

from ._cache import CACHE_ENV_VAR, benchmark_cache, set_benchmark_cache
from ._epfl import (
    DEFAULT_REVISION,
    EPFL_ARITHMETIC,
    EPFL_BENCHMARKS,
    EPFL_RANDOM_CONTROL,
    epfl,
    epfl_names,
    epfl_path,
)

__all__ = [
    "CACHE_ENV_VAR",
    "DEFAULT_REVISION",
    "EPFL_ARITHMETIC",
    "EPFL_BENCHMARKS",
    "EPFL_RANDOM_CONTROL",
    "benchmark_cache",
    "epfl",
    "epfl_names",
    "epfl_path",
    "set_benchmark_cache",
]
