"""Utility data structures and functions."""

from collections.abc import Iterator

class TruthTable:
    def __init__(self, num_vars: int) -> None:
        """Create a TruthTable with 'num_vars' variables with all bits set to 0."""

    def __eq__(self, other: TruthTable) -> bool: ...
    def __ne__(self, other: TruthTable) -> bool: ...
    def __lt__(self, other: TruthTable) -> bool: ...
    def __and__(self, other: TruthTable) -> TruthTable: ...
    def __or__(self, other: TruthTable) -> TruthTable: ...
    def __xor__(self, other: TruthTable) -> TruthTable: ...
    def __invert__(self) -> TruthTable: ...
    def __len__(self) -> int: ...
    def __getitem__(self, index: int) -> bool: ...
    def __setitem__(self, index: int, value: bool) -> None: ...
    def __iter__(self) -> Iterator[bool]: ...
    def num_vars(self) -> int:
        """Returns the number of variables."""

    def num_blocks(self) -> int:
        """Returns the number of blocks."""

    def num_bits(self) -> int:
        """Returns the number of bits."""

    def __copy__(self) -> TruthTable:
        """Returns a shallow copy of the truth table."""

    def __deepcopy__(self, arg: dict, /) -> TruthTable:
        """Returns a deep copy of the truth table."""

    def __assign__(self, other: TruthTable) -> TruthTable:
        """Assigns the truth table from another compatible truth table."""

    def __hash__(self) -> int:
        """Returns the hash of the truth table."""

    def __getstate__(self) -> tuple: ...
    def __setstate__(self, arg: tuple, /) -> None: ...
    def set_bit(self, index: int) -> None:
        """Sets the bit at the given index."""

    def get_bit(self, index: int) -> int:
        """Returns the bit at the given index."""

    def clear_bit(self, index: int) -> None:
        """Clears the bit at the given index."""

    def flip_bit(self, index: int) -> None:
        """Flips the bit at the given index."""

    def get_block(self, block_index: int) -> int:
        """Returns a 64-bit block of bits."""

    def create_nth_var(self, var_index: int, complement: bool = False) -> None:
        """Constructs projections (single-variable functions)."""

    def create_from_binary_string(self, binary: str) -> None:
        """Constructs truth table from binary string."""

    def create_from_hex_string(self, hexadecimal: str) -> None:
        """Constructs truth table from hexadecimal string."""

    def create_random(self) -> None:
        """Constructs a random truth table."""

    def create_majority(self) -> None:
        """Constructs a MAJ truth table."""

    def clear(self) -> None:
        """Clears all bits."""

    def count_ones(self) -> int:
        """Counts ones in truth table."""

    def count_zeroes(self) -> int:
        """Counts zeroes in truth table."""

    def is_const0(self) -> bool:
        """Checks if the truth table is constant 0."""

    def is_const1(self) -> bool:
        """Checks if the truth table is constant 1."""

    def to_binary(self) -> str:
        """Returns the truth table as a string in binary representation."""

    def to_hex(self) -> str:
        """Returns the truth table as a string in hexadecimal representation."""

def ternary_majority(a: TruthTable, b: TruthTable, c: TruthTable) -> TruthTable:
    """Compute the ternary majority of three truth tables."""

def cofactor0(tt: TruthTable, var_index: int) -> TruthTable:
    """Returns the cofactor with respect to 0 of the variable at index `var_index` in the given truth table."""

def cofactor1(tt: TruthTable, var_index: int) -> TruthTable:
    """Returns the cofactor with respect to 1 of the variable at index `var_index` in the given truth table."""
