"""Tests for the EPFL benchmark loader.

Everything that would touch the network is marked `benchmarks` and skipped by
default; the rest runs offline against a fake server or the cache.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from aigverse.benchmarks import (
    EPFL_ARITHMETIC,
    EPFL_BENCHMARKS,
    EPFL_RANDOM_CONTROL,
    epfl,
    epfl_names,
    epfl_path,
)
from aigverse.networks import Aig, NamedAig

if TYPE_CHECKING:
    from pathlib import Path


def test_the_suite_has_the_expected_shape() -> None:
    """The EPFL suite is twenty circuits in two categories of ten."""
    assert len(EPFL_ARITHMETIC) == 10
    assert len(EPFL_RANDOM_CONTROL) == 10
    assert len(EPFL_BENCHMARKS) == 20
    assert not EPFL_ARITHMETIC & EPFL_RANDOM_CONTROL


def test_the_name_sets_are_immutable() -> None:
    """The tables are frozen, so a caller cannot corrupt them for everyone else."""
    assert isinstance(EPFL_ARITHMETIC, frozenset)
    assert isinstance(EPFL_RANDOM_CONTROL, frozenset)
    assert isinstance(EPFL_BENCHMARKS, frozenset)
    with pytest.raises(AttributeError):
        EPFL_ARITHMETIC.add("nope")  # ty: ignore[unresolved-attribute]


def test_names_are_listed_sorted_and_by_category() -> None:
    """`epfl_names` is the discoverable entry point, so it must be ordered."""
    assert epfl_names() == tuple(sorted(EPFL_BENCHMARKS))
    assert epfl_names("arithmetic") == tuple(sorted(EPFL_ARITHMETIC))
    assert epfl_names("random_control") == tuple(sorted(EPFL_RANDOM_CONTROL))
    assert "adder" in epfl_names("arithmetic")
    assert "adder" not in epfl_names("random_control")


def test_unknown_category_is_rejected() -> None:
    """An unknown category names the ones that do exist."""
    with pytest.raises(ValueError, match="unknown category 'sequential'") as excinfo:
        epfl_names("sequential")
    assert "arithmetic" in str(excinfo.value)


def test_unknown_benchmark_is_rejected_before_any_download() -> None:
    """A typo must fail immediately and list the alternatives, not hit the network."""
    with pytest.raises(ValueError, match="unknown EPFL benchmark 'addr'") as excinfo:
        epfl_path("addr")
    assert "adder" in str(excinfo.value)


def test_a_cached_file_is_reused(tmp_path: Path) -> None:
    """A populated cache must satisfy the request without any network access.

    Args:
        tmp_path: Cache directory for this test.
    """
    cached = tmp_path / "master" / "arithmetic" / "adder.aig"
    cached.parent.mkdir(parents=True)
    cached.write_bytes(b"not really an aiger file, but non-empty")

    assert epfl_path("adder", cache_dir=tmp_path) == cached


def test_an_empty_cached_file_is_not_trusted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A zero-byte leftover must be re-fetched rather than returned.

    Args:
        tmp_path: Cache directory for this test.
        monkeypatch: Used to make any download attempt fail loudly.
    """
    stale = tmp_path / "master" / "arithmetic" / "adder.aig"
    stale.parent.mkdir(parents=True)
    stale.write_bytes(b"")

    def _refuse(*_args: object, **_kwargs: object) -> object:
        msg = "download attempted"
        raise AssertionError(msg)

    monkeypatch.setattr("urllib.request.urlopen", _refuse)

    with pytest.raises(AssertionError, match="download attempted"):
        epfl_path("adder", cache_dir=tmp_path)


def test_a_failed_download_leaves_no_partial_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An interrupted transfer must not leave something the cache would trust.

    Args:
        tmp_path: Cache directory for this test.
        monkeypatch: Used to make the download fail.
    """
    import urllib.error

    def _fail(*_args: object, **_kwargs: object) -> object:
        msg = "no route to host"
        raise urllib.error.URLError(msg)

    monkeypatch.setattr("urllib.request.urlopen", _fail)

    with pytest.raises(OSError, match="could not download the EPFL benchmark 'ctrl'"):
        epfl_path("ctrl", cache_dir=tmp_path)

    assert list(tmp_path.rglob("*.aig")) == []
    assert list(tmp_path.rglob("*.part")) == []


def test_the_revision_is_part_of_the_cache_path(tmp_path: Path) -> None:
    """Two revisions of a benchmark must not share one cache entry.

    Args:
        tmp_path: Cache directory for this test.
    """
    for revision in ("master", "abcdef0"):
        cached = tmp_path / revision / "random_control" / "ctrl.aig"
        cached.parent.mkdir(parents=True)
        cached.write_bytes(b"placeholder")

    assert epfl_path("ctrl", cache_dir=tmp_path).parent.parent.name == "master"
    assert epfl_path("ctrl", revision="abcdef0", cache_dir=tmp_path).parent.parent.name == "abcdef0"


@pytest.mark.benchmarks
def test_downloading_and_parsing_a_small_benchmark(tmp_path: Path) -> None:
    """The end-to-end path, against the real repository.

    `ctrl` is the smallest benchmark in the suite, so this stays cheap.

    Args:
        tmp_path: Cache directory for this test.
    """
    ntk = epfl("ctrl", cache_dir=tmp_path)

    assert isinstance(ntk, NamedAig)
    assert isinstance(ntk, Aig)
    assert ntk.num_pis == 7
    assert ntk.num_pos == 26
    assert ntk.num_gates == 174


@pytest.mark.benchmarks
def test_the_second_call_hits_the_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Downloading twice would make a benchmark sweep needlessly slow.

    Args:
        tmp_path: Cache directory for this test.
        monkeypatch: Used to detect a second download attempt.
    """
    first = epfl_path("ctrl", cache_dir=tmp_path)

    def _refuse(*_args: object, **_kwargs: object) -> object:
        msg = "downloaded twice"
        raise AssertionError(msg)

    monkeypatch.setattr("urllib.request.urlopen", _refuse)

    assert epfl_path("ctrl", cache_dir=tmp_path) == first
