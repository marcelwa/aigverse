from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from aigverse.utils import TruthTable

if TYPE_CHECKING:
    from collections.abc import Callable


@pytest.fixture
def tt2_from_binary() -> Callable[[str], TruthTable]:
    """Create a factory for 2-variable truth tables from binary strings.

    Returns:
        A factory that builds a 2-variable truth table from a binary pattern.
    """

    def _build(pattern: str) -> TruthTable:
        tt = TruthTable(2)
        tt.create_from_binary_string(pattern)
        return tt

    return _build


@pytest.fixture
def tt2_and(tt2_from_binary: Callable[[str], TruthTable]) -> TruthTable:
    """Create the 2-variable AND truth table.

    Returns:
        A 2-variable truth table for logical AND.
    """
    return tt2_from_binary("1000")


@pytest.fixture
def tt2_or(tt2_from_binary: Callable[[str], TruthTable]) -> TruthTable:
    """Create the 2-variable OR truth table.

    Returns:
        A 2-variable truth table for logical OR.
    """
    return tt2_from_binary("1101")


@pytest.fixture
def tt2_xor(tt2_from_binary: Callable[[str], TruthTable]) -> TruthTable:
    """Create the 2-variable XOR truth table.

    Returns:
        A 2-variable truth table for logical XOR.
    """
    return tt2_from_binary("0110")
