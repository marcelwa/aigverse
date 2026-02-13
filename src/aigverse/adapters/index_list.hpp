//
// Created by marcel on 02.05.25.
//

#pragma once

#include "aigverse/types.hpp"

#include <fmt/format.h>
#include <fmt/ranges.h>
#include <mockturtle/utils/index_list.hpp>

#include <cstdint>
#include <tuple>
#include <vector>

namespace aigverse
{

using aig_index_list = mockturtle::xag_index_list<true>;

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
