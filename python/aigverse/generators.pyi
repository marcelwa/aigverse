"""Provides generators for random and structured benchmark construction."""

import aigverse.networks

def random_aig(*, num_pis: int, num_gates: int, seed: int = 3405688830) -> aigverse.networks.Aig:
    """Generates a single random AIG with a fixed size.

    Args:
        num_pis: Number of primary inputs.
        num_gates: Number of logic gates.
        seed: Seed controlling random choices.

    Returns:
        A randomly generated AIG.

    Raises:
        ValueError: If ``num_pis`` or ``num_gates`` is ``0``.
        TypeError: If ``num_pis`` or ``num_gates`` cannot be converted to ``uint32``.
    """

def ripple_carry_adder(bitwidth: int) -> aigverse.networks.Aig:
    """Creates a complete ripple-carry adder benchmark network.

    Args:
        bitwidth: Number of bits per operand.

    Returns:
        An ``Aig`` with ``2 * bitwidth`` primary inputs and
        ``bitwidth + 1`` primary outputs (sum plus carry-out).

    Raises:
        ValueError: If ``bitwidth`` is not greater than ``0``.
    """

def carry_lookahead_adder(bitwidth: int) -> aigverse.networks.Aig:
    """Creates a complete carry-lookahead adder benchmark network.

    Args:
        bitwidth: Number of bits per operand.

    Returns:
        An ``Aig`` with ``2 * bitwidth`` primary inputs and
        ``bitwidth + 1`` primary outputs (sum plus carry-out).

    Raises:
        ValueError: If ``bitwidth`` is not greater than ``0``.
    """

def ripple_carry_multiplier(bitwidth: int) -> aigverse.networks.Aig:
    """Creates a complete ripple-carry multiplier benchmark network.

    Args:
        bitwidth: Number of bits per operand.

    Returns:
        An ``Aig`` with ``2 * bitwidth`` primary inputs and
        ``2 * bitwidth`` primary outputs representing the product bits.

    Raises:
        ValueError: If ``bitwidth`` is not greater than ``0``.
    """

def sideways_sum_adder(bitwidth: int) -> aigverse.networks.Aig:
    """Creates a complete sideways sum adder benchmark network.

    Args:
        bitwidth: Number of input bits.

    Returns:
        An ``Aig`` with ``bitwidth`` primary inputs and output bits encoding
        the population count of the input word.

    Raises:
        ValueError: If ``bitwidth`` is not greater than ``0``.
    """

def multiplexer(bitwidth: int) -> aigverse.networks.Aig:
    """Creates a complete word-level n-bit 2:1 MUX network.

    Args:
        bitwidth: Number of bits in each data input word.

    Returns:
        An ``Aig`` with ``1 + 2 * bitwidth`` primary inputs and ``bitwidth``
        primary outputs.

    Raises:
        ValueError: If ``bitwidth`` is not greater than ``0``.
    """

def binary_decoder(num_select_bits: int) -> aigverse.networks.Aig:
    """Creates a complete binary-decoder network.

    Args:
        num_select_bits: Number of select input bits.

    Returns:
        An ``Aig`` with ``num_select_bits`` primary inputs and
        ``2 ** num_select_bits`` primary outputs.

    Raises:
        ValueError: If ``num_select_bits`` is not greater than ``0``.
    """
