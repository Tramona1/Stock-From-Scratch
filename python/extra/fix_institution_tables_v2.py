#!/usr/bin/env python3
"""
Institution Tables Schema Fix (Version 2)

This script updates the institution-related formatting functions
to match the actual database schema, removing fields that don't exist
and making sure column names match exactly what's in the database.
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
logger = logging.getLogger("fix_institution_tables_v2")

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fixed_format_institution_for_db(institution):
    """
    Format institution data for database storage,
    ensuring only columns that exist in the schema are included.
    """
    logger.info(f"Formatting institution data for {institution.get('name', 'unknown')}")
    
    # Create a fixed version with only the fields that exist in the database
    formatted = {
        "id": str(uuid4()),
        "name": institution.get("name"),
        "short_name": institution.get("short_name"),
        "cik": institution.get("cik"),
        # Remove date, filing_date as they don't exist
        "is_hedge_fund": institution.get("is_hedge_fund", False),
        "description": institution.get("description"),
        "website": institution.get("website"),
        "logo_url": institution.get("logo_url"),
        "founder_img_url": institution.get("founder_img_url"),
        "people": institution.get("people", {}),
        "tags": institution.get("tags", []),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    return formatted

def fixed_format_institution_holding_for_db(holding):
    """
    Format institution holding data for database storage,
    ensuring only columns that exist in the schema are included.
    """
    # Create a fixed version with only the fields that exist in the database
    formatted = {
        "id": str(uuid4()),
        "institution_name": holding.get("institution_name"),
        "ticker": holding.get("ticker"),
        # Remove date field as it doesn't exist
        "full_name": holding.get("full_name"),
        "security_type": holding.get("security_type"),
        "put_call": holding.get("put_call"),
        "units": holding.get("units"),
        "units_change": holding.get("units_change"),
        "value": holding.get("value"),
        "sector": holding.get("sector"),
        "shares_outstanding": holding.get("shares_outstanding"),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    return formatted

def fixed_format_institution_activity_for_db(activity):
    """
    Format institution activity data for database storage,
    ensuring only columns that exist in the schema are included.
    """
    # Create a fixed version with only the fields that exist in the database
    formatted = {
        "id": str(uuid4()),
        "institution_name": activity.get("institution_name"),
        "ticker": activity.get("ticker"),
        # Remove filing_date as it doesn't exist
        "report_date": activity.get("report_date"),
        "security_type": activity.get("security_type"),
        "put_call": activity.get("put_call"),
        "units": activity.get("units"),
        "units_change": activity.get("units_change"),
        "shares_outstanding": activity.get("shares_outstanding"),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    return formatted

def fixed_generate_trades_from_activity(activities, fund_name):
    """
    Generate trades data from activity records,
    ensuring only columns that exist in the schema are included.
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
        
        # Create trade record with only fields that exist in the schema
        trade = {
            "id": str(uuid4()),
            "institution_name": fund_name,
            "ticker": activity.get("ticker"),
            "report_date": activity.get("report_date"),
            # Remove filing_date as it doesn't exist
            "action": action,
            "units": units,
            "price": 0,  # Default value
            "value": 0,  # Default value
            "security_type": activity.get("security_type"),
            "put_call": activity.get("put_call"),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        trades.append(trade)
    
    return trades

def print_usage():
    """Print usage instructions for this script."""
    print("""
Usage: python fix_institution_tables_v2.py

This script creates fixed formatting functions for institution data
that match the actual database schema. To use these functions:

1. Import them from this file into hedge_fund_fetcher.py
2. Replace the original formatting functions with these fixed versions
3. Run the hedge fund fetcher again
""")

def main():
    """Main function to explain usage of this script."""
    logger.info("Institution Tables Schema Fix (Version 2)")
    print_usage()
    
    logger.info("To fix the institution tables, update the formatting functions in hedge_fund_fetcher.py")
    logger.info("Example usage:")
    logger.info("  from fix_institution_tables_v2 import fixed_format_institution_for_db")
    logger.info("  # Then replace format_institution_for_db with fixed_format_institution_for_db")

if __name__ == "__main__":
    main() 