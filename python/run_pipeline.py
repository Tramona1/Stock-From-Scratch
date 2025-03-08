#!/usr/bin/env python3
"""
Financial Data Pipeline Runner

This script runs the entire financial data pipeline, executing all data fetchers
in sequence with enhanced logging and error handling. Use this to update all financial
data in one go or to troubleshoot specific components of the pipeline.

Usage:
  python run_pipeline.py [--components COMPONENT1,COMPONENT2,...] [--watchlist]

Options:
  --components COMPONENTS   Comma-separated list of components to run: 
                            insider,political,analyst,economic,fda,darkpool,options,institution
  --watchlist               Only process data for stocks in user watchlists
  --days DAYS               Number of days to look back for data (default: 30)
  --limit LIMIT             Maximum number of records to fetch per request (default: 500)
"""

import os
import sys
import time
import json
import logging
import argparse
import traceback
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Configure detailed logging
os.makedirs("logs", exist_ok=True)
log_filename = f"logs/pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_filename)
    ]
)

logger = logging.getLogger("pipeline_runner")

# Try to use colorlog for prettier console output
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

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Define fetcher configurations
FETCHERS = {
    "insider": {
        "module": "insider_trades_fetcher",
        "class": "InsiderTradesFetcher",
        "description": "Insider trading activity"
    },
    "political": {
        "module": "fetch_political_trades",
        "class": "PoliticalTradesFetcher",
        "description": "Congressional trading activity"
    },
    "analyst": {
        "module": "fetch_analyst_ratings",
        "class": "AnalystRatingsFetcher",
        "description": "Analyst ratings and price targets"
    },
    "economic": {
        "module": "economic_indicators_fetcher",
        "class": "EconomicIndicatorFetcher",
        "description": "Economic indicators and events"
    },
    "fda": {
        "module": "fetch_fda_calendar",
        "class": "FDACalendarFetcher",
        "description": "FDA drug approval events"
    },
    "darkpool": {
        "module": "fetch_dark_pool_data",
        "class": "DarkPoolDataFetcher",
        "description": "Dark pool trading activity"
    },
    "options": {
        "module": "fetch_options_flow",
        "class": "OptionsFlowFetcher",
        "description": "Options flow and unusual activity"
    },
    "institution": {
        "module": "hedge_fund_fetcher",
        "class": "HedgeFundTradesFetcher",
        "description": "Institutional holdings and activity"
    }
}

def log_section(title: str):
    """Log a section header for better readability"""
    separator = "=" * 80
    logger.info(f"\n{separator}\n{title.center(80)}\n{separator}")

def log_subsection(title: str):
    """Log a subsection header"""
    separator = "-" * 60
    logger.info(f"\n{separator}\n{title}\n{separator}")

def log_error(component: str, error_type: str, message: str, exception: Optional[Exception] = None):
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

async def get_watchlist_symbols():
    """Fetch all unique symbols from user watchlists"""
    log_subsection("Fetching Watchlist Symbols")
    
    try:
        from supabase import create_client
        
        # Get Supabase credentials
        supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            log_error("Watchlist", "Missing Credentials", "Supabase credentials not found in environment variables")
            logger.error("❌ Watchlist: Unable to fetch symbols (missing credentials)")
            return []
        
        # Connect to Supabase
        supabase = create_client(supabase_url, supabase_key)
        
        # Fetch watchlist symbols
        response = supabase.table("watchlists").select("ticker").execute()
        
        if hasattr(response, 'error') and response.error:
            log_error("Watchlist", "Query Error", "Error querying watchlists table", Exception(response.error))
            logger.error("❌ Watchlist: Query error")
            return []
        
        # Extract unique tickers
        all_tickers = [item.get("ticker") for item in response.data if item.get("ticker")]
        unique_tickers = list(set(all_tickers))
        
        if not unique_tickers:
            logger.warning("⚠️ No tickers found in watchlists")
            return []
        
        logger.info(f"✅ Found {len(unique_tickers)} unique tickers in watchlists")
        logger.info(f"Sample tickers: {', '.join(unique_tickers[:10])}" + 
                  (f"... (plus {len(unique_tickers) - 10} more)" if len(unique_tickers) > 10 else ""))
        
        return unique_tickers
        
    except Exception as e:
        log_error("Watchlist", "Fetching Error", "Error fetching watchlist symbols", e)
        logger.error("❌ Watchlist: Failed to fetch symbols")
        return []

