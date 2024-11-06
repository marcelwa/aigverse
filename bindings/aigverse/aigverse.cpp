//
// Created by marcel on 04.09.24.
//

#include "aigverse/adapters/edge_list.hpp"
#include "aigverse/algorithms/equivalence_checking.hpp"
#include "aigverse/algorithms/refactoring.hpp"
#include "aigverse/algorithms/resubstitution.hpp"
#include "aigverse/algorithms/rewriting.hpp"
#include "aigverse/algorithms/simulation.hpp"
#include "aigverse/io/read_aiger.hpp"
#include "aigverse/io/write_aiger.hpp"
#include "aigverse/networks/logic_networks.hpp"
#include "aigverse/truth_tables/truth_table.hpp"

#include <pybind11/pybind11.h>

#define PYBIND11_DETAILED_ERROR_MESSAGES

PYBIND11_MODULE(aigverse, m)
{
    // docstring
    m.doc() = "A Python library for working with logic networks, synthesis, and optimization.";

    /**
     * Networks
     */
    aigverse::logic_networks(m);

    /**
     * Truth tables.
     */
    aigverse::truth_tables(m);

    /**
     * Algorithms
     */
    aigverse::equivalence_checking(m);
    aigverse::refactoring(m);
    aigverse::resubstitution(m);
    aigverse::rewriting(m);
    aigverse::simulation(m);

    /**
     * I/O
     */
    aigverse::read_aiger(m);
    aigverse::write_aiger(m);

    /**
     * Adapters
     */
    aigverse::to_edge_list(m);
}
