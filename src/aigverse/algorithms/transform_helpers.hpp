//
// Created by marcel on 06.03.26.
//

#pragma once

#include <mockturtle/algorithms/cleanup.hpp>

#include <optional>
#include <utility>

namespace aigverse::detail
{

/**
 * @brief Helper function to run a transformation either in-place or on a copy of the input network.
 *
 * @tparam Ntk The type of the logic network.
 * @tparam Fn The type of the transformation function, which should accept a non-const reference to an Ntk.
 * @param ntk The input logic network to transform.
 * @param inplace Whether to perform the transformation in-place on the input network (if true) or on a copy (if false).
 * @param fn The transformation function to apply.
 * @return The transformed network if not in-place, otherwise std::nullopt.
 */
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
