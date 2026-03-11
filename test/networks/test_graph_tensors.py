from __future__ import annotations

import numpy as np
import pytest
import torch

from aigverse.networks import Aig, EdgeTensorEncoding, NodeTensorEncoding


@pytest.fixture
def sample_aig() -> Aig:
    """Create a tiny AIG for tensor export tests.

    Returns:
        A small AIG with two PIs, one gate, and one PO.
    """
    aig = Aig()
    a = aig.create_pi()
    b = aig.create_pi()
    c = aig.create_and(a, b)
    aig.create_po(c)
    return aig


@pytest.fixture
def large_aig() -> Aig:
    """Create a larger AIG with many gates and outputs.

    Returns:
        A deterministic larger AIG for stress-style shape and dtype checks.
    """
    aig = Aig()
    pis = [aig.create_pi() for _ in range(12)]

    level = pis
    for _ in range(6):
        next_level = []
        for i in range(0, len(level), 2):
            lhs = level[i]
            rhs = level[(i + 1) % len(level)]
            next_level.extend((aig.create_and(lhs, rhs), aig.create_and(~lhs, rhs)))
        level = next_level

    for signal in level[:10]:
        aig.create_po(signal)

    return aig


def test_graph_tensor_encoding_enums_exposed() -> None:
    """Checks that node and edge tensor encoding enums are available in Python."""
    assert NodeTensorEncoding.INTEGER.value == 0
    assert NodeTensorEncoding.ONE_HOT.value == 1

    assert EdgeTensorEncoding.BINARY.value == 0
    assert EdgeTensorEncoding.SIGNED.value == 1
    assert EdgeTensorEncoding.ONE_HOT.value == 2


def test_to_graph_tensors_int_encoding_shapes(sample_aig: Aig) -> None:
    """Checks default sparse COO tensor shapes and dimensions."""
    tensors = sample_aig.to_graph_tensors(
        node_encoding=NodeTensorEncoding.INTEGER,
        edge_encoding=EdgeTensorEncoding.BINARY,
    )

    edge_index = tensors["edge_index"]
    edge_attr = tensors["edge_attr"]
    node_attr = tensors["node_attr"]

    assert edge_index.ndim == 2
    assert edge_index.shape[0] == 2
    assert edge_index.shape[1] == len(list(sample_aig.to_edge_list()))

    assert edge_attr.ndim == 2
    assert edge_attr.shape[0] == edge_index.shape[1]
    assert edge_attr.shape[1] == 1

    assert node_attr.ndim == 2
    assert node_attr.shape[0] == sample_aig.size + sample_aig.num_pos
    assert node_attr.shape[1] == 2  # base int type + level


def test_to_graph_tensors_one_hot_dimensions(sample_aig: Aig) -> None:
    """Checks one-hot encoding dimensions for nodes and edges."""
    tensors = sample_aig.to_graph_tensors(
        node_encoding=NodeTensorEncoding.ONE_HOT,
        edge_encoding=EdgeTensorEncoding.ONE_HOT,
        include_level=False,
    )

    edge_attr = tensors["edge_attr"]
    node_attr = tensors["node_attr"]

    assert edge_attr.shape[1] == 2
    assert node_attr.shape[1] == 4


def test_to_graph_tensors_signed_edge_encoding_values(sample_aig: Aig) -> None:
    """Checks signed edge encoding maps to +1/-1 values."""
    tensors = sample_aig.to_graph_tensors(
        node_encoding=NodeTensorEncoding.INTEGER,
        edge_encoding=EdgeTensorEncoding.SIGNED,
        include_level=False,
    )
    edge_attr = np.from_dlpack(tensors["edge_attr"])

    assert edge_attr.shape[1] == 1
    unique_values = {float(v) for v in edge_attr[:, 0]}
    assert unique_values.issubset({-1.0, 1.0})


def test_to_graph_tensors_truth_table_feature_dim(sample_aig: Aig) -> None:
    """Checks truth-table feature expansion matches 2^num_pis."""
    tensors = sample_aig.to_graph_tensors(
        node_encoding=NodeTensorEncoding.ONE_HOT,
        edge_encoding=EdgeTensorEncoding.BINARY,
        include_level=False,
        include_fanout=True,
        include_truth_table=True,
    )

    node_attr = tensors["node_attr"]
    tt_dim = 2**sample_aig.num_pis
    assert node_attr.shape[1] == 4 + 1 + tt_dim


