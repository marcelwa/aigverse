#include <pybind11/pybind11.h>

namespace aigverse
{
void bind_logic_networks(pybind11::module_& m);
}

PYBIND11_MODULE(networks, m, pybind11::mod_gil_not_used())  // NOLINT(misc-include-cleaner)
{
    m.doc() = "Logic network data structures";
    aigverse::bind_logic_networks(m);
}
