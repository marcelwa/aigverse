from __future__ import annotations

import sys
from unittest import mock

import pytest

try:
    import networkx as nx  # noqa: F401
    import numpy as np
except ImportError:
    pytest.skip(
        "Key libraries could not be imported. The `AIG.to_networkx()` adapter will not be available. "
        "Skipping NetworkX adapter tests. To enable this functionality, install aigverse's 'adapters' extra:\n\n"
        "  uv pip install aigverse[adapters]\n",
        allow_module_level=True,
    )


from aigverse.networks import Aig, DepthAig, FanoutAig, SequentialAig


@pytest.mark.parametrize("dependency", ["networkx", "numpy"])
def test_missing_dependencies(dependency: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a UserWarning is issued if a dependency is missing."""
    # Ensure a clean state by unloading the adapters module and removing any existing patch
    monkeypatch.delitem(sys.modules, "aigverse.adapters", raising=False)
    monkeypatch.delattr(Aig, "to_networkx", raising=False)

    # Simulate that the dependency is not installed by patching 'sys.modules'
    with mock.patch.dict(sys.modules, {dependency: None}):
        # Check that the expected warning is raised when the module is imported
        with pytest.warns(UserWarning, match="Key libraries could not be imported"):
            import aigverse.adapters  # noqa: F401

        # The monkey-patch should not have been applied
        assert not hasattr(Aig, "to_networkx")

    # Unload the module to ensure a clean state for subsequent tests
    monkeypatch.delitem(sys.modules, "aigverse.adapters", raising=False)


def test_import(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that the aigverse adapters can be imported and correctly monkey-patch Aig."""
    # Ensure a clean state by unloading the adapters module and removing any existing patch
    monkeypatch.delitem(sys.modules, "aigverse.adapters", raising=False)
    monkeypatch.delattr(Aig, "to_networkx", raising=False)
    monkeypatch.delattr(DepthAig, "to_networkx", raising=False)
    monkeypatch.delattr(FanoutAig, "to_networkx", raising=False)
    monkeypatch.delattr(SequentialAig, "to_networkx", raising=False)

    assert not hasattr(Aig, "to_networkx")

    # This import will execute the module's top-level code
    import aigverse.adapters  # noqa: F401

    assert hasattr(Aig, "to_networkx")
    assert hasattr(DepthAig, "to_networkx")
    assert hasattr(FanoutAig, "to_networkx")
    assert hasattr(SequentialAig, "to_networkx")

    import aigverse

    assert not hasattr(aigverse, "to_networkx")  # to_networkx gets deleted from scope correctly

    # Unload the module to ensure a clean state for subsequent tests
    monkeypatch.delitem(sys.modules, "aigverse.adapters", raising=False)


@pytest.fixture
def _import_adapters() -> None:
    """Fixture to ensure adapters are imported for each test in the TestNetworkxAdapter class."""
    import aigverse.adapters  # noqa: F401


@pytest.fixture
def simple_aig() -> Aig:
    """Create a simple AIG with 2 PIs, 1 AND gate, and 3 POs.

    Returns:
        Aig: An instance of Aig with the specified structure.
    """
    aig = Aig()
    a = aig.create_pi()
    b = aig.create_pi()
    g = aig.create_and(a, b)
    aig.create_po(a)
    aig.create_po(b)
    aig.create_po(g)

    return aig


@pytest.mark.usefixtures("_import_adapters")
class TestNetworkxAdapter:
    """Test suite for the NetworkX adapter functionality."""

    @staticmethod
    def test_to_networkx_basic(simple_aig: Aig) -> None:
        """Test basic graph structure and attributes."""
        g = simple_aig.to_networkx()

        # Graph attributes
        assert g.graph["type"] == "AIG"
        assert g.graph["num_pis"] == 2
        assert g.graph["num_pos"] == 3
        assert g.graph["num_gates"] == 1

        # Node count: 1 constant + 2 PIs + 1 gate + 3 synthetic POs
        expected_nodes = simple_aig.nodes() + [simple_aig.po_index(po) + simple_aig.size() for po in simple_aig.pos()]
        assert set(g.nodes) == set(expected_nodes)

        # Edge count: 5
        assert g.number_of_edges() == 5

        # Node attributes: index and type
        for _n, data in g.nodes(data=True):
            assert "index" in data
            assert isinstance(data["type"], np.ndarray)
            assert data["type"].shape == (4,)
            assert np.sum(data["type"]) == 1

        # Edge attributes: type
        for _, _, data in g.edges(data=True):
            assert "type" in data
            assert isinstance(data["type"], np.ndarray)
            assert data["type"].shape == (2,)
            assert np.sum(data["type"]) == 1

    @staticmethod
    def test_to_networkx_levels(simple_aig: Aig) -> None:
        """Test level attributes."""
        g = simple_aig.to_networkx(levels=True)

        assert "levels" in g.graph
        for _n, data in g.nodes(data=True):
            if "level" in data:
                assert isinstance(data["level"], int)
                assert data["level"] >= 0

    @staticmethod
    def test_to_networkx_node_tts_and_graph_tts(simple_aig: Aig) -> None:
        """Test node and graph truth tables as numpy arrays."""
        g = simple_aig.to_networkx(node_tts=True, graph_tts=True)

        # Graph function attribute
        assert "function" in g.graph
        assert isinstance(g.graph["function"], list)
        for arr in g.graph["function"]:
            assert isinstance(arr, np.ndarray)
            assert arr.dtype == np.int8
            assert arr.ndim == 1
            assert set(arr).issubset({0, 1})

        # Node function attribute
        for _n, data in g.nodes(data=True):
            if "function" in data:
                arr = data["function"]
                assert isinstance(arr, np.ndarray)
                assert arr.dtype == np.int8
                assert arr.ndim == 1
                assert set(arr).issubset({0, 1})

    @staticmethod
    def test_to_networkx_fanouts(simple_aig: Aig) -> None:
        """Test fanout attribute."""

        nxg = simple_aig.to_networkx(fanouts=True)
        for _n, data in nxg.nodes(data=True):
            if "fanouts" in data:
                assert isinstance(data["fanouts"], int)
                assert data["fanouts"] >= 0

    @staticmethod
    def test_to_networkx_edge_types(simple_aig: Aig) -> None:
        """Test edge type one-hot encoding for regular and inverted edges."""
        g = simple_aig.to_networkx()

        for _, _, data in g.edges(data=True):
            arr = data["type"]
            assert isinstance(arr, np.ndarray)
            assert arr.shape == (2,)
            assert np.sum(arr) == 1
            assert set(arr).issubset({0, 1})

    @staticmethod
    def test_to_networkx_node_types(simple_aig: Aig) -> None:
        """Test node type one-hot encoding for all node types."""
        g = simple_aig.to_networkx()
        found_types = set()

        for _node, data in g.nodes(data=True):
            arr = data["type"]
            assert isinstance(arr, np.ndarray)
            assert arr.shape == (4,)
            assert np.sum(arr) == 1
            found_types.add(tuple(arr.tolist()))

        # Should have at least const, pi, gate, po
        assert len(found_types) == 4

    @staticmethod
    @pytest.mark.parametrize("dtype", [np.bool_, np.int8, np.int16, np.int32, np.int64, np.float32, np.float64])
    def test_to_networkx_dtype(simple_aig: Aig, dtype: type[np.generic]) -> None:
        """Test that the dtype argument is correctly applied to all numpy arrays."""
        g = simple_aig.to_networkx(node_tts=True, graph_tts=True, dtype=dtype)

        # Check graph function dtype
        if "function" in g.graph:
            for arr in g.graph["function"]:
                assert arr.dtype == dtype

        # Check node attribute dtypes
        for _, data in g.nodes(data=True):
            assert data["type"].dtype == dtype
            if "function" in data:
                assert data["function"].dtype == dtype

        # Check edge attribute dtype
        for _, _, data in g.edges(data=True):
            assert data["type"].dtype == dtype

    @staticmethod
    def test_to_networkx_with_names() -> None:
        """Test that NamedAig names are preserved in NetworkX graph."""
        from aigverse.networks import NamedAig  # Create a NamedAig with names

        aig = NamedAig()
        aig.set_network_name("test_network")

        a = aig.create_pi("input_a")
        b = aig.create_pi("input_b")
        g = aig.create_and(a, b)
        aig.set_name(g, "and_gate")

        aig.create_po(a, "output_a")
        aig.create_po(g, "output_and")

        # Convert to NetworkX
        nx_graph = aig.to_networkx()

        # Check graph name
        assert "name" in nx_graph.graph
        assert nx_graph.graph["name"] == "test_network"

        # Check edge (signal) names
        edge_names = {}
        for src, tgt, data in nx_graph.edges(data=True):
            if "name" in data:
                edge_names[src, tgt] = data["name"]

        # Verify that we have signal names on edges
        # Signals are edges, so we should find names on edges coming from nodes
        assert len(edge_names) > 0, "Should have at least some named signals"

        # Check for PO names on edges going to synthetic PO nodes
        # They should also use "name" attribute
        edge_names_list = list(edge_names.values())
        assert "output_a" in edge_names_list
        assert "output_and" in edge_names_list

    @staticmethod
    def test_to_networkx_without_names(simple_aig: Aig) -> None:
        """Test that regular Aig objects don't have name attributes."""
        g = simple_aig.to_networkx()

        # Graph should not have a name attribute
        assert "name" not in g.graph

        # Edges should not have name attributes
        for _src, _tgt, data in g.edges(data=True):
            assert "name" not in data
