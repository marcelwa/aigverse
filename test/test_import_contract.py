from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest


def test_root_has_no_top_level_aig_export() -> None:
    import aigverse

    assert not hasattr(aigverse, "Aig")


def test_modular_imports_are_available() -> None:
    import aigverse
    from aigverse.networks import Aig

    aig = Aig()
    assert isinstance(aig, Aig)

    assert hasattr(aigverse, "algorithms")
    assert hasattr(aigverse, "io")
    assert hasattr(aigverse, "networks")
    assert hasattr(aigverse, "utils")


def test_lazy_submodule_loading(monkeypatch: pytest.MonkeyPatch) -> None:
    import aigverse

    monkeypatch.delitem(sys.modules, "aigverse.networks", raising=False)
    monkeypatch.delitem(aigverse.__dict__, "networks", raising=False)

    assert "aigverse.networks" not in sys.modules
    _ = aigverse.networks
    assert "aigverse.networks" in sys.modules
