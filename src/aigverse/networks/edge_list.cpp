//
// Created by marcel on 04.09.25.
//

#include "aigverse/networks/edge_list.hpp"

#include "aigverse/types.hpp"

#include <fmt/format.h>
#include <fmt/ranges.h>  // NOLINT(misc-include-cleaner)
#include <mockturtle/traits.hpp>
#include <nanobind/make_iterator.h>  // NOLINT(misc-include-cleaner)
#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>  // NOLINT(misc-include-cleaner)
#include <nanobind/stl/vector.h>  // NOLINT(misc-include-cleaner)

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void ntk_edge_list(nanobind::module_& m, const std::string& network_name)  // NOLINT(misc-use-internal-linkage)
{
    namespace nb = nanobind;

    /**
     * Edge.
     */
    using Edge = edge<Ntk>;  // NOLINT(readability-identifier-naming)
    nb::class_<Edge>(
        m, fmt::format("{}Edge", network_name).c_str(),
        R"pb(Represents a directed edge in a logic network graph. A weight attribute may encode inversion.)pb")
        .def(nb::init<>(),
             R"pb(Creates an empty edge.

The default edge has zero-initialized endpoints and weight.)pb")
        .def(nb::init<const mockturtle::node<Ntk>&, const mockturtle::node<Ntk>&, const int64_t>(), nb::arg("source"),
             nb::arg("target"), nb::arg("weight") = 0,
             R"pb(Creates an edge with explicit source, target, and weight.

Args:
    source: Source node identifier.
    target: Target node identifier.
    weight: Optional edge weight. Defaults to ``0``.)pb")
        .def_rw("source", &Edge::source, R"pb(Source node identifier.)pb")
        .def_rw("target", &Edge::target, R"pb(Target node identifier.)pb")
        .def_rw("weight", &Edge::weight, R"pb(Edge weight value.)pb")
        .def(
            "__repr__", [](const Edge& e) { return fmt::format("{}", e); },
            R"pb(Returns a developer-friendly string representation.)pb")
        .def(
            "__eq__",
            [](const Edge& self, const nb::object& other) -> bool
            {
                if (!nb::isinstance<Edge>(other))
                {
                    return false;
                }

                return self == nb::cast<const Edge>(other);
            },
            nb::arg("other"),
            R"pb(Checks whether two edges are equal.

Args:
    other: Object to compare.

Returns:
    ``True`` if ``other`` is an edge with equal fields, otherwise ``False``.)pb")
        .def(
            "__ne__",
            [](const Edge& self, const nb::object& other) -> bool
            {
                if (!nb::isinstance<Edge>(other))
                {
                    return true;
                }

                return self != nb::cast<const Edge>(other);
            },
            nb::arg("other"),
            R"pb(Checks whether two edges are not equal.

Args:
    other: Object to compare.

Returns:
    ``True`` if ``other`` is not equal to this edge.)pb")

        ;

    nb::implicitly_convertible<nb::tuple, Edge>();  // NOLINT(misc-include-cleaner)

    /**
     * Edge list.
     */
    using EdgeList = edge_list<Ntk>;  // NOLINT(readability-identifier-naming)
    nb::class_<EdgeList>(m, fmt::format("{}EdgeList", network_name).c_str(),
                         R"pb(Represents a list of edges associated with a network.)pb")
        .def(nb::init<>(), R"pb(Creates an empty edge list.)pb")
        .def(nb::init<const Ntk&>(), nb::arg("ntk"),
             R"pb(Creates an edge list for a given network.

Args:
    ntk: Network associated with the edge list.)pb")
        .def(nb::init<const std::vector<Edge>&>(), nb::arg("edges"),
             R"pb(Creates an edge list from existing edges.

Args:
    edges: Initial edge collection.)pb")
        .def(nb::init<const Ntk&, const std::vector<Edge>&>(), nb::arg("ntk"), nb::arg("edges"),
             R"pb(Creates an edge list with network and edge collection.

Args:
    ntk: Network associated with the edge list.
    edges: Initial edge collection.)pb")
        .def_rw("ntk", &EdgeList::ntk, R"pb(Underlying network associated with this list.)pb")
        .def_rw("edges", &EdgeList::edges, R"pb(Stored edges in insertion order.)pb")
        .def(
            "append", [](EdgeList& el, const Edge& e) { el.edges.push_back(e); }, nb::arg("edge"),
            R"pb(Appends an edge to the list.

Args:
    edge: Edge to append.)pb")
        .def(
            "clear", [](EdgeList& el) { el.edges.clear(); }, R"pb(Removes all edges from the list.)pb")
        .def(
            "__iter__", [](const EdgeList& el)
            { return nb::make_iterator(nb::type<EdgeList>(), "edge_iterator", el.edges.begin(), el.edges.end()); },
            R"pb(Returns an iterator over stored edges.)pb", nb::keep_alive<0, 1>())
        .def(
            "__len__", [](const EdgeList& el) { return el.edges.size(); }, R"pb(Returns the number of edges.)pb")
        .def(
            "__getitem__",
            [](const EdgeList& el, std::ptrdiff_t index)
            {
                if (index < 0)
                {
                    index += static_cast<std::ptrdiff_t>(el.edges.size());
                }
                if (index < 0 || static_cast<std::size_t>(index) >= el.edges.size())
                {
                    throw nb::index_error();
                }

                return el.edges[static_cast<std::size_t>(index)];
            },
            nb::arg("index"),
            R"pb(Returns the edge at a given position.

Args:
    index: Edge index. Negative indices are supported.

Returns:
    The edge at the requested position.

Raises:
    IndexError: If ``index`` is out of bounds.)pb")
        .def(
            "__setitem__",
            [](EdgeList& el, std::ptrdiff_t index, const Edge& e)
            {
                if (index < 0)
                {
                    index += static_cast<std::ptrdiff_t>(el.edges.size());
                }
                if (index < 0 || static_cast<std::size_t>(index) >= el.edges.size())
                {
                    throw nb::index_error();
                }

                el.edges[static_cast<std::size_t>(index)] = e;
            },
            nb::arg("index"), nb::arg("edge"),
            R"pb(Replaces the edge at a given position.

Args:
    index: Edge index. Negative indices are supported.
    edge: Replacement edge.

Raises:
    IndexError: If ``index`` is out of bounds.)pb")
        .def(
            "__repr__", [](const EdgeList& el) { return fmt::format("EdgeList({})", el); },
            R"pb(Returns a developer-friendly string representation.)pb")

        ;

    nb::implicitly_convertible<nb::list, EdgeList>();  // NOLINT(misc-include-cleaner)
}

// Explicit instantiation for AIG
template void ntk_edge_list<aigverse::aig>(nanobind::module_& m, const std::string& network_name);

}  // namespace detail

void bind_ntk_edge_list(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::ntk_edge_list<aigverse::aig>(m, "Aig");
}

}  // namespace aigverse
