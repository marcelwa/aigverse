//
// Created by marcel on 03.09.25.
//

#include "aigverse/types.hpp"

#include "edge_list.hpp"
#include "index_list.hpp"

#include <fmt/format.h>
#include <mockturtle/networks/sequential.hpp>
#include <mockturtle/traits.hpp>
#include <mockturtle/views/depth_view.hpp>
#include <mockturtle/views/fanout_view.hpp>
#include <mockturtle/views/names_view.hpp>
#include <nanobind/nanobind.h>
#include <nanobind/stl/optional.h>  // NOLINT(misc-include-cleaner)
#include <nanobind/stl/pair.h>      // NOLINT(misc-include-cleaner)
#include <nanobind/stl/string.h>    // NOLINT(misc-include-cleaner)
#include <nanobind/stl/tuple.h>     // NOLINT(misc-include-cleaner)
#include <nanobind/stl/vector.h>    // NOLINT(misc-include-cleaner)

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <exception>
#include <functional>
#include <string>
#include <utility>
#include <vector>

namespace aigverse
{

namespace detail
{

namespace
{

/**
 * @brief C++20 `std::construct_at` backport for C++17.
 *
 * Constructs an object of type `T` in the pre-allocated storage pointed to by `p`.
 * This is the proper way to construct an object in uninitialized memory (e.g., in
 * nanobind's `__setstate__`).
 *
 * @tparam T Type of object to construct.
 * @tparam Args Constructor argument types.
 * @param p Pointer to pre-allocated, uninitialized storage for `T`.
 * @param args Constructor arguments forwarded to `T`.
 * @return Pointer to the constructed object.
 * @note Once the project moves to C++20, replace usages with
 * `std::construct_at` and remove this backport.
 */
template <typename T, typename... Args>
constexpr T* construct_at(T* p, Args&&... args) noexcept(std::is_nothrow_constructible_v<T, Args...>)
{
    ::new (static_cast<void*>(p)) T(std::forward<Args>(args)...);
    return p;
}
/**
 * @brief Collects all nodes in the network.
 *
 * @tparam Ntk Network type.
 * @param ntk Network instance.
 * @return Vector of all nodes in the network.
 */
template <typename Ntk>
std::vector<mockturtle::node<Ntk>> collect_nodes(const Ntk& ntk)
{
    std::vector<mockturtle::node<Ntk>> nodes;
    nodes.reserve(ntk.size());
    ntk.foreach_node([&nodes](const auto& n) { nodes.push_back(n); });
    return nodes;
}
/**
 * @brief Creates a Python iterator over the nodes of the network.
 *
 * @tparam Ntk Network type.
 * @param ntk Network instance.
 * @return Python iterator over the nodes of the network.
 */
template <typename Ntk>
nanobind::object make_node_iterator(const Ntk& ntk)
{
    namespace nb = nanobind;

    return nb::module_::import_("builtins").attr("iter")(nb::cast(collect_nodes(ntk)));
}
/**
 * @brief Checks if the network contains a specific node.
 *
 * @tparam Ntk Network type.
 * @param ntk Network instance.
 * @param value Node to check for.
 * @return `true` if the node is in the network, `false` otherwise.
 */
template <typename Ntk>
bool contains_node(const Ntk& ntk, const nanobind::object& value)
{
    namespace nb = nanobind;

    if (!nb::isinstance<nb::int_>(value))
    {
        return false;
    }

    const auto node_index = nb::cast<int64_t>(value);
    return node_index >= 0 && static_cast<uint64_t>(node_index) < static_cast<uint64_t>(ntk.size());
}

}  // namespace

template <typename Ntk>
void bind_network(nanobind::module_& m, const std::string& network_name)  // NOLINT(misc-use-internal-linkage)
{
    namespace nb = nanobind;

    // Note: AIG nodes are uint64_t in mockturtle, which nanobind handles via its built-in
    // integer type caster. We cannot (and need not) create nb::class_<Node>. Nodes
    // are simply represented as Python ints.
    using Node = mockturtle::node<Ntk>;  // NOLINT(readability-identifier-naming)

    auto all_caps_network_name = network_name;
    std::transform(all_caps_network_name.begin(), all_caps_network_name.end(), all_caps_network_name.begin(),
                   ::toupper);

    const auto signal_class_doc = fmt::format(
        "Represents a signal in an {}.\n\nSignals point to nodes and may be complemented.", all_caps_network_name);
    const auto network_class_doc =
        fmt::format("Represents an {} and its structural operations.", all_caps_network_name);
    const auto network_init_doc = fmt::format("Creates an empty {} network.", all_caps_network_name);

    using Signal = mockturtle::signal<Ntk>;  // NOLINT(readability-identifier-naming)
    nb::class_<Signal>(m, fmt::format("{}Signal", network_name).c_str(), signal_class_doc.c_str())
        .def(nb::init<const uint64_t, const bool>(), nb::arg("index"), nb::arg("complement"),
             R"pb(Creates a signal from a node index and complement flag.

    Args:
        index: Node index referenced by the signal.
        complement: Whether the signal is complemented.)pb")
        .def_prop_ro(
            "index", [](const Signal& s) { return s.index; }, R"pb(Node index referenced by the signal.)pb")
        .def_prop_ro(
            "complement", [](const Signal& s) -> bool { return s.complement; },
            R"pb(Whether this signal is complemented.)pb")
        .def_prop_ro(
            "data", [](const Signal& s) { return s.data; }, R"pb(Raw packed signal representation.)pb")
        .def(
            "__hash__", [](const Signal& s) { return std::hash<Signal>{}(s); },
            R"pb(Returns a hash value for dictionary/set usage.)pb")
        .def(
            "__repr__", [](const Signal& s) { return fmt::format("Signal({}{})", s.complement ? "!" : "", s.index); },
            R"pb(Returns a developer-friendly string representation.)pb")
        .def(
            "__eq__",
            [](const Signal& self, const nb::object& other) -> bool
            {
                if (!nb::isinstance<Signal>(other))
                {
                    return false;
                }
                return self == nb::cast<const Signal>(other);
            },
            nb::arg("other"),
            R"pb(Returns whether two signals are equal.

    Args:
        other: Object to compare.

    Returns:
        ``True`` if equal, otherwise ``False``.)pb")
        .def(
            "__ne__",
            [](const Signal& self, const nb::object& other) -> bool
            {
                if (!nb::isinstance<Signal>(other))
                {
                    return false;
                }
                return self != nb::cast<const Signal>(other);
            },
            nb::arg("other"),
            R"pb(Returns whether two signals are not equal.

    Args:
        other: Object to compare.

    Returns:
        ``True`` if not equal, otherwise ``False``.)pb")
        .def(
            "__lt__", [](const Signal& s1, const Signal& s2) { return s1 < s2; }, nb::arg("other"),
            R"pb(Returns whether this signal is ordered before another signal.)pb")
        .def(
            "__invert__", [](const Signal& s) { return !s; }, R"pb(Returns the complemented signal.)pb")
        .def(
            "__pos__", [](const Signal& s) { return +s; }, R"pb(Returns a normalized positive-phase signal.)pb")
        .def(
            "__neg__", [](const Signal& s) { return -s; }, R"pb(Returns a normalized negative-phase signal.)pb")
        .def(
            "__xor__", [](const Signal& s, const bool complement) { return s ^ complement; }, nb::arg("complement"),
            R"pb(XORs the signal phase with a Boolean complement bit.

    Args:
        complement: Complement bit to XOR with the current signal phase.

    Returns:
        A phase-adjusted signal.)pb");

    nb::class_<Ntk>(m, network_name.c_str(), network_class_doc.c_str())
        .def(nb::init<>(), network_init_doc.c_str())
        .def("clone", &Ntk::clone, R"pb(Creates a structural copy of the network.)pb")
        .def_prop_ro("size", &Ntk::size, R"pb(Number of nodes in the network.)pb")
        .def_prop_ro("num_gates", &Ntk::num_gates, R"pb(Number of logic gates in the network.)pb")
        .def_prop_ro("num_pis", &Ntk::num_pis, R"pb(Number of primary inputs.)pb")
        .def_prop_ro("num_pos", &Ntk::num_pos, R"pb(Number of primary outputs.)pb")
        .def("get_node", &Ntk::get_node, nb::arg("s"), R"pb(Returns the node referenced by a signal.)pb")
        .def("make_signal", &Ntk::make_signal, nb::arg("n"), R"pb(Creates a signal from a node.)pb")
        .def("is_complemented", &Ntk::is_complemented, nb::arg("s"), R"pb(Returns whether a signal is complemented.)pb")
        .def("node_to_index", &Ntk::node_to_index, nb::arg("n"), R"pb(Returns the integer index of a node.)pb")
        .def("index_to_node", &Ntk::index_to_node, nb::arg("index"), R"pb(Returns the node for an index.)pb")
        .def("pi_index", &Ntk::pi_index, nb::arg("n"), R"pb(Returns the primary-input position of a node.)pb")
        .def("pi_at", &Ntk::pi_at, nb::arg("index"), R"pb(Returns the primary input node at ``index``.)pb")
        .def("po_index", &Ntk::po_index, nb::arg("s"), R"pb(Returns the primary-output position of a signal.)pb")
        .def("po_at", &Ntk::po_at, nb::arg("index"), R"pb(Returns the primary output signal at ``index``.)pb")
        .def("get_constant", &Ntk::get_constant, nb::arg("value"),
             R"pb(Returns the constant signal for a Boolean value.)pb")
        .def("create_pi", &Ntk::create_pi, R"pb(Creates and returns a new primary input signal.)pb")
        .def("create_po", &Ntk::create_po, nb::arg("f"), R"pb(Creates a primary output from signal ``f``.)pb")
        .def_prop_ro("is_combinational", &Ntk::is_combinational, R"pb(Whether the network is combinational.)pb")
        .def("create_buf", &Ntk::create_buf, nb::arg("a"), R"pb(Creates a buffer.)pb")
        .def("create_not", &Ntk::create_not, nb::arg("a"), R"pb(Creates an inversion.)pb")
        .def("create_and", &Ntk::create_and, nb::arg("a"), nb::arg("b"), R"pb(Creates an AND.)pb")
        .def("create_nand", &Ntk::create_nand, nb::arg("a"), nb::arg("b"), R"pb(Creates a NAND.)pb")
        .def("create_or", &Ntk::create_or, nb::arg("a"), nb::arg("b"), R"pb(Creates an OR.)pb")
        .def("create_nor", &Ntk::create_nor, nb::arg("a"), nb::arg("b"), R"pb(Creates a NOR.)pb")
        .def("create_xor", &Ntk::create_xor, nb::arg("a"), nb::arg("b"), R"pb(Creates an XOR.)pb")
        .def("create_xnor", &Ntk::create_xnor, nb::arg("a"), nb::arg("b"), R"pb(Creates an XNOR.)pb")
        .def("create_lt", &Ntk::create_lt, nb::arg("a"), nb::arg("b"), R"pb(Creates a less-than comparator.)pb")
        .def("create_le", &Ntk::create_le, nb::arg("a"), nb::arg("b"), R"pb(Creates a less-or-equal comparator.)pb")
        .def("create_maj", &Ntk::create_maj, nb::arg("a"), nb::arg("b"), nb::arg("c"), R"pb(Creates a majority.)pb")
        .def("create_ite", &Ntk::create_ite, nb::arg("cond"), nb::arg("f_then"), nb::arg("f_else"),
             R"pb(Creates an if-then-else.)pb")
        .def("create_xor3", &Ntk::create_xor3, nb::arg("a"), nb::arg("b"), nb::arg("c"),
             R"pb(Creates a 3-input XOR.)pb")
        .def("create_nary_and", &Ntk::create_nary_and, nb::arg("fs"), R"pb(Creates an n-ary AND.)pb")
        .def("create_nary_or", &Ntk::create_nary_or, nb::arg("fs"), R"pb(Creates an n-ary OR.)pb")
        .def("create_nary_xor", &Ntk::create_nary_xor, nb::arg("fs"), R"pb(Creates an n-ary XOR.)pb")
        .def("clone_node", &Ntk::clone_node, nb::arg("other"), nb::arg("source"), nb::arg("children"),
             R"pb(Clones one node from ``other`` into this network.)pb")
        .def(
            "nodes", [](const Ntk& ntk) { return collect_nodes(ntk); },
            R"pb(Returns a list of all nodes in order of creation.)pb")
        .def(
            "gates",
            [](const Ntk& ntk)
            {
                std::vector<Node> gates;
                gates.reserve(ntk.num_gates());
                ntk.foreach_gate([&gates](const auto& g) { gates.push_back(g); });
                return gates;
            },
            R"pb(Returns a list of all non-constant and non-PI nodes in order of creation.)pb")
        .def(
            "pis",
            [](const Ntk& ntk)
            {
                std::vector<Node> pis;
                pis.reserve(ntk.num_pis());
                ntk.foreach_pi([&pis](const auto& pi) { pis.push_back(pi); });
                return pis;
            },
            R"pb(Returns a list of all primary input nodes in order of creation.)pb")
        .def(
            "pos",
            [](const Ntk& ntk)
            {
                std::vector<Signal> pos;
                pos.reserve(ntk.num_pos());
                ntk.foreach_po([&pos](const auto& po) { pos.push_back(po); });
                return pos;
            },
            R"pb(Returns a list of all primary output signals in order of creation.)pb")
        .def(
            "fanins",
            [](const Ntk& ntk, const Node& n)
            {
                std::vector<Signal> fanins;
                fanins.reserve(ntk.fanin_size(n));
                ntk.foreach_fanin(n, [&fanins](const auto& f) { fanins.push_back(f); });
                return fanins;
            },
            nb::arg("n"), R"pb(Returns fanin signals of node ``n``.)pb")
        .def(
            "fanin_size", [](const Ntk& ntk, const Node& n) { return ntk.fanin_size(n); }, nb::arg("n"),
            R"pb(Returns the number of fanins of node ``n``.)pb")
        .def(
            "fanout_size", [](const Ntk& ntk, const Node& n) { return ntk.fanout_size(n); }, nb::arg("n"),
            R"pb(Returns the number of fanouts of node ``n``.)pb")
        .def("is_constant", &Ntk::is_constant, nb::arg("n"), R"pb(Returns whether ``n`` is a constant node.)pb")
        .def("is_pi", &Ntk::is_pi, nb::arg("n"), R"pb(Returns whether ``n`` is a primary input.)pb")
        .def("has_and", &Ntk::has_and, nb::arg("a"), nb::arg("b"),
             R"pb(Returns whether an AND with fanins ``a`` and ``b`` already exists.)pb")
        .def(
            "is_and", [](const Ntk& ntk, const Node& n) { return ntk.is_and(n); }, nb::arg("n"),
            R"pb(Returns whether ``n`` is an AND node.)pb")
        .def(
            "is_or", [](const Ntk& ntk, const Node& n) { return ntk.is_or(n); }, nb::arg("n"),
            R"pb(Returns whether ``n`` is an OR node.)pb")
        .def(
            "is_xor", [](const Ntk& ntk, const Node& n) { return ntk.is_xor(n); }, nb::arg("n"),
            R"pb(Returns whether ``n`` is an XOR node.)pb")
        .def(
            "is_maj", [](const Ntk& ntk, const Node& n) { return ntk.is_maj(n); }, nb::arg("n"),
            R"pb(Returns whether ``n`` is a majority node.)pb")
        .def(
            "is_ite", [](const Ntk& ntk, const Node& n) { return ntk.is_ite(n); }, nb::arg("n"),
            R"pb(Returns whether ``n`` is an if-then-else node.)pb")
        .def(
            "is_xor3", [](const Ntk& ntk, const Node& n) { return ntk.is_xor3(n); }, nb::arg("n"),
            R"pb(Returns whether ``n`` is a 3-input XOR node.)pb")
        .def(
            "is_nary_and", [](const Ntk& ntk, const Node& n) { return ntk.is_nary_and(n); }, nb::arg("n"),
            R"pb(Returns whether ``n`` is an n-ary AND node.)pb")
        .def(
            "is_nary_or", [](const Ntk& ntk, const Node& n) { return ntk.is_nary_or(n); }, nb::arg("n"),
            R"pb(Returns whether ``n`` is an n-ary OR node.)pb")
        .def(
            "to_edge_list", [](const Ntk& ntk, const int64_t regular_weight = 0, const int64_t inverted_weight = 1)
            { return aigverse::to_edge_list(ntk, regular_weight, inverted_weight); }, nb::arg("regular_weight") = 0,
            nb::arg("inverted_weight") = 1,
            R"pb(Converts the network to an edge list.

Args:
    regular_weight: Weight assigned to non-inverted edges.
    inverted_weight: Weight assigned to inverted edges.

Returns:
    The corresponding edge-list representation.)pb",
            nb::rv_policy::move)
        .def(
            "to_index_list",
            [](const Ntk& ntk)
            {
                aigverse::aig_index_list il{};
                mockturtle::encode(il, ntk);
                return il;
            },
            R"pb(Converts the network to an index-list encoding.

Returns:
    The corresponding index-list representation.)pb",
            nb::rv_policy::move)
        .def("__len__", &Ntk::size, R"pb(Returns the number of nodes.)pb")
        .def(
            "__repr__",
            [network_name](const Ntk& ntk)
            {
                return fmt::format("{}(pis={}, pos={}, gates={}, size={})", network_name, ntk.num_pis(), ntk.num_pos(),
                                   ntk.num_gates(), ntk.size());
            },
            R"pb(Returns a developer-friendly string representation.)pb")
        .def(
            "__iter__", [](const Ntk& ntk) { return make_node_iterator(ntk); },
            R"pb(Returns an iterator over all nodes.)pb", nb::sig("def __iter__(self) -> Iterator[int]"))
        .def(
            "__contains__", [](const Ntk& ntk, const nb::object& value) { return contains_node(ntk, value); },
            nb::arg("value"), R"pb(Returns whether a node index is contained in the network.)pb")
        .def(
            "__bool__", [](const Ntk& ntk) { return ntk.size() > 1; },
            R"pb(Returns ``True`` for non-trivial networks.)pb")
        .def(
            "__copy__", [](const Ntk& ntk) { return ntk.clone(); }, R"pb(Returns a shallow structural copy.)pb")
        .def(
            "__deepcopy__", [](const Ntk& ntk, const nb::dict&) { return ntk.clone(); }, nb::arg("memo"),
            R"pb(Returns a deep structural copy.)pb")
        .def(
            "__setstate__",
            [](Ntk& ntk, const nb::object& state)
            {
                if (!nb::isinstance<nb::tuple>(state))
                {
                    throw nb::value_error("Invalid state: expected a tuple of size 1 containing an index list");
                }

                const auto tuple_state = nb::cast<nb::tuple>(state);

                if (tuple_state.size() != 1)
                {
                    throw nb::value_error("Invalid state: expected a tuple of size 1 containing an index list");
                }

                try
                {
                    const aigverse::aig_index_list il{nb::cast<std::vector<uint32_t>>(tuple_state[0])};

                    Ntk restored{};
                    mockturtle::decode(restored, il);

                    // ntk is uninitialized memory provided by nanobind; must construct in-place
                    construct_at(&ntk, std::move(restored));
                }
                catch (const nb::cast_error& e)  // NOLINT(misc-include-cleaner)
                {
                    const auto message = fmt::format("Invalid state: expected an index list. {}", e.what());
                    throw nb::value_error(message.c_str());
                }
                catch (const std::exception& e)
                {
                    const auto message = fmt::format("Failed to restore network state: {}", e.what());
                    throw nb::value_error(message.c_str());
                }
            },
            nb::arg("state"),
            R"pb(Restores a network from a pickled state tuple.

Args:
    state: Tuple containing one index-list payload.

Raises:
    ValueError: If the state shape or payload is invalid.)pb")
        .def(
            "__getstate__",
            [](const Ntk& ntk)
            {
                aigverse::aig_index_list il{};
                mockturtle::encode(il, ntk);
                return nb::make_tuple(nb::cast(il.raw()));
            },
            R"pb(Returns pickle state as an index-list tuple.)pb");

