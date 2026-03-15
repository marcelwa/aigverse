from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any

import pytest

from aigverse.networks import SequentialAig

if TYPE_CHECKING:
    from aigverse.networks import AigSignal


def test_sequential_aig_initialization() -> None:
    """Test basic initialization and properties of SequentialAig."""
    saig = SequentialAig()
    assert saig.size == 1
    assert saig.num_gates == 0
    assert saig.num_pis == 0
    assert saig.num_pos == 0
    assert saig.num_registers == 0
    assert saig.num_cis == 0
    assert saig.num_cos == 0
    assert saig.is_combinational


def test_create_and_use_register_in_aig() -> None:
    """Test creating and using a register in an AIG.

    Raises:
        AssertionError: If the expected properties do not match.
    """
    # Create a sequential AIG
    saig = SequentialAig()

    # Create primary inputs
    x1 = saig.create_pi()
    x2 = saig.create_pi()
    x3 = saig.create_pi()

    # Check initial network properties
    assert saig.size == 4
    assert saig.num_registers == 0
    assert saig.num_pis == 3
    assert saig.num_pos == 0

    # Create gates and outputs
    f1 = saig.create_and(x1, x2)
    saig.create_po(f1)
    saig.create_po(~f1)

    # Create a register input
    f2 = saig.create_and(f1, x3)
    saig.create_ri(f2)

    # Create a register output and connect to PO
    ro = saig.create_ro()
    saig.create_po(ro)

    # Check final network properties
    assert saig.num_pos == 3
    assert saig.num_registers == 1

    # Check each primary output
    assert saig.po_at(0) == f1
    assert saig.po_at(1) == ~f1

    for i, s in enumerate(saig.pos()):
        if i == 0:
            assert s == f1
        elif i == 1:
            assert s == ~f1
        elif i == 2:
            assert f2.data == saig.po_at(i).data
        else:
            raise AssertionError


def test_sequential_aig_ci_co_nodes(
    sequential_aig_ci_co_fixture: tuple[SequentialAig, AigSignal, AigSignal, AigSignal],
) -> None:
    """Test combinational interface (CI) and combinational output (CO) nodes."""
    saig, pi1, pi2, ro1 = sequential_aig_ci_co_fixture

    # Both PIs and ROs are CIs
    assert saig.is_ci(saig.get_node(pi1))
    assert saig.is_ci(saig.get_node(pi2))
    assert saig.is_ci(saig.get_node(ro1))

    # Only ROs are ROs
    assert not saig.is_ro(saig.get_node(pi1))
    assert not saig.is_ro(saig.get_node(pi2))
    assert saig.is_ro(saig.get_node(ro1))

    # Check CI and CO counts
    assert saig.num_cis == 3  # 2 PIs + 1 RO
    assert saig.num_cos == 2  # 1 PO + 1 RI


def test_sequential_aig_combinational_check() -> None:
    """Test checking if a sequential AIG is combinational."""
    saig = SequentialAig()

    # Initially it's combinational (no registers)
    assert saig.is_combinational

    # Add a register, making it sequential
    saig.create_ro()
    assert not saig.is_combinational

    # Create a new sequential AIG
    saig2 = SequentialAig()

    # Only add PIs and POs (still combinational)
    pi = saig2.create_pi()
    saig2.create_po(pi)
    assert saig2.is_combinational


def test_sequential_aig_repr(
    sequential_aig_single_register: tuple[SequentialAig, AigSignal, AigSignal, AigSignal],
) -> None:
    saig, _, _, _ = sequential_aig_single_register

    assert repr(saig) == "SequentialAig(pis=1, pos=1, gates=1, registers=1)"


def test_sequential_aig_to_index_list_raises(
    sequential_aig_single_register: tuple[SequentialAig, AigSignal, AigSignal, AigSignal],
) -> None:
    saig, _, _, _ = sequential_aig_single_register

    with pytest.raises(TypeError, match="register state"):
        saig.to_index_list()


def test_sequential_aig_clone_and_copy_preserve_wrapper_type(
    sequential_aig_single_register: tuple[SequentialAig, AigSignal, AigSignal, AigSignal],
) -> None:
    saig, _, _, _ = sequential_aig_single_register

    cloned = saig.clone()
    shallow = copy.copy(saig)
    deep = copy.deepcopy(saig)

    for candidate in (cloned, shallow, deep):
        assert isinstance(candidate, SequentialAig)
        assert candidate.num_registers == 1
        assert candidate.num_pos == 1
        assert candidate.num_pis == 1


def test_sequential_aig_pickle_raises(
    sequential_aig_single_register: tuple[SequentialAig, AigSignal, AigSignal, AigSignal],
) -> None:
    import pickle

    saig, _, _, _ = sequential_aig_single_register

    with pytest.raises(ValueError, match="combinational-only"):
        pickle.dumps(saig)


def test_sequential_aig_setstate_raises() -> None:
    import copyreg
    import pickle

    class Dummy:
        pass

    # Build a pickle payload that reconstructs SequentialAig via __new__,
    # forcing nanobind to route restoration through __setstate__.
    def make_pickle(state_tuple: tuple[Any, ...]) -> bytes:
        copyreg.pickle(
            Dummy,
            lambda _: (SequentialAig.__new__, (SequentialAig,), state_tuple),
        )
        return pickle.dumps(Dummy())

    with pytest.raises(ValueError, match="combinational-only"):
        pickle.loads(make_pickle(([0, 0],)))


