#include "aigverse/types.hpp"

#include <fmt/format.h>
#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>      // NOLINT(misc-include-cleaner)
#include <nanobind/stl/unique_ptr.h>  // NOLINT(misc-include-cleaner)
#include <nanobind/stl/vector.h>      // NOLINT(misc-include-cleaner)

#include <cstdint>
#include <memory>
#include <numeric>
#include <string>
#include <type_traits>
#include <vector>

namespace aigverse
{
namespace
{
namespace nb = nanobind;

void check_index(const uint64_t index, const uint64_t size)
{
    // Check the full handle before mockturtle's node_to_index narrows it to uint32_t.
    if (index >= size)
    {
        throw nb::index_error("node or interface index out of range");
    }
}

void check_children(const klut& ntk, const std::vector<uint64_t>& children)
{
    for (const auto child : children)
    {
        check_index(child, ntk.size());
    }
}

uint64_t create_node(klut& ntk, const std::vector<uint64_t>& children, const truth_table& function)
{
    if (children.size() > klut::max_fanin_size)
    {
        throw nb::value_error("a LUT supports at most 32 fanins");
    }
    if (function.num_vars() != children.size())
    {
        throw nb::value_error("truth table variable count must equal the number of fanins");
    }
    check_children(ntk, children);
    return ntk.create_node(children, function);
}

std::vector<uint64_t> nodes(const klut& ntk)
{
    std::vector<uint64_t> result(ntk.size());
    std::iota(result.begin(), result.end(), uint64_t{0});
    return result;
}

template <typename View>
std::unique_ptr<View> clone_view(const View& ntk)
{
    // Default construction keeps node_map's network pointer on the final, heap-owned view.
    auto result      = std::make_unique<View>();
    result->_storage = ntk.klut::clone()._storage;
    if constexpr (std::is_same_v<View, named_klut>)
    {
        result->set_network_name(ntk.get_network_name());
        ntk.foreach_node(
            [&](const auto n)
            {
                if (ntk.has_name(n))
                {
                    result->set_name(n, ntk.get_name(n));
                }
            });
        ntk.foreach_po(
            [&](const auto, const auto index)
            {
                if (ntk.has_output_name(index))
                {
                    result->set_output_name(index, ntk.get_output_name(index));
                }
            });
    }
    else if constexpr (std::is_same_v<View, depth_klut>)
    {
        result->update_levels();
    }
    else
    {
        result->update_fanout();
    }
    return result;
}

template <typename View>
auto bind_view(nb::module_& m, const char* name, const char* doc)
{
    auto view = nb::class_<View, klut>(m, name, doc);
    // Native depth/fanout copies share node_map storage; base construction rebuilds private metadata.
    if constexpr (std::is_same_v<View, named_klut>)
    {
        view.def(nb::init<const View&>(), nb::arg("ntk"), nb::keep_alive<1, 2>(),
                 R"pb(Copies names while sharing network storage. Use clone() for independence.)pb");
    }
    return view.def(nb::init<>(), R"pb(Creates an empty view.)pb")
        .def(nb::init<const klut&>(), nb::arg("ntk"), nb::keep_alive<1, 2>(),
             R"pb(Creates a view sharing the network's storage. Use clone() for independence.)pb")
        .def("clone", &clone_view<View>, R"pb(Creates an independent network and rebuilds view metadata.)pb")
        .def("__copy__", &clone_view<View>, R"pb(Returns an independent copy of the view.)pb")
        .def(
            "__deepcopy__", [](const View& ntk, const nb::dict&) { return clone_view(ntk); }, nb::arg("memo"),
            R"pb(Returns an independent copy of the view.)pb");
}
}  // namespace

void bind_klut_networks(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    auto network =
        nb::class_<klut>(m, "Klut", R"pb(A combinational network of arbitrary truth-table gates.

Signals and nodes are integer handles. Constants 0 and 1 are distinct nodes;
inversion uses create_not(), not complemented edges. A LUT has at most 32 fanins.)pb")
            .def(nb::init<>(), R"pb(Creates an empty k-LUT network.)pb")
            .def(
                "__init__", [](klut* self, const klut& ntk) { new (self) klut(ntk.clone()); }, nb::arg("ntk"),
                R"pb(Creates an independent structural copy, discarding augmented view metadata.)pb")
            .def("clone", &klut::clone, R"pb(Creates an independent structural copy.)pb")
            .def("__copy__", &klut::clone, R"pb(Returns an independent structural copy.)pb")
            .def(
                "__deepcopy__", [](const klut& ntk, const nb::dict&) { return ntk.clone(); }, nb::arg("memo"),
                R"pb(Returns an independent structural copy.)pb")
            .def_prop_ro("size", &klut::size, R"pb(Number of nodes, including both constants.)pb")
            .def_prop_ro("num_gates", &klut::num_gates, R"pb(Number of LUT gates.)pb")
            .def_prop_ro("num_pis", &klut::num_pis, R"pb(Number of primary inputs.)pb")
            .def_prop_ro("num_pos", &klut::num_pos, R"pb(Number of primary outputs.)pb")
            .def_prop_ro("is_combinational", &klut::is_combinational, R"pb(Whether the network is combinational.)pb")
            .def("get_constant", &klut::get_constant, nb::arg("value"), R"pb(Returns the Boolean constant signal.)pb")
            .def("create_pi", &klut::create_pi, R"pb(Creates a primary input signal.)pb")
            .def(
                "create_po",
                [](klut& ntk, const uint64_t f)
                {
                    check_index(f, ntk.size());
                    return ntk.create_po(f);
                },
                nb::arg("f"), R"pb(Creates a primary output from an existing signal.)pb")
            .def("create_node", &create_node, nb::arg("children"), nb::arg("function"),
                 R"pb(Creates a LUT with the given ordered fanins and truth table.

Args:
    children: Existing signals, at most 32. The first fanin is truth-table variable 0.
    function: A truth table with one variable per fanin; zero fanins create a constant.

Returns:
    The signal of the structurally hashed LUT.

Raises:
    ValueError: If the fanin count exceeds 32 or differs from the truth-table dimension.
    IndexError: If a fanin does not exist.)pb")
            .def(
                "get_node",
                [](const klut& ntk, const uint64_t s)
                {
                    check_index(s, ntk.size());
                    return s;
                },
                nb::arg("s"), R"pb(Returns the node referenced by a signal.)pb")
            .def(
                "make_signal",
                [](const klut& ntk, const uint64_t n)
                {
                    check_index(n, ntk.size());
                    return n;
                },
                nb::arg("n"), R"pb(Returns the signal for a node.)pb")
            .def(
                "node_to_index",
                [](const klut& ntk, const uint64_t n)
                {
                    check_index(n, ntk.size());
                    return n;
                },
                nb::arg("n"), R"pb(Returns the integer index of a node.)pb")
            .def(
                "index_to_node",
                [](const klut& ntk, const uint64_t index)
                {
                    check_index(index, ntk.size());
                    return index;
                },
                nb::arg("index"), R"pb(Returns the node for an existing index.)pb")
            .def(
                "is_complemented",
                [](const klut& ntk, const uint64_t s)
                {
                    check_index(s, ntk.size());
                    return false;
                },
                nb::arg("s"), R"pb(Returns False: k-LUT signals have no complemented edges.)pb")
            .def(
                "pi_at",
                [](const klut& ntk, const uint64_t index)
                {
                    check_index(index, ntk.num_pis());
                    return ntk.pi_at(static_cast<uint32_t>(index));
                },
                nb::arg("index"), R"pb(Returns the primary input node at index.)pb")
            .def(
                "po_at",
                [](const klut& ntk, const uint64_t index)
                {
                    check_index(index, ntk.num_pos());
                    return ntk.po_at(static_cast<uint32_t>(index));
                },
                nb::arg("index"), R"pb(Returns the primary output signal at index.)pb")
            .def(
                "po_index",
                [](const klut& ntk, const uint64_t s)
                {
                    check_index(s, ntk.size());
                    const auto index = ntk.po_index(s);
                    if (index >= ntk.num_pos())
                    {
                        throw nb::value_error("signal does not drive a primary output");
                    }
                    return index;
                },
                nb::arg("s"), R"pb(Returns the first primary-output position driven by a signal.)pb")
            .def("nodes", &nodes, R"pb(Returns all nodes in creation order.)pb")
            .def(
                "gates",
                [](const klut& ntk)
                {
                    std::vector<uint64_t> result;
                    result.reserve(ntk.num_gates());
                    ntk.foreach_gate([&](const auto n) { result.push_back(n); });
                    return result;
                },
                R"pb(Returns all LUT nodes in creation order.)pb")
            .def(
                "pis",
                [](const klut& ntk)
                {
                    std::vector<uint64_t> result;
                    result.reserve(ntk.num_pis());
                    ntk.foreach_pi([&](const auto n) { result.push_back(n); });
                    return result;
                },
                R"pb(Returns primary input nodes in interface order.)pb")
            .def(
                "pos",
                [](const klut& ntk)
                {
                    std::vector<uint64_t> result;
                    result.reserve(ntk.num_pos());
                    ntk.foreach_po([&](const auto n) { result.push_back(n); });
                    return result;
                },
                R"pb(Returns primary output signals in interface order.)pb")
            .def(
                "fanins",
                [](const klut& ntk, const uint64_t n)
                {
                    check_index(n, ntk.size());
                    std::vector<uint64_t> result;
                    result.reserve(ntk.fanin_size(n));
                    ntk.foreach_fanin(n, [&](const auto f) { result.push_back(f); });
                    return result;
                },
                nb::arg("n"), R"pb(Returns the ordered fanin signals of a node.)pb")
            .def(
                "node_function",
                [](const klut& ntk, const uint64_t n)
                {
                    check_index(n, ntk.size());
                    return ntk.node_function(n);
                },
                nb::arg("n"), R"pb(Returns an independent copy of the node's local truth table.)pb")
            .def("__len__", &klut::size, R"pb(Returns the number of nodes.)pb")
            .def(
                "__bool__", [](const klut& ntk) { return ntk.size() > 2 || ntk.num_pos() > 0; },
                R"pb(Returns whether the network has inputs, gates, or outputs.)pb")
            .def(
                "__iter__",
                [](const klut& ntk) { return nb::module_::import_("builtins").attr("iter")(nb::cast(nodes(ntk))); },
                R"pb(Iterates over all nodes.)pb", nb::sig("def __iter__(self) -> Iterator[int]"))
            .def(
                "__contains__",
                [](const klut& ntk, const nb::object& value)
                {
                    uint64_t n{};
                    return nb::isinstance<nb::int_>(value) && nb::try_cast(value, n) && n < ntk.size();
                },
                nb::arg("value"), R"pb(Returns whether an integer handle belongs to this network.)pb")
            .def(
                "__repr__",
                [](const klut& ntk)
                {
                    return fmt::format("Klut(pis={}, pos={}, gates={}, size={})", ntk.num_pis(), ntk.num_pos(),
                                       ntk.num_gates(), ntk.size());
                },
                R"pb(Returns a developer-friendly network summary.)pb");

    network.def(
        "create_buf",
        [](klut& ntk, const uint64_t a)
        {
            check_index(a, ntk.size());
            return ntk.create_buf(a);
        },
        nb::arg("a"), R"pb(Creates a BUF function from existing signals.)pb");
    network.def(
        "create_not",
        [](klut& ntk, const uint64_t a)
        {
            check_index(a, ntk.size());
            return ntk.create_not(a);
        },
        nb::arg("a"), R"pb(Creates a NOT function from existing signals.)pb");
    network.def(
        "create_and",
        [](klut& ntk, const uint64_t a, const uint64_t b)
        {
            check_index(a, ntk.size());
            check_index(b, ntk.size());
            return ntk.create_and(a, b);
        },
        nb::arg("a"), nb::arg("b"), R"pb(Creates an AND function from existing signals.)pb");
    network.def(
        "create_nand",
        [](klut& ntk, const uint64_t a, const uint64_t b)
        {
            check_index(a, ntk.size());
            check_index(b, ntk.size());
            return ntk.create_nand(a, b);
        },
        nb::arg("a"), nb::arg("b"), R"pb(Creates a NAND function from existing signals.)pb");
    network.def(
        "create_or",
        [](klut& ntk, const uint64_t a, const uint64_t b)
        {
            check_index(a, ntk.size());
            check_index(b, ntk.size());
            return ntk.create_or(a, b);
        },
        nb::arg("a"), nb::arg("b"), R"pb(Creates an OR function from existing signals.)pb");
    network.def(
        "create_xor",
        [](klut& ntk, const uint64_t a, const uint64_t b)
        {
            check_index(a, ntk.size());
            check_index(b, ntk.size());
            return ntk.create_xor(a, b);
        },
        nb::arg("a"), nb::arg("b"), R"pb(Creates an XOR function from existing signals.)pb");
    network.def(
        "create_lt",
        [](klut& ntk, const uint64_t a, const uint64_t b)
        {
            check_index(a, ntk.size());
            check_index(b, ntk.size());
            return ntk.create_lt(a, b);
        },
        nb::arg("a"), nb::arg("b"), R"pb(Creates an LT function from existing signals.)pb");
    network.def(
        "create_le",
        [](klut& ntk, const uint64_t a, const uint64_t b)
        {
            check_index(a, ntk.size());
            check_index(b, ntk.size());
            return ntk.create_le(a, b);
        },
        nb::arg("a"), nb::arg("b"), R"pb(Creates an LE function from existing signals.)pb");
    network.def(
        "create_maj",
        [](klut& ntk, const uint64_t a, const uint64_t b, const uint64_t c)
        {
            check_index(a, ntk.size());
            check_index(b, ntk.size());
            check_index(c, ntk.size());
            return ntk.create_maj(a, b, c);
        },
        nb::arg("a"), nb::arg("b"), nb::arg("c"), R"pb(Creates a MAJ function from existing signals.)pb");
    network.def(
        "create_ite",
        [](klut& ntk, const uint64_t cond, const uint64_t f_then, const uint64_t f_else)
        {
            check_index(cond, ntk.size());
            check_index(f_then, ntk.size());
            check_index(f_else, ntk.size());
            return ntk.create_ite(cond, f_then, f_else);
        },
        nb::arg("cond"), nb::arg("f_then"), nb::arg("f_else"), R"pb(Creates an ITE function from existing signals.)pb");
    network.def(
        "create_xor3",
        [](klut& ntk, const uint64_t a, const uint64_t b, const uint64_t c)
        {
            check_index(a, ntk.size());
            check_index(b, ntk.size());
            check_index(c, ntk.size());
            return ntk.create_xor3(a, b, c);
        },
        nb::arg("a"), nb::arg("b"), nb::arg("c"), R"pb(Creates an XOR3 function from existing signals.)pb");
    network.def(
        "create_nary_and",
        [](klut& ntk, const std::vector<uint64_t>& fs)
        {
            check_children(ntk, fs);
            return ntk.create_nary_and(fs);
        },
        nb::arg("fs"), R"pb(Creates an n-ary AND as a tree of binary LUTs.)pb");
    network.def(
        "create_nary_or",
        [](klut& ntk, const std::vector<uint64_t>& fs)
        {
            check_children(ntk, fs);
            return ntk.create_nary_or(fs);
        },
        nb::arg("fs"), R"pb(Creates an n-ary OR as a tree of binary LUTs.)pb");
    network.def(
        "create_nary_xor",
        [](klut& ntk, const std::vector<uint64_t>& fs)
        {
            check_children(ntk, fs);
            return ntk.create_nary_xor(fs);
        },
        nb::arg("fs"), R"pb(Creates an n-ary XOR as a tree of binary LUTs.)pb");
    network.def(
        "fanin_size",
        [](const klut& ntk, const uint64_t n)
        {
            check_index(n, ntk.size());
            return ntk.fanin_size(n);
        },
        nb::arg("n"), R"pb(Returns the number of fanins.)pb");
    network.def(
        "fanout_size",
        [](const klut& ntk, const uint64_t n)
        {
            check_index(n, ntk.size());
            return ntk.fanout_size(n);
        },
        nb::arg("n"), R"pb(Returns the reference count, including primary outputs.)pb");
    network.def(
        "is_constant",
        [](const klut& ntk, const uint64_t n)
        {
            check_index(n, ntk.size());
            return ntk.is_constant(n);
        },
        nb::arg("n"), R"pb(Returns whether the node is a Boolean constant.)pb");
    network.def(
        "is_pi",
        [](const klut& ntk, const uint64_t n)
        {
            check_index(n, ntk.size());
            return ntk.is_pi(n);
        },
        nb::arg("n"), R"pb(Returns whether the node is a primary input.)pb");
    network.def(
        "is_function",
        [](const klut& ntk, const uint64_t n)
        {
            check_index(n, ntk.size());
            return ntk.is_function(n);
        },
        nb::arg("n"), R"pb(Returns whether the node is a LUT gate.)pb");
    network.def(
        "constant_value",
        [](const klut& ntk, const uint64_t n)
        {
            check_index(n, ntk.size());
            if (!ntk.is_constant(n))
            {
                throw nb::value_error("node is not a constant");
            }
            return ntk.constant_value(n);
        },
        nb::arg("n"), R"pb(Returns the Boolean value of a constant node.)pb");

    auto named = bind_view<named_klut>(m, "NamedKlut", R"pb(A k-LUT network view with signal and interface names.)pb");
    named
        .def("create_pi", &named_klut::create_pi, nb::arg("name") = "",
             R"pb(Creates an optionally named primary input.)pb")
        .def(
            "create_po",
            [](named_klut& ntk, const uint64_t f, const std::string& name)
            {
                check_index(f, ntk.size());
                return ntk.create_po(f, name);
            },
            nb::arg("f"), nb::arg("name") = "", R"pb(Creates an optionally named primary output.)pb")
        .def("set_network_name", &named_klut::set_network_name, nb::arg("name"), R"pb(Sets the network name.)pb")
        .def("get_network_name", &named_klut::get_network_name, R"pb(Returns the network name.)pb")
        .def(
            "has_name",
            [](const named_klut& ntk, const uint64_t s)
            {
                check_index(s, ntk.size());
                return ntk.has_name(s);
            },
            nb::arg("s"), R"pb(Returns whether the signal has a name.)pb")
        .def(
            "set_name",
            [](named_klut& ntk, const uint64_t s, const std::string& name)
            {
                check_index(s, ntk.size());
                ntk.set_name(s, name);
            },
            nb::arg("s"), nb::arg("name"), R"pb(Sets a signal's name.)pb")
        .def(
            "get_name",
            [](const named_klut& ntk, const uint64_t s)
            {
                check_index(s, ntk.size());
                return ntk.get_name(s);
            },
            nb::arg("s"), R"pb(Returns a signal's name.)pb")
        .def(
            "has_output_name",
            [](const named_klut& ntk, const uint64_t index)
            {
                check_index(index, ntk.num_pos());
                return ntk.has_output_name(static_cast<uint32_t>(index));
            },
            nb::arg("index"), R"pb(Returns whether the primary output has a name.)pb")
        .def(
            "set_output_name",
            [](named_klut& ntk, const uint64_t index, const std::string& name)
            {
                check_index(index, ntk.num_pos());
                ntk.set_output_name(static_cast<uint32_t>(index), name);
            },
            nb::arg("index"), nb::arg("name"), R"pb(Sets a primary output's name.)pb")
        .def(
            "get_output_name",
            [](const named_klut& ntk, const uint64_t index)
            {
                check_index(index, ntk.num_pos());
                return ntk.get_output_name(static_cast<uint32_t>(index));
            },
            nb::arg("index"), R"pb(Returns a primary output's name.)pb");

    auto depth = bind_view<depth_klut>(m, "DepthKlut", R"pb(A k-LUT network view with unit-cost LUT levels.

Very deep chains can overflow the native stack and terminate the process.
The limit depends on the platform and thread stack.)pb");
    depth
        .def_prop_ro("num_levels", &depth_klut::depth,
                     R"pb(Current depth in LUT levels; update_levels() refreshes shared changes.)pb")
        .def(
            "level",
            [](const depth_klut& ntk, const uint64_t n)
            {
                check_index(n, ntk.size());
                return ntk.fanin_size(n) == 0 ? 0 : ntk.level(n);
            },
            nb::arg("n"), R"pb(Returns the level of a node.)pb")
        .def(
            "is_on_critical_path",
            [](depth_klut& ntk, const uint64_t n)
            {
                check_index(n, ntk.size());
                ntk.update_levels();
                return ntk.is_on_critical_path(n);
            },
            nb::arg("n"), R"pb(Recomputes levels and returns whether a node lies on a critical path.)pb")
        .def("update_levels", &depth_klut::update_levels,
             R"pb(Recomputes levels and critical paths from current outputs.)pb")
        .def(
            "create_po",
            [](depth_klut& ntk, const uint64_t f)
            {
                check_index(f, ntk.size());
                const auto index = ntk.klut::create_po(f);
                ntk.update_levels();
                return index;
            },
            nb::arg("f"), R"pb(Creates an output and recomputes levels from all current outputs.)pb");

    auto fanout = bind_view<fanouts_klut>(m, "FanoutKlut", R"pb(A k-LUT network view with gate fanout lists.)pb");
    fanout.def("update_fanout", &fanouts_klut::update_fanout, R"pb(Recomputes fanout lists.)pb")
        .def(
            "fanouts",
            [](const fanouts_klut& ntk, const uint64_t n)
            {
                check_index(n, ntk.size());
                std::vector<uint64_t> result;
                auto                  count = ntk.fanout_size(n);
                // Native PI creation does not resize fanout metadata until a gate uses the PI.
                if (count <= ntk.num_pos())
                {
                    ntk.foreach_po(
                        [&](const auto f)
                        {
                            if (f == n)
                            {
                                --count;
                            }
                        });
                    if (count == 0)
                    {
                        return result;
                    }
                }
                result.reserve(count);
                // Gates are append-only, so repeated fanins produce consecutive duplicate fanouts.
                ntk.foreach_fanout(n,
                                   [&](const auto f)
                                   {
                                       if (result.empty() || result.back() != f)
                                       {
                                           result.push_back(f);
                                       }
                                   });
                return result;
            },
            nb::arg("n"), R"pb(Returns the gate fanouts of a node; primary outputs are excluded.)pb");
}
}  // namespace aigverse
