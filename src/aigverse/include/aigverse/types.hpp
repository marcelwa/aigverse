//
// Created by marcel on 06.11.24.
//

#ifndef AIGVERSE_TYPES_HPP
#define AIGVERSE_TYPES_HPP

#include <kitty/dynamic_truth_table.hpp>
#include <mockturtle/networks/aig.hpp>
#include <mockturtle/networks/sequential.hpp>
#include <mockturtle/utils/index_list.hpp>
#include <mockturtle/views/depth_view.hpp>
#include <mockturtle/views/fanout_view.hpp>

namespace aigverse
{

/**
 * Alias for the AIG.
 */
using aig = mockturtle::aig_network;
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
 * Alias for the AIG index list.
 */
using aig_index_list = mockturtle::xag_index_list<true>;
/**
 * Alias for the truth table.
 */
using truth_table = kitty::dynamic_truth_table;

}  // namespace aigverse

#endif  // AIGVERSE_TYPES_HPP
