from __future__ import annotations

import pytest

from aigverse.networks import Aig


@pytest.fixture
def half_adder_reference() -> Aig:
    """Create a 2-input half-adder reference network.

    Returns:
        A reference network with sum and carry outputs.
    """
    reference = Aig()
    a = reference.create_pi()
    b = reference.create_pi()
    reference.create_po(reference.create_xor(a, b))
    reference.create_po(reference.create_and(a, b))
    return reference


@pytest.fixture
def one_bit_multiplier_reference() -> Aig:
    """Create a 1-bit multiplier reference network.

    Returns:
        A reference network with product and zero MSB outputs.
    """
    reference = Aig()
    a = reference.create_pi()
    b = reference.create_pi()
    reference.create_po(reference.create_and(a, b))
    reference.create_po(reference.get_constant(False))
    return reference


@pytest.fixture
def mux1_reference() -> Aig:
    """Create a 1-bit multiplexer reference network.

    Returns:
        A reference network with one ITE output.
    """
    reference = Aig()
    cond = reference.create_pi()
    t0 = reference.create_pi()
    e0 = reference.create_pi()
    reference.create_po(reference.create_ite(cond, t0, e0))
    return reference


@pytest.fixture
def decoder1_reference() -> Aig:
    """Create a 1-select decoder reference network.

    Returns:
        A reference network with NOT and identity outputs.
    """
    reference = Aig()
    x = reference.create_pi()
    reference.create_po(~x)
    reference.create_po(x)
    return reference
