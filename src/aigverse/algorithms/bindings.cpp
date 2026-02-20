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

PYBIND11_MODULE(algorithms, m)
{
    m.doc() = "Synthesis and optimization algorithms";
    aigverse::bind_equivalence_checking(m);
    aigverse::bind_refactoring(m);
    aigverse::bind_resubstitution(m);
    aigverse::bind_rewriting(m);
    aigverse::bind_balancing(m);
    aigverse::bind_simulation(m);
}
