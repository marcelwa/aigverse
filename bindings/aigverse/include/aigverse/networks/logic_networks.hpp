//
// Created by marcel on 04.09.24.
//

#ifndef AIGVERSE_LOGIC_NETWORKS_HPP
#define AIGVERSE_LOGIC_NETWORKS_HPP

#include <fmt/format.h>
#include <mockturtle/networks/aig.hpp>
#include <mockturtle/networks/mig.hpp>
#include <mockturtle/networks/xag.hpp>
#include <mockturtle/traits.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/pytypes.h>
#include <pybind11/stl.h>

#include <functional>
#include <string>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void network(pybind11::module& m, const std::string& network_name)
{
    namespace py = pybind11;
    using namespace pybind11::literals;

    /**
     * Network node.
     */
    py::class_<mockturtle::node<Ntk>>(m, fmt::format("{}Node", network_name).c_str())
        .def("__hash__", [](const mockturtle::node<Ntk>& n) { return std::hash<mockturtle::node<Ntk>>{}(n); })

        ;

    /**
     * Network signal.
     */
    py::class_<mockturtle::signal<Ntk>>(m, fmt::format("{}Signal", network_name).c_str())
        .def("__hash__", [](const mockturtle::signal<Ntk>& s) { return std::hash<mockturtle::signal<Ntk>>{}(s); })

        ;

    py::implicitly_convertible<py::int_, mockturtle::node<Ntk>>();

    /**
     * Network.
     */
    py::class_<Ntk>(m, network_name.c_str())
        .def(py::init<>())

        .def("size", &Ntk::size)
        .def("num_gates", &Ntk::num_gates)
        .def("num_pis", &Ntk::num_pis)
        .def("num_pos", &Ntk::num_pos)

        .def("nodes",
             [](const Ntk& ntk)
             {
                 std::vector<mockturtle::node<Ntk>> nodes{};
                 nodes.reserve(ntk.size());
                 ntk.foreach_node([&nodes](const auto& n) { nodes.push_back(n); });
                 return nodes;
             })
        .def("gates",
             [](const Ntk& ntk)
             {
                 std::vector<mockturtle::node<Ntk>> gates{};
                 gates.reserve(ntk.num_gates());
                 ntk.foreach_gate([&gates](const auto& g) { gates.push_back(g); });
                 return gates;
             })
        .def("pis",
             [](const Ntk& ntk)
             {
                 std::vector<mockturtle::node<Ntk>> pis{};
                 pis.reserve(ntk.num_pis());
                 ntk.foreach_pi([&pis](const auto& pi) { pis.push_back(pi); });
                 return pis;
             })
        .def("pos",
             [](const Ntk& ntk)
             {
                 std::vector<mockturtle::signal<Ntk>> pos{};
                 pos.reserve(ntk.num_pos());
                 ntk.foreach_po([&pos](const auto& po) { pos.push_back(po); });
                 return pos;
             })
        .def(
            "fanins",
            [](const Ntk& ntk, const mockturtle::node<Ntk>& n)
            {
                std::vector<mockturtle::signal<Ntk>> fanins{};
                fanins.reserve(ntk.fanin_size(n));
                ntk.foreach_fanin(n, [&fanins](const auto& f) { fanins.push_back(f); });
                return fanins;
            },
            "n"_a)

        .def(
            "fanin_size", [](const Ntk& ntk, const mockturtle::node<Ntk>& n) { return ntk.fanin_size(n); }, "n"_a)
        .def(
            "fanout_size", [](const Ntk& ntk, const mockturtle::node<Ntk>& n) { return ntk.fanout_size(n); }, "n"_a)

        .def("is_constant", &Ntk::is_constant, "n"_a)
        .def("is_pi", &Ntk::is_pi, "n"_a)

        // for some reason, the is_* functions need redefinition to match with Ntk
        .def(
            "is_and", [](const Ntk& ntk, const mockturtle::node<Ntk>& n) { return ntk.is_and(n); }, "n"_a)
        .def(
            "is_or", [](const Ntk& ntk, const mockturtle::node<Ntk>& n) { return ntk.is_or(n); }, "n"_a)
        .def(
            "is_xor", [](const Ntk& ntk, const mockturtle::node<Ntk>& n) { return ntk.is_xor(n); }, "n"_a)
        .def(
            "is_maj", [](const Ntk& ntk, const mockturtle::node<Ntk>& n) { return ntk.is_maj(n); }, "n"_a)
        .def(
            "po_index", [](const Ntk& ntk, const mockturtle::signal<Ntk>& s) { return ntk.po_index(s); }, "s"_a)
        .def("po_at", [](const Ntk& ntk, const uint32_t index) { return ntk.po_at(index); }, "index"_a);

    //    /**
    //     * Network parsing function.
    //     */
    //    m.def(
    //        fmt::format("read_{}", network_name).c_str(),
    //        [](const std::string& filename) -> Ntk
    //        {
    //            auto reader = fiction::network_reader<std::shared_ptr<Ntk>>(filename, std::cout);
    //
    //            if (const auto ntks = reader.get_networks(); !ntks.empty())
    //            {
    //                auto ntk = *ntks.front();
    //                ntk.substitute_po_signals();
    //                return ntk;
    //            }
    //
    //            throw std::runtime_error("Could not parse specification file");
    //        },
    //        "filename"_a);
}

}  // namespace detail

inline void logic_networks(pybind11::module& m)
{
    /**
     * Logic networks.
     */
    detail::network<mockturtle::aig_network>(m, "Aig");
    //        detail::network<mockturtle::mig_network>(m, "Mig");
    //        detail::network<mockturtle::xag_network>(m, "Xag");
}

}  // namespace aigverse

#endif  // AIGVERSE_LOGIC_NETWORKS_HPP
