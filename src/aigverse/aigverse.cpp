//
// Created by marcel on 04.09.24.
//

#include <pybind11/pybind11.h>

#define PYBIND11_DETAILED_ERROR_MESSAGES

namespace aigverse
{
// Networks
void bind_logic_networks(pybind11::module_& m);

// Truth tables
void bind_truth_table(pybind11::module_& m);
void bind_truth_table_operations(pybind11::module_& m);

// Algorithms
void bind_equivalence_checking(pybind11::module_& m);
void bind_refactoring(pybind11::module_& m);
void bind_resubstitution(pybind11::module_& m);
void bind_rewriting(pybind11::module_& m);
void bind_balancing(pybind11::module_& m);
void bind_simulation(pybind11::module_& m);

// I/O
void bind_read_aiger(pybind11::module_& m);
void bind_write_aiger(pybind11::module_& m);
void bind_read_pla(pybind11::module_& m);
void bind_read_verilog(pybind11::module_& m);
void bind_write_verilog(pybind11::module_& m);
void bind_write_dot(pybind11::module_& m);

// Adapters
void bind_to_edge_list(pybind11::module_& m);
void bind_to_index_list(pybind11::module_& m);
}  // namespace aigverse

PYBIND11_MODULE(pyaigverse, m, pybind11::mod_gil_not_used())
{
    // docstring
    m.doc() = "A Python library for working with logic networks, synthesis, and optimization.";

    /**
     * Networks
     */
    aigverse::bind_logic_networks(m);

    /**
     * Truth tables.
     */
    aigverse::bind_truth_table(m);
    aigverse::bind_truth_table_operations(m);

    /**
     * Algorithms
     */
    aigverse::bind_equivalence_checking(m);
    aigverse::bind_refactoring(m);
    aigverse::bind_resubstitution(m);
    aigverse::bind_rewriting(m);
    aigverse::bind_balancing(m);
    aigverse::bind_simulation(m);

    /**
     * I/O
     */
    aigverse::bind_read_aiger(m);
    aigverse::bind_write_aiger(m);
    aigverse::bind_read_pla(m);
    aigverse::bind_read_verilog(m);
    aigverse::bind_write_verilog(m);
    aigverse::bind_write_dot(m);

    /**
     * Adapters
     */
    aigverse::bind_to_edge_list(m);
    aigverse::bind_to_index_list(m);
}
