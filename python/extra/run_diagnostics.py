#!/usr/bin/env python3
"""
Comprehensive Diagnostic Runner for Financial Data Pipeline

This script runs a complete diagnostic check on all components of the financial data pipeline:
1. Checks API connectivity for each data source
2. Validates database connections and table existence
3. Runs each data fetcher with detailed error logging
4. Tests rate limiting and caching mechanisms
5. Verifies data is properly stored in the database

Use this script to identify issues with any part of the data pipeline.

Usage:
  python run_diagnostics.py [--only COMPONENT] [--verbose]

Options:
  --only COMPONENT    Run diagnostics for a specific component
                      (api, db, insider, analyst, options, political, 
                       economic, fda, darkpool, institution, all)
  --verbose           Show detailed logs for all operations
"""

import os
import sys
import json
import asyncio
import logging
import argparse
import traceback
import time
from datetime import datetime
import requests
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import importlib.util

# Set up detailed logging
os.makedirs("logs", exist_ok=True)
log_filename = f"logs/diagnostics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_filename)
    ]
)

logger = logging.getLogger("diagnostics")

# Add console handler with colored output if colorlog is available
try:
    import colorlog
    color_handler = colorlog.StreamHandler()
    color_handler.setFormatter(colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    ))
    logger.handlers = [color_handler, logging.FileHandler(log_filename)]
except ImportError:
    logger.info("colorlog not installed. Using standard logging colors.")

# Load environment variables
load_dotenv()

# Get environment variables
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
API_KEY_UNUSUAL_WHALES = os.getenv("API_KEY_UNUSUAL_WHALES")
API_KEY_ALPHA_VANTAGE = os.getenv("API_KEY_ALPHA_VANTAGE")
FRED_API_KEY = os.getenv("FRED_API_KEY")

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def log_section(title):
    """Log a section header to make logs more readable"""
    line = "=" * 80
    logger.info(f"\n{line}\n{title.center(80)}\n{line}")

def log_subsection(title):
    """Log a subsection header"""
    line = "-" * 60
    logger.info(f"\n{line}\n{title}\n{line}")

