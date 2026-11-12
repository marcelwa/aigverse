//
// Created by marcel on 06.11.24.
//

#pragma once

#include <kitty/dynamic_truth_table.hpp>
#include <mockturtle/networks/aig.hpp>
#include <mockturtle/networks/klut.hpp>
#include <mockturtle/networks/sequential.hpp>
#include <mockturtle/utils/index_list/index_list.hpp>
#include <mockturtle/views/depth_view.hpp>
#include <mockturtle/views/fanout_view.hpp>
#include <mockturtle/views/names_view.hpp>

namespace aigverse
{

/**
 * Alias for the AIG.
 */
using aig = mockturtle::aig_network;
/**
 * Alias for the named AIG.
 */
using named_aig = mockturtle::names_view<aig>;
/**
 * Alias for the depth AIG.
 */
using depth_aig = mockturtle::depth_view<aig>;
/**
 * Alias for the fanout AIG.
 */
using fanouts_aig = mockturtle::fanout_view<aig>;
/**
 * Alias for the sequential AIG.
 */
using sequential_aig = mockturtle::sequential<aig>;
/**
 * Combinational k-LUT networks and their augmented views.
 */
using klut         = mockturtle::klut_network;
using named_klut   = mockturtle::names_view<klut>;
using depth_klut   = mockturtle::depth_view<klut>;
using fanouts_klut = mockturtle::fanout_view<klut>;
/**
 * Alias for the AIG index list.
 */
using aig_index_list = mockturtle::xag_index_list<true>;
/**
 * Alias for the truth table.
 */
using truth_table = kitty::dynamic_truth_table;

}  // namespace aigverse
