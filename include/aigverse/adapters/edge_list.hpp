//
// Created by marcel on 05.09.24.
//

#ifndef AIGVERSE_EDGE_LIST_HPP
#define AIGVERSE_EDGE_LIST_HPP

#include "aigverse/types.hpp"

#include <fmt/format.h>
#include <fmt/ranges.h>
#include <mockturtle/traits.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <cstdint>
#include <string>
#include <tuple>
#include <vector>

namespace aigverse
{

/**
 * Edge of a network.
 *
 * @tparam Ntk Network type.
 */
template <typename Ntk>
struct edge
{
    /**
     * Default constructor.
     */
    constexpr edge() noexcept = default;
    /**
     * Constructor.
     *
     * @param source Source node of the edge.
     * @param target Target node of the edge.
     * @param weight Weight of the edge.
     */
    constexpr edge(const mockturtle::node<Ntk>& source, const mockturtle::node<Ntk>& target,
                   const int64_t weight = 0) noexcept :
            source(source),
            target(target),
            weight(weight)
    {}
    /**
     * Equality operator.
     *
     * @param other Edge to compare with.
     * @return True if the edges are equal, false otherwise.
     */
    [[nodiscard]] constexpr bool operator==(const edge& other) const noexcept
    {
        return source == other.source && target == other.target && weight == other.weight;
    }
    /**
     * Inequality operator.
     *
     * @param other Edge to compare with.
     * @return True if the edges are not equal, false otherwise.
     */
    [[nodiscard]] constexpr bool operator!=(const edge& other) const noexcept
    {
        return !(*this == other);
    }
    /**
     * Implicit conversion to tuple.
     */
    [[nodiscard]] constexpr operator std::tuple<mockturtle::node<Ntk>, mockturtle::node<Ntk>, int64_t>() const noexcept
    {
        return {source, target, weight};
    }
    /**
     * Source node of the edge.
     */
    mockturtle::node<Ntk> source{};
    /**
     * Target node of the edge.
     */
    mockturtle::node<Ntk> target{};
    /**
     * Weight of the edge.
     */
    int64_t weight{0};
};
/**
 * List of edges of a network.
 *
 * @tparam Ntk Network type.
 */
template <typename Ntk>
struct edge_list
{
    /**
     * Default constructor.
     */
    edge_list() = default;
    /**
     * Constructor.
     *
     * @param ntk Network.
     */
    explicit edge_list(const Ntk& ntk) : ntk{ntk} {};
    /**
     * Constructor.
     *
     * @param ntk Network.
     * @param edges Edges of the network.
     */
    edge_list(const Ntk& ntk, const std::vector<edge<Ntk>>& edges) : ntk{ntk}, edges{edges} {};
    /**
     * Implicit conversion to vector.
     *
     * @return Edges of the network.
     */
    [[nodiscard]] operator std::vector<edge<Ntk>>() const noexcept
    {
        return edges;
    }
    /**
     * Network.
     */
    [[maybe_unused]] Ntk ntk;
    /**
     * Edges of the network.
     */
    std::vector<edge<Ntk>> edges{};
};
template <typename Ntk>
[[nodiscard]] edge_list<typename Ntk::base_type> bind_to_edge_list(const Ntk& ntk, const int64_t regular_weight = 0,
                                                                   const int64_t inverted_weight = 1) noexcept
{
    auto el = edge_list<typename Ntk::base_type>(ntk);

    // constants, primary inputs, and regular nodes
    ntk.foreach_node(
        [&ntk, regular_weight, inverted_weight, &el](const auto& n)
        {
            ntk.foreach_fanin(n,
                              [&ntk, regular_weight, inverted_weight, &el, &n](const auto& f)
                              {
                                  el.edges.emplace_back(ntk.node_to_index(ntk.get_node(f)), ntk.node_to_index(n),
                                                        ntk.is_complemented(f) ? inverted_weight : regular_weight);
                              });
        });

    // primary outputs
    ntk.foreach_po(
        [&ntk, regular_weight, inverted_weight, &el](const auto& po)
        {
            el.edges.emplace_back(ntk.node_to_index(ntk.get_node(po)), ntk.size() + ntk.po_index(po),
                                  ntk.is_complemented(po) ? inverted_weight : regular_weight);
        });

    // register connections (RI to RO)
    if constexpr (mockturtle::has_foreach_ri_v<Ntk> && mockturtle::has_ri_to_ro_v<Ntk>)
    {
        ntk.foreach_ri(
            [&ntk, regular_weight, inverted_weight, &el](const auto& ri)
            {
                // add the feedback loop edge from the driving node to the register output
                el.edges.emplace_back(ntk.node_to_index(ntk.get_node(ri)), ntk.node_to_index(ntk.ri_to_ro(ri)),
                                      ntk.is_complemented(ri) ? inverted_weight : regular_weight);
            });
    }

    return el;
}

namespace detail
{

// Forward declaration of binding template.
template <typename Ntk>
void ntk_edge_list(pybind11::module& m, const std::string& network_name);

// Explicit instantiation declaration for AIG.
extern template void ntk_edge_list<aigverse::aig>(pybind11::module& m, const std::string& network_name);

}  // namespace detail

// Wrapper declaration (implemented in .cpp)
void bind_to_edge_list(pybind11::module& m);

}  // namespace aigverse

namespace fmt
{

// make edge compatible with fmt::format
template <typename Ntk>
struct formatter<aigverse::edge<Ntk>>
{
    template <typename ParseContext>
    constexpr auto parse(ParseContext& ctx)
    {
        return ctx.begin();
    }

    template <typename FormatContext>
    auto format(const aigverse::edge<Ntk>& e, FormatContext& ctx) const
    {
        return format_to(ctx.out(), "Edge(s:{},t:{},w:{})", e.source, e.target, e.weight);
    }
};

// make edge_list compatible with fmt::format
template <typename Ntk>
struct formatter<aigverse::edge_list<Ntk>>
{
    template <typename ParseContext>
    constexpr auto parse(ParseContext& ctx)
    {
        return ctx.begin();
    }

    template <typename FormatContext>
    auto format(const aigverse::edge_list<Ntk>& el, FormatContext& ctx) const
    {
        return format_to(ctx.out(), "{}", el.edges);
    }
};

}  // namespace fmt

#endif  // AIGVERSE_EDGE_LIST_HPP
