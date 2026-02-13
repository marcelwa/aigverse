//
// Created by marcel on 03.09.25.
//

#include "aigverse/types.hpp"

#include <fmt/format.h>
#include <mockturtle/algorithms/cleanup.hpp>
#include <mockturtle/networks/sequential.hpp>
#include <mockturtle/traits.hpp>
#include <mockturtle/views/depth_view.hpp>
#include <mockturtle/views/fanout_view.hpp>
#include <mockturtle/views/names_view.hpp>
#include <pybind11/cast.h>
#include <pybind11/pybind11.h>
#include <pybind11/pytypes.h>
#include <pybind11/stl.h>  // NOLINT(misc-include-cleaner)

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

template <typename Ntk>
void bind_network(pybind11::module_& m, const std::string& network_name)  // NOLINT(misc-use-internal-linkage)
{
    namespace py = pybind11;

    using Node = mockturtle::node<Ntk>;  // NOLINT(readability-identifier-naming)
    py::class_<Node>(m, fmt::format("{}Node", network_name).c_str())
        .def(py::init<const uint64_t>(), py::arg("index"))
        .def("__hash__", [](const Node& n) { return std::hash<Node>{}(n); })
        .def("__repr__", [](const Node& n) { return fmt::format("Node({})", n); })
        .def("__eq__",
             [](const Node& self, const py::object& other) -> bool
             {
                 if (!py::isinstance<Node>(other))
                 {
                     return false;
                 }
                 return self == other.cast<const Node>();
             })
        .def("__ne__",
             [](const Node& self, const py::object& other) -> bool
             {
                 if (!py::isinstance<Node>(other))
                 {
                     return false;
                 }
                 return self != other.cast<const Node>();
             })
        .def("__lt__", [](const Node& n1, const Node& n2) { return n1 < n2; });

    py::implicitly_convertible<py::int_, Node>();  // NOLINT(misc-include-cleaner)

    using Signal = mockturtle::signal<Ntk>;  // NOLINT(readability-identifier-naming)
    py::class_<Signal>(m, fmt::format("{}Signal", network_name).c_str())
        .def(py::init<const uint64_t, const bool>(), py::arg("index"), py::arg("complement"))
        .def("get_index", [](const Signal& s) { return s.index; })
        .def("get_complement", [](const Signal& s) { return s.complement; })
        .def("get_data", [](const Signal& s) { return s.data; })
        .def("__hash__", [](const Signal& s) { return std::hash<Signal>{}(s); })
        .def("__repr__", [](const Signal& s) { return fmt::format("Signal({}{})", s.complement ? "!" : "", s.index); })
        .def("__eq__",
             [](const Signal& self, const py::object& other) -> bool
             {
                 if (!py::isinstance<Signal>(other))
                 {
                     return false;
                 }
                 return self == other.cast<const Signal>();
             })
        .def("__ne__",
             [](const Signal& self, const py::object& other) -> bool
             {
                 if (!py::isinstance<Signal>(other))
                 {
                     return false;
                 }
                 return self != other.cast<const Signal>();
             })
        .def("__lt__", [](const Signal& s1, const Signal& s2) { return s1 < s2; })
        .def("__invert__", [](const Signal& s) { return !s; })
        .def("__pos__", [](const Signal& s) { return +s; })
        .def("__neg__", [](const Signal& s) { return -s; })
        .def("__xor__", [](const Signal& s, const bool complement) { return s ^ complement; });

    py::class_<Ntk>(m, network_name.c_str())
        .def(py::init<>())
        .def("clone", &Ntk::clone)
        .def("size", &Ntk::size)
        .def("num_gates", &Ntk::num_gates)
        .def("num_pis", &Ntk::num_pis)
        .def("num_pos", &Ntk::num_pos)
        .def("get_node", &Ntk::get_node, py::arg("s"))
        .def("make_signal", &Ntk::make_signal, py::arg("n"))
        .def("is_complemented", &Ntk::is_complemented, py::arg("s"))
        .def("node_to_index", &Ntk::node_to_index, py::arg("n"))
        .def("index_to_node", &Ntk::index_to_node, py::arg("index"))
        .def("pi_index", &Ntk::pi_index, py::arg("n"))
        .def("pi_at", &Ntk::pi_at, py::arg("index"))
        .def("po_index", &Ntk::po_index, py::arg("s"))
        .def("po_at", &Ntk::po_at, py::arg("index"))
        .def("get_constant", &Ntk::get_constant, py::arg("value"))
        .def("create_pi", &Ntk::create_pi)
        .def("create_po", &Ntk::create_po, py::arg("f"))
        .def("is_combinational", &Ntk::is_combinational)
        .def("create_buf", &Ntk::create_buf, py::arg("a"))
        .def("create_not", &Ntk::create_not, py::arg("a"))
        .def("create_and", &Ntk::create_and, py::arg("a"), py::arg("b"))
        .def("create_nand", &Ntk::create_nand, py::arg("a"), py::arg("b"))
        .def("create_or", &Ntk::create_or, py::arg("a"), py::arg("b"))
        .def("create_nor", &Ntk::create_nor, py::arg("a"), py::arg("b"))
        .def("create_xor", &Ntk::create_xor, py::arg("a"), py::arg("b"))
        .def("create_xnor", &Ntk::create_xnor, py::arg("a"), py::arg("b"))
        .def("create_lt", &Ntk::create_lt, py::arg("a"), py::arg("b"))
        .def("create_le", &Ntk::create_le, py::arg("a"), py::arg("b"))
        .def("create_maj", &Ntk::create_maj, py::arg("a"), py::arg("b"), py::arg("c"))
        .def("create_ite", &Ntk::create_ite, py::arg("cond"), py::arg("f_then"), py::arg("f_else"))
        .def("create_xor3", &Ntk::create_xor3, py::arg("a"), py::arg("b"), py::arg("c"))
        .def("create_nary_and", &Ntk::create_nary_and, py::arg("fs"))
        .def("create_nary_or", &Ntk::create_nary_or, py::arg("fs"))
        .def("create_nary_xor", &Ntk::create_nary_xor, py::arg("fs"))
        .def("clone_node", &Ntk::clone_node, py::arg("other"), py::arg("source"), py::arg("children"))
        .def("nodes",
             [](const Ntk& ntk)
             {
                 std::vector<Node> nodes;
                 nodes.reserve(ntk.size());
                 ntk.foreach_node([&nodes](const auto& n) { nodes.push_back(n); });
                 return nodes;
             })
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
            py::arg("n"))
        .def(
            "fanin_size", [](const Ntk& ntk, const Node& n) { return ntk.fanin_size(n); }, py::arg("n"))
        .def(
            "fanout_size", [](const Ntk& ntk, const Node& n) { return ntk.fanout_size(n); }, py::arg("n"))
        .def("is_constant", &Ntk::is_constant, py::arg("n"))
        .def("is_pi", &Ntk::is_pi, py::arg("n"))
        .def("has_and", &Ntk::has_and, py::arg("a"), py::arg("b"))
        .def(
            "is_and", [](const Ntk& ntk, const Node& n) { return ntk.is_and(n); }, py::arg("n"))
        .def(
            "is_or", [](const Ntk& ntk, const Node& n) { return ntk.is_or(n); }, py::arg("n"))
        .def(
            "is_xor", [](const Ntk& ntk, const Node& n) { return ntk.is_xor(n); }, py::arg("n"))
        .def(
            "is_maj", [](const Ntk& ntk, const Node& n) { return ntk.is_maj(n); }, py::arg("n"))
        .def(
            "is_ite", [](const Ntk& ntk, const Node& n) { return ntk.is_ite(n); }, py::arg("n"))
        .def(
            "is_xor3", [](const Ntk& ntk, const Node& n) { return ntk.is_xor3(n); }, py::arg("n"))
        .def(
            "is_nary_and", [](const Ntk& ntk, const Node& n) { return ntk.is_nary_and(n); }, py::arg("n"))
        .def(
            "is_nary_or", [](const Ntk& ntk, const Node& n) { return ntk.is_nary_or(n); }, py::arg("n"))
        .def(py::pickle(
                 [](const Ntk& ntk)
                 {
                     aigverse::aig_index_list il{};
                     mockturtle::encode(il, ntk);
                     return py::make_tuple(py::cast(il.raw()));
                 },
                 [](const py::tuple& state)
                 {
                     if (state.size() != 1)
                     {
                         // NOLINTNEXTLINE(misc-include-cleaner)
                         throw py::value_error("Invalid state: expected a tuple of size 1 containing an index list");
                     }
                     try
                     {
                         const aigverse::aig_index_list il{state[0].cast<std::vector<uint32_t>>()};

                         Ntk ntk{};
                         mockturtle::decode(ntk, il);

                         return ntk;
                     }
                     catch (const py::cast_error& e)  // NOLINT(misc-include-cleaner)
                     {
                         throw py::value_error(fmt::format("Invalid state: expected an index list. {}", e.what()));
                     }
                     catch (const std::exception& e)
                     {
                         throw py::value_error(fmt::format("Failed to restore network state: {}", e.what()));
                     }
                 }),
             py::arg("state"))
        .def("cleanup_dangling", [](Ntk& ntk) { ntk = mockturtle::cleanup_dangling(ntk); });

    using NamedNtk = mockturtle::names_view<Ntk>;
    py::class_<NamedNtk, Ntk>(m, fmt::format("Named{}", network_name).c_str())
        .def(py::init<>())
        .def(py::init<const NamedNtk&>(), py::arg("ntk"))
        .def(py::init<const Ntk&>(), py::arg("ntk"))
        .def("create_pi", &NamedNtk::create_pi, py::arg("name") = "")
        .def("create_po", &NamedNtk::create_po, py::arg("f"), py::arg("name") = "")
        .def("set_network_name", &NamedNtk::set_network_name, py::arg("name"))
        .def("get_network_name", &NamedNtk::get_network_name)
        .def("has_name", &NamedNtk::has_name, py::arg("s"))
        .def("set_name", &NamedNtk::set_name, py::arg("s"), py::arg("name"))
        .def("get_name", &NamedNtk::get_name, py::arg("s"))
        .def("has_output_name", &NamedNtk::has_output_name, py::arg("index"))
        .def("set_output_name", &NamedNtk::set_output_name, py::arg("index"), py::arg("name"))
        .def("get_output_name", &NamedNtk::get_output_name, py::arg("index"));

    using DepthNtk = mockturtle::depth_view<Ntk>;
    py::class_<DepthNtk, Ntk>(m, fmt::format("Depth{}", network_name).c_str())
        .def(py::init<>())
        .def(py::init<const DepthNtk&>(), py::arg("ntk"))
        .def(py::init<const Ntk&>(), py::arg("ntk"))
        .def("num_levels", &DepthNtk::depth)
        .def("level", &DepthNtk::level, py::arg("n"))
        .def("is_on_critical_path", &DepthNtk::is_on_critical_path, py::arg("n"))
        .def("update_levels", &DepthNtk::update_levels)
        .def("create_po", &DepthNtk::create_po, py::arg("f"));

    using FanoutNtk = mockturtle::fanout_view<Ntk>;
    py::class_<FanoutNtk, Ntk>(m, fmt::format("Fanout{}", network_name).c_str())
        .def(py::init<>())
        .def(py::init<const Ntk&>(), py::arg("ntk"))
        .def(py::init<const FanoutNtk&>(), py::arg("ntk"))
        .def(
            "fanouts",
            [](const FanoutNtk& ntk, const Node& n)
            {
                std::vector<Node> fanouts;
                fanouts.reserve(ntk.fanout_size(n));
                ntk.foreach_fanout(n, [&fanouts](const auto& f) { fanouts.push_back(f); });
                return fanouts;
            },
            py::arg("n"));

    using Register = mockturtle::register_t;  // NOLINT(readability-identifier-naming)
    py::class_<Register>(m, fmt::format("{}Register", network_name).c_str())
        .def(py::init<>())
        .def(py::init<const Register&>(), py::arg("register"))
        .def_readwrite("control", &Register::control)
        .def_readwrite("init", &Register::init)
        .def_readwrite("type", &Register::type);

    using SequentialNtk = mockturtle::sequential<Ntk>;
    py::class_<SequentialNtk, Ntk>(m, fmt::format("Sequential{}", network_name).c_str())
        .def(py::init<>())
        .def("create_pi", &SequentialNtk::create_pi)
        .def("create_po", &SequentialNtk::create_po, py::arg("f"))
        .def("create_ro", &SequentialNtk::create_ro)
        .def("create_ri", &SequentialNtk::create_ri, py::arg("f"))
        .def("is_combinational", &SequentialNtk::is_combinational)
        .def("is_ci", &SequentialNtk::is_ci, py::arg("n"))
        .def("is_pi", &SequentialNtk::is_pi, py::arg("n"))
        .def("is_ro", &SequentialNtk::is_ro, py::arg("n"))
        .def("num_pis", &SequentialNtk::num_pis)
        .def("num_pos", &SequentialNtk::num_pos)
        .def("num_cis", &SequentialNtk::num_cis)
        .def("num_cos", &SequentialNtk::num_cos)
        .def("num_registers", &SequentialNtk::num_registers)
        .def("pi_at", &SequentialNtk::pi_at, py::arg("index"))
        .def("po_at", &SequentialNtk::po_at, py::arg("index"))
        .def("ci_at", &SequentialNtk::ci_at, py::arg("index"))
        .def("co_at", &SequentialNtk::co_at, py::arg("index"))
        .def("ro_at", &SequentialNtk::ro_at, py::arg("index"))
        .def("ri_at", &SequentialNtk::ri_at, py::arg("index"))
        .def("set_register", &SequentialNtk::set_register, py::arg("index"), py::arg("reg"))
        .def("register_at", &SequentialNtk::register_at, py::arg("index"))
        .def("pi_index", &SequentialNtk::pi_index, py::arg("n"))
        .def("ci_index", &SequentialNtk::ci_index, py::arg("n"))
        .def("co_index", &SequentialNtk::co_index, py::arg("s"))
        .def("ro_index", &SequentialNtk::ro_index, py::arg("n"))
        .def("ri_index", &SequentialNtk::ri_index, py::arg("s"))
        .def("ro_to_ri", &SequentialNtk::ro_to_ri, py::arg("s"))
        .def("ri_to_ro", &SequentialNtk::ri_to_ro, py::arg("s"))
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
             });
}

// Explicit instantiation for AIG
template void bind_network<aigverse::aig>(pybind11::module_&, const std::string&);

}  // namespace detail

void bind_logic_networks(pybind11::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::bind_network<aigverse::aig>(m, "Aig");
}

}  // namespace aigverse
