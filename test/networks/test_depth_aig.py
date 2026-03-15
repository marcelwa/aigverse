from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from aigverse.networks import DepthAig

if TYPE_CHECKING:
    from aigverse.networks import AigSignal


def test_depth_aig() -> None:
    aig = DepthAig()

    assert hasattr(aig, "num_levels")
    assert hasattr(aig, "level")
    assert hasattr(aig, "is_on_critical_path")
    assert hasattr(aig, "update_levels")
    assert hasattr(aig, "create_po")

    # Create primary inputs
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    x3 = aig.create_pi()

    assert aig.num_levels == 0

    # Create AND gates
    n4 = aig.create_and(~x1, x2)
    n5 = aig.create_and(x1, n4)
    n6 = aig.create_and(x3, n5)
    n7 = aig.create_and(n4, x2)
    n8 = aig.create_and(~n5, ~n7)
    n9 = aig.create_and(~n8, n4)

    # Create primary outputs
    aig.create_po(n6)
    aig.create_po(n9)

    # Check the depth of the AIG
    assert aig.num_levels == 4

    assert aig.level(aig.get_node(x1)) == 0
    assert aig.level(aig.get_node(x2)) == 0
    assert aig.level(aig.get_node(x3)) == 0
    assert aig.level(aig.get_node(n4)) == 1
    assert aig.level(aig.get_node(n5)) == 2
    assert aig.level(aig.get_node(n6)) == 3
    assert aig.level(aig.get_node(n7)) == 2
    assert aig.level(aig.get_node(n8)) == 3
    assert aig.level(aig.get_node(n9)) == 4

    # Copy constructor
    aig2 = DepthAig(aig)

    assert aig2.num_levels == 4


def test_depth_aig_repr(depth_aig_single_and: tuple[DepthAig, AigSignal]) -> None:
    aig, _ = depth_aig_single_and

    assert repr(aig) == "DepthAig(pis=2, pos=1, gates=1, depth=1)"


def test_depth_aig_clone_and_copy_preserve_wrapper_type(depth_aig_single_and: tuple[DepthAig, AigSignal]) -> None:
    aig, gate = depth_aig_single_and

    cloned = aig.clone()
    shallow = copy.copy(aig)
    deep = copy.deepcopy(aig)

    for candidate in (cloned, shallow, deep):
        assert isinstance(candidate, DepthAig)
        assert candidate.num_levels == 1
        assert candidate.level(candidate.get_node(gate)) == 1
