#!/usr/bin/env python3
"""
Dark Pool Data Insertion Test

This script tests the direct insertion of dark pool data into Supabase,
bypassing the full fetcher pipeline to isolate data insertion issues.
"""

import os
import sys
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("dark_pool_test.log")
    ]
)
logger = logging.getLogger("dark_pool_test")

# Add the parent directory to the path so we can import unusual_whales_api
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from python.unusual_whales_api import get_dark_pool_recent, format_dark_pool_trade_for_db

# Load environment variables
load_dotenv()

# Constants
DARK_POOL_TABLE = "dark_pool_trades"
DARK_POOL_DATA_TABLE = "dark_pool_data"

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
# Try different possible names for the service key
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_SECRET_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error(f"Supabase credentials missing - URL: {bool(SUPABASE_URL)}, KEY: {bool(SUPABASE_KEY)}")
    logger.error("Please ensure SUPABASE_URL and one of SUPABASE_SERVICE_ROLE_KEY, SUPABASE_KEY, SUPABASE_ANON_KEY, SUPABASE_SECRET_KEY, or NEXT_PUBLIC_SUPABASE_ANON_KEY are set in your .env file")
    sys.exit(1)

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Successfully initialized Supabase client")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {str(e)}")
    sys.exit(1)

def test_raw_data_retrieval():
    """Test retrieving raw data from the Unusual Whales API"""
    limit = 5  # Small limit for testing
    
    try:
        # Fetch recent dark pool trades
        logger.info(f"Fetching {limit} recent dark pool trades from API...")
        trades = get_dark_pool_recent(limit=limit)
        
        if trades:
            logger.info(f"✅ Successfully retrieved {len(trades)} dark pool trades")
            # Show first trade for debugging
            logger.info(f"Sample trade: {json.dumps(trades[0], indent=2)}")
            return trades
        else:
            logger.warning("⚠️ No dark pool trades returned from API")
            return []
    except Exception as e:
        logger.error(f"❌ Error fetching dark pool trades: {str(e)}")
        return []

def test_data_formatting(trades):
    """Test formatting dark pool trade data for DB insertion"""
    if not trades:
        logger.warning("No trades to format")
        return []
        
    try:
        # Format each trade for DB insertion
        formatted_trades = []
        for trade in trades:
            formatted = format_dark_pool_trade_for_db(trade)
            formatted_trades.append(formatted)
            
        logger.info(f"✅ Successfully formatted {len(formatted_trades)} trades")
        # Show first formatted trade
        logger.info(f"Sample formatted trade: {json.dumps(formatted_trades[0], indent=2)}")
        return formatted_trades
    except Exception as e:
        logger.error(f"❌ Error formatting trades: {str(e)}")
        return []

def test_direct_insertion(trades):
    """Test direct insertion of trades into Supabase"""
    if not trades:
        logger.warning("No trades to insert")
        return False
        
    try:
        # Try inserting each trade individually
        for i, trade in enumerate(trades):
            # Ensure trade has required fields
            if "ticker" not in trade or not trade["ticker"]:
                logger.warning(f"Trade {i} missing ticker field, skipping")
                continue
                
            logger.info(f"Inserting trade {i+1}/{len(trades)} for {trade['ticker']}...")
            
            # Create a copy of the trade data to avoid modifying the original
            insert_data = trade.copy()
            
            # Try to insert the trade
            response = supabase.table(DARK_POOL_TABLE).insert(insert_data).execute()
            
            # Check for errors
            if hasattr(response, 'error') and response.error:
                logger.error(f"❌ Error inserting trade {i+1}: {response.error}")
            else:
                logger.info(f"✅ Successfully inserted trade {i+1}")
                
        logger.info(f"Insertion test completed for {len(trades)} trades")
        return True
    except Exception as e:
        logger.error(f"❌ Error during insertion test: {str(e)}")
        return False

