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

    using Signal = mockturtle::signal<Ntk>;  // NOLINT(readability-identifier-naming)
    nb::class_<Signal>(m, fmt::format("{}Signal", network_name).c_str())
        .def(nb::init<const uint64_t, const bool>(), nb::arg("index"), nb::arg("complement"))
        .def_prop_ro("index", [](const Signal& s) { return s.index; })
        .def_prop_ro("complement", [](const Signal& s) -> bool { return s.complement; })
        .def_prop_ro("data", [](const Signal& s) { return s.data; })
        .def("__hash__", [](const Signal& s) { return std::hash<Signal>{}(s); })
        .def("__repr__", [](const Signal& s) { return fmt::format("Signal({}{})", s.complement ? "!" : "", s.index); })
        .def("__eq__",
             [](const Signal& self, const nb::object& other) -> bool
             {
                 if (!nb::isinstance<Signal>(other))
                 {
                     return false;
                 }
                 return self == nb::cast<const Signal>(other);
             })
        .def("__ne__",
             [](const Signal& self, const nb::object& other) -> bool
             {
                 if (!nb::isinstance<Signal>(other))
                 {
                     return false;
                 }
                 return self != nb::cast<const Signal>(other);
             })
        .def("__lt__", [](const Signal& s1, const Signal& s2) { return s1 < s2; })
        .def("__invert__", [](const Signal& s) { return !s; })
        .def("__pos__", [](const Signal& s) { return +s; })
        .def("__neg__", [](const Signal& s) { return -s; })
        .def("__xor__", [](const Signal& s, const bool complement) { return s ^ complement; });

    nb::class_<Ntk>(m, network_name.c_str())
        .def(nb::init<>())
        .def("clone", &Ntk::clone)
        .def_prop_ro("size", &Ntk::size)
        .def_prop_ro("num_gates", &Ntk::num_gates)
        .def_prop_ro("num_pis", &Ntk::num_pis)
        .def_prop_ro("num_pos", &Ntk::num_pos)
        .def("get_node", &Ntk::get_node, nb::arg("s"))
        .def("make_signal", &Ntk::make_signal, nb::arg("n"))
        .def("is_complemented", &Ntk::is_complemented, nb::arg("s"))
        .def("node_to_index", &Ntk::node_to_index, nb::arg("n"))
        .def("index_to_node", &Ntk::index_to_node, nb::arg("index"))
        .def("pi_index", &Ntk::pi_index, nb::arg("n"))
        .def("pi_at", &Ntk::pi_at, nb::arg("index"))
        .def("po_index", &Ntk::po_index, nb::arg("s"))
        .def("po_at", &Ntk::po_at, nb::arg("index"))
        .def("get_constant", &Ntk::get_constant, nb::arg("value"))
        .def("create_pi", &Ntk::create_pi)
        .def("create_po", &Ntk::create_po, nb::arg("f"))
        .def_prop_ro("is_combinational", &Ntk::is_combinational)
        .def("create_buf", &Ntk::create_buf, nb::arg("a"))
        .def("create_not", &Ntk::create_not, nb::arg("a"))
        .def("create_and", &Ntk::create_and, nb::arg("a"), nb::arg("b"))
        .def("create_nand", &Ntk::create_nand, nb::arg("a"), nb::arg("b"))
        .def("create_or", &Ntk::create_or, nb::arg("a"), nb::arg("b"))
        .def("create_nor", &Ntk::create_nor, nb::arg("a"), nb::arg("b"))
        .def("create_xor", &Ntk::create_xor, nb::arg("a"), nb::arg("b"))
        .def("create_xnor", &Ntk::create_xnor, nb::arg("a"), nb::arg("b"))
        .def("create_lt", &Ntk::create_lt, nb::arg("a"), nb::arg("b"))
        .def("create_le", &Ntk::create_le, nb::arg("a"), nb::arg("b"))
        .def("create_maj", &Ntk::create_maj, nb::arg("a"), nb::arg("b"), nb::arg("c"))
        .def("create_ite", &Ntk::create_ite, nb::arg("cond"), nb::arg("f_then"), nb::arg("f_else"))
        .def("create_xor3", &Ntk::create_xor3, nb::arg("a"), nb::arg("b"), nb::arg("c"))
        .def("create_nary_and", &Ntk::create_nary_and, nb::arg("fs"))
        .def("create_nary_or", &Ntk::create_nary_or, nb::arg("fs"))
        .def("create_nary_xor", &Ntk::create_nary_xor, nb::arg("fs"))
        .def("clone_node", &Ntk::clone_node, nb::arg("other"), nb::arg("source"), nb::arg("children"))
        .def("nodes", [](const Ntk& ntk) { return collect_nodes(ntk); })
        .def("gates",
             [](const Ntk& ntk)
             {
                 std::vector<Node> gates;
                 gates.reserve(ntk.num_gates());
                 ntk.foreach_gate([&gates](const auto& g) { gates.push_back(g); });
                 return gates;
             })
        .def("pis",
             [](const Ntk& ntk)
             {
                 std::vector<Node> pis;
                 pis.reserve(ntk.num_pis());
                 ntk.foreach_pi([&pis](const auto& pi) { pis.push_back(pi); });
                 return pis;
             })
        .def("pos",
             [](const Ntk& ntk)
             {
                 std::vector<Signal> pos;
                 pos.reserve(ntk.num_pos());
                 ntk.foreach_po([&pos](const auto& po) { pos.push_back(po); });
                 return pos;
             })
        .def(
            "fanins",
            [](const Ntk& ntk, const Node& n)
            {
                std::vector<Signal> fanins;
                fanins.reserve(ntk.fanin_size(n));
                ntk.foreach_fanin(n, [&fanins](const auto& f) { fanins.push_back(f); });
                return fanins;
            },
            nb::arg("n"))
        .def(
            "fanin_size", [](const Ntk& ntk, const Node& n) { return ntk.fanin_size(n); }, nb::arg("n"))
        .def(
            "fanout_size", [](const Ntk& ntk, const Node& n) { return ntk.fanout_size(n); }, nb::arg("n"))
        .def("is_constant", &Ntk::is_constant, nb::arg("n"))
        .def("is_pi", &Ntk::is_pi, nb::arg("n"))
        .def("has_and", &Ntk::has_and, nb::arg("a"), nb::arg("b"))
        .def(
            "is_and", [](const Ntk& ntk, const Node& n) { return ntk.is_and(n); }, nb::arg("n"))
        .def(
            "is_or", [](const Ntk& ntk, const Node& n) { return ntk.is_or(n); }, nb::arg("n"))
        .def(
            "is_xor", [](const Ntk& ntk, const Node& n) { return ntk.is_xor(n); }, nb::arg("n"))
        .def(
            "is_maj", [](const Ntk& ntk, const Node& n) { return ntk.is_maj(n); }, nb::arg("n"))
        .def(
            "is_ite", [](const Ntk& ntk, const Node& n) { return ntk.is_ite(n); }, nb::arg("n"))
        .def(
            "is_xor3", [](const Ntk& ntk, const Node& n) { return ntk.is_xor3(n); }, nb::arg("n"))
        .def(
            "is_nary_and", [](const Ntk& ntk, const Node& n) { return ntk.is_nary_and(n); }, nb::arg("n"))
        .def(
            "is_nary_or", [](const Ntk& ntk, const Node& n) { return ntk.is_nary_or(n); }, nb::arg("n"))
        .def(
            "to_edge_list", [](const Ntk& ntk, const int64_t regular_weight = 0, const int64_t inverted_weight = 1)
            { return aigverse::to_edge_list(ntk, regular_weight, inverted_weight); }, nb::arg("regular_weight") = 0,
            nb::arg("inverted_weight") = 1, nb::rv_policy::move)
        .def(
            "to_index_list",
            [](const Ntk& ntk)
            {
                aigverse::aig_index_list il{};
                mockturtle::encode(il, ntk);
                return il;
            },
            nb::rv_policy::move)
        .def("__len__", &Ntk::size)
        .def("__repr__",
             [network_name](const Ntk& ntk)
             {
                 return fmt::format("{}(pis={}, pos={}, gates={}, size={})", network_name, ntk.num_pis(), ntk.num_pos(),
                                    ntk.num_gates(), ntk.size());
             })
        .def(
            "__iter__", [](const Ntk& ntk) { return make_node_iterator(ntk); },
            nb::sig("def __iter__(self) -> Iterator[int]"))
        .def("__contains__", [](const Ntk& ntk, const nb::object& value) { return contains_node(ntk, value); })
        .def("__bool__", [](const Ntk& ntk) { return ntk.size() > 1; })
        .def("__copy__", [](const Ntk& ntk) { return ntk.clone(); })
        .def(
            "__deepcopy__", [](const Ntk& ntk, const nb::dict&) { return ntk.clone(); }, nb::arg("memo"))
        .def("__setstate__",
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
             })
        .def("__getstate__",
             [](const Ntk& ntk)
             {
                 aigverse::aig_index_list il{};
                 mockturtle::encode(il, ntk);
                 return nb::make_tuple(nb::cast(il.raw()));
             });

    using NamedNtk = mockturtle::names_view<Ntk>;
    nb::class_<NamedNtk, Ntk>(m, fmt::format("Named{}", network_name).c_str())
        .def(nb::init<>())
        .def(nb::init<const NamedNtk&>(), nb::arg("ntk"))
        .def(nb::init<const Ntk&>(), nb::arg("ntk"))
        .def("create_pi", &NamedNtk::create_pi, nb::arg("name") = "")
        .def("create_po", &NamedNtk::create_po, nb::arg("f"), nb::arg("name") = "")
        .def("set_network_name", &NamedNtk::set_network_name, nb::arg("name"))
        .def("get_network_name", &NamedNtk::get_network_name)
        .def("has_name", &NamedNtk::has_name, nb::arg("s"))
        .def("set_name", &NamedNtk::set_name, nb::arg("s"), nb::arg("name"))
        .def("get_name", &NamedNtk::get_name, nb::arg("s"))
        .def("has_output_name", &NamedNtk::has_output_name, nb::arg("index"))
        .def("set_output_name", &NamedNtk::set_output_name, nb::arg("index"), nb::arg("name"))
        .def("get_output_name", &NamedNtk::get_output_name, nb::arg("index"))
        .def("__repr__",
             [network_name](const NamedNtk& ntk)
             {
                 return fmt::format("Named{}(name={}, pis={}, pos={}, gates={})", network_name, ntk.get_network_name(),
                                    ntk.num_pis(), ntk.num_pos(), ntk.num_gates());
             });

    using DepthNtk = mockturtle::depth_view<Ntk>;
    nb::class_<DepthNtk, Ntk>(m, fmt::format("Depth{}", network_name).c_str())
        .def(nb::init<>())
        .def(nb::init<const DepthNtk&>(), nb::arg("ntk"))
        .def(nb::init<const Ntk&>(), nb::arg("ntk"))
        .def_prop_ro("num_levels", &DepthNtk::depth)
        .def("level", &DepthNtk::level, nb::arg("n"))
        .def("is_on_critical_path", &DepthNtk::is_on_critical_path, nb::arg("n"))
        .def("update_levels", &DepthNtk::update_levels)
        .def("create_po", &DepthNtk::create_po, nb::arg("f"))
        .def("__repr__",
             [network_name](const DepthNtk& ntk)
             {
                 return fmt::format("Depth{}(pis={}, pos={}, gates={}, depth={})", network_name, ntk.num_pis(),
                                    ntk.num_pos(), ntk.num_gates(), ntk.depth());
             });

    using FanoutNtk = mockturtle::fanout_view<Ntk>;
    nb::class_<FanoutNtk, Ntk>(m, fmt::format("Fanout{}", network_name).c_str())
        .def(nb::init<>())
        .def(nb::init<const Ntk&>(), nb::arg("ntk"))
        .def(nb::init<const FanoutNtk&>(), nb::arg("ntk"))
        .def(
            "fanouts",
            [](const FanoutNtk& ntk, const Node& n)
            {
                std::vector<Node> fanouts;
                fanouts.reserve(ntk.fanout_size(n));
                ntk.foreach_fanout(n, [&fanouts](const auto& f) { fanouts.push_back(f); });
                return fanouts;
            },
            nb::arg("n"));

    using Register = mockturtle::register_t;  // NOLINT(readability-identifier-naming)
    nb::class_<Register>(m, fmt::format("{}Register", network_name).c_str())
        .def(nb::init<>())
        .def(nb::init<const Register&>(), nb::arg("register"))
        .def_rw("control", &Register::control)
        .def_rw("init", &Register::init)
        .def_rw("type", &Register::type);

    using SequentialNtk = mockturtle::sequential<Ntk>;
    nb::class_<SequentialNtk, Ntk>(m, fmt::format("Sequential{}", network_name).c_str())
        .def(nb::init<>())
        .def("create_pi", &SequentialNtk::create_pi)
        .def("create_po", &SequentialNtk::create_po, nb::arg("f"))
        .def("create_ro", &SequentialNtk::create_ro)
        .def("create_ri", &SequentialNtk::create_ri, nb::arg("f"))
        .def_prop_ro("is_combinational", &SequentialNtk::is_combinational)
        .def("is_ci", &SequentialNtk::is_ci, nb::arg("n"))
        .def("is_pi", &SequentialNtk::is_pi, nb::arg("n"))
        .def("is_ro", &SequentialNtk::is_ro, nb::arg("n"))
        .def_prop_ro("num_pis", &SequentialNtk::num_pis)
        .def_prop_ro("num_pos", &SequentialNtk::num_pos)
        .def_prop_ro("num_cis", &SequentialNtk::num_cis)
        .def_prop_ro("num_cos", &SequentialNtk::num_cos)
        .def_prop_ro("num_registers", &SequentialNtk::num_registers)
        .def("pi_at", &SequentialNtk::pi_at, nb::arg("index"))
        .def("po_at", &SequentialNtk::po_at, nb::arg("index"))
        .def("ci_at", &SequentialNtk::ci_at, nb::arg("index"))
        .def("co_at", &SequentialNtk::co_at, nb::arg("index"))
        .def("ro_at", &SequentialNtk::ro_at, nb::arg("index"))
        .def("ri_at", &SequentialNtk::ri_at, nb::arg("index"))
        .def("set_register", &SequentialNtk::set_register, nb::arg("index"), nb::arg("reg"))
        .def("register_at", &SequentialNtk::register_at, nb::arg("index"))
        .def("pi_index", &SequentialNtk::pi_index, nb::arg("n"))
        .def("ci_index", &SequentialNtk::ci_index, nb::arg("n"))
        .def("co_index", &SequentialNtk::co_index, nb::arg("s"))
        .def("ro_index", &SequentialNtk::ro_index, nb::arg("n"))
        .def("ri_index", &SequentialNtk::ri_index, nb::arg("s"))
        .def("ro_to_ri", &SequentialNtk::ro_to_ri, nb::arg("s"))
        .def("ri_to_ro", &SequentialNtk::ri_to_ro, nb::arg("s"))
        .def("to_index_list",
             [network_name](const SequentialNtk&) -> aigverse::aig_index_list
             {
                 const auto message = fmt::format("Sequential{} does not support to_index_list() because AigIndexList "
                                                  "is combinational-only and would drop register state.",
                                                  network_name);
                 throw nb::type_error(message.c_str());
             })
        .def(
            "to_edge_list",
            [](const SequentialNtk& ntk, const int64_t regular_weight = 0, const int64_t inverted_weight = 1)
            { return aigverse::to_edge_list(ntk, regular_weight, inverted_weight); }, nb::arg("regular_weight") = 0,
            nb::arg("inverted_weight") = 1, nb::rv_policy::move)
        .def("pis",
             [](const SequentialNtk& ntk)
             {
                 std::vector<Node> pis;
                 pis.reserve(ntk.num_pis());
                 ntk.foreach_pi([&pis](const auto& pi) { pis.push_back(pi); });
                 return pis;
             })
        .def("pos",
             [](const SequentialNtk& ntk)
             {
                 std::vector<Signal> pos;
                 pos.reserve(ntk.num_pos());
                 ntk.foreach_po([&pos](const auto& po) { pos.push_back(po); });
                 return pos;
             })
        .def("cis",
             [](const SequentialNtk& ntk)
             {
                 std::vector<Node> cis;
                 cis.reserve(ntk.num_cis());
                 ntk.foreach_ci([&cis](const auto& ci) { cis.push_back(ci); });
                 return cis;
             })
        .def("cos",
             [](const SequentialNtk& ntk)
             {
                 std::vector<Signal> cos;
                 cos.reserve(ntk.num_cos());
                 ntk.foreach_co([&cos](const auto& co) { cos.push_back(co); });
                 return cos;
             })
        .def("ros",
             [](const SequentialNtk& ntk)
             {
                 std::vector<Node> ros;
                 ros.reserve(ntk.num_registers());
                 ntk.foreach_ro([&ros](const auto& ro) { ros.push_back(ro); });
                 return ros;
             })
        .def("ris",
             [](const SequentialNtk& ntk)
             {
                 std::vector<Signal> ris;
                 ris.reserve(ntk.num_registers());
                 ntk.foreach_ri([&ris](const auto& ri) { ris.push_back(ri); });
                 return ris;
             })
        .def("registers",
             [](const SequentialNtk& ntk)
             {
                 std::vector<std::pair<Signal, Node>> regs;
                 regs.reserve(ntk.num_registers());
                 ntk.foreach_register([&regs](const auto& reg) { regs.push_back(reg); });
                 return regs;
             })
        .def("__repr__",
             [network_name](const SequentialNtk& ntk)
             {
                 return fmt::format("Sequential{}(pis={}, pos={}, gates={}, registers={})", network_name, ntk.num_pis(),
                                    ntk.num_pos(), ntk.num_gates(), ntk.num_registers());
             });
}

// Explicit instantiation for AIG
template void bind_network<aigverse::aig>(nanobind::module_&, const std::string&);

}  // namespace detail

void bind_logic_networks(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::bind_network<aigverse::aig>(m, "Aig");
}

}  // namespace aigverse
