"""aigverse adapters for ML tasks."""

from __future__ import annotations

try:
    import networkx as nx  # noqa: F401
    import numpy as np  # noqa: F401

except ImportError:
    import warnings

    warnings.warn(
        "Key libraries could not be imported. The `AIG.to_networkx()` adapter will not be available. "
        "To enable this functionality, install aigverse's 'adapters' extra:\n\n"
        "  uv pip install aigverse[adapters]\n",
        category=ImportWarning,
        stacklevel=2,
    )

else:
    from .. import Aig
    from .networkx import to_networkx

    Aig.to_networkx = to_networkx  # type: ignore[method-assign]

    del to_networkx
