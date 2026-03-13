from __future__ import annotations

from pathlib import Path

import pytest

from aigverse.networks import Aig


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Apply suite markers based on test paths for consistent categorization.

    Args:
        items: Collected pytest items to classify with markers.
    """
    for item in items:
        test_path = Path(str(item.fspath)).as_posix()

        if "/test/algorithms/" in test_path:
            item.add_marker(pytest.mark.algorithms)
        elif "/test/networks/" in test_path:
            item.add_marker(pytest.mark.networks)
        elif "/test/inout/" in test_path:
            item.add_marker(pytest.mark.io)
        elif "/test/generators/" in test_path:
            item.add_marker(pytest.mark.generators)
        elif "/test/adapters/" in test_path:
            item.add_marker(pytest.mark.adapters)
        elif "/test/truth_tables/" in test_path:
            item.add_marker(pytest.mark.tts)


@pytest.fixture
def simple_and_aig() -> Aig:
    """Create a simple AIG with 2 PIs, 1 AND gate, and 1 PO.

    Returns:
        A simple AIG network instance.
    """
    aig = Aig()
    x0 = aig.create_pi()
    x1 = aig.create_pi()
    aig.create_po(aig.create_and(x0, x1))
    return aig


@pytest.fixture
def simple_or_aig() -> Aig:
    """Create a simple AIG with 2 PIs, 1 OR gate, and 1 PO.

    Returns:
        A simple AIG network instance.
    """
    aig = Aig()
    x0 = aig.create_pi()
    x1 = aig.create_pi()
    aig.create_po(aig.create_or(x0, x1))
    return aig


@pytest.fixture
def three_input_and_chain_aig() -> Aig:
    """Create a 3-input AIG with a small AND-chain cone and 1 PO.

    Returns:
        A three-input AIG with an AND-chain output.
    """
    aig = Aig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    x3 = aig.create_pi()

    a1 = aig.create_and(x1, x2)
    a2 = aig.create_and(x1, x3)
    a3 = aig.create_and(a1, a2)
    aig.create_po(a3)
    return aig
