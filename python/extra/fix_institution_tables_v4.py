#!/usr/bin/env python3
"""
Institution Tables Fixer v4 (Ultra Minimal)

This script provides ultra minimal formatting functions that will work with
the actual database schema, no matter what fields are available.
"""

import os
import sys
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("fix_institution_tables_v4")

def fixed_format_institution_for_db(institution):
    """Format institution data for database storage with absolutely minimal fields."""
    logger.info(f"Formatting institution data for {institution.get('name', 'Unknown')}")
    
    now = datetime.utcnow().isoformat()
    institution_id = str(uuid.uuid4())
    
    # Create a bare minimum record with only required fields
    formatted_institution = {
        "id": institution_id,
        "name": institution.get("name", "Unknown Institution"),
        "created_at": now,
        "updated_at": now
    }
    
    return formatted_institution

def fixed_format_institution_holding_for_db(holding):
    """Format institution holding data for database storage with absolutely minimal fields."""
    now = datetime.utcnow().isoformat()
    holding_id = str(uuid.uuid4())
    
    # Create a bare minimum record with only required fields
    formatted_holding = {
        "id": holding_id,
        "institution_name": holding.get("institution_name", "Unknown Institution"),
        "ticker": holding.get("ticker", ""),
        "created_at": now,
        "updated_at": now
    }
    
    # Only add units if it's a number
    units = holding.get("units")
    if units is not None and (isinstance(units, int) or isinstance(units, float)):
        formatted_holding["units"] = units
    
    return formatted_holding

def fixed_format_institution_activity_for_db(activity):
    """Format institution activity data for database storage with absolutely minimal fields."""
    now = datetime.utcnow().isoformat()
    activity_id = str(uuid.uuid4())
    
    # Create a bare minimum record with only required fields
    formatted_activity = {
        "id": activity_id,
        "institution_name": activity.get("institution_name", "Unknown Institution"),
        "ticker": activity.get("ticker", ""),
        "created_at": now,
        "updated_at": now
    }
    
    # Add units and units_change only if they're numbers
    units = activity.get("units")
    if units is not None and (isinstance(units, int) or isinstance(units, float)):
        formatted_activity["units"] = units
    
    units_change = activity.get("units_change")
    if units_change is not None and (isinstance(units_change, int) or isinstance(units_change, float)):
        formatted_activity["units_change"] = units_change
    
    # Only add report_date if it's a string
    report_date = activity.get("report_date")
    if report_date and isinstance(report_date, str):
        formatted_activity["report_date"] = report_date
    
    return formatted_activity

def fixed_generate_trades_from_activity(activities, fund_name):
    """
    Generate trades from activity data with absolutely minimal fields.
    
    Args:
        activities: List of activity records
        fund_name: Name of the institution/fund
    
    Returns:
        List of trade records
    """
    trades = []
    now = datetime.utcnow().isoformat()
    
    for activity in activities:
        units_change = activity.get("units_change", 0)
        
        # Skip if no change in units
        if units_change == 0:
            continue
        
        # Determine if it's a buy or sell based on units_change
        action = "BUY" if units_change > 0 else "SELL"
        
        # Make units_change positive for SELL actions
        units = abs(units_change)
        
        # Generate trade record with only essential fields
        trade = {
            "id": str(uuid.uuid4()),
            "institution_name": fund_name,
            "ticker": activity.get("ticker", ""),
            "action": action,
            "units": units,
            "created_at": now,
            "updated_at": now
        }
        
        # Only add report_date if it's in the activity
        report_date = activity.get("report_date")
        if report_date and isinstance(report_date, str):
            trade["report_date"] = report_date
        
        trades.append(trade)
    
    return trades

def print_usage():
    """Print usage instructions for this script."""
    print("""
Usage: python fix_institution_tables_v4.py

This script provides ultra minimal formatting functions for institution data.
To use these functions, import them into hedge_fund_fetcher.py:

from fix_institution_tables_v4 import (
    fixed_format_institution_for_db,
    fixed_format_institution_holding_for_db,
    fixed_format_institution_activity_for_db,
    fixed_generate_trades_from_activity
)

These functions only include guaranteed fields that exist in the database.
""")

def main():
    """Main function"""
    print_usage()
    
    # Example usage
    logger.info("Example usage of fix_institution_tables_v4.py:")
    
    institution = {
        "name": "Example Institution",
        "description": "This is an example institution"
    }
    
    holding = {
        "institution_name": "Example Institution",
        "ticker": "AAPL",
        "units": 1000
    }
    
    activity = {
        "institution_name": "Example Institution",
        "ticker": "AAPL",
        "units": 1000,
        "units_change": 500,
        "report_date": "2025-03-08"
    }
    
    formatted_institution = fixed_format_institution_for_db(institution)
    formatted_holding = fixed_format_institution_holding_for_db(holding)
    formatted_activity = fixed_format_institution_activity_for_db(activity)
    
    logger.info(f"Formatted institution: {json.dumps(formatted_institution, indent=2)}")
    logger.info(f"Formatted holding: {json.dumps(formatted_holding, indent=2)}")
    logger.info(f"Formatted activity: {json.dumps(formatted_activity, indent=2)}")
    
    # Generate trades
    activities = [formatted_activity]
    trades = fixed_generate_trades_from_activity(activities, "Example Institution")
    
    logger.info(f"Generated trades: {json.dumps(trades, indent=2)}")

if __name__ == "__main__":
    main() 