#pragma once

#include "aigverse/types.hpp"

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
#include <stdexcept>
#include <utility>
#include <vector>

namespace aigverse
{

/**
 * @brief Node encoding mode for exported graph tensors.
 *
 * This enum controls how the categorical node-type prefix is laid out inside
 * ``node_attr``. All exported node features use ``float32`` storage so the
 * result can be consumed directly by NumPy/DLPack users without dtype juggling.
 *
 * The node-type categories always appear in the canonical order
 * ``[constant, pi, gate, po]``:
 * - `INTEGER`: Store that category as a single scalar label.
 * - `ONE_HOT`: Store that category as a one-hot prefix of length four.
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
 * This enum controls how edge polarity is laid out inside ``edge_attr``.
 * As with node features, all edge features use ``float32`` storage.
 *
 * The polarity categories always appear in the canonical order
 * ``[regular, inverted]``:
 * - `BINARY`: Store polarity as ``0.0`` or ``1.0``.
 * - `SIGNED`: Store polarity as ``+1.0`` or ``-1.0``.
 * - `ONE_HOT`: Store polarity as a length-two one-hot vector.
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
 * This overload is convenient when the exporter naturally materializes a
 * ``std::vector`` first.
 *
 * @tparam T Element type.
 * @param data Moved data buffer.
 * @param shape Target tensor shape.
 * @return NumPy-backed ndarray that owns the provided data.
 */
template <typename T>
nanobind::ndarray<nanobind::numpy, T> make_owned_ndarray(std::vector<T>&&                          data,
                                                         const std::initializer_list<std::size_t>& shape)
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

template <typename T>
// Raw contiguous storage is intentional here because the export hot path
// fully overwrites the buffer before handing it off to nanobind.
// NOLINTNEXTLINE(*-avoid-c-arrays)
nanobind::ndarray<nanobind::numpy, T> make_owned_ndarray(std::unique_ptr<T[]>&&                    data,
                                                         const std::initializer_list<std::size_t>& shape)
{
    namespace nb = nanobind;

    auto        storage     = std::move(data);
    auto*       raw_storage = storage.release();
    nb::capsule owner(raw_storage,
                      [](void* ptr) noexcept
                      {
                          delete[] static_cast<T*>(ptr);  // NOLINT(cppcoreguidelines-owning-memory)
                      });

    return nb::ndarray<nb::numpy, T>(raw_storage, shape, owner);
}

/**
 * @brief Expands one dynamic truth table into a contiguous float feature slice.
 *
 * ``kitty::dynamic_truth_table`` stores bits in 64-bit blocks. Iterating those
 * blocks directly avoids paying the helper-call and index-arithmetic overhead of
 * ``kitty::get_bit`` for every output feature.
 *
 * @param destination Start of the destination feature slice.
 * @param tt Source truth table.
 * @param invert Whether to invert each exported bit.
 */
// Direct writes into the caller-provided slice are a performance optimization.
// NOLINTBEGIN(cppcoreguidelines-pro-bounds-pointer-arithmetic)
inline void write_truth_table_bits(float* destination, const aigverse::truth_table& tt, const bool invert = false)
{
    std::size_t bit_offset = 0;
    const auto  tt_dim     = static_cast<std::size_t>(tt.num_bits());

    for (const auto block : tt)
    {
        const auto remaining_bits = tt_dim - bit_offset;
        const auto block_bits     = remaining_bits < 64 ? remaining_bits : 64;
        const auto bits           = invert ? ~block : block;

        for (std::size_t bit = 0; bit < block_bits; ++bit)
        {
            destination[bit_offset + bit] = static_cast<float>((bits >> bit) & 0x1ULL);
        }

        bit_offset += block_bits;
    }
}
// NOLINTEND(cppcoreguidelines-pro-bounds-pointer-arithmetic)

/**
 * @brief Exports an AIG-style network to sparse COO-like graph tensors.
 *
 * The result dictionary contains:
 * - ``edge_index`` with shape ``(2, E)``
 * - ``edge_attr`` with shape ``(E, D_edge)``
 * - ``node_attr`` with shape ``(N, D_node)``
 *
 * Export order is stable and intentionally simple:
 * - rows ``[0, ntk.size())`` in ``node_attr`` correspond to ``foreach_node``
 *   order
 * - rows ``[ntk.size(), ntk.size() + ntk.num_pos())`` correspond to synthetic
 *   PO rows in ``foreach_po`` order
 * - columns in ``edge_index`` are emitted in the same order as the exporter
 *   traverses fanins, then POs, then optional register inputs
 *
 * All returned tensors are NumPy-backed ndarrays and can be consumed by DLPack
 * consumers such as PyTorch via ``torch.from_dlpack``.
 *
 * The implementation is written around the export hot path: it precomputes the
 * exact output sizes, fills the buffers linearly, avoids repeated PO index
 * lookups by using row counters, and uses raw arrays for buffers that are fully
 * overwritten to avoid paying an unnecessary zero-fill cost.
 *
 * @tparam Ntk Network type.
 * @param ntk Input network.
 * @param node_encoding Node-type encoding mode.
 * @param edge_encoding Edge-type encoding mode.
 * @param levels Whether to append depth-based level features.
 * @param fanouts Whether to append fanout-size features.
 * @param node_tts Whether to append node truth-table bits.
 * @return Dictionary of exported tensors.
 */
template <typename Ntk>
nanobind::dict to_graph_tensors(const Ntk& ntk, const node_tensor_encoding node_encoding,

                                /**
                                 * @brief Creates an owning NumPy-backed nanobind ndarray from a raw array.
                                 *
                                 * This overload exists for the hot export path, where the tensor storage is
                                 * fully overwritten and a raw array avoids the default zero-initialization that
                                 * ``std::vector(count, value)`` would perform.
                                 *
                                 * @tparam T Element type.
                                 * @param data Moved raw array buffer.
                                 * @param shape Target tensor shape.
                                 * @return NumPy-backed ndarray that owns the provided data.
                                 */
                                const edge_tensor_encoding edge_encoding, const bool levels = false,
                                const bool fanouts = false, const bool node_tts = false)
{
    namespace nb = nanobind;

    // Number of node-type categories used for one-hot encodings:
    // [constant, primary input, internal gate, primary output].
    constexpr std::size_t node_type_one_hot_dim = 4;

    // Canonical integer labels for node types; shared across all node encodings.
    constexpr int64_t type_constant = 0;
    constexpr int64_t type_pi       = 1;
    constexpr int64_t type_gate     = 2;
    constexpr int64_t type_po       = 3;

    // Precompute the exact number of emitted edges so the export loops can fill
    // the destination buffers linearly without growth checks or reallocations.
    // This formula relies on AIG-style fixed fanin counts; the shared exporter
    // is intentionally optimized for that dominant case.
    std::size_t edge_count =
        (static_cast<std::size_t>(Ntk::max_fanin_size) * static_cast<std::size_t>(ntk.num_gates())) +
        static_cast<std::size_t>(ntk.num_pos());
    if constexpr (mockturtle::has_foreach_ri_v<Ntk> && mockturtle::has_ri_to_ro_v<Ntk>)
    {
        edge_count += static_cast<std::size_t>(ntk.num_registers());
    }

    // edge_index and edge_attr are fully overwritten during export, so raw
    // storage avoids paying for a zero-initialization pass that would be thrown
    // away immediately.
    // NOLINTBEGIN(*-avoid-c-arrays)
    std::unique_ptr<int64_t[]> edge_index{new int64_t[2 * edge_count]};

    const std::size_t edge_dim = edge_encoding == edge_tensor_encoding::ONE_HOT ? 2 : 1;

    std::unique_ptr<float[]> edge_attr{new float[edge_count * edge_dim]};
    // NOLINTEND(*-avoid-c-arrays)

    // Direct pointer-based writes benchmarked better than zero-filled vector
    // materialization for this exporter.
    // NOLINTBEGIN(cppcoreguidelines-pro-bounds-pointer-arithmetic)
    auto* edge_sources = edge_index.get();
    auto* edge_targets = edge_sources + edge_count;
    auto* edge_values  = edge_attr.get();

    std::size_t edge_cursor = 0;
    const auto  append_edge = [&](const int64_t source, const int64_t target, const bool inverted)
    {
        // edge_index is stored in the conventional COO layout with one row for
        // sources and one row for targets.
        edge_sources[edge_cursor] = source;
        edge_targets[edge_cursor] = target;

        // The encoding branch remains here because it is shared by all export
        // modes, but each branch writes directly into the final contiguous edge
        // buffer without temporary objects.
        switch (edge_encoding)
        {
            case edge_tensor_encoding::BINARY:
            {
                edge_values[edge_cursor] = inverted ? 1.0f : 0.0f;
                break;
            }
            case edge_tensor_encoding::SIGNED:
            {
                edge_values[edge_cursor] = inverted ? -1.0f : 1.0f;
                break;
            }
            case edge_tensor_encoding::ONE_HOT:
            {
                edge_values[edge_cursor * 2]       = inverted ? 0.0f : 1.0f;
                edge_values[(edge_cursor * 2) + 1] = inverted ? 1.0f : 0.0f;
                break;
            }
        }

        ++edge_cursor;
    };
    // NOLINTEND(cppcoreguidelines-pro-bounds-pointer-arithmetic)

    int64_t edge_target = 0;
    ntk.foreach_node(
        [&](const auto& n)
        {
            // Node rows are emitted in foreach_node order, so a monotonic
            // counter is enough and avoids repeated index remapping work.
            const auto target = edge_target++;
            ntk.foreach_fanin(n,
                              [&](const auto& f)
                              {
                                  const auto source = static_cast<int64_t>(ntk.node_to_index(ntk.get_node(f)));
                                  append_edge(source, target, ntk.is_complemented(f));
                              });
        });

    auto po_target = static_cast<int64_t>(ntk.size());
    ntk.foreach_po(
        [&](const auto& po)
        {
            // Synthetic PO rows are appended after the real network nodes.
            // Using a running target counter avoids the old repeated PO index
            // lookup, which was expensive on mockturtle AIGs because it scanned
            // the outputs linearly.
            const auto source = static_cast<int64_t>(ntk.node_to_index(ntk.get_node(po)));
            const auto target = po_target++;
            append_edge(source, target, ntk.is_complemented(po));
        });

    if constexpr (mockturtle::has_foreach_ri_v<Ntk> && mockturtle::has_ri_to_ro_v<Ntk>)
    {
        ntk.foreach_ri(
            [&](const auto& ri)
            {
                const auto source = static_cast<int64_t>(ntk.node_to_index(ntk.get_node(ri)));
                const auto target = static_cast<int64_t>(ntk.node_to_index(ntk.ri_to_ro(ri)));
                append_edge(source, target, ntk.is_complemented(ri));
            });
    }

    if (edge_cursor != edge_count)
    {
        throw std::runtime_error("inconsistent edge count during graph tensor export");
    }

    std::size_t tt_dim = 0;

    // Truth-table simulation is optional because it is by far the most
    // expensive feature family when enabled.
    std::optional<mockturtle::node_map<aigverse::truth_table, Ntk>> node_truth_tables{};
    if (node_tts)
    {
        if (ntk.num_pis() > 16)
        {
            throw std::invalid_argument("truth-table export is only supported up to 16 primary inputs");
        }

        node_truth_tables = mockturtle::simulate_nodes<aigverse::truth_table>(
            ntk, mockturtle::default_simulator<aigverse::truth_table>{static_cast<unsigned>(ntk.num_pis())});

        if (ntk.size() > 0)
        {
            tt_dim = node_truth_tables.value()[ntk.get_constant(false)].num_bits();
        }
    }

    const std::size_t base_dim   = node_encoding == node_tensor_encoding::ONE_HOT ? node_type_one_hot_dim : 1;
    const std::size_t node_dim   = base_dim + (levels ? 1 : 0) + (fanouts ? 1 : 0) + (node_tts ? tt_dim : 0);
    const std::size_t node_count = ntk.size() + ntk.num_pos();

    // node_attr is also fully overwritten row-by-row, so it gets the same raw
    // storage treatment as the edge buffers.
    // NOLINTNEXTLINE(*-avoid-c-arrays)
    std::unique_ptr<float[]> node_attr{new float[node_count * node_dim]};
    auto*                    node_values = node_attr.get();

    std::optional<mockturtle::depth_view<Ntk>> depth_ntk{};
    if (levels)
    {
        // Construct the depth view only when level features are requested.
        depth_ntk.emplace(ntk);
    }

    const auto* simulated_nodes = node_tts ? &node_truth_tables.value() : nullptr;

    // Direct feature-slice writes are intentional runtime optimizations.
    // NOLINTBEGIN(cppcoreguidelines-pro-bounds-pointer-arithmetic)
    const auto fill_base = [&](const std::size_t row, const int64_t type_index) -> float*
    {
        auto* row_data = node_values + (row * node_dim);
        if (node_encoding == node_tensor_encoding::INTEGER)
        {
            row_data[0] = static_cast<float>(type_index);
            return row_data + 1;
        }

        // Only the one-hot prefix needs clearing here. The trailing optional
        // features are written unconditionally by the code paths that enabled
        // them, so clearing the full row would just add extra memory traffic.
        row_data[0]                                    = 0.0f;
        row_data[1]                                    = 0.0f;
        row_data[2]                                    = 0.0f;
        row_data[3]                                    = 0.0f;
        row_data[static_cast<std::size_t>(type_index)] = 1.0f;
        return row_data + node_type_one_hot_dim;
    };

    std::size_t node_row = 0;
    ntk.foreach_node(
        [&](const auto& n)
        {
            // Node rows follow foreach_node order, so a linear cursor is enough
            // and matches the row numbers used by the edge exporter above.
            const auto row        = node_row++;
            int64_t    type_index = type_gate;
            if (ntk.is_constant(n))
            {
                type_index = type_constant;
            }
            else if (ntk.is_pi(n))
            {
                type_index = type_pi;
            }

            auto* feature_offset = fill_base(row, type_index);

            if (levels)
            {
                *feature_offset++ = static_cast<float>(depth_ntk->level(n));
            }
            if (fanouts)
            {
                *feature_offset++ = static_cast<float>(ntk.fanout_size(n));
            }
            if (node_tts)
            {
                write_truth_table_bits(feature_offset, (*simulated_nodes)[n]);
            }
        });

    std::size_t po_row = 0;
    ntk.foreach_po(
        [&](const auto& po)
        {
            // Synthetic PO feature rows are appended after real nodes in the
            // same order used for PO edges.
            const auto po_idx = po_row++;
            const auto row    = static_cast<std::size_t>(ntk.size()) + po_idx;
            const auto driver = ntk.get_node(po);

            auto* feature_offset = fill_base(row, type_po);

            if (levels)
            {
                *feature_offset++ = static_cast<float>(depth_ntk->level(driver) + 1);
            }
            if (fanouts)
            {
                *feature_offset++ = 0.0f;
            }
            if (node_tts)
            {
                write_truth_table_bits(feature_offset, (*simulated_nodes)[driver], ntk.is_complemented(po));
            }
        });
    // NOLINTEND(cppcoreguidelines-pro-bounds-pointer-arithmetic)

    auto result = nb::dict();

    // Hand off ownership to nanobind capsules so downstream DLPack consumers
    // can borrow the buffers without an extra copy.
    // NOLINTBEGIN(cppcoreguidelines-pro-bounds-avoid-unchecked-container-access)
    result["edge_index"] = make_owned_ndarray(std::move(edge_index), {2, edge_count});
    result["edge_attr"]  = make_owned_ndarray(std::move(edge_attr), {edge_count, edge_dim});
    result["node_attr"]  = make_owned_ndarray(std::move(node_attr), {node_count, node_dim});
    // NOLINTEND(cppcoreguidelines-pro-bounds-avoid-unchecked-container-access)

    return result;
}

}  // namespace detail

}  // namespace aigverse
