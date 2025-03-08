#!/usr/bin/env python3
"""
Minimal Fix Validation Script

This script tests the minimal fix by creating and inserting a single record
to each institution-related table, with only the required fields.
"""

import os
import sys
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv
from supabase import create_client, Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("validate_minimal_fix")

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import our minimal formatters
try:
    from fix_institution_tables_minimal import (
        fixed_format_institution_for_db,
        fixed_format_institution_holding_for_db,
        fixed_format_institution_activity_for_db,
        fixed_generate_trades_from_activity
    )
    logger.info("Successfully imported minimal formatters")
except ImportError:
    logger.error("Failed to import minimal formatters")
    sys.exit(1)

# Load environment variables
load_dotenv()

def initialize_supabase() -> Client:
    """Initialize Supabase client."""
    supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("Missing Supabase credentials")
        
    supabase = create_client(supabase_url, supabase_key)
    logger.info("Successfully initialized Supabase client")
    return supabase

def test_institution_insertion(supabase: Client) -> str:
    """
    Test inserting a minimal institution record.
    
    Returns:
        The name of the institution if successful
    """
    try:
        # Create a test institution with a unique name
        test_name = f"TEST_MINIMAL_{uuid.uuid4().hex[:8]}"
        institution = {"name": test_name}
        
        # Format using our minimal formatter
        formatted = fixed_format_institution_for_db(institution)
        logger.info(f"Formatted institution: {json.dumps(formatted, indent=2)}")
        
        # Insert into database
        result = supabase.table("institutions").insert(formatted).execute()
        
        if hasattr(result, 'data') and result.data:
            logger.info(f"Successfully inserted institution {test_name}")
            return test_name
        else:
            logger.error(f"Failed to insert institution: {result}")
            return ""
    except Exception as e:
        logger.error(f"Error inserting institution: {str(e)}")
        return ""

def test_holding_insertion(supabase: Client, institution_name: str) -> bool:
    """
    Test inserting a minimal holding record.
    
    Args:
        supabase: Supabase client
        institution_name: Name of the institution
        
    Returns:
        True if successful
    """
    try:
        # Create a test holding
        holding = {
            "institution_name": institution_name,
            "ticker": "AAPL"
        }
        
        # Format using our minimal formatter
        formatted = fixed_format_institution_holding_for_db(holding)
        logger.info(f"Formatted holding: {json.dumps(formatted, indent=2)}")
        
        # Insert into database
        result = supabase.table("institution_holdings").insert(formatted).execute()
        
        if hasattr(result, 'data') and result.data:
            logger.info("Successfully inserted holding")
            return True
        else:
            logger.error(f"Failed to insert holding: {result}")
            return False
    except Exception as e:
        logger.error(f"Error inserting holding: {str(e)}")
        return False

def test_activity_insertion(supabase: Client, institution_name: str) -> bool:
    """
    Test inserting a minimal activity record.
    
    Args:
        supabase: Supabase client
        institution_name: Name of the institution
        
    Returns:
        True if successful
    """
    try:
        # Create a test activity
        activity = {
            "institution_name": institution_name,
            "ticker": "AAPL",
            "report_date": datetime.now().strftime("%Y-%m-%d")
        }
        
        # Format using our minimal formatter
        formatted = fixed_format_institution_activity_for_db(activity)
        logger.info(f"Formatted activity: {json.dumps(formatted, indent=2)}")
        
        # Insert into database
        result = supabase.table("institution_activity").insert(formatted).execute()
        
        if hasattr(result, 'data') and result.data:
            logger.info("Successfully inserted activity")
            return True
        else:
            logger.error(f"Failed to insert activity: {result}")
            return False
    except Exception as e:
        logger.error(f"Error inserting activity: {str(e)}")
        return False

def test_trade_insertion(supabase: Client, institution_name: str) -> bool:
    """
    Test inserting a minimal trade record.
    
    Args:
        supabase: Supabase client
        institution_name: Name of the institution
        
    Returns:
        True if successful
    """
    try:
        # Create a test activity to generate a trade from
        activity = {
            "institution_name": institution_name,
            "ticker": "AAPL",
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "units_change": 100  # Positive value for a BUY trade
        }
        
        # Format the activity
        formatted_activity = fixed_format_institution_activity_for_db(activity)
        
        # Generate a trade from the activity
        trades = fixed_generate_trades_from_activity([formatted_activity], institution_name)
        
        if not trades:
            logger.error("Failed to generate trade")
            return False
            
        trade = trades[0]
        logger.info(f"Generated trade: {json.dumps(trade, indent=2)}")
        
        # Insert into database
        result = supabase.table("hedge_fund_trades").insert(trade).execute()
        
        if hasattr(result, 'data') and result.data:
            logger.info("Successfully inserted trade")
            return True
        else:
            logger.error(f"Failed to insert trade: {result}")
            return False
    except Exception as e:
        logger.error(f"Error inserting trade: {str(e)}")
        return False

def clean_test_data(supabase: Client, institution_name: str) -> None:
    """Clean up test data from database."""
    try:
        # Delete trades
        supabase.table("hedge_fund_trades").delete().eq("institution_name", institution_name).execute()
        logger.info(f"Deleted trades for {institution_name}")
        
        # Delete activity
        supabase.table("institution_activity").delete().eq("institution_name", institution_name).execute()
        logger.info(f"Deleted activity for {institution_name}")
        
        # Delete holdings
        supabase.table("institution_holdings").delete().eq("institution_name", institution_name).execute()
        logger.info(f"Deleted holdings for {institution_name}")
        
        # Delete institution
        supabase.table("institutions").delete().eq("name", institution_name).execute()
        logger.info(f"Deleted institution {institution_name}")
    except Exception as e:
        logger.error(f"Error cleaning test data: {str(e)}")

def main():
    """Main function to run validation."""
    logger.info("Starting minimal fix validation")
    
    try:
        # Initialize Supabase
        supabase = initialize_supabase()
        
        # Test institution insertion
        institution_name = test_institution_insertion(supabase)
        
        if not institution_name:
            logger.error("Failed to insert institution, stopping validation")
            return
            
        # Test holding insertion
        holding_success = test_holding_insertion(supabase, institution_name)
        
        # Test activity insertion
        activity_success = test_activity_insertion(supabase, institution_name)
        
        # Test trade insertion
        trade_success = test_trade_insertion(supabase, institution_name)
        
        # Summary
        logger.info("\n===== VALIDATION SUMMARY =====")
        logger.info(f"Institution insertion: {'SUCCESS' if institution_name else 'FAILED'}")
        logger.info(f"Holding insertion: {'SUCCESS' if holding_success else 'FAILED'}")
        logger.info(f"Activity insertion: {'SUCCESS' if activity_success else 'FAILED'}")
        logger.info(f"Trade insertion: {'SUCCESS' if trade_success else 'FAILED'}")
        
        if institution_name and holding_success and activity_success and trade_success:
            logger.info("\nALL TESTS PASSED! The minimal fix works correctly.")
        else:
            logger.warning("\nSome tests failed. The minimal fix needs further adjustments.")
        
        # Clean up test data
        clean_test_data(supabase, institution_name)
        
    except Exception as e:
        logger.error(f"Error in validation: {str(e)}")
    
    logger.info("Minimal fix validation completed")

if __name__ == "__main__":
    main() 