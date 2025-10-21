//
// Created by marcel on 03.09.25.
//

#include "aigverse/networks/logic_networks.hpp"

#include <fmt/format.h>
#include <mockturtle/algorithms/cleanup.hpp>
#include <mockturtle/traits.hpp>
#include <mockturtle/views/depth_view.hpp>
#include <mockturtle/views/fanout_view.hpp>
#include <mockturtle/views/names_view.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <cstdint>
#include <functional>
#include <string>
#include <utility>
#include <vector>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void bind_network(pybind11::module_& m, const std::string& network_name)
{
    namespace py = pybind11;
    using namespace pybind11::literals;

    using Node = mockturtle::node<Ntk>;
    py::class_<Node>(m, fmt::format("{}Node", network_name).c_str())
        .def(py::init<const uint64_t>(), "index"_a)
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

    py::implicitly_convertible<py::int_, Node>();

    using Signal = mockturtle::signal<Ntk>;
    py::class_<Signal>(m, fmt::format("{}Signal", network_name).c_str())
        .def(py::init<const uint64_t, const bool>(), "index"_a, "complement"_a)
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
        .def("get_node", &Ntk::get_node, "s"_a)
        .def("make_signal", &Ntk::make_signal, "n"_a)
        .def("is_complemented", &Ntk::is_complemented, "s"_a)
        .def("node_to_index", &Ntk::node_to_index, "n"_a)
        .def("index_to_node", &Ntk::index_to_node, "index"_a)
        .def("pi_index", &Ntk::pi_index, "n"_a)
        .def("pi_at", &Ntk::pi_at, "index"_a)
        .def("po_index", &Ntk::po_index, "s"_a)
        .def("po_at", &Ntk::po_at, "index"_a)
        .def("get_constant", &Ntk::get_constant, "value"_a)
        .def("create_pi", &Ntk::create_pi)
        .def("create_po", &Ntk::create_po, "f"_a)
        .def("is_combinational", &Ntk::is_combinational)
        .def("create_buf", &Ntk::create_buf, "a"_a)
        .def("create_not", &Ntk::create_not, "a"_a)
        .def("create_and", &Ntk::create_and, "a"_a, "b"_a)
        .def("create_nand", &Ntk::create_nand, "a"_a, "b"_a)
        .def("create_or", &Ntk::create_or, "a"_a, "b"_a)
        .def("create_nor", &Ntk::create_nor, "a"_a, "b"_a)
        .def("create_xor", &Ntk::create_xor, "a"_a, "b"_a)
        .def("create_xnor", &Ntk::create_xnor, "a"_a, "b"_a)
        .def("create_lt", &Ntk::create_lt, "a"_a, "b"_a)
        .def("create_le", &Ntk::create_le, "a"_a, "b"_a)
        .def("create_maj", &Ntk::create_maj, "a"_a, "b"_a, "c"_a)
        .def("create_ite", &Ntk::create_ite, "cond"_a, "f_then"_a, "f_else"_a)
        .def("create_xor3", &Ntk::create_xor3, "a"_a, "b"_a, "c"_a)
        .def("create_nary_and", &Ntk::create_nary_and, "fs"_a)
        .def("create_nary_or", &Ntk::create_nary_or, "fs"_a)
        .def("create_nary_xor", &Ntk::create_nary_xor, "fs"_a)
        .def("clone_node", &Ntk::clone_node, "other"_a, "source"_a, "children"_a)
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
            "n"_a)
        .def(
            "fanin_size", [](const Ntk& ntk, const Node& n) { return ntk.fanin_size(n); }, "n"_a)
        .def(
            "fanout_size", [](const Ntk& ntk, const Node& n) { return ntk.fanout_size(n); }, "n"_a)
        .def("is_constant", &Ntk::is_constant, "n"_a)
        .def("is_pi", &Ntk::is_pi, "n"_a)
        .def("has_and", &Ntk::has_and, "a"_a, "b"_a)
        .def(
            "is_and", [](const Ntk& ntk, const Node& n) { return ntk.is_and(n); }, "n"_a)
        .def(
            "is_or", [](const Ntk& ntk, const Node& n) { return ntk.is_or(n); }, "n"_a)
        .def(
            "is_xor", [](const Ntk& ntk, const Node& n) { return ntk.is_xor(n); }, "n"_a)
        .def(
            "is_maj", [](const Ntk& ntk, const Node& n) { return ntk.is_maj(n); }, "n"_a)
        .def(
            "is_ite", [](const Ntk& ntk, const Node& n) { return ntk.is_ite(n); }, "n"_a)
        .def(
            "is_xor3", [](const Ntk& ntk, const Node& n) { return ntk.is_xor3(n); }, "n"_a)
        .def(
            "is_nary_and", [](const Ntk& ntk, const Node& n) { return ntk.is_nary_and(n); }, "n"_a)
        .def(
            "is_nary_or", [](const Ntk& ntk, const Node& n) { return ntk.is_nary_or(n); }, "n"_a)
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
                         throw py::value_error("Invalid state: expected a tuple of size 1 containing an index list");
                     }
                     try
                     {
                         const aigverse::aig_index_list il{state[0].cast<std::vector<uint32_t>>()};

                         Ntk ntk{};
                         mockturtle::decode(ntk, il);

                         return ntk;
                     }
                     catch (const py::cast_error& e)
                     {
                         throw py::value_error(fmt::format("Invalid state: expected an index list. {}", e.what()));
                     }
                     catch (const std::exception& e)
                     {
                         throw py::value_error(fmt::format("Failed to restore network state: {}", e.what()));
                     }
                 }),
             "state"_a)
        .def("cleanup_dangling", [](Ntk& ntk) { ntk = mockturtle::cleanup_dangling(ntk); });

    using NamedNtk = mockturtle::names_view<Ntk>;
    py::class_<NamedNtk, Ntk>(m, fmt::format("Named{}", network_name).c_str())
        .def(py::init<>())
        .def(py::init<const NamedNtk&>(), "ntk"_a)
        .def(py::init<const Ntk&>(), "ntk"_a)
        .def("create_pi", &NamedNtk::create_pi, "name"_a = "")
        .def("create_po", &NamedNtk::create_po, "f"_a, "name"_a = "")
        .def("set_network_name", &NamedNtk::set_network_name, "name"_a)
        .def("get_network_name", &NamedNtk::get_network_name)
        .def("has_name", &NamedNtk::has_name, "s"_a)
        .def("set_name", &NamedNtk::set_name, "s"_a, "name"_a)
        .def("get_name", &NamedNtk::get_name, "s"_a)
        .def("has_output_name", &NamedNtk::has_output_name, "index"_a)
        .def("set_output_name", &NamedNtk::set_output_name, "index"_a, "name"_a)
        .def("get_output_name", &NamedNtk::get_output_name, "index"_a);

    using DepthNtk = mockturtle::depth_view<Ntk>;
    py::class_<DepthNtk, Ntk>(m, fmt::format("Depth{}", network_name).c_str())
        .def(py::init<>())
        .def(py::init<const DepthNtk&>(), "ntk"_a)
        .def(py::init<const Ntk&>(), "ntk"_a)
        .def("num_levels", &DepthNtk::depth)
        .def("level", &DepthNtk::level, "n"_a)
        .def("is_on_critical_path", &DepthNtk::is_on_critical_path, "n"_a)
        .def("update_levels", &DepthNtk::update_levels)
        .def("create_po", &DepthNtk::create_po, "f"_a);

    using FanoutNtk = mockturtle::fanout_view<Ntk>;
    py::class_<FanoutNtk, Ntk>(m, fmt::format("Fanout{}", network_name).c_str())
        .def(py::init<>())
        .def(py::init<const Ntk&>(), "ntk"_a)
        .def(py::init<const FanoutNtk&>(), "ntk"_a)
        .def(
            "fanouts",
            [](const FanoutNtk& ntk, const Node& n)
            {
                std::vector<Node> fanouts;
                fanouts.reserve(ntk.fanout_size(n));
                ntk.foreach_fanout(n, [&fanouts](const auto& f) { fanouts.push_back(f); });
                return fanouts;
            },
            "n"_a);

    using Register = mockturtle::register_t;
    py::class_<Register>(m, fmt::format("{}Register", network_name).c_str())
        .def(py::init<>())
        .def(py::init<const Register&>(), "register"_a)
        .def_readwrite("control", &Register::control)
        .def_readwrite("init", &Register::init)
        .def_readwrite("type", &Register::type);

    using SequentialNtk = mockturtle::sequential<Ntk>;
    py::class_<SequentialNtk, Ntk>(m, fmt::format("Sequential{}", network_name).c_str())
        .def(py::init<>())
        .def("create_pi", &SequentialNtk::create_pi)
        .def("create_po", &SequentialNtk::create_po, "f"_a)
        .def("create_ro", &SequentialNtk::create_ro)
        .def("create_ri", &SequentialNtk::create_ri, "f"_a)
        .def("is_combinational", &SequentialNtk::is_combinational)
        .def("is_ci", &SequentialNtk::is_ci, "n"_a)
        .def("is_pi", &SequentialNtk::is_pi, "n"_a)
        .def("is_ro", &SequentialNtk::is_ro, "n"_a)
        .def("num_pis", &SequentialNtk::num_pis)
        .def("num_pos", &SequentialNtk::num_pos)
        .def("num_cis", &SequentialNtk::num_cis)
        .def("num_cos", &SequentialNtk::num_cos)
        .def("num_registers", &SequentialNtk::num_registers)
        .def("pi_at", &SequentialNtk::pi_at, "index"_a)
        .def("po_at", &SequentialNtk::po_at, "index"_a)
        .def("ci_at", &SequentialNtk::ci_at, "index"_a)
        .def("co_at", &SequentialNtk::co_at, "index"_a)
        .def("ro_at", &SequentialNtk::ro_at, "index"_a)
        .def("ri_at", &SequentialNtk::ri_at, "index"_a)
        .def("set_register", &SequentialNtk::set_register, "index"_a, "reg"_a)
        .def("register_at", &SequentialNtk::register_at, "index"_a)
        .def("pi_index", &SequentialNtk::pi_index, "n"_a)
        .def("ci_index", &SequentialNtk::ci_index, "n"_a)
        .def("co_index", &SequentialNtk::co_index, "s"_a)
        .def("ro_index", &SequentialNtk::ro_index, "n"_a)
        .def("ri_index", &SequentialNtk::ri_index, "s"_a)
        .def("ro_to_ri", &SequentialNtk::ro_to_ri, "s"_a)
        .def("ri_to_ro", &SequentialNtk::ri_to_ro, "s"_a)
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

void bind_logic_networks(pybind11::module_& m)
{
    detail::bind_network<aigverse::aig>(m, "Aig");
}

}  // namespace aigverse