def test_to_graph_tensors_torch_from_dlpack(sample_aig: Aig) -> None:
    """Ensures PyTorch can consume all exported tensors via DLPack."""
    tensors = sample_aig.to_graph_tensors(
        node_encoding=NodeTensorEncoding.ONE_HOT,
        edge_encoding=EdgeTensorEncoding.BINARY,
    )

    edge_index = torch.from_dlpack(tensors["edge_index"])
    edge_attr = torch.from_dlpack(tensors["edge_attr"])
    node_attr = torch.from_dlpack(tensors["node_attr"])

    assert edge_index.shape[0] == 2
    assert edge_attr.shape[0] == edge_index.shape[1]
    assert node_attr.shape[0] == sample_aig.size + sample_aig.num_pos
    assert edge_index.dtype == torch.int64
    assert edge_attr.dtype == torch.float32
    assert node_attr.dtype == torch.float32


def test_to_graph_tensors_numpy_from_dlpack(sample_aig: Aig) -> None:
    """Ensures NumPy can consume exported tensors via DLPack protocol."""
    tensors = sample_aig.to_graph_tensors(
        node_encoding=NodeTensorEncoding.INTEGER,
        edge_encoding=EdgeTensorEncoding.BINARY,
    )

    edge_index = np.from_dlpack(tensors["edge_index"])
    edge_attr = np.from_dlpack(tensors["edge_attr"])
    node_attr = np.from_dlpack(tensors["node_attr"])

    assert edge_index.shape[0] == 2
    assert edge_attr.shape[0] == edge_index.shape[1]
    assert node_attr.shape[0] == sample_aig.size + sample_aig.num_pos
    assert edge_index.dtype == np.int64
    assert edge_attr.dtype == np.float32
    assert node_attr.dtype == np.float32


def test_to_graph_tensors_dlpack_pointer_aliasing(sample_aig: Aig) -> None:
    """Checks Torch and NumPy views share the same backing storage pointer."""
    tensors = sample_aig.to_graph_tensors(
        node_encoding=NodeTensorEncoding.INTEGER,
        edge_encoding=EdgeTensorEncoding.BINARY,
    )

    edge_attr_torch = torch.from_dlpack(tensors["edge_attr"])
    edge_attr_np = np.from_dlpack(tensors["edge_attr"])

    assert edge_attr_torch.data_ptr() == edge_attr_np.__array_interface__["data"][0]


def test_to_graph_tensors_dlpack_mutation_propagation(sample_aig: Aig) -> None:
    """Checks mutations in Torch are visible in NumPy for the same DLPack export."""
    tensors = sample_aig.to_graph_tensors(
        node_encoding=NodeTensorEncoding.INTEGER,
        edge_encoding=EdgeTensorEncoding.BINARY,
    )

    edge_attr_torch = torch.from_dlpack(tensors["edge_attr"])
    edge_attr_np = np.from_dlpack(tensors["edge_attr"])

    original = float(edge_attr_torch[0, 0].item())
    edge_attr_torch[0, 0] = original + 7.0

    assert float(edge_attr_np[0, 0]) == pytest.approx(original + 7.0)


def test_to_graph_tensors_large_aig_shapes_and_dtypes(large_aig: Aig) -> None:
    """Checks export invariants on a larger AIG."""
    tensors = large_aig.to_graph_tensors(
        node_encoding=NodeTensorEncoding.ONE_HOT,
        edge_encoding=EdgeTensorEncoding.SIGNED,
        include_level=True,
        include_fanout=True,
        include_truth_table=False,
    )

    edge_index = np.from_dlpack(tensors["edge_index"])
    edge_attr = np.from_dlpack(tensors["edge_attr"])
    node_attr = np.from_dlpack(tensors["node_attr"])

    assert edge_index.shape == (2, len(list(large_aig.to_edge_list())))
    assert edge_attr.shape == (edge_index.shape[1], 1)
    assert node_attr.shape[0] == large_aig.size + large_aig.num_pos
    assert node_attr.shape[1] == 6  # one-hot(4) + level + fanout

    assert edge_index.dtype == np.int64
    assert edge_attr.dtype == np.float32
    assert node_attr.dtype == np.float32


def test_to_graph_tensors_empty_aig_edge_case() -> None:
    """Checks tensor export for an empty AIG (no PIs, no POs, no gates)."""
    empty_aig = Aig()
    tensors = empty_aig.to_graph_tensors(
        node_encoding=NodeTensorEncoding.INTEGER,
        edge_encoding=EdgeTensorEncoding.ONE_HOT,
        include_level=False,
        include_fanout=False,
        include_truth_table=False,
    )

    edge_index = np.from_dlpack(tensors["edge_index"])
    edge_attr = np.from_dlpack(tensors["edge_attr"])
    node_attr = np.from_dlpack(tensors["node_attr"])

    assert edge_index.shape == (2, 0)
    assert edge_attr.shape == (0, 2)
    assert node_attr.shape == (empty_aig.size + empty_aig.num_pos, 1)

    assert edge_index.dtype == np.int64
    assert edge_attr.dtype == np.float32
    assert node_attr.dtype == np.float32
