"""Tests for the canonical ABC script expansions."""

from __future__ import annotations

import pytest

from aigverse.abc import SCRIPTS, expand_script

# Every command a script expands to must be an ABC builtin, never an `abc.rc`
# alias -- the bridge runs ABC with `-s`, so aliases would not resolve.
_BUILTINS = frozenset({"balance", "rewrite", "refactor", "resub", "dc2", "strash", "fraig"})


@pytest.mark.parametrize("name", sorted(SCRIPTS))
def test_scripts_expand_to_builtins_only(name: str) -> None:
    for command in expand_script(name):
        head = command.split()[0]
        assert head in _BUILTINS, f"{name!r} uses non-builtin {head!r}"


@pytest.mark.parametrize("name", sorted(SCRIPTS))
def test_expansions_are_non_empty(name: str) -> None:
    assert expand_script(name)


def test_unknown_script_lists_alternatives() -> None:
    with pytest.raises(KeyError, match="resyn2"):
        expand_script("does-not-exist")


def test_scripts_mapping_is_read_only() -> None:
    with pytest.raises(TypeError):
        SCRIPTS["resyn2"] = ()  # ty: ignore[invalid-assignment]


def test_resyn2_matches_the_abc_rc_alias() -> None:
    """Pins the expansion of the most widely used script.

    `resyn2` is defined in ABC's `abc.rc` as
    ``b; rw; rf; b; rw; rwz; b; rfz; rwz; b``.
    """
    assert expand_script("resyn2") == (
        "balance",
        "rewrite",
        "refactor",
        "balance",
        "rewrite",
        "rewrite -z",
        "balance",
        "refactor -z",
        "rewrite -z",
        "balance",
    )
