//
// Created by marcel on 06.03.26.
//

#pragma once

#include <mockturtle/algorithms/cleanup.hpp>

#include <optional>
#include <utility>

namespace aigverse::detail
{

template <typename Ntk, typename Fn>
std::optional<Ntk> run_transform(Ntk& ntk, const bool inplace, Fn&& fn)
{
    if (inplace)
    {
        std::forward<Fn>(fn)(ntk);
        return std::nullopt;
    }

    auto ntk_clone = ntk.clone();
    std::forward<Fn>(fn)(ntk_clone);
    return mockturtle::cleanup_dangling(ntk_clone);
}

}  // namespace aigverse::detail
