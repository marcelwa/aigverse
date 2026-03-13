from __future__ import annotations

import pytest

from aigverse.networks import Aig


@pytest.fixture
def _import_adapters() -> None:
    """Ensure adapter monkey patches are applied before adapter tests run."""
    import aigverse.adapters  # noqa: F401


@pytest.fixture
def simple_aig() -> Aig:
    """Create a simple AIG with 2 PIs, 1 AND gate, and 3 POs.

    Returns:
        A simple AIG used by adapter conversion tests.
    """
    aig = Aig()
    a = aig.create_pi()
    b = aig.create_pi()
    g = aig.create_and(a, b)
    aig.create_po(a)
    aig.create_po(b)
    aig.create_po(g)

    return aig