    using NamedNtk = mockturtle::names_view<Ntk>;
    nb::class_<NamedNtk, Ntk>(m, fmt::format("Named{}", network_name).c_str(),
                              R"pb(Extends a network with input/output and node names.)pb")
        .def(nb::init<>(), R"pb(Creates an empty named view.)pb")
        .def(nb::init<const NamedNtk&>(), nb::arg("ntk"), R"pb(Copies from another named view.)pb")
        .def(nb::init<const Ntk&>(), nb::arg("ntk"), R"pb(Creates a named view over an existing network.)pb")
        .def(
            "clone", [](const NamedNtk& ntk) { return NamedNtk{ntk}; },
            R"pb(Creates a structural copy including names.)pb")
        .def(
            "__copy__", [](const NamedNtk& ntk) { return NamedNtk{ntk}; },
            R"pb(Returns a shallow copy of the named view.)pb")
        .def(
            "__deepcopy__", [](const NamedNtk& ntk, const nb::dict&) { return NamedNtk{ntk}; }, nb::arg("memo"),
            R"pb(Returns a deep copy of the named view.)pb")
        .def("create_pi", &NamedNtk::create_pi, nb::arg("name") = "",
             R"pb(Creates a primary input with an optional name.)pb")
        .def("create_po", &NamedNtk::create_po, nb::arg("f"), nb::arg("name") = "",
             R"pb(Creates a primary output with an optional name.)pb")
        .def("set_network_name", &NamedNtk::set_network_name, nb::arg("name"), R"pb(Sets the network name.)pb")
        .def("get_network_name", &NamedNtk::get_network_name, R"pb(Returns the network name.)pb")
        .def("has_name", &NamedNtk::has_name, nb::arg("s"), R"pb(Returns whether signal ``s`` has a name.)pb")
        .def("set_name", &NamedNtk::set_name, nb::arg("s"), nb::arg("name"), R"pb(Assigns a name to signal ``s``.)pb")
        .def("get_name", &NamedNtk::get_name, nb::arg("s"), R"pb(Returns the name of signal ``s``.)pb")
        .def("has_output_name", &NamedNtk::has_output_name, nb::arg("index"),
             R"pb(Returns whether output ``index`` has a name.)pb")
        .def("set_output_name", &NamedNtk::set_output_name, nb::arg("index"), nb::arg("name"),
             R"pb(Sets the name of output ``index``.)pb")
        .def("get_output_name", &NamedNtk::get_output_name, nb::arg("index"),
             R"pb(Returns the name of output ``index``.)pb")
        .def(
            "__repr__",
            [network_name](const NamedNtk& ntk)
            {
                return fmt::format("Named{}(name={}, pis={}, pos={}, gates={})", network_name, ntk.get_network_name(),
                                   ntk.num_pis(), ntk.num_pos(), ntk.num_gates());
            },
            R"pb(Returns a developer-friendly string representation.)pb");

