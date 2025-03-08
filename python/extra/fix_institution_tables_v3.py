#!/usr/bin/env python3
"""
Institution Tables Schema Fix (Version 3)

This script provides minimal formatting functions for institution data
that use only the most essential fields that are guaranteed to be in the schema.
"""

import os
import sys
import logging
from datetime import datetime
from uuid import uuid4

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("fix_institution_tables_v3")

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fixed_format_institution_for_db(institution):
    """
    Format institution data for database storage using only essential fields.
    """
    logger.info(f"Formatting institution data for {institution.get('name', 'unknown')}")
    
    # Use only guaranteed fields
    formatted = {
        "id": str(uuid4()),
        "name": institution.get("name", "Unknown Institution"),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Add some optional fields if they exist in the data
    if "short_name" in institution:
        formatted["short_name"] = institution["short_name"]
    if "description" in institution:
        formatted["description"] = institution["description"]
    
    return formatted

def fixed_format_institution_holding_for_db(holding):
    """
    Format institution holding data for database storage using only essential fields.
    """
    # Use only guaranteed fields
    formatted = {
        "id": str(uuid4()),
        "institution_name": holding.get("institution_name", "Unknown Institution"),
        "ticker": holding.get("ticker", ""),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Add some optional fields if in the data
    if "units" in holding:
        formatted["units"] = holding["units"]
    if "value" in holding:
        formatted["value"] = holding["value"]
    
    return formatted

def fixed_format_institution_activity_for_db(activity):
    """
    Format institution activity data for database storage using only essential fields.
    """
    # Use only guaranteed fields
    formatted = {
        "id": str(uuid4()),
        "institution_name": activity.get("institution_name", "Unknown Institution"),
        "ticker": activity.get("ticker", ""),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Add some optional fields if in the data
    if "report_date" in activity:
        formatted["report_date"] = activity["report_date"]
    if "units" in activity:
        formatted["units"] = activity["units"]
    if "units_change" in activity:
        formatted["units_change"] = activity["units_change"]
    
    return formatted

def fixed_generate_trades_from_activity(activities, fund_name):
    """
    Generate trades data from activity records using only essential fields.
    """
    trades = []
    
    for activity in activities:
        # Skip if missing required fields
        if not activity.get("ticker") or not activity.get("units_change"):
            continue
            
        units_change = activity.get("units_change", 0)
        if not units_change:
            continue  # Skip if no change in units
        
        # Determine action based on units change
        action = "BUY" if units_change > 0 else "SELL"
        units = abs(units_change)
        
        # Create minimal trade record
        trade = {
            "id": str(uuid4()),
            "institution_name": fund_name,
            "ticker": activity.get("ticker", ""),
            "action": action,
            "units": units,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Add report_date if available
        if "report_date" in activity:
            trade["report_date"] = activity["report_date"]
        
        trades.append(trade)
    
    return trades

def print_usage():
    """Print usage instructions for this script."""
    print("""
Usage: python fix_institution_tables_v3.py

This script creates minimal formatting functions for institution data
that use only the most essential fields guaranteed to be in the schema.

To use these functions:

1. Import them from this file into hedge_fund_fetcher.py
2. Replace the original formatting functions with these fixed versions
3. Run the hedge fund fetcher again
""")

def main():
    """Main function to explain usage of this script."""
    logger.info("Institution Tables Schema Fix (Version 3)")
    print_usage()
    
    logger.info("To fix the institution tables, update the formatting functions in hedge_fund_fetcher.py")
    logger.info("Example usage:")
    logger.info("  from fix_institution_tables_v3 import fixed_format_institution_for_db")
    logger.info("  # Then replace format_institution_for_db with fixed_format_institution_for_db")

if __name__ == "__main__":
    main() 