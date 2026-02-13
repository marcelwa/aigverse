//
// Created by marcel on 04.09.25.
//

#include "edge_list.hpp"

#include "aigverse/types.hpp"

#include <fmt/format.h>
#include <fmt/ranges.h>  // NOLINT(misc-include-cleaner)
#include <mockturtle/traits.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/pytypes.h>
#include <pybind11/stl.h>  // NOLINT(misc-include-cleaner)

#include <cstddef>
#include <cstdint>
#include <string>
#include <tuple>
#include <vector>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void ntk_edge_list(pybind11::module_& m, const std::string& network_name)  // NOLINT(misc-use-internal-linkage)
{
    namespace py = pybind11;

    /**
     * Edge.
     */
    using Edge = edge<Ntk>;  // NOLINT(readability-identifier-naming)
    py::class_<Edge>(m, fmt::format("{}Edge", network_name).c_str())
        .def(py::init<>())
        .def(py::init<const mockturtle::node<Ntk>&, const mockturtle::node<Ntk>&, const int64_t>(), py::arg("source"),
             py::arg("target"), py::arg("weight") = 0)
        .def_readwrite("source", &Edge::source)
        .def_readwrite("target", &Edge::target)
        .def_readwrite("weight", &Edge::weight)
        .def("__repr__", [](const Edge& e) { return fmt::format("{}", e); })
        .def("__eq__",
             [](const Edge& self, const py::object& other) -> bool
             {
                 if (!py::isinstance<Edge>(other))
                 {
                     return false;
                 }

                 return self == other.cast<const Edge>();
             })
        .def("__ne__",
             [](const Edge& self, const py::object& other) -> bool
             {
                 if (!py::isinstance<Edge>(other))
                 {
                     return false;
                 }

                 return self != other.cast<const Edge>();
             })

        ;

    py::implicitly_convertible<py::tuple, Edge>();  // NOLINT(misc-include-cleaner)

    /**
     * Edge list.
     */
    using EdgeList = edge_list<Ntk>;  // NOLINT(readability-identifier-naming)
    py::class_<EdgeList>(m, fmt::format("{}EdgeList", network_name).c_str())
        .def(py::init<>())
        .def(py::init<const Ntk&>(), py::arg("ntk"))
        .def(py::init<const Ntk&, const std::vector<Edge>&>(), py::arg("ntk"), py::arg("edges"))
        .def_readwrite("ntk", &EdgeList::ntk)
        .def_readwrite("edges", &EdgeList::edges)
        .def(
            "append", [](EdgeList& el, const Edge& e) { el.edges.push_back(e); }, py::arg("edge"))
        .def("clear", [](EdgeList& el) { el.edges.clear(); })
        .def(
            "__iter__", [](const EdgeList& el) { return py::make_iterator(el.edges); }, py::keep_alive<0, 1>())
        .def("__len__", [](const EdgeList& el) { return el.edges.size(); })
        .def("__getitem__",
             [](const EdgeList& el, const std::size_t index)
             {
                 if (index >= el.edges.size())
                 {
                     throw py::index_error();
                 }

                 return el.edges[index];
             })
        .def("__setitem__",
             [](EdgeList& el, const std::size_t index, const Edge& e)
             {
                 if (index >= el.edges.size())
                 {
                     throw py::index_error();
                 }

                 el.edges[index] = e;
             })
        .def("__repr__", [](const EdgeList& el) { return fmt::format("EdgeList({})", el); })

        ;

    py::implicitly_convertible<py::list, EdgeList>();  // NOLINT(misc-include-cleaner)

    m.def("to_edge_list", &to_edge_list<mockturtle::sequential<Ntk>>, py::arg("ntk"), py::arg("regular_weight") = 0,
          py::arg("inverted_weight") = 1);
    m.def("to_edge_list", &to_edge_list<Ntk>, py::arg("ntk"), py::arg("regular_weight") = 0,
          py::arg("inverted_weight") = 1);
}

// Explicit instantiation for AIG
template void ntk_edge_list<aigverse::aig>(pybind11::module_& m, const std::string& network_name);

}  // namespace detail

void bind_to_edge_list(pybind11::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::ntk_edge_list<aigverse::aig>(m, "Aig");
}

}  // namespace aigverse
