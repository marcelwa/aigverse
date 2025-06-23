from __future__ import annotations

from aigverse import Aig, DepthAig, FanoutAig, SequentialAig


def test_import():
    """Test that the aigverse adapters can be imported and correctly monkey-patches Aig."""
    assert not hasattr(Aig, "to_networkx")

    from aigverse import adapters  # noqa: F401

    assert hasattr(Aig, "to_networkx")
    assert hasattr(DepthAig, "to_networkx")
    assert hasattr(FanoutAig, "to_networkx")
    assert hasattr(SequentialAig, "to_networkx")

    import aigverse

    assert not hasattr(aigverse, "to_networkx")  # to_networkx gets deleted from scope correctly
