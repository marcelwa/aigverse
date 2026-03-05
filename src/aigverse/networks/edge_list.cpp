//
// Created by marcel on 04.09.25.
//

#include "edge_list.hpp"

#include "aigverse/types.hpp"

#include <fmt/format.h>
#include <fmt/ranges.h>  // NOLINT(misc-include-cleaner)
#include <mockturtle/networks/sequential.hpp>
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
    nb::class_<Edge>(m, fmt::format("{}Edge", network_name).c_str())
        .def(nb::init<>())
        .def(nb::init<const mockturtle::node<Ntk>&, const mockturtle::node<Ntk>&, const int64_t>(), nb::arg("source"),
             nb::arg("target"), nb::arg("weight") = 0)
        .def_rw("source", &Edge::source)
        .def_rw("target", &Edge::target)
        .def_rw("weight", &Edge::weight)
        .def("__repr__", [](const Edge& e) { return fmt::format("{}", e); })
        .def("__eq__",
             [](const Edge& self, const nb::object& other) -> bool
             {
                 if (!nb::isinstance<Edge>(other))
                 {
                     return false;
                 }

                 return self == nb::cast<const Edge>(other);
             })
        .def("__ne__",
             [](const Edge& self, const nb::object& other) -> bool
             {
                 if (!nb::isinstance<Edge>(other))
                 {
                     return true;
                 }

                 return self != nb::cast<const Edge>(other);
             })

        ;

    nb::implicitly_convertible<nb::tuple, Edge>();  // NOLINT(misc-include-cleaner)

    /**
     * Edge list.
     */
    using EdgeList = edge_list<Ntk>;  // NOLINT(readability-identifier-naming)
    nb::class_<EdgeList>(m, fmt::format("{}EdgeList", network_name).c_str())
        .def(nb::init<>())
        .def(nb::init<const Ntk&>(), nb::arg("ntk"))
        .def(nb::init<const Ntk&, const std::vector<Edge>&>(), nb::arg("ntk"), nb::arg("edges"))
        .def_rw("ntk", &EdgeList::ntk)
        .def_rw("edges", &EdgeList::edges)
        .def(
            "append", [](EdgeList& el, const Edge& e) { el.edges.push_back(e); }, nb::arg("edge"))
        .def("clear", [](EdgeList& el) { el.edges.clear(); })
        .def(
            "__iter__", [](const EdgeList& el)
            { return nb::make_iterator(nb::type<EdgeList>(), "edge_iterator", el.edges.begin(), el.edges.end()); },
            nb::keep_alive<0, 1>())
        .def("__len__", [](const EdgeList& el) { return el.edges.size(); })
        .def("__getitem__",
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
             })
        .def("__setitem__",
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
             })
        .def("__repr__", [](const EdgeList& el) { return fmt::format("EdgeList({})", el); })

        ;

    nb::implicitly_convertible<nb::list, EdgeList>();  // NOLINT(misc-include-cleaner)

    m.def("to_edge_list", &to_edge_list<mockturtle::sequential<Ntk>>, nb::arg("ntk"), nb::arg("regular_weight") = 0,
          nb::arg("inverted_weight") = 1);
    m.def("to_edge_list", &to_edge_list<Ntk>, nb::arg("ntk"), nb::arg("regular_weight") = 0,
          nb::arg("inverted_weight") = 1);
}

// Explicit instantiation for AIG
template void ntk_edge_list<aigverse::aig>(nanobind::module_& m, const std::string& network_name);

}  // namespace detail

void bind_ntk_edge_list(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::ntk_edge_list<aigverse::aig>(m, "Aig");
}

}  // namespace aigverse
