"""aigverse adapters for ML tasks."""

from __future__ import annotations

from .. import Aig
from .networkx import to_networkx

Aig.to_networkx = to_networkx  # type: ignore[attr-defined]

del to_networkx
