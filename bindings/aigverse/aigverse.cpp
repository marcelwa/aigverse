//
// Created by marcel on 04.09.24.
//

#include "aigverse/networks/logic_networks.hpp"

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
}
