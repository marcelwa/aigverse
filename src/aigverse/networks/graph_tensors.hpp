#pragma once

#include "aigverse/types.hpp"

#include "edge_list.hpp"

#include <kitty/bit_operations.hpp>
#include <mockturtle/algorithms/simulation.hpp>  // NOLINT(misc-include-cleaner)
#include <mockturtle/utils/node_map.hpp>         // NOLINT(misc-include-cleaner)
#include <mockturtle/views/depth_view.hpp>
#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>

#include <cstddef>
#include <cstdint>
#include <initializer_list>
#include <memory>
#include <optional>
#include <utility>
#include <vector>

namespace aigverse
{

/**
 * @brief Node encoding mode for exported graph tensors.
 *
 * This enum controls how categorical node type features are represented
 * in the exported tensors. The types will be `float32` for all modes, but the encoding scheme differs:
 * - `INTEGER`: Node types are represented as integer class labels.
 * - `ONE_HOT`: Node types are represented as one-hot encoded vectors, where the dimension corresponds to the number
 *              of node categories in the order `[constant, pi, gate, po]`.
 */
enum class node_tensor_encoding : uint8_t
{
    /// Labels are encoded as 0.0 (constant), 1.0 (PI), 2.0 (gate), and 3.0 (PO).
    INTEGER,
    /// Labels are encoded as one-hot vectors in the order [constant, pi, gate, po].
    ONE_HOT,
};

/**
 * @brief Edge encoding mode for exported graph tensors.
 *
 * This enum controls how categorical edge type features are represented
 * in the exported tensors. The types will be `float32` for all modes, but the encoding scheme differs:
 * - `BINARY`: Edge polarity is represented as binary indicators (0.0 or 1.0).
 * - `SIGNED`: Edge polarity is represented as +1.0 for regular and -1.0 for inverted.
 * - `ONE_HOT`: Edge polarity is represented as one-hot encoded vectors in the order `[regular, inverted]`.
 */
enum class edge_tensor_encoding : uint8_t
{
    /// Labels are encoded as 0.0 (regular) and 1.0 (inverted).
    BINARY,
    /// Labels are encoded as +1.0 (regular) and -1.0 (inverted).
    SIGNED,
    /// Labels are encoded as one-hot vectors in the order [regular, inverted].
    ONE_HOT,
};

namespace detail
{

/**
 * @brief Creates an owning NumPy-backed nanobind ndarray from a moved vector.
 *
 * The returned array keeps data alive via capsule-managed ownership of a heap
 * vector, making it safe to consume through DLPack in downstream frameworks.
 *
 * @tparam T Element type.
 * @param data Moved data buffer.
 * @param shape Target tensor shape.
 * @return NumPy-backed ndarray that owns the provided data.
 */
template <typename T>
nanobind::ndarray<nanobind::numpy, T> make_owned_ndarray(std::vector<T>&&                     data,
                                                         const std::initializer_list<size_t>& shape)
{
    namespace nb = nanobind;

    // Use unique_ptr as an exception-safe staging owner while creating the capsule.
    // Once the capsule is constructed, ownership is intentionally transferred to
    // the capsule deleter via release().
    auto  storage     = std::make_unique<std::vector<T>>(std::move(data));
    auto* raw_storage = storage.get();
    // nanobind::capsule stores a raw pointer plus a C-style destructor callback.
    // The callback is the final owner and performs the matching delete.
    nb::capsule owner(raw_storage,
                      [](void* ptr) noexcept
                      {
                          delete static_cast<std::vector<T>*>(ptr);  // NOLINT(cppcoreguidelines-owning-memory)
                      });
    storage.release();

    return nb::ndarray<nb::numpy, T>(raw_storage->data(), shape, owner);
}
/**
 * @brief Exports an AIG-style network to sparse COO-like graph tensors.
 *
 * The result dictionary contains:
 * - ``edge_index`` with shape ``(2, E)``
 * - ``edge_attr`` with shape ``(E, D_edge)``
 * - ``node_attr`` with shape ``(N, D_node)``
 *
 * All returned tensors are NumPy-backed ndarrays and can be consumed by DLPack
 * consumers (e.g., PyTorch via ``torch.from_dlpack``).
 *
 * @tparam Ntk Network type.
 * @param ntk Input network.
 * @param node_encoding Node-type encoding mode.
 * @param edge_encoding Edge-type encoding mode.
 * @param include_level Whether to append depth-based level features.
 * @param include_fanout Whether to append fanout-size features.
 * @param include_truth_table Whether to append truth-table bits.
 * @return Dictionary of exported tensors.
 */
template <typename Ntk>
nanobind::dict to_graph_tensors(const Ntk& ntk, const node_tensor_encoding node_encoding,
                                const edge_tensor_encoding edge_encoding, const bool include_level,
                                const bool include_fanout, const bool include_truth_table)
{
    namespace nb = nanobind;

    constexpr size_t node_type_one_hot_dim = 4;

    constexpr int64_t type_constant = 0;
    constexpr int64_t type_pi       = 1;
    constexpr int64_t type_gate     = 2;
    constexpr int64_t type_po       = 3;

    const auto edges      = aigverse::to_edge_list(ntk).edges;
    const auto edge_count = edges.size();

    std::vector<int64_t> edge_index(2 * edge_count, 0);
    for (size_t i = 0; i < edge_count; ++i)
    {
        edge_index[i]              = static_cast<int64_t>(edges[i].source);
        edge_index[edge_count + i] = static_cast<int64_t>(edges[i].target);
    }

    const size_t edge_dim = edge_encoding == edge_tensor_encoding::ONE_HOT ? 2 : 1;

    std::vector<float> edge_attr(edge_count * edge_dim, 0.0f);
    for (size_t i = 0; i < edge_count; ++i)
    {
        const auto inverted = edges[i].weight != 0;
        switch (edge_encoding)
        {
            case edge_tensor_encoding::BINARY:
            {
                edge_attr[i] = inverted ? 1.0f : 0.0f;
                break;
            }
            case edge_tensor_encoding::SIGNED:
            {
                edge_attr[i] = inverted ? -1.0f : 1.0f;
                break;
            }
            case edge_tensor_encoding::ONE_HOT:
            {
                edge_attr[i * 2]       = inverted ? 0.0f : 1.0f;
                edge_attr[(i * 2) + 1] = inverted ? 1.0f : 0.0f;
                break;
            }
        }
    }

    size_t tt_dim = 0;

    std::optional<mockturtle::node_map<aigverse::truth_table, Ntk>> node_tts{};
    std::vector<aigverse::truth_table>                              output_tts{};
    if (include_truth_table)
    {
        node_tts = mockturtle::simulate_nodes<aigverse::truth_table>(
            ntk, mockturtle::default_simulator<aigverse::truth_table>{static_cast<unsigned>(ntk.num_pis())});
        output_tts = mockturtle::simulate<aigverse::truth_table>(
            ntk, mockturtle::default_simulator<aigverse::truth_table>{static_cast<unsigned>(ntk.num_pis())});

        if (ntk.size() > 0)
        {
            tt_dim = node_tts.value()[ntk.get_constant(false)].num_bits();
        }
    }

    const size_t base_dim = node_encoding == node_tensor_encoding::ONE_HOT ? node_type_one_hot_dim : 1;
    const size_t node_dim =
        base_dim + (include_level ? 1 : 0) + (include_fanout ? 1 : 0) + (include_truth_table ? tt_dim : 0);
    const size_t node_count = ntk.size() + ntk.num_pos();

    std::vector<float> node_attr(node_count * node_dim, 0.0f);

    std::optional<mockturtle::depth_view<Ntk>> depth_ntk{};
    if (include_level)
    {
        depth_ntk.emplace(ntk);
    }
    const auto po_level = include_level ? static_cast<float>(depth_ntk->depth() + 1) : 0.0f;

    const auto fill_base = [&](const size_t row, const int64_t type_index) -> size_t
    {
        const size_t offset = row * node_dim;
        if (node_encoding == node_tensor_encoding::INTEGER)
        {
            node_attr[offset] = static_cast<float>(type_index);
            return offset + 1;
        }

        node_attr[offset + static_cast<size_t>(type_index)] = 1.0f;
        return offset + node_type_one_hot_dim;
    };

    ntk.foreach_node(
        [&](const auto& n)
        {
            const auto row        = static_cast<size_t>(ntk.node_to_index(n));
            int64_t    type_index = type_gate;
            if (ntk.is_constant(n))
            {
                type_index = type_constant;
            }
            else if (ntk.is_pi(n))
            {
                type_index = type_pi;
            }

            auto feature_offset = fill_base(row, type_index);

            if (include_level)
            {
                node_attr[feature_offset++] = static_cast<float>(depth_ntk->level(n));
            }
            if (include_fanout)
            {
                node_attr[feature_offset++] = static_cast<float>(ntk.fanout_size(n));
            }
            if (include_truth_table)
            {
                const auto& tt = node_tts.value()[n];
                for (size_t i = 0; i < tt_dim; ++i)
                {
                    node_attr[feature_offset + i] = kitty::get_bit(tt, static_cast<uint64_t>(i)) ? 1.0f : 0.0f;
                }
            }
        });

    ntk.foreach_po(
        [&](const auto& po)
        {
            const auto po_idx = static_cast<size_t>(ntk.po_index(po));
            const auto row    = static_cast<size_t>(ntk.size()) + po_idx;

            auto feature_offset = fill_base(row, type_po);

            if (include_level)
            {
                node_attr[feature_offset++] = po_level;
            }
            if (include_fanout)
            {
                node_attr[feature_offset++] = 0.0f;
            }
            if (include_truth_table)
            {
                const auto& tt = output_tts[po_idx];
                for (size_t i = 0; i < tt_dim; ++i)
                {
                    node_attr[feature_offset + i] = kitty::get_bit(tt, i) ? 1.0f : 0.0f;
                }
            }
        });

    auto result = nb::dict();

    result["edge_index"] = make_owned_ndarray(std::move(edge_index), {2, edge_count});
    result["edge_attr"]  = make_owned_ndarray(std::move(edge_attr), {edge_count, edge_dim});
    result["node_attr"]  = make_owned_ndarray(std::move(node_attr), {node_count, node_dim});

    return result;
}

}  // namespace detail

}  // namespace aigverse
