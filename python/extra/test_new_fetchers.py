#!/usr/bin/env python3
"""
Test New Fetchers

This script tests all the newly implemented fetcher modules to verify they 
correctly fetch data from the Unusual Whales API and store it in Supabase.
"""

import os
import sys
import asyncio
import logging
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/test_fetchers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("test_fetchers")

# Load environment variables
load_dotenv()

# Import the fetcher modules
try:
    from fetch_dark_pool_data import DarkPoolDataFetcher
    from fetch_options_flow import OptionsFlowFetcher
    from fetch_fda_calendar import FDACalendarFetcher
    from fetch_political_trades import PoliticalTradesFetcher
    from fetch_economic_reports import EconomicReportsFetcher
    from fetch_stock_info import StockInfoFetcher
    
    logger.info("Successfully imported all fetcher modules")
except ImportError as e:
    logger.error(f"Failed to import fetcher modules: {str(e)}")
    sys.exit(1)

async def test_dark_pool_fetcher():
    """Test the Dark Pool Data Fetcher"""
    logger.info("=== Testing Dark Pool Data Fetcher ===")
    try:
        fetcher = DarkPoolDataFetcher()
        
        # Test with a limited set of tickers
        test_tickers = ["AAPL", "MSFT", "TSLA"]
        logger.info(f"Testing Dark Pool fetcher with tickers: {test_tickers}")
        
        result = await fetcher.run(tickers=test_tickers, limit=5)
        
        logger.info(f"Dark Pool Fetcher Result: {json.dumps(result, indent=2)}")
        
        return result.get("status") == "success"
    except Exception as e:
        logger.error(f"Error testing Dark Pool fetcher: {str(e)}")
        return False

async def test_options_flow_fetcher():
    """Test the Options Flow Fetcher"""
    logger.info("=== Testing Options Flow Fetcher ===")
    try:
        fetcher = OptionsFlowFetcher()
        
        # Test with a limited set of tickers
        test_tickers = ["AAPL", "MSFT", "TSLA"]
        logger.info(f"Testing Options Flow fetcher with tickers: {test_tickers}")
        
        result = await fetcher.run(tickers=test_tickers, limit=5)
        
        logger.info(f"Options Flow Fetcher Result: {json.dumps(result, indent=2)}")
        
        return result.get("status") == "success"
    except Exception as e:
        logger.error(f"Error testing Options Flow fetcher: {str(e)}")
        return False

async def test_fda_calendar_fetcher():
    """Test the FDA Calendar Fetcher"""
    logger.info("=== Testing FDA Calendar Fetcher ===")
    try:
        fetcher = FDACalendarFetcher()
        
        # Test with a shorter time period
        days_ahead = 30
        logger.info(f"Testing FDA Calendar fetcher for next {days_ahead} days")
        
        result = await fetcher.run(days_ahead=days_ahead)
        
        logger.info(f"FDA Calendar Fetcher Result: {json.dumps(result, indent=2)}")
        
        return result.get("status") == "success"
    except Exception as e:
        logger.error(f"Error testing FDA Calendar fetcher: {str(e)}")
        return False

async def test_political_trades_fetcher():
    """Test the Political Trades Fetcher"""
    logger.info("=== Testing Political Trades Fetcher ===")
    try:
        fetcher = PoliticalTradesFetcher()
        
        # Test with a short time period and low limit
        days = 10
        limit = 10
        logger.info(f"Testing Political Trades fetcher for past {days} days with limit {limit}")
        
        result = await fetcher.run(days=days, limit=limit)
        
        logger.info(f"Political Trades Fetcher Result: {json.dumps(result, indent=2)}")
        
        return result.get("status") == "success"
    except Exception as e:
        logger.error(f"Error testing Political Trades fetcher: {str(e)}")
        return False

async def test_economic_reports_fetcher():
    """Test the Economic Reports Fetcher"""
    logger.info("=== Testing Economic Reports Fetcher ===")
    try:
        fetcher = EconomicReportsFetcher()
        
        logger.info("Testing Economic Reports fetcher")
        
        result = await fetcher.run()
        
        logger.info(f"Economic Reports Fetcher Result: {json.dumps(result, indent=2)}")
        
        # Clean up resources
        fetcher.close()
        
        return result.get("status") == "success"
    except Exception as e:
        logger.error(f"Error testing Economic Reports fetcher: {str(e)}")
        return False

async def test_stock_info_fetcher():
    """Test the Stock Info Fetcher"""
    logger.info("=== Testing Stock Info Fetcher ===")
    try:
        fetcher = StockInfoFetcher()
        
        # Test with a limited set of tickers
        test_tickers = ["AAPL", "MSFT", "TSLA"]
        logger.info(f"Testing Stock Info fetcher with tickers: {test_tickers}")
        
        result = await fetcher.run(tickers=test_tickers)
        
        logger.info(f"Stock Info Fetcher Result: {json.dumps(result, indent=2)}")
        
        return result.get("status") == "success"
    except Exception as e:
        logger.error(f"Error testing Stock Info fetcher: {str(e)}")
        return False

async def main():
    """Run tests for all fetchers"""
    logger.info("Starting to test all new fetchers")
    start_time = time.time()
    
    # Store test results
    results = {}
    
    # Test each fetcher with delay between tests to avoid rate limiting issues
    tests = [
        ("dark_pool", test_dark_pool_fetcher()),
        ("options_flow", test_options_flow_fetcher()),
        ("fda_calendar", test_fda_calendar_fetcher()),
        ("political_trades", test_political_trades_fetcher()),
        ("economic_reports", test_economic_reports_fetcher()),
        ("stock_info", test_stock_info_fetcher())
    ]
    
    for name, test_coro in tests:
        try:
            logger.info(f"Running test for {name}")
            success = await test_coro
            results[name] = "PASSED" if success else "FAILED"
            
            # Add a delay between tests to avoid rate limiting
            await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"Error running test for {name}: {str(e)}")
            results[name] = "ERROR"
    
    # Print summary
    logger.info("===== TEST RESULTS SUMMARY =====")
    for name, result in results.items():
        logger.info(f"{name}: {result}")
    
    # Calculate total execution time
    end_time = time.time()
    execution_time = end_time - start_time
    logger.info(f"Total execution time: {execution_time:.2f} seconds")

    # Return overall success/failure
    return all(result == "PASSED" for result in results.values())

if __name__ == "__main__":
    asyncio.run(main()) 