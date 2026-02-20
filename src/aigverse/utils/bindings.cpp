#include <pybind11/pybind11.h>

namespace aigverse
{
void bind_truth_table(pybind11::module_& m);
void bind_truth_table_operations(pybind11::module_& m);
void bind_to_edge_list(pybind11::module_& m);
void bind_to_index_list(pybind11::module_& m);
}  // namespace aigverse

PYBIND11_MODULE(utils, m, pybind11::mod_gil_not_used())  // NOLINT(misc-include-cleaner)
{
    m.doc() = "Utility data structures and functions";
    aigverse::bind_truth_table(m);
    aigverse::bind_truth_table_operations(m);
    aigverse::bind_to_edge_list(m);
    aigverse::bind_to_index_list(m);
}