    using DepthNtk = mockturtle::depth_view<Ntk>;
    nb::class_<DepthNtk, Ntk>(m, fmt::format("Depth{}", network_name).c_str(),
                              R"pb(Extends a network with depth information.)pb")
        .def(nb::init<>(), R"pb(Creates an empty depth view.)pb")
        .def(nb::init<const DepthNtk&>(), nb::arg("ntk"), R"pb(Copies from another depth view.)pb")
        .def(nb::init<const Ntk&>(), nb::arg("ntk"), R"pb(Creates a depth view over an existing network.)pb")
        .def(
            "clone", [](const DepthNtk& ntk) { return DepthNtk{ntk}; }, R"pb(Creates a copy of the depth view.)pb")
        .def(
            "__copy__", [](const DepthNtk& ntk) { return DepthNtk{ntk}; },
            R"pb(Returns a shallow copy of the depth view.)pb")
        .def(
            "__deepcopy__", [](const DepthNtk& ntk, const nb::dict&) { return DepthNtk{ntk}; }, nb::arg("memo"),
            R"pb(Returns a deep copy of the depth view.)pb")
        .def_prop_ro("num_levels", &DepthNtk::depth, R"pb(Current network depth in levels.)pb")
        .def("level", &DepthNtk::level, nb::arg("n"), R"pb(Returns the level of node ``n``.)pb")
        .def("is_on_critical_path", &DepthNtk::is_on_critical_path, nb::arg("n"),
             R"pb(Returns whether node ``n`` is on at least one critical path.)pb")
        .def("update_levels", &DepthNtk::update_levels, R"pb(Recomputes level information.)pb")
        .def("create_po", &DepthNtk::create_po, nb::arg("f"), R"pb(Creates an output and updates depth information.)pb")
        .def(
            "__repr__",
            [network_name](const DepthNtk& ntk)
            {
                return fmt::format("Depth{}(pis={}, pos={}, gates={}, depth={})", network_name, ntk.num_pis(),
                                   ntk.num_pos(), ntk.num_gates(), ntk.depth());
            },
            R"pb(Returns a developer-friendly string representation.)pb");

