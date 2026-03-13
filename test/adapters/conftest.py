from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from aigverse.networks import Aig, SequentialAig

if TYPE_CHECKING:
    from aigverse.networks import AigSignal


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


@pytest.fixture
def sequential_single_register_aig() -> tuple[SequentialAig, AigSignal]:
    """Create a simple SequentialAig with one RI/RO pair and one AND gate.

    Returns:
        A tuple containing the network and the register input signal.
    """
    aig = SequentialAig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    aig.create_ro()
    f1 = aig.create_and(x1, x2)
    aig.create_ri(f1)
    return aig, f1


@pytest.fixture
def sequential_two_registers_aig() -> tuple[SequentialAig, AigSignal, AigSignal, AigSignal]:
    """Create a SequentialAig with two register pairs and mixed logic.

    Returns:
        A tuple containing the network and the three key gate signals.
    """
    aig = SequentialAig()

    x1 = aig.create_pi()
    x2 = aig.create_pi()

    ro1 = aig.create_ro()
    ro2 = aig.create_ro()

    f1 = aig.create_and(ro1, ro2)
    f2 = aig.create_and(x1, x2)
    f3 = aig.create_and(x1, ~x2)

    aig.create_po(f3)
    aig.create_ri(f1)
    aig.create_ri(f2)

    return aig, f1, f2, f3


@pytest.fixture
def sequential_feedback_aig() -> tuple[SequentialAig, AigSignal]:
    """Create a SequentialAig with a single feedback loop register.

    Returns:
        A tuple containing the network and the feedback-driving signal.
    """
    saig = SequentialAig()
    x1 = saig.create_pi()
    ro = saig.create_ro()
    f1 = saig.create_and(x1, ro)
    saig.create_ri(f1)
    return saig, f1
