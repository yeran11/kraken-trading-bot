#!/usr/bin/env python3
"""
Fix Dust Position - Clean up worthless positions and add minimum checks
"""
import json
import os
from loguru import logger

def fix_dust_positions():
    """Remove dust positions (positions worth less than $1)"""

    logger.info("=== DUST POSITION CLEANUP ===")

    # Check if positions file exists
    if not os.path.exists('positions.json'):
        logger.warning("No positions.json file found - positions only in memory")
        logger.info("Creating empty positions.json file")
        with open('positions.json', 'w') as f:
            json.dump({}, f, indent=2)
        return

    # Load positions
    with open('positions.json', 'r') as f:
        positions = json.load(f)

    if not positions:
        logger.info("No positions in file")
        return

    logger.info(f"Found {len(positions)} position(s)")

    # Check each position
    dust_positions = []
    valid_positions = {}

    for symbol, pos in positions.items():
        entry_price = pos.get('entry_price', 0)
        quantity = pos.get('quantity', 0)
        position_value = entry_price * quantity

        logger.info(f"{symbol}: Entry=${entry_price:.6f}, Qty={quantity:.4f}, Value=${position_value:.6f}")

        # Flag dust positions (worth less than $1)
        if position_value < 1.0:
            logger.warning(f"🗑️  DUST: {symbol} worth only ${position_value:.6f} - REMOVING")
            dust_positions.append(symbol)
        else:
            valid_positions[symbol] = pos
            logger.success(f"✓ VALID: {symbol} worth ${position_value:.2f}")

    # Save cleaned positions
    if dust_positions:
        logger.info(f"Removing {len(dust_positions)} dust position(s): {dust_positions}")

        with open('positions.json', 'w') as f:
            json.dump(valid_positions, f, indent=2)

        # Backup removed positions
        with open('dust_positions_backup.json', 'w') as f:
            json.dump({sym: positions[sym] for sym in dust_positions}, f, indent=2)

        logger.success(f"✅ Cleaned! Removed {len(dust_positions)} dust position(s)")
        logger.info(f"Backup saved to dust_positions_backup.json")
    else:
        logger.success("✅ No dust positions found - all positions are valid!")

    logger.info(f"Final position count: {len(valid_positions)}")

if __name__ == "__main__":
    fix_dust_positions()
