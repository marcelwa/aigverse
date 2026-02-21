#include <pybind11/pybind11.h>

namespace aigverse
{
void bind_equivalence_checking(pybind11::module_& m);
void bind_refactoring(pybind11::module_& m);
void bind_resubstitution(pybind11::module_& m);
void bind_rewriting(pybind11::module_& m);
void bind_balancing(pybind11::module_& m);
void bind_simulation(pybind11::module_& m);
}  // namespace aigverse

PYBIND11_MODULE(algorithms, m)  // NOLINT(misc-include-cleaner)
{
    m.doc() = "Synthesis and optimization algorithms";
    pybind11::module_::import("aigverse.networks");  // ensure network types are registered
    pybind11::module_::import("aigverse.utils");     // ensure truth-table types are registered
    aigverse::bind_equivalence_checking(m);
    aigverse::bind_refactoring(m);
    aigverse::bind_resubstitution(m);
    aigverse::bind_rewriting(m);
    aigverse::bind_balancing(m);
    aigverse::bind_simulation(m);
}