def test_aggregated_data_insertion():
    """Test insertion of aggregated dark pool data"""
    # Create a test record for the dark_pool_data table
    test_data = {
        "id": f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "symbol": "TEST",
        "data_date": datetime.now().strftime("%Y-%m-%d"),
        "volume": 1000000,
        "blocks_count": 50,
        "largest_block_size": 50000,
        "total_premium": 0.05,
        "price": 150.0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    try:
        logger.info(f"Inserting test data into {DARK_POOL_DATA_TABLE}...")
        response = supabase.table(DARK_POOL_DATA_TABLE).insert(test_data).execute()
        
        # Check for errors
        if hasattr(response, 'error') and response.error:
            logger.error(f"❌ Error inserting test data: {response.error}")
            return False
        else:
            logger.info(f"✅ Successfully inserted test data into {DARK_POOL_DATA_TABLE}")
            
            # Verify the insertion by querying
            verify = supabase.table(DARK_POOL_DATA_TABLE).select("*").eq("id", test_data["id"]).execute()
            
            if verify.data and len(verify.data) > 0:
                logger.info(f"✅ Successfully verified data exists in {DARK_POOL_DATA_TABLE}")
                
                # Clean up test data
                cleanup = supabase.table(DARK_POOL_DATA_TABLE).delete().eq("id", test_data["id"]).execute()
                logger.info(f"✅ Test data cleaned up from {DARK_POOL_DATA_TABLE}")
            else:
                logger.error(f"❌ Could not verify test data in {DARK_POOL_DATA_TABLE}")
                
            return True
    except Exception as e:
        logger.error(f"❌ Error testing aggregated data insertion: {str(e)}")
        return False

def check_table_exists(table_name):
    """Check if a table exists in the database"""
    try:
        # Try to select one row - if it succeeds, the table exists
        response = supabase.table(table_name).select("*").limit(1).execute()
        return True
    except Exception as e:
        if "relation" in str(e).lower() and "does not exist" in str(e).lower():
            return False
        if hasattr(e, 'code') and e.code == '42P01':
            return False
        # For other errors, assume table exists but there's a different issue
        return True

def verify_table_structure():
    """Verify the table structure of dark pool tables"""
    tables = [DARK_POOL_TABLE, DARK_POOL_DATA_TABLE]
    
    for table in tables:
        try:
            # First check if table exists
            if not check_table_exists(table):
                logger.error(f"❌ Table {table} does not exist!")
                continue
                
            # Try to get structure from a row
            response = supabase.table(table).select("*").limit(1).execute()
            
            if response.data and len(response.data) > 0:
                # Get keys from first row
                logger.info(f"✅ Table {table} exists with columns:")
                for key in response.data[0].keys():
                    logger.info(f"  - {key}")
            else:
                logger.warning(f"⚠️ Table {table} exists but is empty")
                
        except Exception as e:
            logger.error(f"❌ Error checking table structure for {table}: {str(e)}")

def check_existing_data():
    """Check if there's any existing data in the tables"""
    tables = [DARK_POOL_TABLE, DARK_POOL_DATA_TABLE]
    
    for table in tables:
        try:
            # First check if table exists
            if not check_table_exists(table):
                logger.error(f"❌ Table {table} does not exist!")
                continue
                
            response = supabase.table(table).select("*").limit(5).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"✅ Table {table} has {len(response.data)} records")
                # Show a sample record
                logger.info(f"Sample record: {json.dumps(response.data[0], indent=2)}")
            else:
                logger.warning(f"⚠️ Table {table} has no records")
        except Exception as e:
            logger.error(f"❌ Error checking existing data in {table}: {str(e)}")

def main():
    """Main function to run tests"""
    logger.info("Starting Dark Pool Data Insertion Tests")
    
    # Check existing data
    check_existing_data()
    
    # Verify table structure
    verify_table_structure()
    
    # Test raw data retrieval
    trades = test_raw_data_retrieval()
    
    if trades:
        # Test data formatting
        formatted_trades = test_data_formatting(trades)
        
        if formatted_trades:
            # Test direct insertion
            test_direct_insertion(formatted_trades)
    
    # Test aggregated data insertion
    test_aggregated_data_insertion()
    
    logger.info("Completed Dark Pool Data Insertion Tests")

if __name__ == "__main__":
    main() 