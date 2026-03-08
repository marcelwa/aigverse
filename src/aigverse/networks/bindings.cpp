#include <nanobind/nanobind.h>

namespace aigverse
{
void bind_logic_networks(nanobind::module_& m);
void bind_ntk_edge_list(nanobind::module_& m);
void bind_ntk_index_list(nanobind::module_& m);
}  // namespace aigverse

NB_MODULE(networks, m)
{
    m.doc() = R"pb(Provides logic network data structures and derived views.

This module includes network types, edge and index list utilities, and helper
objects for structural manipulation.)pb";
    aigverse::bind_logic_networks(m);
    aigverse::bind_ntk_edge_list(m);
    aigverse::bind_ntk_index_list(m);
}
