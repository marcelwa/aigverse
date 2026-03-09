#include <nanobind/nanobind.h>

namespace aigverse
{
void bind_random_generators(nanobind::module_& m);
void bind_arithmetic_generators(nanobind::module_& m);
void bind_control_generators(nanobind::module_& m);
}  // namespace aigverse

NB_MODULE(generators, m)
{
    m.doc() = R"pb(Provides generators for random and structured benchmark construction.)pb";
    nanobind::module_::import_("aigverse.networks");
    aigverse::bind_random_generators(m);
    aigverse::bind_arithmetic_generators(m);
    aigverse::bind_control_generators(m);
}
