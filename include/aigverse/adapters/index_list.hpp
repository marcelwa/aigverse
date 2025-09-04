//
// Created by marcel on 02.05.25.
//

#ifndef AIGVERSE_INDEX_LIST_HPP
#define AIGVERSE_INDEX_LIST_HPP

#include "aigverse/types.hpp"

#include <fmt/format.h>
#include <fmt/ranges.h>
#include <mockturtle/utils/index_list.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <cstddef>
#include <cstdint>
#include <string>
#include <tuple>
#include <vector>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void ntk_index_list(pybind11::module_& m, const std::string& network_name);

extern template void ntk_index_list<aigverse::aig>(pybind11::module_& m, const std::string& network_name);

}  // namespace detail

// Wrapper declaration (implemented in .cpp)
void bind_to_index_list(pybind11::module_& m);

}  // namespace aigverse

namespace fmt
{

// make index_list compatible with fmt::format
template <>
struct formatter<aigverse::aig_index_list>
{
    template <typename ParseContext>
    constexpr auto parse(ParseContext& ctx)
    {
        return ctx.begin();
    }

    template <typename FormatContext>
    auto format(const aigverse::aig_index_list& il, FormatContext& ctx) const
    {
        std::vector<std::tuple<uint32_t, uint32_t>> gates{};
        gates.reserve(il.num_gates());

        il.foreach_gate([&gates](const auto& lit0, const auto& lit1) { gates.emplace_back(lit0, lit1); });

        std::vector<uint32_t> outputs{};
        outputs.reserve(il.num_pos());

        il.foreach_po([&outputs](const auto& lit) { outputs.push_back(lit); });

        return format_to(ctx.out(), "#PIs: {}, #POs: {}, #Gates: {}, Gates: {}, POs: {}", il.num_pis(), il.num_pos(),
                         il.num_gates(), gates, outputs);
    }
};

}  // namespace fmt

#endif  // AIGVERSE_INDEX_LIST_HPP
