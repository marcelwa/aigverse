"""aigverse adapters for ML tasks."""

from __future__ import annotations

try:  # ruff:ignore[non-empty-init-module]
    import networkx as nx  # ruff:ignore[unused-import]
    import numpy as np  # ruff:ignore[unused-import]

except ImportError:
    import warnings

    warnings.warn(
        "Key libraries could not be imported. The `AIG.to_networkx()` adapter will not be available. "
        "To enable this functionality, install aigverse's 'adapters' extra:\n\n"
        "  uv pip install aigverse[adapters]\n",
        category=UserWarning,
        stacklevel=2,
    )

else:
    from ..networks import Aig
    from .networkx import to_networkx

    Aig.to_networkx = to_networkx  # type: ignore[method-assign]

    del to_networkx
