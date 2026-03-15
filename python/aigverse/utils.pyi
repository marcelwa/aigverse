"""Provides utility data structures and functions."""

from collections.abc import Iterator

class TruthTable:
    """Represents a dynamic Boolean truth table."""

    def __init__(self, num_vars: int) -> None:
        """Creates a truth table with all bits initialized to ``0``.

        Args:
            num_vars: Number of Boolean variables.
        """

    def __eq__(self, other: object) -> bool:
        """Checks equality with another truth table."""

    def __ne__(self, other: object) -> bool:
        """Checks inequality with another truth table."""

    def __lt__(self, other: TruthTable) -> bool:
        """Lexicographically compares two truth tables."""

    def __and__(self, other: TruthTable) -> TruthTable:
        """Computes bitwise AND with another truth table."""

    def __or__(self, other: TruthTable) -> TruthTable:
        """Computes bitwise OR with another truth table."""

    def __xor__(self, other: TruthTable) -> TruthTable:
        """Computes bitwise XOR with another truth table."""

    def __invert__(self) -> TruthTable:
        """Computes bitwise NOT."""

    def __len__(self) -> int:
        """Returns the number of bits."""

    def __getitem__(self, index: int) -> bool:
        """Returns one bit by index.

        Args:
            index: Bit index.

        Returns:
            The bit value.

        Raises:
            IndexError: If ``index`` is out of range.
        """

    def __setitem__(self, index: int, value: bool) -> None:
        """Sets one bit by index.

        Args:
            index: Bit index.
            value: New bit value.

        Raises:
            IndexError: If ``index`` is out of range.
        """

    def __iter__(self) -> Iterator[bool]:
        """Returns an iterator over all bits."""

    def num_vars(self) -> int:
        """Returns the number of variables."""

    def num_blocks(self) -> int:
        """Returns the number of storage blocks."""

    def num_bits(self) -> int:
        """Returns the number of truth table bits."""

    def __copy__(self) -> TruthTable:
        """Returns a shallow copy of the truth table."""

    def __deepcopy__(self, arg: dict, /) -> TruthTable:
        """Returns a deep copy of the truth table."""

    def __assign__(self, other: TruthTable) -> TruthTable:
        """Assigns from another truth table with a compatible shape.

        Args:
            other: Source truth table.

        Returns:
            The updated truth table.
        """

    def __hash__(self) -> int:
        """Returns a hash value for dictionary/set usage."""

    def __getstate__(self) -> tuple:
        """Returns pickle state as ``(num_vars, words)``."""

    def __setstate__(self, state: tuple) -> None:
        """Restores a truth table from pickle state.

        Args:
            state: Tuple ``(num_vars, words)``.

        Raises:
            RuntimeError: If the serialized state is malformed.
            TypeError: If nanobind cannot convert the pickle payload to the expected C++ types.
        """

    def set_bit(self, index: int) -> None:
        """Sets one bit to ``1``.

        Args:
            index: Bit index.

        Raises:
            IndexError: If ``index`` is out of range.
        """

    def get_bit(self, index: int) -> bool:
        """Returns one bit value.

        Args:
            index: Bit index.

        Returns:
            The bit value.

        Raises:
            IndexError: If ``index`` is out of range.
        """

    def clear_bit(self, index: int) -> None:
        """Clears one bit to ``0``.

        Args:
            index: Bit index.

        Raises:
            IndexError: If ``index`` is out of range.
        """

    def flip_bit(self, index: int) -> None:
        """Toggles one bit value.

        Args:
            index: Bit index.

        Raises:
            IndexError: If ``index`` is out of range.
        """

    def get_block(self, block_index: int) -> int:
        """Returns one 64-bit storage block.

        Args:
            block_index: Block index.

        Returns:
            The block value.

        Raises:
            IndexError: If ``block_index`` is out of range.
        """

    def create_nth_var(self, var_index: int, complement: bool = False) -> None:
        """Creates the projection function for one variable.

        Args:
            var_index: Variable index to project.
            complement: Whether to complement the projection.

        Raises:
            IndexError: If ``var_index`` is out of range.
        """

    def create_from_binary_string(self, binary: str) -> None:
        """Loads bit values from a binary string.

        Args:
            binary: Binary string of length ``num_bits``.

        Raises:
            ValueError: If the string length does not match ``num_bits``.
        """

    def create_from_hex_string(self, hexadecimal: str) -> None:
        """Loads bit values from a hexadecimal string.

        Args:
            hexadecimal: Hex string matching the truth table size.

        Raises:
            ValueError: If the string length does not match the expected size.
        """

    def create_random(self) -> None:
        """Fills the truth table with random bits."""

    def create_majority(self) -> None:
        """Fills the truth table with the majority function."""

    def clear(self) -> None:
        """Clears all bits to ``0``."""

    def count_ones(self) -> int:
        """Returns the number of set bits."""

    def count_zeroes(self) -> int:
        """Returns the number of cleared bits."""

    def is_const0(self) -> bool:
        """Returns whether all bits are ``0``."""

    def is_const1(self) -> bool:
        """Returns whether all bits are ``1``."""

    def to_binary(self) -> str:
        """Returns the truth table as a binary string."""

    def to_hex(self) -> str:
        """Returns the truth table as a hexadecimal string."""

def ternary_majority(a: TruthTable, b: TruthTable, c: TruthTable) -> TruthTable:
    """Computes the ternary majority of three truth tables.

    Args:
        a: First truth table.
        b: Second truth table.
        c: Third truth table.

    Returns:
        The bitwise majority truth table.
    """

def cofactor0(tt: TruthTable, var_index: int) -> TruthTable:
    """Computes the cofactor with respect to assigning one variable to ``0``.

    Args:
        tt: Input truth table.
        var_index: Index of the variable to cofactor.

    Returns:
        The cofactored truth table with ``var_index`` fixed to ``0``.

    Raises:
        ValueError: If ``var_index`` is out of range.
    """

def cofactor1(tt: TruthTable, var_index: int) -> TruthTable:
    """Computes the cofactor with respect to assigning one variable to ``1``.

    Args:
        tt: Input truth table.
        var_index: Index of the variable to cofactor.

    Returns:
        The cofactored truth table with ``var_index`` fixed to ``1``.

    Raises:
        ValueError: If ``var_index`` is out of range.
    """