async def run_fetcher(fetcher_key: str, days: int = 30, limit: int = 500, symbols: Optional[List[str]] = None):
    """Run a specific data fetcher with enhanced error handling"""
    if fetcher_key not in FETCHERS:
        logger.error(f"❌ Unknown fetcher: {fetcher_key}")
        return False
    
    fetcher_config = FETCHERS[fetcher_key]
    module_name = fetcher_config["module"]
    class_name = fetcher_config["class"]
    description = fetcher_config["description"]
    
    log_section(f"RUNNING {fetcher_key.upper()} FETCHER: {description}")
    
    start_time = time.time()
    
    try:
        # Dynamically import the module
        logger.info(f"Importing {module_name}...")
        
        try:
            module = __import__(module_name)
            logger.info(f"✅ Module {module_name} imported successfully")
        except ImportError as e:
            log_error(fetcher_key, "Import Error", f"Failed to import module {module_name}", e)
            logger.error(f"❌ {fetcher_key}: Module import failed")
            return False
        
        # Get the fetcher class
        try:
            fetcher_class = getattr(module, class_name)
            logger.info(f"✅ Class {class_name} found in module")
        except AttributeError as e:
            log_error(fetcher_key, "Class Error", f"Class {class_name} not found in {module_name}", e)
            logger.error(f"❌ {fetcher_key}: Class not found")
            return False
        
        # Create an instance of the fetcher
        logger.info(f"Creating instance of {class_name}...")
        
        try:
            # Initialize with days parameter if the constructor accepts it
            try:
                fetcher = fetcher_class(days_to_fetch=days)
            except TypeError:
                # Fall back to default constructor if days_to_fetch is not accepted
                fetcher = fetcher_class()
            
            logger.info(f"✅ Created instance of {class_name}")
        except Exception as e:
            log_error(fetcher_key, "Initialization Error", f"Failed to initialize {class_name}", e)
            logger.error(f"❌ {fetcher_key}: Initialization failed")
            return False
        
        # Check if the fetcher supports watchlist-specific fetching
        if symbols and hasattr(fetcher, "fetch_for_watchlist"):
            logger.info(f"Running fetcher for {len(symbols)} watchlist symbols...")
            
            try:
                # Run the fetcher with watchlist symbols
                success = await fetcher.fetch_for_watchlist(symbols)
                
                if success:
                    elapsed_time = time.time() - start_time
                    logger.info(f"✅ {fetcher_key}: Completed watchlist fetch in {elapsed_time:.2f}s")
                    return True
                else:
                    log_error(fetcher_key, "Execution Error", "Fetcher failed during watchlist execution")
                    logger.error(f"❌ {fetcher_key}: Watchlist fetch failed")
                    return False
                    
            except Exception as e:
                log_error(fetcher_key, "Watchlist Error", "Error during watchlist-specific fetching", e)
                logger.error(f"❌ {fetcher_key}: Watchlist method failed")
                
                # Fall back to regular run method
                logger.info("Falling back to standard fetch method...")
        
        # Run the standard fetch method
        logger.info(f"Running {class_name}.run()...")
        
        try:
            # Try with limit parameter if available
            try:
                if hasattr(fetcher, "set_limit") and callable(getattr(fetcher, "set_limit")):
                    fetcher.set_limit(limit)
                    logger.info(f"Set limit to {limit}")
            except Exception as e:
                logger.debug(f"Could not set limit: {str(e)}")
            
            # Run the fetcher
            # Check if the run method is a coroutine function before awaiting it
            if asyncio.iscoroutinefunction(fetcher.run):
                success = await fetcher.run()
            else:
                success = fetcher.run()
            
            if success:
                elapsed_time = time.time() - start_time
                logger.info(f"✅ {fetcher_key}: Completed successfully in {elapsed_time:.2f}s")
                return True
            else:
                log_error(fetcher_key, "Execution Error", "Fetcher failed to complete")
                logger.error(f"❌ {fetcher_key}: Failed to complete")
                return False
                
        except Exception as e:
            log_error(fetcher_key, "Execution Error", "Error running fetcher", e)
            logger.error(f"❌ {fetcher_key}: Execution failed")
            return False
            
    except Exception as e:
        elapsed_time = time.time() - start_time
        log_error(fetcher_key, "Unknown Error", f"Unexpected error after {elapsed_time:.2f}s", e)
        logger.error(f"❌ {fetcher_key}: Unexpected error")
        return False

