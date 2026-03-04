from __future__ import annotations

from aigverse.networks import FanoutAig


def test_fanout_aig() -> None:
    aig = FanoutAig()
    assert hasattr(aig, "fanouts")

    # Create primary inputs
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    x3 = aig.create_pi()

    # Create AND gates
    n4 = aig.create_and(x1, x2)
    n5 = aig.create_and(n4, x3)
    n6 = aig.create_and(n4, n5)

    # Create primary outputs
    aig.create_po(n6)

    # Check the fanout of n4
    fanout_list = aig.fanouts(aig.get_node(n4))
    assert len(fanout_list) == 2
    assert aig.get_node(n6) in fanout_list
    assert aig.get_node(n5) in fanout_list

    # fanouts() only collect internal fanouts (no POs) while fanout_size() will collect all
    assert len(aig.fanouts(aig.get_node(n6))) == 0
    assert aig.fanout_size(aig.get_node(n6)) == 1