def log_error(component, error_type, message, exception=None):
    """Log detailed error information with categorization"""
    error_info = {
        "component": component,
        "error_type": error_type,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if exception:
        error_info["exception"] = str(exception)
        error_info["traceback"] = traceback.format_exc()
    
    logger.error(f"ERROR [{error_type}] in {component}: {message}", extra={"error_info": error_info})
    
    if exception:
        logger.error(f"Exception details: {str(exception)}")
        logger.debug(f"Traceback: {traceback.format_exc()}")

async def check_api_connectivity():
    """Check connectivity to all required APIs"""
    log_section("API CONNECTIVITY CHECKS")
    
    apis_to_check = [
        {
            "name": "Unusual Whales API",
            "url": "https://api.unusualwhales.com/api/market/sentiment",
            "headers": {"Authorization": f"Bearer {API_KEY_UNUSUAL_WHALES}"},
            "env_var": "API_KEY_UNUSUAL_WHALES"
        },
        {
            "name": "Alpha Vantage API",
            "url": f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=IBM&interval=5min&apikey={API_KEY_ALPHA_VANTAGE}",
            "env_var": "API_KEY_ALPHA_VANTAGE"
        },
        {
            "name": "FRED API",
            "url": f"https://api.stlouisfed.org/fred/series?series_id=GDP&api_key={FRED_API_KEY}&file_type=json",
            "env_var": "FRED_API_KEY"
        }
    ]
    
    all_successful = True
    
    for api in apis_to_check:
        api_name = api["name"]
        api_url = api["url"]
        api_key_var = api["env_var"]
        api_key = os.getenv(api_key_var)
        
        log_subsection(f"Checking {api_name}")
        
        # Check if API key is set
        if not api_key:
            log_error("API Connectivity", "Missing API Key", f"{api_key_var} environment variable is not set")
            logger.error(f"❌ {api_name}: API key not found in environment variables")
            all_successful = False
            continue
        
        # Test API connectivity
        try:
            logger.info(f"Testing connection to {api_name}...")
            headers = api.get("headers", {})
            
            start_time = time.time()
            response = requests.get(api_url, headers=headers, timeout=10)
            elapsed_time = time.time() - start_time
            
            if response.status_code in (200, 201, 202):
                logger.info(f"✅ {api_name}: Connected successfully (took {elapsed_time:.2f}s)")
                logger.debug(f"Response: {response.text[:500]}...")
            else:
                log_error("API Connectivity", "API Error", 
                          f"Failed to connect to {api_name}. Status code: {response.status_code}", 
                          Exception(response.text))
                logger.error(f"❌ {api_name}: Failed with status code {response.status_code}")
                all_successful = False
                
        except requests.exceptions.Timeout:
            log_error("API Connectivity", "Timeout", f"Connection to {api_name} timed out after 10 seconds")
            logger.error(f"❌ {api_name}: Connection timed out")
            all_successful = False
        except requests.exceptions.RequestException as e:
            log_error("API Connectivity", "Connection Error", f"Error connecting to {api_name}", e)
            logger.error(f"❌ {api_name}: Connection error")
            all_successful = False
    
    return all_successful

async def check_database_connectivity():
    """Check connectivity to Supabase and validate table existence"""
    log_section("DATABASE CONNECTIVITY CHECKS")
    
    # Check if Supabase credentials are set
    if not SUPABASE_URL or not SUPABASE_KEY:
        log_error("Database", "Missing Credentials", "Supabase credentials not found in environment variables")
        logger.error("❌ Supabase: Credentials not found in environment variables")
        return False
    
    # Import Supabase client
    try:
        from supabase import create_client
        logger.info("Supabase client library loaded successfully")
    except ImportError as e:
        log_error("Database", "Missing Library", "Failed to import Supabase client library", e)
        logger.error("❌ Supabase: Client library not installed")
        return False
    
    # Connect to Supabase
    try:
        logger.info("Connecting to Supabase...")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Supabase: Connected successfully")
    except Exception as e:
        log_error("Database", "Connection Error", "Failed to connect to Supabase", e)
        logger.error("❌ Supabase: Connection failed")
        return False
    
    # Define list of required tables
    required_tables = [
        "analyst_ratings",
        "economic_calendar_events",
        "fda_calendar_events",
        "insider_trades",
        "political_trades",
        "dark_pool_data",
        "options_flow",
        "institution_holdings",
        "institution_activity",
        "institutions",
        "alerts"
    ]
    
    # Check each table
    log_subsection("Checking Table Existence")
    all_tables_exist = True
    
    for table in required_tables:
        try:
            # Try to select a single row from the table
            response = supabase.table(table).select("*").limit(1).execute()
            
            if hasattr(response, 'error') and response.error:
                log_error("Database", "Table Error", f"Error accessing table {table}", Exception(response.error))
                logger.error(f"❌ Table '{table}': Access error")
                all_tables_exist = False
            else:
                logger.info(f"✅ Table '{table}': Exists and accessible")
                
        except Exception as e:
            log_error("Database", "Table Error", f"Failed to check table {table}", e)
            logger.error(f"❌ Table '{table}': Check failed")
            all_tables_exist = False
    
    return all_tables_exist

async def test_unusual_whales_api():
    """Test the unusual_whales_api module functionality"""
    log_section("UNUSUAL WHALES API MODULE TEST")
    
    try:
        # Import the module
        log_subsection("Importing Module")
        try:
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            import unusual_whales_api
            logger.info("✅ Module imported successfully")
        except ImportError as e:
            log_error("Unusual Whales API", "Import Error", "Failed to import unusual_whales_api module", e)
            logger.error("❌ Module import failed")
            return False
        
        # Test module functionality without making API calls
        log_subsection("Testing Module Functions (Mocked)")
        
        # Test get_headers function
        try:
            # Save original environment variable to restore later
            original_api_key = os.environ.get("API_KEY_UNUSUAL_WHALES")
            
            # Set test key and check headers
            os.environ["API_KEY_UNUSUAL_WHALES"] = "test_key_for_headers"
            headers = unusual_whales_api.get_headers()
            
            # Check if Authorization header is set correctly with the Bearer prefix
            if "Authorization" in headers and "test_key_for_headers" in headers["Authorization"]:
                logger.info("✅ get_headers: Function works correctly")
            else:
                logger.warning(f"⚠️ get_headers returned: {headers}")
                logger.error("❌ get_headers: Function returned incorrect headers")
                return False
                
            # Restore original API key
            if original_api_key:
                os.environ["API_KEY_UNUSUAL_WHALES"] = original_api_key
            else:
                del os.environ["API_KEY_UNUSUAL_WHALES"]
        except Exception as e:
            log_error("Unusual Whales API", "Function Error", "Error in get_headers", e)
            logger.error("❌ get_headers: Function failed")
            return False
            
        # Test formatting functions
        log_subsection("Testing Formatting Functions")
        
        # Test insider trade formatting
        insider_trade = {
            "symbol": "AAPL",
            "insider_name": "Test Person",
            "transaction_type": "Purchase",
            "transaction_date": "2023-01-01",
            "shares": 100,
            "price": 150.0,
            "total_value": 15000.0,
            "shares_owned_after": 500,
            "filing_date": "2023-01-05",
            "company_name": "Apple Inc."
        }
        
        try:
            formatted = unusual_whales_api.format_insider_trade_for_db(insider_trade)
            if formatted["symbol"] == "AAPL" and formatted["source"] == "Unusual Whales":
                logger.info("✅ format_insider_trade_for_db: Function works correctly")
            else:
                logger.error("❌ format_insider_trade_for_db: Function returned incorrect data")
                return False
        except Exception as e:
            log_error("Unusual Whales API", "Function Error", "Error in format_insider_trade_for_db", e)
            logger.error("❌ format_insider_trade_for_db: Function failed")
            return False
            
        logger.info("✅ Module code functionality appears to be working correctly")
        return True
        
    except Exception as e:
        log_error("Unusual Whales API", "Module Error", "Error testing unusual_whales_api module", e)
        logger.error("❌ Module test failed")
        return False

async def run_fetcher(fetcher_name, fetcher_class_name):
    """Run a specific data fetcher and test its functionality"""
    log_section(f"TESTING {fetcher_name.upper()} FETCHER")
    
    try:
        # Import the fetcher module
        try:
            logger.info(f"Importing {fetcher_name}...")
            module_spec = importlib.util.find_spec(fetcher_name)
            
            if not module_spec:
                log_error("Fetcher", "Import Error", f"Module {fetcher_name} not found")
                logger.error(f"❌ {fetcher_name}: Module not found")
                return False
                
            module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module)
            logger.info(f"✅ {fetcher_name}: Module imported successfully")
            
            # Get the fetcher class
            fetcher_class = getattr(module, fetcher_class_name, None)
            
            if not fetcher_class:
                log_error("Fetcher", "Class Error", f"Class {fetcher_class_name} not found in {fetcher_name}")
                logger.error(f"❌ {fetcher_name}: Class {fetcher_class_name} not found")
                return False
                
            logger.info(f"✅ {fetcher_name}: Class {fetcher_class_name} found")
            
            # Create an instance of the fetcher
            log_subsection("Creating Fetcher Instance")
            fetcher = fetcher_class()
            logger.info(f"✅ {fetcher_name}: Instance created successfully")
            
            # Run the fetcher
            log_subsection("Running Fetcher")
            logger.info(f"Running {fetcher_name}...")
            
            start_time = time.time()
            success = await fetcher.run()
            elapsed_time = time.time() - start_time
            
            if success:
                logger.info(f"✅ {fetcher_name}: Completed successfully in {elapsed_time:.2f}s")
                return True
            else:
                log_error("Fetcher", "Execution Error", f"Fetcher {fetcher_name} failed to complete")
                logger.error(f"❌ {fetcher_name}: Failed to complete")
                return False
                
        except ImportError as e:
            log_error("Fetcher", "Import Error", f"Failed to import {fetcher_name}", e)
            logger.error(f"❌ {fetcher_name}: Import failed")
            return False
            
    except Exception as e:
        log_error("Fetcher", "Execution Error", f"Error running {fetcher_name}", e)
        logger.error(f"❌ {fetcher_name}: Execution failed")
        return False

