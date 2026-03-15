from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from aigverse.networks import FanoutAig

if TYPE_CHECKING:
    from aigverse.networks import AigSignal


def test_fanout_aig(fanout_aig_branching: tuple[FanoutAig, AigSignal, AigSignal, AigSignal]) -> None:
    aig, n4, n5, n6 = fanout_aig_branching
    assert hasattr(aig, "fanouts")

    # Check the fanout of n4
    fanout_list = aig.fanouts(aig.get_node(n4))
    assert len(fanout_list) == 2
    assert aig.get_node(n6) in fanout_list
    assert aig.get_node(n5) in fanout_list

    # fanouts() only collect internal fanouts (no POs) while fanout_size() will collect all
    assert len(aig.fanouts(aig.get_node(n6))) == 0
    assert aig.fanout_size(aig.get_node(n6)) == 1


def test_fanout_aig_clone_and_copy_preserve_wrapper_type(
    fanout_aig_linear: tuple[FanoutAig, AigSignal, AigSignal],
) -> None:
    aig, gate0, _ = fanout_aig_linear

    cloned = aig.clone()
    shallow = copy.copy(aig)
    deep = copy.deepcopy(aig)

    for candidate in (cloned, shallow, deep):
        assert isinstance(candidate, FanoutAig)
        assert candidate.fanout_size(candidate.get_node(gate0)) == 1
