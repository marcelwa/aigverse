#include "aigverse/types.hpp"

#include "transform_helpers.hpp"

#include <mockturtle/algorithms/cleanup.hpp>
#include <mockturtle/algorithms/collapse_mapped.hpp>
#include <mockturtle/algorithms/lut_mapper.hpp>
#include <mockturtle/algorithms/lut_mapping.hpp>
#include <mockturtle/algorithms/satlut_mapping.hpp>
#include <mockturtle/utils/name_utils.hpp>
#include <mockturtle/views/mapping_view.hpp>
#include <nanobind/nanobind.h>
#include <nanobind/stl/optional.h>  // NOLINT(misc-include-cleaner)
#include <nanobind/stl/string.h>    // NOLINT(misc-include-cleaner)

#include <cstdint>
#include <limits>
#include <optional>
#include <stdexcept>
#include <string>
#include <type_traits>

namespace aigverse
{
namespace
{
namespace nb = nanobind;

uint32_t unsigned_parameter(const int64_t value, const char* name,
                            const uint32_t maximum = std::numeric_limits<uint32_t>::max())
{
    if (value < 0 || static_cast<uint64_t>(value) > maximum)
    {
        throw std::invalid_argument(std::string(name) + " must be between 0 and " + std::to_string(maximum));
    }
    return static_cast<uint32_t>(value);
}

template <typename Ntk, typename Result>
void bind_mapping(nb::module_& m)
{
    m.def(
        "lut_mapping",
        [](const Ntk& ntk, const std::string& algorithm, const int64_t cut_size, const int64_t cut_limit,
           const std::optional<bool> area_oriented_mapping, const int64_t area_flow_rounds,
           const std::optional<int64_t> ela_rounds, const bool verbose, const std::optional<bool> compute_truth,
           const std::optional<bool> minimize_truth_table, const std::optional<int64_t> required_delay,
           const std::optional<int64_t> relax_required, const std::optional<bool> recompute_cuts,
           const std::optional<int64_t> area_share_rounds, const std::optional<bool> edge_optimization,
           const std::optional<bool> cut_expansion, const std::optional<bool> remove_dominated_cuts,
           const std::optional<int64_t> conflict_limit, const std::optional<int64_t> window_size) -> Result
        {
            detail::require_combinational(ntk);
            const bool heuristic = algorithm == "heuristic";
            const bool sat       = algorithm == "sat" || algorithm == "sat_windowed";
            if (!heuristic && !sat && algorithm != "classic")
            {
                throw nb::value_error("algorithm must be 'heuristic', 'classic', 'sat', or 'sat_windowed'");
            }
            if (cut_size < 2 || cut_size > 16)
            {
                throw nb::value_error("cut_size must be between 2 and 16");
            }
            if (cut_limit < 1 || cut_limit > (heuristic ? 31 : 24))
            {
                throw nb::value_error("cut_limit must be between 1 and 31 for heuristic, or 1 and 24 otherwise");
            }
            if (!heuristic &&
                (compute_truth.has_value() || minimize_truth_table.has_value() || required_delay.has_value() ||
                 relax_required.has_value() || recompute_cuts.has_value() || area_share_rounds.has_value() ||
                 edge_optimization.has_value() || cut_expansion.has_value() || remove_dominated_cuts.has_value()))
            {
                throw nb::value_error("these controls are supported only by algorithm='heuristic'");
            }
            if (!heuristic && !area_oriented_mapping.value_or(true))
            {
                throw nb::value_error("classic and SAT mapping require area_oriented_mapping=True");
            }
            if (conflict_limit.has_value() && !sat)
            {
                throw nb::value_error("conflict_limit is supported only by SAT mapping");
            }
            if (window_size.has_value() && algorithm != "sat_windowed")
            {
                throw nb::value_error("window_size is supported only by algorithm='sat_windowed'");
            }

            mockturtle::lut_map_params modern{};
            modern.cut_enumeration_ps.cut_size             = static_cast<uint32_t>(cut_size);
            modern.cut_enumeration_ps.cut_limit            = static_cast<uint32_t>(cut_limit);
            const bool truth                               = compute_truth.value_or(false);
            modern.cut_enumeration_ps.minimize_truth_table = minimize_truth_table.value_or(truth);
            modern.area_oriented_mapping                   = area_oriented_mapping.value_or(!heuristic);
            modern.area_flow_rounds                        = unsigned_parameter(area_flow_rounds, "area_flow_rounds");
            modern.ela_rounds            = unsigned_parameter(ela_rounds.value_or(heuristic ? 2 : 1), "ela_rounds");
            modern.area_share_rounds     = unsigned_parameter(area_share_rounds.value_or(2), "area_share_rounds");
            modern.required_delay        = unsigned_parameter(required_delay.value_or(0), "required_delay");
            modern.relax_required        = unsigned_parameter(relax_required.value_or(0), "relax_required");
            modern.recompute_cuts        = recompute_cuts.value_or(true);
            modern.edge_optimization     = edge_optimization.value_or(true);
            modern.cut_expansion         = cut_expansion.value_or(modern.recompute_cuts && !truth);
            modern.remove_dominated_cuts = remove_dominated_cuts.value_or(true);
            modern.verbose               = verbose;
            if (modern.cut_enumeration_ps.minimize_truth_table && !truth)
            {
                throw nb::value_error("minimize_truth_table=True requires compute_truth=True");
            }
            if (modern.cut_expansion && (truth || !modern.recompute_cuts))
            {
                throw nb::value_error("cut_expansion=True requires recompute_cuts=True and compute_truth=False");
            }
            if (modern.area_oriented_mapping && (required_delay.has_value() || relax_required.has_value()))
            {
                throw nb::value_error("timing controls require area_oriented_mapping=False");
            }
            if (modern.required_delay > 0 && modern.relax_required > 0)
            {
                throw nb::value_error("required_delay and relax_required cannot both be positive");
            }
            // Native percentage relaxation converts the scaled depth back to uint32_t.
            if (ntk.num_gates() != 0 &&
                modern.relax_required > (uint64_t{100} * std::numeric_limits<uint32_t>::max() / ntk.num_gates()) - 100)
            {
                throw nb::value_error("relax_required may overflow the native depth range for this network");
            }
            if (static_cast<uint64_t>(modern.area_flow_rounds) + modern.ela_rounds +
                    (heuristic ? modern.area_share_rounds + uint64_t{3} : uint64_t{1}) >
                std::numeric_limits<uint32_t>::max())
            {
                throw nb::value_error("combined mapping rounds exceed the uint32 range");
            }
            const auto conflicts =
                unsigned_parameter(conflict_limit.value_or(10000), "conflict_limit", std::numeric_limits<int>::max());
            const auto window = unsigned_parameter(window_size.value_or(32), "window_size");
            if (window == 0)
            {
                throw nb::value_error("window_size must be positive");
            }

            const auto                   snapshot = detail::snapshot_network(ntk);
            const nb::gil_scoped_release release{};
            auto                         cleaned = mockturtle::cleanup_dangling(snapshot);
            klut                         mapped;
            if (heuristic && cleaned.num_gates() != 0)
            {
                mapped = truth ? mockturtle::lut_map<Ntk, true>(cleaned, modern) : mockturtle::lut_map(cleaned, modern);
            }
            else
            {
                mockturtle::mapping_view<aig> mapping(cleaned);
                if (cleaned.num_gates() != 0)
                {
                    mockturtle::lut_mapping_params classic{};
                    classic.cut_enumeration_ps.cut_size = static_cast<uint32_t>(cut_size);
                    // Classic/SAT reserve one retained cut for the node itself.
                    classic.cut_enumeration_ps.cut_limit = static_cast<uint32_t>(cut_limit + 1);
                    classic.rounds                       = modern.area_flow_rounds + 1;
                    classic.rounds_ela                   = modern.ela_rounds;
                    classic.verbose                      = verbose;
                    mockturtle::lut_mapping(mapping, classic);
                    if (sat)
                    {
                        mockturtle::satlut_mapping_params recovery{};
                        recovery.cut_enumeration_ps = classic.cut_enumeration_ps;
                        recovery.conflict_limit     = conflicts;
                        recovery.verbose            = verbose;
                        if (algorithm == "sat_windowed")
                        {
                            mockturtle::satlut_mapping(mapping, window, recovery);
                        }
                        else
                        {
                            mockturtle::satlut_mapping(mapping, recovery);
                        }
                    }
                }
                auto collapsed = mockturtle::collapse_mapped_network<klut>(mapping);
                if (!collapsed)
                {
                    throw std::runtime_error("LUT mapping could not be collapsed");
                }
                mapped = *collapsed;
            }
            Result result(mapped);
            if constexpr (std::is_same_v<Result, named_klut>)
            {
                mockturtle::restore_pio_names_by_order(snapshot, result);
                mockturtle::restore_network_name(snapshot, result);
            }
            return result;
        },
        nb::arg("ntk"), nb::kw_only(), nb::arg("algorithm") = "heuristic", nb::arg("cut_size") = 6,
        nb::arg("cut_limit") = 8, nb::arg("area_oriented_mapping") = nb::none(), nb::arg("area_flow_rounds") = 1,
        nb::arg("ela_rounds") = nb::none(), nb::arg("verbose") = false, nb::arg("compute_truth") = nb::none(),
        nb::arg("minimize_truth_table") = nb::none(), nb::arg("required_delay") = nb::none(),
        nb::arg("relax_required") = nb::none(), nb::arg("recompute_cuts") = nb::none(),
        nb::arg("area_share_rounds") = nb::none(), nb::arg("edge_optimization") = nb::none(),
        nb::arg("cut_expansion") = nb::none(), nb::arg("remove_dominated_cuts") = nb::none(),
        nb::arg("conflict_limit") = nb::none(), nb::arg("window_size") = nb::none(),
        R"pb(Maps a combinational AIG to a fresh k-LUT network, preserving its interface.

Args:
    ntk: The AIG to map. NamedAig produces NamedKlut with PI/PO names and order preserved.
    algorithm: ``"heuristic"`` (default), ``"classic"``, ``"sat"``, or ``"sat_windowed"``.
        SAT modes improve a classic seed on the original AIG before collapsing it.
    cut_size: Maximum LUT fanin count, from 2 to 16.
    cut_limit: Retained nontrivial cuts per node, from 1 to 31 for heuristic or 1 to 24 otherwise.
    area_oriented_mapping: Defaults to False for heuristic, True otherwise. Only heuristic supports False.
    area_flow_rounds: Additional area-flow passes after initialization, nonnegative.
    ela_rounds: Exact local area passes, nonnegative. Defaults to 2 for heuristic, 1 otherwise.
    verbose: Whether to print native progress information.
    compute_truth: Heuristic only; compute cut truth tables during mapping (default False).
        Every returned LUT has its truth table regardless of this setting.
    minimize_truth_table: Heuristic only; minimize cut support. Defaults to compute_truth;
        True requires compute_truth=True.
    required_delay: Heuristic only; absolute depth target (default 0, no target).
    relax_required: Heuristic only; percentage depth relaxation (default 0).
        Extreme values are rejected using the input gate count as a conservative bound on depth.
        Timing controls require delay orientation and cannot both be positive. They are heuristic targets.
    recompute_cuts: Heuristic only; recompute cuts at each pass (default True).
    area_share_rounds: Heuristic only; backward area-sharing passes (default 2).
    edge_optimization: Heuristic only; reduce LUT input edges (default True).
    cut_expansion: Heuristic only; expand cuts. Defaults to True only with recompute_cuts=True
        and compute_truth=False; explicitly enabling it otherwise is invalid.
    remove_dominated_cuts: Heuristic only; discard contained cuts (default True).
    conflict_limit: SAT modes only; conflicts per solve (default 10000, 0 means unlimited), at most INT_MAX.
        This is neither a cumulative resource limit nor an optimality certificate.
    window_size: sat_windowed only; positive maximum number of original-network gates per window (default 32).

Returns:
    An independent Klut, or NamedKlut for NamedAig. The input is unchanged.

Raises:
    TypeError: If an integer control is outside the signed 64-bit range accepted by the binding.
    ValueError: If the input is sequential, a control is out of range, or controls are incompatible.)pb");
}
}  // namespace

void bind_lut_mapping(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    bind_mapping<named_aig, named_klut>(m);
    bind_mapping<aig, klut>(m);
}
}  // namespace aigverse