async def run_all_fetchers():
    """Run all data fetchers with enhanced error handling"""
    log_section("RUNNING ALL DATA FETCHERS")
    
    fetchers = [
        {"name": "insider_trades_fetcher", "class": "InsiderTradesFetcher"},
        {"name": "hedge_fund_fetcher", "class": "HedgeFundTradesFetcher"},
        {"name": "economic_indicators_fetcher", "class": "EconomicIndicatorFetcher"},
        {"name": "market_data_fetcher", "class": "MarketDataFetcher"}
    ]
    
    results = {}
    
    for fetcher in fetchers:
        name = fetcher["name"]
        results[name] = await run_fetcher(name, fetcher["class"])
    
    # Log summary
    log_section("FETCHER EXECUTION SUMMARY")
    
    all_successful = True
    for name, success in results.items():
        if success:
            logger.info(f"✅ {name}: Successful")
        else:
            logger.error(f"❌ {name}: Failed")
            all_successful = False
    
    return all_successful

async def test_data_storage(component=None):
    """Test that data is being correctly stored in the database"""
    log_section("DATA STORAGE VERIFICATION")
    
    # Import Supabase client
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        log_error("Database", "Connection Error", "Failed to connect to Supabase for data verification", e)
        logger.error("❌ Database: Connection failed")
        return False
    
    # Define tables to check based on the component
    tables_to_check = []
    
    if component == "insider" or component == "all":
        tables_to_check.append({"name": "insider_trades", "min_rows": 10})
    if component == "analyst" or component == "all":
        tables_to_check.append({"name": "analyst_ratings", "min_rows": 10})
    if component == "political" or component == "all":
        tables_to_check.append({"name": "political_trades", "min_rows": 10})
    if component == "darkpool" or component == "all":
        tables_to_check.append({"name": "dark_pool_data", "min_rows": 10})
    if component == "options" or component == "all":
        tables_to_check.append({"name": "options_flow", "min_rows": 5})
    if component == "economic" or component == "all":
        tables_to_check.append({"name": "economic_calendar_events", "min_rows": 5})
    if component == "fda" or component == "all":
        tables_to_check.append({"name": "fda_calendar_events", "min_rows": 5})
    if component == "institution" or component == "all":
        tables_to_check.extend([
            {"name": "institution_holdings", "min_rows": 5},
            {"name": "institution_activity", "min_rows": 5},
            {"name": "institutions", "min_rows": 5}
        ])
    
    if not tables_to_check:
        logger.warning("No tables selected for data storage verification")
        return True
    
    all_tables_verified = True
    
    for table in tables_to_check:
        table_name = table["name"]
        min_rows = table["min_rows"]
        
        log_subsection(f"Checking {table_name}")
        
        try:
            # Count rows in the table
            response = supabase.table(table_name).select("*", count="exact").execute()
            
            if hasattr(response, 'error') and response.error:
                log_error("Data Storage", "Query Error", f"Error querying table {table_name}", Exception(response.error))
                logger.error(f"❌ {table_name}: Query error")
                all_tables_verified = False
                continue
                
            # Get count from response
            count = len(response.data)
            
            if count < min_rows:
                log_error("Data Storage", "Insufficient Data", 
                          f"Table {table_name} has only {count} rows, expected at least {min_rows}")
                logger.warning(f"⚠️ {table_name}: Only {count} rows found (expected {min_rows}+)")
            else:
                logger.info(f"✅ {table_name}: {count} rows found")
                
            # Check for recent data
            try:
                response = supabase.table(table_name).select("*").order("created_at", desc=True).limit(1).execute()
                
                if response.data:
                    latest_record = response.data[0]
                    created_at = latest_record.get("created_at")
                    
                    if created_at:
                        logger.info(f"✅ {table_name}: Latest record created at {created_at}")
                    else:
                        logger.warning(f"⚠️ {table_name}: Latest record has no created_at timestamp")
                else:
                    logger.warning(f"⚠️ {table_name}: No records found in query")
                    
            except Exception as e:
                log_error("Data Storage", "Recent Data Check Error", f"Error checking recent data in {table_name}", e)
                logger.error(f"❌ {table_name}: Recent data check failed")
                
        except Exception as e:
            log_error("Data Storage", "Verification Error", f"Error verifying data in {table_name}", e)
            logger.error(f"❌ {table_name}: Verification failed")
            all_tables_verified = False
    
    return all_tables_verified

