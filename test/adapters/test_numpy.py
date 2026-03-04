from __future__ import annotations

import pytest

try:
    import numpy as np
except ImportError:
    pytest.skip(
        "NumPy could not be imported. The TruthTable to NumPy conversion will not be available. "
        "Skipping NumPy conversion tests. To enable this functionality, install numpy:\n\n"
        "  uv pip install numpy\n",
        allow_module_level=True,
    )

from aigverse.utils import TruthTable


class TestNumpyConversion:
    """Test suite for the TruthTable to NumPy conversion functionality."""

    @staticmethod
    def test_to_numpy_array() -> None:
        """Test conversion to different types of numpy arrays via np.array."""
        tt = TruthTable(3)  # 8 bits
        tt.create_from_binary_string("10100101")

        # Expected data
        expected_bool = [True, False, True, False, False, True, False, True]
        expected_int = [1, 0, 1, 0, 0, 1, 0, 1]
        expected_float = [1.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 1.0]

        # Default conversion (should be bool)
        arr_bool = np.array(tt)
        assert arr_bool.dtype == np.bool_
        assert arr_bool.shape == (8,)
        np.testing.assert_array_equal(arr_bool, expected_bool)

        # Integer conversion
        arr_int = np.array(tt, dtype=np.int32)
        assert arr_int.dtype == np.int32
        assert arr_int.shape == (8,)
        np.testing.assert_array_equal(arr_int, expected_int)

        # Floating point conversion
        arr_float = np.array(tt, dtype=np.float64)
        assert arr_float.dtype == np.float64
        assert arr_float.shape == (8,)
        np.testing.assert_allclose(arr_float, expected_float)

    @staticmethod
    def test_to_numpy_asarray() -> None:
        """Test conversion to numpy array via np.asarray."""
        tt = TruthTable(3)  # 8 bits
        tt.create_from_binary_string("10100101")

        expected_data = [1, 0, 1, 0, 0, 1, 0, 1]

        # asarray should create a new array from the TruthTable sequence
        arr = np.asarray(tt, dtype=np.uint8)
        assert isinstance(arr, np.ndarray)
        assert arr.dtype == np.uint8
        assert arr.shape == (8,)
        np.testing.assert_array_equal(arr, expected_data)

        # Modifying the original TruthTable should not affect the array because
        # TruthTable is not a numpy array, so asarray makes a copy.
        tt[0] = False
        np.testing.assert_array_equal(arr, expected_data)  # arr should be unchanged

    @staticmethod
    def test_small_truth_table_to_numpy() -> None:
        """Test conversion of a small (0-var, 1-bit) truth table."""
        tt = TruthTable(0)  # 0 vars, 1 bit
        assert len(tt) == 1

        # bit is 0
        arr = np.array(tt)
        assert arr.shape == (1,)
        assert arr.dtype == np.bool_
        np.testing.assert_array_equal(arr, [False])

        # bit is 1
        tt[0] = True
        arr = np.array(tt)
        assert arr.shape == (1,)
        assert arr.dtype == np.bool_
        np.testing.assert_array_equal(arr, [True])