async def run_pipeline(components: List[str], use_watchlist: bool, days: int, limit: int):
    """Run the entire data pipeline or specified components"""
    log_section("STARTING FINANCIAL DATA PIPELINE")
    
    # Record start time
    pipeline_start = time.time()
    
    # Print configuration
    logger.info(f"Pipeline configuration:")
    logger.info(f"- Components: {', '.join(components) if components else 'ALL'}")
    logger.info(f"- Watchlist only: {use_watchlist}")
    logger.info(f"- Days to fetch: {days}")
    logger.info(f"- Limit per request: {limit}")
    
    # Get watchlist symbols if needed
    symbols = None
    if use_watchlist:
        symbols = await get_watchlist_symbols()
        if not symbols:
            log_error("Pipeline", "Empty Watchlist", "No symbols found in watchlist")
            logger.warning("⚠️ Proceeding with full data fetch since watchlist is empty")
    
    # Determine which components to run
    component_keys = components if components else list(FETCHERS.keys())
    
    # Run each component
    results = {}
    
    for key in component_keys:
        if key not in FETCHERS:
            logger.warning(f"⚠️ Unknown component: {key}, skipping")
            continue
            
        results[key] = await run_fetcher(key, days, limit, symbols)
    
    # Log summary
    log_section("PIPELINE EXECUTION SUMMARY")
    
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    for component, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        logger.info(f"{component.ljust(15)}: {status}")
    
    pipeline_duration = time.time() - pipeline_start
    
    if success_count == total_count:
        logger.info(f"\n✅✅✅ ALL COMPONENTS COMPLETED SUCCESSFULLY: {success_count}/{total_count}")
    else:
        logger.warning(f"\n⚠️⚠️⚠️ SOME COMPONENTS FAILED: {success_count}/{total_count} successful")
    
    logger.info(f"Total pipeline execution time: {pipeline_duration:.2f} seconds")
    logger.info(f"Complete log available at: {log_filename}")
    
    return success_count == total_count

async def main():
    """Main entry point for the pipeline runner"""
    parser = argparse.ArgumentParser(description="Run the financial data pipeline")
    parser.add_argument("--components", help="Comma-separated list of components to run")
    parser.add_argument("--watchlist", action="store_true", help="Only process data for watchlist stocks")
    parser.add_argument("--days", type=int, default=30, help="Number of days to look back for data")
    parser.add_argument("--limit", type=int, default=500, help="Maximum number of records to fetch per request")
    
    args = parser.parse_args()
    
    # Parse components
    components = []
    if args.components:
        components = [c.strip() for c in args.components.split(",") if c.strip()]
    
    # Validate components
    invalid_components = [c for c in components if c not in FETCHERS]
    if invalid_components:
        logger.warning(f"⚠️ Unknown components specified: {', '.join(invalid_components)}")
        logger.info(f"Available components: {', '.join(FETCHERS.keys())}")
    
    # Run the pipeline
    success = await run_pipeline(
        components=[c for c in components if c in FETCHERS],
        use_watchlist=args.watchlist,
        days=args.days,
        limit=args.limit
    )
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main()) 