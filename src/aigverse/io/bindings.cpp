#include <nanobind/nanobind.h>

namespace aigverse
{
void bind_read_aiger(nanobind::module_& m);
void bind_write_aiger(nanobind::module_& m);
void bind_read_pla(nanobind::module_& m);
void bind_read_verilog(nanobind::module_& m);
void bind_write_verilog(nanobind::module_& m);
void bind_write_dot(nanobind::module_& m);
}  // namespace aigverse

NB_MODULE(io, m)
{
    m.doc() = R"pb(Provides file import and export functions for logic networks.

The module contains readers and writers for common file formats in the domain.)pb";
    nanobind::module_::import_("aigverse.networks");  // ensure network types are registered
    aigverse::bind_read_aiger(m);
    aigverse::bind_write_aiger(m);
    aigverse::bind_read_pla(m);
    aigverse::bind_read_verilog(m);
    aigverse::bind_write_verilog(m);
    aigverse::bind_write_dot(m);
}