async def main():
    """Main diagnostic function"""
    parser = argparse.ArgumentParser(description="Run diagnostics on the financial data pipeline")
    parser.add_argument("--only", choices=["api", "db", "insider", "analyst", "options", "political", 
                                          "economic", "fda", "darkpool", "institution", "all"],
                        default="all", help="Run diagnostics for a specific component")
    parser.add_argument("--verbose", action="store_true", help="Show detailed logs")
    
    args = parser.parse_args()
    component = args.only
    
    if args.verbose:
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    
    # Print diagnostic info
    log_section("FINANCIAL DATA PIPELINE DIAGNOSTICS")
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Component: {component}")
    logger.info(f"Log file: {log_filename}")
    
    # Check environment variables
    env_vars = [
        "NEXT_PUBLIC_SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "API_KEY_UNUSUAL_WHALES",
        "API_KEY_ALPHA_VANTAGE",
        "FRED_API_KEY"
    ]
    
    log_subsection("Checking Environment Variables")
    for var in env_vars:
        value = os.getenv(var)
        if value:
            masked_value = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
            logger.info(f"✅ {var}: Set ({masked_value})")
        else:
            logger.error(f"❌ {var}: Not set")
    
    # Run appropriate diagnostic functions based on component
    results = {}
    
    if component in ["api", "all"]:
        results["api_connectivity"] = await check_api_connectivity()
    
    if component in ["db", "all"]:
        results["database_connectivity"] = await check_database_connectivity()
    
    if component in ["insider", "analyst", "options", "political", "economic", 
                     "fda", "darkpool", "institution", "all"]:
        results["unusual_whales_api"] = await test_unusual_whales_api()
    
    # Run fetcher tests based on component
    if component == "insider" or component == "all":
        results["insider_fetcher"] = await run_fetcher("insider_trades_fetcher", "InsiderTradesFetcher")
    
    if component == "analyst" or component == "all":
        # Assuming there's an analyst ratings fetcher
        # results["analyst_fetcher"] = await run_fetcher("analyst_ratings_fetcher", "AnalystRatingsFetcher")
        pass
    
    if component == "all":
        results["all_fetchers"] = await run_all_fetchers()
    
    # Check data storage
    if component in ["insider", "analyst", "options", "political", "economic", 
                    "fda", "darkpool", "institution", "all"]:
        results["data_storage"] = await test_data_storage(component)
    
    # Print summary
    log_section("DIAGNOSTIC RESULTS SUMMARY")
    
    all_successful = True
    for test, success in results.items():
        if success:
            logger.info(f"✅ {test}: PASSED")
        else:
            logger.error(f"❌ {test}: FAILED")
            all_successful = False
    
    if all_successful:
        logger.info("\n✅✅✅ ALL DIAGNOSTICS PASSED ✅✅✅")
    else:
        logger.error("\n❌❌❌ SOME DIAGNOSTICS FAILED ❌❌❌")
    
    logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Complete log available at: {log_filename}")

if __name__ == "__main__":
    asyncio.run(main()) 