    using FanoutNtk = mockturtle::fanout_view<Ntk>;
    nb::class_<FanoutNtk, Ntk>(m, fmt::format("Fanout{}", network_name).c_str(),
                               R"pb(Extends a network with fanout information.)pb")
        .def(nb::init<>(), R"pb(Creates an empty fanout view.)pb")
        .def(nb::init<const Ntk&>(), nb::arg("ntk"), R"pb(Creates a fanout view over an existing network.)pb")
        .def(nb::init<const FanoutNtk&>(), nb::arg("ntk"), R"pb(Copies from another fanout view.)pb")
        .def(
            "clone", [](const FanoutNtk& ntk) { return FanoutNtk{ntk}; },
            R"pb(Creates a structural copy of the fanout view.)pb")
        .def(
            "__copy__", [](const FanoutNtk& ntk) { return FanoutNtk{ntk}; },
            R"pb(Returns a shallow copy of the fanout view.)pb")
        .def(
            "__deepcopy__", [](const FanoutNtk& ntk, const nb::dict&) { return FanoutNtk{ntk}; }, nb::arg("memo"),
            R"pb(Returns a deep copy of the fanout view.)pb")
        .def(
            "fanouts",
            [](const FanoutNtk& ntk, const Node& n)
            {
                std::vector<Node> fanouts;
                fanouts.reserve(ntk.fanout_size(n));
                ntk.foreach_fanout(n, [&fanouts](const auto& f) { fanouts.push_back(f); });
                return fanouts;
            },
            nb::arg("n"), R"pb(Returns fanout nodes of node ``n``.)pb");

