#!/usr/bin/env python3
"""
Institution Fix Verification Script

This script checks if the institution schema fixes are working by:
1. Formatting a sample institution using our fixed formatters
2. Inserting the formatted data into the database
3. Querying the database to verify the data was inserted correctly
"""

import os
import sys
import logging
import json
from datetime import datetime
import uuid
from typing import Dict, List, Any
from dotenv import load_dotenv
from supabase import create_client, Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("verify_institution_fix")

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import our fixed formatters
try:
    from fix_institution_tables_v4 import (
        fixed_format_institution_for_db,
        fixed_format_institution_holding_for_db,
        fixed_format_institution_activity_for_db,
        fixed_generate_trades_from_activity
    )
    logger.info("Successfully imported fixed formatters from v4")
except ImportError:
    logger.error("Failed to import fixed formatters, please make sure fix_institution_tables_v4.py exists")
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

def create_sample_institution() -> Dict[str, Any]:
    """Create a sample institution for testing."""
    return {
        "name": "TEST INSTITUTION",
        "short_name": "Test Inst",
        "description": "This is a test institution created for verification purposes"
    }

def create_sample_holding(institution_name: str) -> Dict[str, Any]:
    """Create a sample holding for testing."""
    return {
        "institution_name": institution_name,
        "ticker": "AAPL",
        "units": 1000,
        "date": "2025-03-08"
    }

def create_sample_activity(institution_name: str) -> Dict[str, Any]:
    """Create a sample activity for testing."""
    return {
        "institution_name": institution_name,
        "ticker": "AAPL",
        "units": 1000,
        "units_change": 500,
        "report_date": "2025-03-08"
    }

def verify_institution_insertion(supabase: Client, institution_name: str) -> bool:
    """Verify that the institution was inserted correctly."""
    try:
        result = supabase.table("institutions").select("*").eq("name", institution_name).execute()
        data = result.data
        
        if data and len(data) > 0:
            logger.info(f"Institution {institution_name} was successfully inserted")
            logger.info(f"Institution data: {json.dumps(data[0], indent=2)}")
            return True
        else:
            logger.warning(f"Institution {institution_name} was not found in the database")
            return False
    except Exception as e:
        logger.error(f"Error verifying institution insertion: {str(e)}")
        return False

def verify_holding_insertion(supabase: Client, institution_name: str, ticker: str) -> bool:
    """Verify that the holding was inserted correctly."""
    try:
        result = supabase.table("institution_holdings").select("*").eq("institution_name", institution_name).eq("ticker", ticker).execute()
        data = result.data
        
        if data and len(data) > 0:
            logger.info(f"Holding for {institution_name} and ticker {ticker} was successfully inserted")
            logger.info(f"Holding data: {json.dumps(data[0], indent=2)}")
            return True
        else:
            logger.warning(f"Holding for {institution_name} and ticker {ticker} was not found in the database")
            return False
    except Exception as e:
        logger.error(f"Error verifying holding insertion: {str(e)}")
        return False

def verify_activity_insertion(supabase: Client, institution_name: str, ticker: str) -> bool:
    """Verify that the activity was inserted correctly."""
    try:
        result = supabase.table("institution_activity").select("*").eq("institution_name", institution_name).eq("ticker", ticker).execute()
        data = result.data
        
        if data and len(data) > 0:
            logger.info(f"Activity for {institution_name} and ticker {ticker} was successfully inserted")
            logger.info(f"Activity data: {json.dumps(data[0], indent=2)}")
            return True
        else:
            logger.warning(f"Activity for {institution_name} and ticker {ticker} was not found in the database")
            return False
    except Exception as e:
        logger.error(f"Error verifying activity insertion: {str(e)}")
        return False

def verify_trade_insertion(supabase: Client, institution_name: str, ticker: str) -> bool:
    """Verify that the trade was inserted correctly."""
    try:
        result = supabase.table("hedge_fund_trades").select("*").eq("institution_name", institution_name).eq("ticker", ticker).execute()
        data = result.data
        
        if data and len(data) > 0:
            logger.info(f"Trade for {institution_name} and ticker {ticker} was successfully inserted")
            logger.info(f"Trade data: {json.dumps(data[0], indent=2)}")
            return True
        else:
            logger.warning(f"Trade for {institution_name} and ticker {ticker} was not found in the database")
            return False
    except Exception as e:
        logger.error(f"Error verifying trade insertion: {str(e)}")
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

async def main():
    """Run verification of institution schema fixes."""
    logger.info("Starting institution schema fix verification")
    
    try:
        # Initialize Supabase
        supabase = initialize_supabase()
        
        # Create sample data
        institution_name = f"TEST_INSTITUTION_{uuid.uuid4().hex[:8]}"
        sample_institution = create_sample_institution()
        sample_institution["name"] = institution_name  # Use unique name
        
        sample_holding = create_sample_holding(institution_name)
        sample_activity = create_sample_activity(institution_name)
        
        # Format data using our fixed formatters
        formatted_institution = fixed_format_institution_for_db(sample_institution)
        formatted_holding = fixed_format_institution_holding_for_db(sample_holding)
        formatted_activity = fixed_format_institution_activity_for_db(sample_activity)
        
        # Generate a trade from the activity
        activities = [formatted_activity]
        trades = fixed_generate_trades_from_activity(activities, institution_name)
        
        logger.info(f"Formatted institution: {json.dumps(formatted_institution, indent=2)}")
        logger.info(f"Formatted holding: {json.dumps(formatted_holding, indent=2)}")
        logger.info(f"Formatted activity: {json.dumps(formatted_activity, indent=2)}")
        logger.info(f"Generated trades: {json.dumps(trades, indent=2)}")
        
        # Try to insert data into database
        logger.info("Attempting to insert institution")
        institution_result = supabase.table("institutions").insert(formatted_institution).execute()
        
        logger.info("Attempting to insert holding")
        holding_result = supabase.table("institution_holdings").insert(formatted_holding).execute()
        
        logger.info("Attempting to insert activity")
        activity_result = supabase.table("institution_activity").insert(formatted_activity).execute()
        
        logger.info("Attempting to insert trade")
        if trades:
            trade_result = supabase.table("hedge_fund_trades").insert(trades[0]).execute()
        
        # Verify insertions
        institution_verified = verify_institution_insertion(supabase, institution_name)
        holding_verified = verify_holding_insertion(supabase, institution_name, sample_holding["ticker"])
        activity_verified = verify_activity_insertion(supabase, institution_name, sample_activity["ticker"])
        trade_verified = verify_trade_insertion(supabase, institution_name, sample_activity["ticker"])
        
        # Summary
        all_verified = institution_verified and holding_verified and activity_verified and trade_verified
        
        if all_verified:
            logger.info("SUCCESS: All insertions were verified. The schema fixes are working!")
        else:
            logger.warning("PARTIAL SUCCESS: Not all insertions were verified.")
            logger.warning(f"Institution: {institution_verified}")
            logger.warning(f"Holding: {holding_verified}")
            logger.warning(f"Activity: {activity_verified}")
            logger.warning(f"Trade: {trade_verified}")
        
        # Clean up test data
        clean_test_data(supabase, institution_name)
        
    except Exception as e:
        logger.error(f"Error in verification process: {str(e)}")
    
    logger.info("Institution schema fix verification completed")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 