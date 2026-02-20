from __future__ import annotations

import sys


def test_root_has_no_top_level_aig_export() -> None:
    import aigverse

    assert not hasattr(aigverse, "Aig")


def test_modular_imports_are_available() -> None:
    import aigverse
    from aigverse.networks import Aig

    assert Aig is not None

    assert hasattr(aigverse, "algorithms")
    assert hasattr(aigverse, "io")
    assert hasattr(aigverse, "networks")
    assert hasattr(aigverse, "utils")


def test_lazy_submodule_loading() -> None:
    import aigverse

    sys.modules.pop("aigverse.networks", None)
    aigverse.__dict__.pop("networks", None)

    assert "aigverse.networks" not in sys.modules
    _ = aigverse.networks
    assert "aigverse.networks" in sys.modules