def test_sequential_aig_register_operations(
    sequential_two_registers_full: tuple[
        SequentialAig,
        AigSignal,
        AigSignal,
        AigSignal,
        AigSignal,
        AigSignal,
        AigSignal,
    ],
) -> None:
    """Test register operations in a sequential AIG."""
    saig, _pi1, _pi2, _ro1, _ro2, _f1, _f2 = sequential_two_registers_full

    # Test register_at (should return default empty register)
    reg = saig.register_at(0)
    assert not reg.control
    assert reg.init == 3
    assert not reg.type

    # Test set_register
    new_reg = saig.register_at(0)
    new_reg.control = "clock"
    new_reg.init = 0
    new_reg.type = "rising_edge"
    saig.set_register(0, new_reg)

    # Verify register was set properly
    updated_reg = saig.register_at(0)
    assert updated_reg.control == "clock"
    assert updated_reg.init == 0
    assert updated_reg.type == "rising_edge"

    # Make sure the second register is unaffected
    reg2 = saig.register_at(1)
    assert not reg2.control
    assert reg2.init == 3
    assert not reg2.type


def test_sequential_aig_index_methods(
    sequential_two_registers_full: tuple[
        SequentialAig,
        AigSignal,
        AigSignal,
        AigSignal,
        AigSignal,
        AigSignal,
        AigSignal,
    ],
) -> None:
    """Test index methods in a sequential AIG."""
    saig, pi1, pi2, ro1, ro2, f1, f2 = sequential_two_registers_full

    # Test pi_index
    assert saig.pi_index(saig.get_node(pi1)) == 0
    assert saig.pi_index(saig.get_node(pi2)) == 1

    # Test ci_index (includes PIs and ROs)
    assert saig.ci_index(saig.get_node(pi1)) == 0
    assert saig.ci_index(saig.get_node(pi2)) == 1
    assert saig.ci_index(saig.get_node(ro1)) == 2
    assert saig.ci_index(saig.get_node(ro2)) == 3

    # Test ro_index
    assert saig.ro_index(saig.get_node(ro1)) == 0
    assert saig.ro_index(saig.get_node(ro2)) == 1

    # Test co_index and ri_index
    assert saig.co_index(f1) == 0  # First PO
    assert saig.co_index(f2) == 1  # Second PO
    assert saig.ri_index(f1) == 0  # First RI
    assert saig.ri_index(f2) == 1  # Second RI


def test_sequential_aig_ro_ri_conversion(
    sequential_aig_single_register: tuple[SequentialAig, AigSignal, AigSignal, AigSignal],
) -> None:
    """Test conversion between register outputs and register inputs."""
    saig, _, ro, f = sequential_aig_single_register

    # Test ro_to_ri
    ri_signal = saig.ro_to_ri(ro)
    assert ri_signal == f

    # Test ri_to_ro
    ro_node = saig.ri_to_ro(f)
    assert ro_node == saig.get_node(ro)


def test_sequential_aig_ro_at_ri_at(
    sequential_two_registers_full: tuple[
        SequentialAig,
        AigSignal,
        AigSignal,
        AigSignal,
        AigSignal,
        AigSignal,
        AigSignal,
    ],
) -> None:
    """Test accessing register outputs and inputs by index."""
    saig, _pi1, _pi2, ro1, ro2, f1, f2 = sequential_two_registers_full

    # Test ro_at and ri_at
    assert saig.ro_at(0) == saig.get_node(ro1)
    assert saig.ro_at(1) == saig.get_node(ro2)
    assert saig.ri_at(0) == f1
    assert saig.ri_at(1) == f2


def test_sequential_aig_iteration(
    sequential_two_registers_full: tuple[
        SequentialAig,
        AigSignal,
        AigSignal,
        AigSignal,
        AigSignal,
        AigSignal,
        AigSignal,
    ],
) -> None:
    """Test iteration methods in a sequential AIG."""
    saig, pi1, pi2, ro1, ro2, f1, f2 = sequential_two_registers_full

    # Test CI iteration
    cis = saig.cis()
    assert len(cis) == 4  # 2 PIs + 2 ROs
    assert saig.get_node(pi1) in cis
    assert saig.get_node(pi2) in cis
    assert saig.get_node(ro1) in cis
    assert saig.get_node(ro2) in cis

    # Test CO iteration
    cos = saig.cos()
    assert len(cos) == 4  # 2 POs + 2 RIs
    assert f1 in cos
    assert f2 in cos

    # Test RO iteration
    ros = saig.ros()
    assert len(ros) == 2
    assert saig.get_node(ro1) in ros
    assert saig.get_node(ro2) in ros

    # Test RI iteration
    ris = saig.ris()
    assert len(ris) == 2
    assert f1 in ris
    assert f2 in ris

    # Test registers iteration
    registers = saig.registers()
    assert len(registers) == 2

    # The register pairs are (ri, ro_node) where ro_node is the actual node ID
    # of the register output
    register_dict = dict(registers)
    assert f1 in register_dict
    assert f2 in register_dict

    # Check that register values match correctly
    assert register_dict[f1] == saig.get_node(ro1)  # First register maps to ro1 node
    assert register_dict[f2] == saig.get_node(ro2)  # Second register maps to ro2 node

    # Alternative way to verify the relationship between ri and ro
    assert saig.ri_to_ro(f1) == saig.get_node(ro1)
    assert saig.ri_to_ro(f2) == saig.get_node(ro2)
