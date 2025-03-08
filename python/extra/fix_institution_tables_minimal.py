#!/usr/bin/env python3
"""
Institution Tables Fixer (Minimal)

This script provides the most minimal possible formatting functions
that will work with the actual database schema.

Based on error messages, we know the following required fields:
- institutions: id, name, created_at, updated_at
- institution_holdings: id, institution_name, created_at, updated_at
- institution_activity: id, institution_name, created_at, updated_at
- hedge_fund_trades: id, institution_name, created_at, updated_at
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
logger = logging.getLogger("fix_institution_tables_minimal")

def fixed_format_institution_for_db(institution):
    """Format institution data for database storage with only required fields."""
    logger.info(f"Formatting institution with minimal fields: {institution.get('name', 'Unknown')}")
    
    now = datetime.utcnow().isoformat()
    institution_id = str(uuid.uuid4())
    
    # Create a record with only guaranteed required fields
    formatted_institution = {
        "id": institution_id,
        "name": institution.get("name", "Unknown Institution"),
        "created_at": now,
        "updated_at": now
    }
    
    return formatted_institution

def fixed_format_institution_holding_for_db(holding):
    """Format institution holding data for database storage with only required fields."""
    now = datetime.utcnow().isoformat()
    holding_id = str(uuid.uuid4())
    
    # Create a record with only guaranteed required fields
    formatted_holding = {
        "id": holding_id,
        "institution_name": holding.get("institution_name", "Unknown Institution"),
        "created_at": now,
        "updated_at": now
    }
    
    # Add ticker only if it exists (appears to be present in schema)
    if "ticker" in holding and holding["ticker"]:
        formatted_holding["ticker"] = holding["ticker"]
    
    return formatted_holding

def fixed_format_institution_activity_for_db(activity):
    """Format institution activity data for database storage with only required fields."""
    now = datetime.utcnow().isoformat()
    activity_id = str(uuid.uuid4())
    
    # Create a record with only guaranteed required fields
    formatted_activity = {
        "id": activity_id,
        "institution_name": activity.get("institution_name", "Unknown Institution"),
        "created_at": now,
        "updated_at": now
    }
    
    # Add ticker only if it exists (appears to be present in schema)
    if "ticker" in activity and activity["ticker"]:
        formatted_activity["ticker"] = activity["ticker"]
    
    # Add report_date only if it exists (appears to be present in schema)
    if "report_date" in activity and activity["report_date"]:
        formatted_activity["report_date"] = activity["report_date"]
    
    return formatted_activity

def fixed_generate_trades_from_activity(activities, fund_name):
    """
    Generate trades from activity data with only required fields.
    
    Args:
        activities: List of activity records
        fund_name: Name of the institution/fund
    
    Returns:
        List of trade records
    """
    trades = []
    now = datetime.utcnow().isoformat()
    
    for activity in activities:
        # Generate trade record with only essential fields
        trade = {
            "id": str(uuid.uuid4()),
            "institution_name": fund_name,
            "created_at": now,
            "updated_at": now,
            "action": "BUY"  # Default to BUY as action is required
        }
        
        # Add ticker only if it exists in activity
        if "ticker" in activity and activity["ticker"]:
            trade["ticker"] = activity["ticker"]
        
        # Override default action if units_change exists
        if "units_change" in activity and activity["units_change"] is not None:
            units_change = activity["units_change"]
            if isinstance(units_change, (int, float)):
                trade["action"] = "BUY" if units_change > 0 else "SELL"
        
        # Add report_date if it exists in activity
        if "report_date" in activity and activity["report_date"]:
            trade["report_date"] = activity["report_date"]
        
        trades.append(trade)
    
    return trades

def print_usage():
    """Print usage instructions for this script."""
    print("""
Usage: python fix_institution_tables_minimal.py

This script provides the most minimal possible formatting functions
that will work with the actual database schema.

To use these functions, import them into hedge_fund_fetcher.py:

from fix_institution_tables_minimal import (
    fixed_format_institution_for_db,
    fixed_format_institution_holding_for_db,
    fixed_format_institution_activity_for_db,
    fixed_generate_trades_from_activity
)

These functions only include the guaranteed required fields present in the database schema.
""")

def main():
    """Main function"""
    print_usage()
    
    # Example usage
    logger.info("Example usage of fix_institution_tables_minimal.py:")
    
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