    using Register = mockturtle::register_t;  // NOLINT(readability-identifier-naming)
    nb::class_<Register>(m, fmt::format("{}Register", network_name).c_str(),
                         R"pb(Represents metadata for one sequential register.)pb")
        .def(nb::init<>(), R"pb(Creates a default register descriptor.)pb")
        .def(nb::init<const Register&>(), nb::arg("register"), R"pb(Copies a register descriptor.)pb")
        .def_rw("control", &Register::control, R"pb(Optional control signal.)pb")
        .def_rw("init", &Register::init, R"pb(Initial value of the register.)pb")
        .def_rw("type", &Register::type, R"pb(Register type/category.)pb");

    using SequentialNtk = mockturtle::sequential<Ntk>;
    nb::class_<SequentialNtk, Ntk>(m, fmt::format("Sequential{}", network_name).c_str(),
                                   R"pb(Represents a sequential network with register interfaces.)pb")
        .def(nb::init<>(), R"pb(Creates an empty sequential network.)pb")
        .def(
            "clone", [](const SequentialNtk& ntk) { return SequentialNtk{ntk}; },
            R"pb(Creates a structural copy of the sequential network.)pb")
        .def(
            "__copy__", [](const SequentialNtk& ntk) { return SequentialNtk{ntk}; },
            R"pb(Returns a shallow copy of the sequential network.)pb")
        .def(
            "__deepcopy__", [](const SequentialNtk& ntk, const nb::dict&) { return SequentialNtk{ntk}; },
            nb::arg("memo"), R"pb(Returns a deep copy of the sequential network.)pb")
        .def("create_pi", &SequentialNtk::create_pi, R"pb(Creates a primary input.)pb")
        .def("create_po", &SequentialNtk::create_po, nb::arg("f"), R"pb(Creates a primary output.)pb")
        .def("create_ro", &SequentialNtk::create_ro, R"pb(Creates a register output node.)pb")
        .def("create_ri", &SequentialNtk::create_ri, nb::arg("f"), R"pb(Creates a register input signal.)pb")
        .def_prop_ro("is_combinational", &SequentialNtk::is_combinational,
                     R"pb(Whether the network is combinational.)pb")
        .def("is_ci", &SequentialNtk::is_ci, nb::arg("n"), R"pb(Returns whether ``n`` is a combinational input.)pb")
        .def("is_pi", &SequentialNtk::is_pi, nb::arg("n"), R"pb(Returns whether ``n`` is a primary input.)pb")
        .def("is_ro", &SequentialNtk::is_ro, nb::arg("n"), R"pb(Returns whether ``n`` is a register output.)pb")
        .def_prop_ro("num_pis", &SequentialNtk::num_pis, R"pb(Number of primary inputs.)pb")
        .def_prop_ro("num_pos", &SequentialNtk::num_pos, R"pb(Number of primary outputs.)pb")
        .def_prop_ro("num_cis", &SequentialNtk::num_cis, R"pb(Number of combinational inputs.)pb")
        .def_prop_ro("num_cos", &SequentialNtk::num_cos, R"pb(Number of combinational outputs.)pb")
        .def_prop_ro("num_registers", &SequentialNtk::num_registers, R"pb(Number of registers.)pb")
        .def("pi_at", &SequentialNtk::pi_at, nb::arg("index"), R"pb(Returns primary input at ``index``.)pb")
        .def("po_at", &SequentialNtk::po_at, nb::arg("index"), R"pb(Returns primary output at ``index``.)pb")
        .def("ci_at", &SequentialNtk::ci_at, nb::arg("index"), R"pb(Returns combinational input at ``index``.)pb")
        .def("co_at", &SequentialNtk::co_at, nb::arg("index"), R"pb(Returns combinational output at ``index``.)pb")
        .def("ro_at", &SequentialNtk::ro_at, nb::arg("index"), R"pb(Returns register output at ``index``.)pb")
        .def("ri_at", &SequentialNtk::ri_at, nb::arg("index"), R"pb(Returns register input at ``index``.)pb")
        .def("set_register", &SequentialNtk::set_register, nb::arg("index"), nb::arg("reg"),
             R"pb(Sets metadata for register ``index``.)pb")
        .def("register_at", &SequentialNtk::register_at, nb::arg("index"),
             R"pb(Returns metadata for register ``index``.)pb")
        .def("pi_index", &SequentialNtk::pi_index, nb::arg("n"), R"pb(Returns PI index of node ``n``.)pb")
        .def("ci_index", &SequentialNtk::ci_index, nb::arg("n"), R"pb(Returns CI index of node ``n``.)pb")
        .def("co_index", &SequentialNtk::co_index, nb::arg("s"), R"pb(Returns CO index of signal ``s``.)pb")
        .def("ro_index", &SequentialNtk::ro_index, nb::arg("n"), R"pb(Returns RO index of node ``n``.)pb")
        .def("ri_index", &SequentialNtk::ri_index, nb::arg("s"), R"pb(Returns RI index of signal ``s``.)pb")
        .def("ro_to_ri", &SequentialNtk::ro_to_ri, nb::arg("s"), R"pb(Maps a register output signal to its input.)pb")
        .def("ri_to_ro", &SequentialNtk::ri_to_ro, nb::arg("s"), R"pb(Maps a register input signal to its output.)pb")
        .def(
            "to_index_list",
            [network_name](const SequentialNtk&) -> aigverse::aig_index_list
            {
                const auto message = fmt::format("Sequential{} does not support to_index_list() because AigIndexList "
                                                 "is combinational-only and would drop register state.",
                                                 network_name);
                throw nb::type_error(message.c_str());
            },
            R"pb(Sequential networks cannot be encoded as combinational index lists.)pb",
            nb::sig("def to_index_list(self) -> NoReturn"))
        .def(
            "__getstate__",
            [network_name](const SequentialNtk&) -> nb::tuple
            {
                const auto message = fmt::format("Sequential{} does not support pickling via aig_index_list because "
                                                 "it is combinational-only and would drop register/stateful data; "
                                                 "to_index_list() is also disabled for this reason.",
                                                 network_name);
                throw nb::value_error(message.c_str());
            },
            R"pb(Sequential networks are not pickleable via combinational index-list state.)pb",
            nb::sig("def __getstate__(self) -> NoReturn"))
        .def(
            "__setstate__",
            [network_name](SequentialNtk&, const nb::object&) -> void
            {
                const auto message = fmt::format("Sequential{} does not support unpickling via aig_index_list because "
                                                 "it is combinational-only and would drop register/stateful data; "
                                                 "to_index_list() is also disabled for this reason.",
                                                 network_name);
                throw nb::value_error(message.c_str());
            },
            R"pb(Sequential networks cannot be restored from combinational index-list state.)pb", nb::arg("state"),
            nb::sig("def __setstate__(self, state: object) -> NoReturn"))
        .def(
            "to_edge_list",
            [](const SequentialNtk& ntk, const int64_t regular_weight = 0, const int64_t inverted_weight = 1)
            { return aigverse::to_edge_list(ntk, regular_weight, inverted_weight); }, nb::arg("regular_weight") = 0,
            nb::arg("inverted_weight") = 1, R"pb(Converts the sequential network to an edge list.)pb",
            nb::rv_policy::move)
        .def(
            "pis",
            [](const SequentialNtk& ntk)
            {
                std::vector<Node> pis;
                pis.reserve(ntk.num_pis());
                ntk.foreach_pi([&pis](const auto& pi) { pis.push_back(pi); });
                return pis;
            },
            R"pb(Returns all primary input nodes.)pb")
        .def(
            "pos",
            [](const SequentialNtk& ntk)
            {
                std::vector<Signal> pos;
                pos.reserve(ntk.num_pos());
                ntk.foreach_po([&pos](const auto& po) { pos.push_back(po); });
                return pos;
            },
            R"pb(Returns all primary output signals.)pb")
        .def(
            "cis",
            [](const SequentialNtk& ntk)
            {
                std::vector<Node> cis;
                cis.reserve(ntk.num_cis());
                ntk.foreach_ci([&cis](const auto& ci) { cis.push_back(ci); });
                return cis;
            },
            R"pb(Returns all combinational input nodes.)pb")
        .def(
            "cos",
            [](const SequentialNtk& ntk)
            {
                std::vector<Signal> cos;
                cos.reserve(ntk.num_cos());
                ntk.foreach_co([&cos](const auto& co) { cos.push_back(co); });
                return cos;
            },
            R"pb(Returns all combinational output signals.)pb")
        .def(
            "ros",
            [](const SequentialNtk& ntk)
            {
                std::vector<Node> ros;
                ros.reserve(ntk.num_registers());
                ntk.foreach_ro([&ros](const auto& ro) { ros.push_back(ro); });
                return ros;
            },
            R"pb(Returns all register output nodes.)pb")
        .def(
            "ris",
            [](const SequentialNtk& ntk)
            {
                std::vector<Signal> ris;
                ris.reserve(ntk.num_registers());
                ntk.foreach_ri([&ris](const auto& ri) { ris.push_back(ri); });
                return ris;
            },
            R"pb(Returns all register input signals.)pb")
        .def(
            "registers",
            [](const SequentialNtk& ntk)
            {
                std::vector<std::pair<Signal, Node>> regs;
                regs.reserve(ntk.num_registers());
                ntk.foreach_register([&regs](const auto& reg) { regs.push_back(reg); });
                return regs;
            },
            R"pb(Returns all register pairs as ``(ri_signal, ro_node)`` tuples.)pb")
        .def(
            "__repr__",
            [network_name](const SequentialNtk& ntk)
            {
                return fmt::format("Sequential{}(pis={}, pos={}, gates={}, registers={})", network_name, ntk.num_pis(),
                                   ntk.num_pos(), ntk.num_gates(), ntk.num_registers());
            },
            R"pb(Returns a developer-friendly string representation.)pb");
}

// Explicit instantiation for AIG
template void bind_network<aigverse::aig>(nanobind::module_&, const std::string&);

}  // namespace detail

void bind_logic_networks(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::bind_network<aigverse::aig>(m, "Aig");
}

}  // namespace aigverse
