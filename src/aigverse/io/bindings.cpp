#include <pybind11/pybind11.h>

namespace aigverse
{
void bind_read_aiger(pybind11::module_& m);
void bind_write_aiger(pybind11::module_& m);
void bind_read_pla(pybind11::module_& m);
void bind_read_verilog(pybind11::module_& m);
void bind_write_verilog(pybind11::module_& m);
void bind_write_dot(pybind11::module_& m);
}  // namespace aigverse

PYBIND11_MODULE(io, m)
{
    m.doc() = "Input/Output functionality";
    aigverse::bind_read_aiger(m);
    aigverse::bind_write_aiger(m);
    aigverse::bind_read_pla(m);
    aigverse::bind_read_verilog(m);
    aigverse::bind_write_verilog(m);
    aigverse::bind_write_dot(m);
}
