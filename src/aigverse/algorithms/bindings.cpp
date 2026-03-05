#include <nanobind/nanobind.h>

namespace aigverse
{
void bind_equivalence_checking(nanobind::module_& m);
void bind_refactoring(nanobind::module_& m);
void bind_resubstitution(nanobind::module_& m);
void bind_rewriting(nanobind::module_& m);
void bind_balancing(nanobind::module_& m);
void bind_simulation(nanobind::module_& m);
}  // namespace aigverse

NB_MODULE(algorithms, m)
{
    m.doc() = "Synthesis and optimization algorithms";
    nanobind::module_::import_("aigverse.networks");  // ensure network types are registered
    nanobind::module_::import_("aigverse.utils");     // ensure truth-table types are registered
    aigverse::bind_equivalence_checking(m);
    aigverse::bind_refactoring(m);
    aigverse::bind_resubstitution(m);
    aigverse::bind_rewriting(m);
    aigverse::bind_balancing(m);
    aigverse::bind_simulation(m);
}
