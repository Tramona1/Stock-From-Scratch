#!/usr/bin/env python3
"""
Supabase Data Insertion Debugging Script

This script tests each component's data fetching and insertion capabilities
to diagnose why data isn't being stored in the Supabase tables.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from supabase import create_client, Client

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("debug_insertion.log")
    ]
)
logger = logging.getLogger("debug_insertion")

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from unusual_whales_api import (
    get_insider_trades, format_insider_transaction_for_db,
    get_analyst_ratings, format_analyst_rating_for_db,
    get_political_trades, format_political_trade_for_db,
    get_dark_pool_recent, format_dark_pool_trade_for_db,
    get_fda_calendar, format_fda_calendar_event_for_db,
    get_economic_calendar, format_economic_calendar_event_for_db,
    get_ticker_option_contracts, get_option_contract_flow, format_option_flow_for_db,
    get_institutions, format_institution_for_db,
    get_institution_holdings, format_institution_holding_for_db,
    get_institution_activity, format_institution_activity_for_db,
    get_stock_info, format_stock_info_for_db
)

# Load environment variables
load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL") or os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Supabase credentials not found in environment variables")
    logger.error(f"URL: {bool(SUPABASE_URL)}, KEY: {bool(SUPABASE_KEY)}")
    logger.error("Please check your .env file for NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
    sys.exit(1)

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Successfully initialized Supabase client")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {str(e)}")
    sys.exit(1)

def test_supabase_connection():
    """Test the Supabase connection and permissions"""
    try:
        # Try a simple query to test the connection
        result = supabase.table("test").select("*").limit(1).execute()
        logger.info("Supabase connection test: SUCCESS")
        
        # Test RLS permissions on each table
        tables = [
            "insider_trades", "analyst_ratings", "dark_pool_trades", 
            "economic_calendar", "economic_events", "economic_indicators",
            "economic_news", "economic_reports", "fda_calendar",
            "fred_metadata", "fred_observations", "fred_user_series",
            "hedge_fund_trades", "institution_activity", "institution_holdings",
            "institutions", "market_indicators", "options_flow_data",
            "options_flow", "political_trades", "stock_info"
        ]
        
        for table in tables:
            try:
                # Test if we can select from the table
                select_result = supabase.table(table).select("*").limit(1).execute()
                logger.info(f"✅ SELECT from {table}: SUCCESS")
                
                # Try to insert a test record (but don't actually insert it)
                test_record = {
                    "test_field": "test_value",
                    "created_at": datetime.now().isoformat()
                }
                # Just check if the endpoint exists without actually inserting
                insert_endpoint = f"{SUPABASE_URL}/rest/v1/{table}"
                logger.info(f"✅ {table} table exists and is accessible")
                
            except Exception as e:
                logger.error(f"❌ Access test for {table} failed: {str(e)}")
                
    except Exception as e:
        logger.error(f"Supabase connection test failed: {str(e)}")

def test_api_data_retrieval():
    """Test data retrieval from the Unusual Whales API"""
    limit = 5  # Small limit for testing
    
    # Test insider trades API
    logger.info("Testing Insider Trades API...")
    try:
        insider_trades = get_insider_trades(days=3, limit=limit)
        if insider_trades:
            logger.info(f"✅ Insider Trades API returned {len(insider_trades)} records")
            logger.info(f"Sample data: {json.dumps(insider_trades[0], indent=2)}")
            
            # Test data formatting
            formatted = format_insider_transaction_for_db(insider_trades[0])
            logger.info(f"Formatted data: {json.dumps(formatted, indent=2)}")
        else:
            logger.warning("⚠️ Insider Trades API returned no data")
    except Exception as e:
        logger.error(f"❌ Insider Trades API test failed: {str(e)}")
    
    # Test analyst ratings API
    logger.info("\nTesting Analyst Ratings API...")
    try:
        ratings = get_analyst_ratings(days=3, limit=limit)
        if ratings:
            logger.info(f"✅ Analyst Ratings API returned {len(ratings)} records")
            logger.info(f"Sample data: {json.dumps(ratings[0], indent=2)}")
            
            # Test data formatting
            formatted = format_analyst_rating_for_db(ratings[0])
            logger.info(f"Formatted data: {json.dumps(formatted, indent=2)}")
        else:
            logger.warning("⚠️ Analyst Ratings API returned no data")
    except Exception as e:
        logger.error(f"❌ Analyst Ratings API test failed: {str(e)}")
    
    # Test political trades API
    logger.info("\nTesting Political Trades API...")
    try:
        political_trades = get_political_trades(days=30, limit=limit)
        if political_trades:
            logger.info(f"✅ Political Trades API returned {len(political_trades)} records")
            logger.info(f"Sample data: {json.dumps(political_trades[0], indent=2)}")
            
            # Test data formatting
            formatted = format_political_trade_for_db(political_trades[0])
            logger.info(f"Formatted data: {json.dumps(formatted, indent=2)}")
        else:
            logger.warning("⚠️ Political Trades API returned no data")
    except Exception as e:
        logger.error(f"❌ Political Trades API test failed: {str(e)}")
    
    # Test dark pool API
    logger.info("\nTesting Dark Pool API...")
    try:
        dark_pool_trades = get_dark_pool_recent(limit=limit)
        if dark_pool_trades:
            logger.info(f"✅ Dark Pool API returned {len(dark_pool_trades)} records")
            logger.info(f"Sample data: {json.dumps(dark_pool_trades[0], indent=2)}")
            
            # Test data formatting
            formatted = format_dark_pool_trade_for_db(dark_pool_trades[0])
            logger.info(f"Formatted data: {json.dumps(formatted, indent=2)}")
        else:
            logger.warning("⚠️ Dark Pool API returned no data")
    except Exception as e:
        logger.error(f"❌ Dark Pool API test failed: {str(e)}")
    
    # Test FDA calendar API
    logger.info("\nTesting FDA Calendar API...")
    try:
        fda_events = get_fda_calendar(limit=limit)
        if fda_events:
            logger.info(f"✅ FDA Calendar API returned {len(fda_events)} records")
            logger.info(f"Sample data: {json.dumps(fda_events[0], indent=2)}")
            
            # Test data formatting
            formatted = format_fda_calendar_event_for_db(fda_events[0])
            logger.info(f"Formatted data: {json.dumps(formatted, indent=2)}")
        else:
            logger.warning("⚠️ FDA Calendar API returned no data")
    except Exception as e:
        logger.error(f"❌ FDA Calendar API test failed: {str(e)}")
    
    # Test economic calendar API
    logger.info("\nTesting Economic Calendar API...")
    try:
        economic_events = get_economic_calendar()
        if economic_events:
            logger.info(f"✅ Economic Calendar API returned {len(economic_events)} records")
            logger.info(f"Sample data: {json.dumps(economic_events[0], indent=2)}")
            
            # Test data formatting
            formatted = format_economic_calendar_event_for_db(economic_events[0])
            logger.info(f"Formatted data: {json.dumps(formatted, indent=2)}")
        else:
            logger.warning("⚠️ Economic Calendar API returned no data")
    except Exception as e:
        logger.error(f"❌ Economic Calendar API test failed: {str(e)}")
    
    # Test options flow API
    logger.info("\nTesting Options Flow API...")
    try:
        # First get option contracts for a popular ticker
        ticker = "AAPL"
        contracts = get_ticker_option_contracts(ticker)
        if contracts:
            logger.info(f"✅ Options Contracts API returned {len(contracts)} contracts for {ticker}")
            if len(contracts) > 0:
                contract_id = contracts[0].get("contract_id")
                logger.info(f"Testing Option Flow for contract: {contract_id}")
                flow_data = get_option_contract_flow(contract_id)
                if flow_data:
                    logger.info(f"✅ Option Flow API returned data for contract {contract_id}")
                    
                    # Test data formatting
                    formatted = format_option_flow_for_db(flow_data)
                    logger.info(f"Formatted data: {json.dumps(formatted, indent=2)}")
                else:
                    logger.warning(f"⚠️ Option Flow API returned no data for contract {contract_id}")
        else:
            logger.warning(f"⚠️ Options Contracts API returned no contracts for {ticker}")
    except Exception as e:
        logger.error(f"❌ Options Flow API test failed: {str(e)}")
    
    # Test institutions API
    logger.info("\nTesting Institutions API...")
    try:
        institutions = get_institutions(limit=limit)
        if institutions:
            logger.info(f"✅ Institutions API returned {len(institutions)} records")
            logger.info(f"Sample data: {json.dumps(institutions[0], indent=2)}")
            
            # Test data formatting
            formatted = format_institution_for_db(institutions[0])
            logger.info(f"Formatted data: {json.dumps(formatted, indent=2)}")
            
            # Test institution holdings API
            if len(institutions) > 0:
                name = institutions[0].get("name")
                logger.info(f"Testing Institution Holdings for: {name}")
                holdings = get_institution_holdings(name=name, limit=limit)
                if holdings:
                    logger.info(f"✅ Institution Holdings API returned {len(holdings)} records")
                    
                    # Test data formatting
                    formatted_holding = format_institution_holding_for_db(holdings[0])
                    logger.info(f"Formatted holding: {json.dumps(formatted_holding, indent=2)}")
                    
                    # Test institution activity API
                    logger.info(f"Testing Institution Activity for: {name}")
                    activities = get_institution_activity(name=name, limit=limit)
                    if activities:
                        logger.info(f"✅ Institution Activity API returned {len(activities)} records")
                        
                        # Test data formatting
                        formatted_activity = format_institution_activity_for_db(activities[0])
                        logger.info(f"Formatted activity: {json.dumps(formatted_activity, indent=2)}")
                    else:
                        logger.warning(f"⚠️ Institution Activity API returned no data for {name}")
                else:
                    logger.warning(f"⚠️ Institution Holdings API returned no data for {name}")
        else:
            logger.warning("⚠️ Institutions API returned no data")
    except Exception as e:
        logger.error(f"❌ Institutions API test failed: {str(e)}")
    
    # Test stock info API
    logger.info("\nTesting Stock Info API...")
    try:
        ticker = "AAPL"
        stock_info = get_stock_info(ticker)
        if stock_info:
            logger.info(f"✅ Stock Info API returned data for {ticker}")
            logger.info(f"Sample data: {json.dumps(stock_info, indent=2)}")
            
            # Test data formatting
            formatted = format_stock_info_for_db(stock_info, ticker)
            logger.info(f"Formatted data: {json.dumps(formatted, indent=2)}")
        else:
            logger.warning(f"⚠️ Stock Info API returned no data for {ticker}")
    except Exception as e:
        logger.error(f"❌ Stock Info API test failed: {str(e)}")

def test_direct_data_insertion():
    """Test direct insertion of data into Supabase tables"""
    logger.info("\n==========================================")
    logger.info("TESTING DIRECT DATA INSERTION INTO TABLES")
    logger.info("==========================================")
    
    # Test insider trades insertion
    logger.info("\nTesting direct insertion into insider_trades...")
    try:
        test_data = {
            "filing_id": str(datetime.now().timestamp()),  # Using UUID format for filing_id
            "symbol": "TEST",
            "company_name": "Test Company",
            "insider_name": "Test Insider",
            "relation": "Director",
            "transaction_type": "Purchase",
            "transaction_date": datetime.now().strftime("%Y-%m-%d"),
            "shares": 1000,
            "price": 50.0,
            "value": 50000.0,
            "shares_owned": 5000,
            "filing_date": datetime.now().strftime("%Y-%m-%d"),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table("insider_trades").insert(test_data).execute()
        logger.info(f"✅ Successfully inserted test data into insider_trades")
    except Exception as e:
        logger.error(f"❌ Insertion into insider_trades failed: {str(e)}")
    
    # Test analyst ratings insertion
    logger.info("\nTesting direct insertion into analyst_ratings...")
    try:
        test_data = {
            "symbol": "TEST",
            "company_name": "Test Company",
            "analyst_firm": "Test Firm",
            "analyst_name": "Test Analyst",
            "rating": "Buy",
            "previous_rating": "Hold",
            "rating_change": "Upgrade",
            "rating_date": datetime.now().strftime("%Y-%m-%d"),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table("analyst_ratings").insert(test_data).execute()
        logger.info("✅ Successfully inserted test data into analyst_ratings")
    except Exception as e:
        logger.error(f"❌ Insertion into analyst_ratings failed: {str(e)}")
    
    # Test dark pool trades insertion
    logger.info("\nTesting direct insertion into dark_pool_trades...")
    try:
        test_data = {
            "ticker": "TEST",
            "executed_at": datetime.now().isoformat(),
            "price": 100.0,
            "size": 10000,
            "premium": 1000000.0,
            "volume": 5000000,
            "market_center": "TEST",
            "ext_hour_sold_codes": "Test Codes",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table("dark_pool_trades").insert(test_data).execute()
        logger.info("✅ Successfully inserted test data into dark_pool_trades")
    except Exception as e:
        logger.error(f"❌ Insertion into dark_pool_trades failed: {str(e)}")
    
    # Test political trades insertion
    logger.info("\nTesting direct insertion into political_trades...")
    try:
        test_data = {
            "symbol": "TEST",
            "politician_name": "Test Politician",
            "position": "Senator",
            "party": "Independent",
            "state": "Test State",
            "transaction_date": datetime.now().strftime("%Y-%m-%d"),
            "transaction_type": "Purchase",
            "amount": 10000.0,
            "filing_date": datetime.now().strftime("%Y-%m-%d"),
            "disclosure_date": datetime.now().strftime("%Y-%m-%d"),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table("political_trades").insert(test_data).execute()
        logger.info("✅ Successfully inserted test data into political_trades")
    except Exception as e:
        logger.error(f"❌ Insertion into political_trades failed: {str(e)}")
    
    # Test FDA calendar insertion
    logger.info("\nTesting direct insertion into fda_calendar...")
    try:
        import uuid
        test_data = {
            "id": str(uuid.uuid4()),  # Generate a UUID
            "ticker": "TEST",
            "drug": "Test Drug",
            "catalyst": "Test Catalyst",
            "indication": "Test Indication",
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "status": "Phase 3",
            "created_at": datetime.now().isoformat(),
            "fetched_at": datetime.now().isoformat()
        }
        
        result = supabase.table("fda_calendar").insert(test_data).execute()
        logger.info("✅ Successfully inserted test data into fda_calendar")
    except Exception as e:
        logger.error(f"❌ Insertion into fda_calendar failed: {str(e)}")
    
    # Test economic events insertion
    logger.info("\nTesting direct insertion into economic_events...")
    try:
        test_data = {
            "id": f"test-event-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "event_name": "Test Economic Event",
            "event_time": datetime.now().isoformat(),
            "event_type": "report",
            "forecast": "5.0",
            "previous_value": "4.8",
            "reported_period": "Test Period",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table("economic_events").insert(test_data).execute()
        logger.info("✅ Successfully inserted test data into economic_events")
    except Exception as e:
        logger.error(f"❌ Insertion into economic_events failed: {str(e)}")
    
    # Test options flow data insertion
    logger.info("\nTesting direct insertion into options_flow_data...")
    try:
        test_data = {
            "ticker": "TEST",
            "sentiment": "bullish",
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "call_volume": 1000,
            "put_volume": 500,
            "call_put_ratio": 2.0,
            "avg_call_premium": 100000.0,
            "avg_put_premium": 50000.0,
            "largest_trade_type": "call",
            "largest_trade_premium": 200000.0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table("options_flow_data").insert(test_data).execute()
        logger.info("✅ Successfully inserted test data into options_flow_data")
    except Exception as e:
        logger.error(f"❌ Insertion into options_flow_data failed: {str(e)}")
    
    # Test institutions insertion
    logger.info("\nTesting direct insertion into institutions...")
    try:
        test_data = {
            "name": "Test Institution",
            "short_name": "TEST",
            "cik": "0000000000",
            "description": "Test institution description",
            "is_hedge_fund": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table("institutions").insert(test_data).execute()
        logger.info("✅ Successfully inserted test data into institutions")
    except Exception as e:
        logger.error(f"❌ Insertion into institutions failed: {str(e)}")
    
    # Test institution holdings insertion
    logger.info("\nTesting direct insertion into institution_holdings...")
    try:
        test_data = {
            "institution_name": "Test Institution",
            "ticker": "TEST",
            "full_name": "Test Company",
            "security_type": "Share",
            "units": 10000,
            "units_change": 1000,
            "value": 1000000.0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table("institution_holdings").insert(test_data).execute()
        logger.info("✅ Successfully inserted test data into institution_holdings")
    except Exception as e:
        logger.error(f"❌ Insertion into institution_holdings failed: {str(e)}")
    
    # Test stock info insertion
    logger.info("\nTesting direct insertion into stock_info...")
    try:
        test_data = {
            "ticker": "TEST",
            "company_name": "Test Company",
            "sector": "Technology",
            "industry": "Software",
            "description": "Test company description",
            "market_cap": 10000000000.0,
            "current_price": 100.0,
            "avg_volume": 1000000,
            "price_updated_at": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table("stock_info").insert(test_data).execute()
        logger.info("✅ Successfully inserted test data into stock_info")
    except Exception as e:
        logger.error(f"❌ Insertion into stock_info failed: {str(e)}")

def check_table_contents():
    """Check if tables have data"""
    logger.info("\n==========================================")
    logger.info("CHECKING TABLE CONTENTS")
    logger.info("==========================================")
    
    tables = [
        "insider_trades", "analyst_ratings", "dark_pool_trades", 
        "economic_calendar", "economic_events", "economic_indicators",
        "economic_news", "economic_reports", "fda_calendar",
        "fred_metadata", "fred_observations", "fred_user_series",
        "hedge_fund_trades", "institution_activity", "institution_holdings",
        "institutions", "market_indicators", "options_flow_data",
        "options_flow", "political_trades", "stock_info"
    ]
    
    for table in tables:
        try:
            result = supabase.table(table).select("*").execute()
            
            if result.data:
                record_count = len(result.data)
                logger.info(f"✅ {table} has {record_count} records")
                if record_count > 0:
                    logger.info(f"Sample record: {json.dumps(result.data[0], indent=2)}")
            else:
                logger.warning(f"⚠️ {table} exists but is empty")
        except Exception as e:
            logger.error(f"❌ Error checking contents of {table}: {str(e)}")

def check_supabase_schema(table_name):
    """Get the schema for a table"""
    try:
        # Call Supabase RPC function to get table info
        result = supabase.rpc(
            "get_table_info",
            {"table_name": table_name}
        ).execute()
        
        return result.data
    except Exception as e:
        logger.error(f"Error getting schema for {table_name}: {str(e)}")
        return None

def verify_table_schemas():
    """Verify schemas of all tables"""
    logger.info("\n==========================================")
    logger.info("VERIFYING TABLE SCHEMAS")
    logger.info("==========================================")
    
    tables = [
        "insider_trades", "analyst_ratings", "dark_pool_trades", 
        "economic_calendar", "economic_events", "economic_indicators",
        "economic_news", "economic_reports", "fda_calendar",
        "fred_metadata", "fred_observations", "fred_user_series",
        "hedge_fund_trades", "institution_activity", "institution_holdings",
        "institutions", "market_indicators", "options_flow_data",
        "options_flow", "political_trades", "stock_info"
    ]
    
    for table in tables:
        schema = check_supabase_schema(table)
        if schema and isinstance(schema, list) and len(schema) > 0:
            columns = [col["column_name"] for col in schema]
            logger.info(f"✅ {table} schema verified, contains columns:")
            for col in columns:
                logger.info(f"  - {col}")
        else:
            logger.warning(f"⚠️ Could not verify schema for {table}")

def main():
    """Run all tests"""
    logger.info("Starting Supabase Data Insertion Debug Tests")
    test_supabase_connection()
    test_api_data_retrieval()
    test_direct_data_insertion()
    check_table_contents()
    verify_table_schemas()
    logger.info("Completed Supabase Data Insertion Debug Tests")

if __name__ == "__main__":
    main() 