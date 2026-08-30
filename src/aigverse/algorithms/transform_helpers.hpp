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
 * The copy is also what makes the released GIL safe, and the rule the `algorithms` bindings follow: a binding may
 * release the GIL only if it never writes to the caller's network. Every mockturtle view shares that network's storage
 * rather than copying it, and the marking mutators (`incr_trav_id`, `set_visited`, `clear_values`) are `const` members
 * writing through that shared storage, so a `const Ntk&` is not a promise of read-only. A binding whose algorithm
 * builds a view therefore either runs on a clone, as this function and `balancing`, `aig_cut_rewriting`, and
 * `equivalence_checking` do, or keeps the GIL, as `cleanup_dangling` does.
 *
 * The in-place path writes to the caller's network by definition, so a network transformed in place must not be shared
 * across threads.
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
