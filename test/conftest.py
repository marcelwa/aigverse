from __future__ import annotations

import sys
import sysconfig
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from aigverse.generators import random_aig
from aigverse.networks import Aig, NamedKlut

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(scope="session", autouse=True)
def _check_free_threading() -> Generator[None]:
    if sysconfig.get_config_var("Py_GIL_DISABLED"):
        assert not getattr(sys, "_is_gil_enabled", lambda: True)()
    yield
    if sysconfig.get_config_var("Py_GIL_DISABLED"):
        assert not getattr(sys, "_is_gil_enabled", lambda: True)()


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
        elif "/test/benchmarks/" in test_path:
            item.add_marker(pytest.mark.benchmarks)
        elif "/test/abc/" in test_path:
            item.add_marker(pytest.mark.abc)


@pytest.fixture
def race_prone_aig() -> Aig:
    """Create a network large enough for concurrent traversals to overlap.

    Returns:
        A 600-gate random AIG network.
    """
    return random_aig(num_pis=10, num_gates=600, seed=42)


@pytest.fixture
def named_klut_basic() -> NamedKlut:
    """Create a named two-input k-LUT network with an AND output.

    Returns:
        The named k-LUT network.
    """
    ntk = NamedKlut()
    ntk.set_network_name("top")
    a = ntk.create_pi("a")
    b = ntk.create_pi("b")
    ntk.create_po(ntk.create_and(a, b), "out")
    return ntk


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
