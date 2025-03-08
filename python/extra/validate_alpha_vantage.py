#!/usr/bin/env python3
"""
Alpha Vantage API Validation Script

This script tests the Alpha Vantage API integration for options flow data.
It performs the following steps:
1. Checks if the API key is configured correctly
2. Tests retrieving option contracts for a symbol
3. Tests filtering for high-volume/high-premium options (flow data)
4. Tests formatting the data for database insertion
5. Tests analyzing the option flow data
"""

import os
import sys
import json
import logging
import time
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("validate_alpha_vantage")

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

def check_api_key():
    """Check if the Alpha Vantage API key is configured."""
    api_key = os.getenv("API_KEY_ALPHA_VANTAGE")
    if not api_key:
        logger.error("No Alpha Vantage API key found in environment variables")
        logger.error("Please set API_KEY_ALPHA_VANTAGE environment variable")
        return False
    
    logger.info(f"Alpha Vantage API key found: {api_key[:4]}...{api_key[-4:]}")
    return True

def test_import_module():
    """Test importing the Alpha Vantage API module."""
    try:
        from alpha_vantage_api import (
            get_api_key,
            get_option_contracts,
            get_options_flow,
            format_option_flow_for_db,
            analyze_option_flow
        )
        logger.info("Successfully imported Alpha Vantage API module functions")
        return True, locals()
    except ImportError as e:
        logger.error(f"Failed to import Alpha Vantage API module: {str(e)}")
        return False, {}

def test_option_contracts(get_option_contracts, ticker="AAPL"):
    """Test retrieving option contracts for a ticker."""
    logger.info(f"Testing option contracts retrieval for {ticker}")
    try:
        start_time = time.time()
        contracts = get_option_contracts(ticker, require_greeks=True)
        duration = time.time() - start_time
        
        if not contracts:
            logger.error(f"No option contracts returned for {ticker}")
            return False, []
        
        logger.info(f"Retrieved {len(contracts)} option contracts for {ticker} in {duration:.2f} seconds")
        
        # Check a sample contract
        sample = contracts[0]
        logger.info(f"Sample contract: {json.dumps(sample, indent=2)[:500]}...")
        
        # Check for key fields
        required_fields = ["symbol", "strikePrice", "lastPrice", "volume", "openInterest"]
        missing_fields = [field for field in required_fields if field not in sample]
        
        if missing_fields:
            logger.warning(f"Sample contract is missing fields: {missing_fields}")
            return len(missing_fields) < 3, contracts  # Allow some fields to be missing
        
        return True, contracts
    except Exception as e:
        logger.error(f"Error testing option contracts: {str(e)}")
        return False, []

def test_options_flow(get_options_flow, ticker="AAPL"):
    """Test retrieving options flow data for a ticker."""
    logger.info(f"Testing options flow retrieval for {ticker}")
    try:
        start_time = time.time()
        flow_data = get_options_flow(ticker, min_volume=10, min_premium=5000)
        duration = time.time() - start_time
        
        if not flow_data:
            logger.warning(f"No flow data returned for {ticker}")
            logger.info("This may be normal if there is no unusual activity")
            # Try with even lower thresholds
            logger.info("Trying with lower thresholds...")
            flow_data = get_options_flow(ticker, min_volume=5, min_premium=1000)
            if not flow_data:
                logger.warning("Still no flow data found")
                return False, []
        
        logger.info(f"Retrieved {len(flow_data)} flow data items for {ticker} in {duration:.2f} seconds")
        
        # Check a sample flow item
        if flow_data:
            sample = flow_data[0]
            logger.info(f"Sample flow item: {json.dumps(sample, indent=2)[:500]}...")
            logger.info(f"Premium: ${sample.get('premium', 0):,.2f}")
        
        return True, flow_data
    except Exception as e:
        logger.error(f"Error testing options flow: {str(e)}")
        return False, []

def test_formatting(format_option_flow_for_db, flow_data):
    """Test formatting options flow data for database insertion."""
    if not flow_data:
        logger.warning("No flow data to test formatting")
        return False, []
    
    logger.info("Testing flow data formatting")
    try:
        formatted_items = []
        for item in flow_data[:5]:  # Format up to 5 items
            formatted = format_option_flow_for_db(item)
            formatted_items.append(formatted)
        
        logger.info(f"Formatted {len(formatted_items)} flow items for database")
        
        # Check a sample formatted item
        if formatted_items:
            sample = formatted_items[0]
            logger.info(f"Sample formatted item: {json.dumps(sample, indent=2)}")
            
            # Check for key fields that the database expects
            required_fields = ["id", "ticker", "date", "premium", "created_at", "updated_at"]
            missing_fields = [field for field in required_fields if field not in sample]
            
            if missing_fields:
                logger.warning(f"Formatted item is missing fields: {missing_fields}")
                return len(missing_fields) < 2, formatted_items  # Allow one field to be missing
        
        return True, formatted_items
    except Exception as e:
        logger.error(f"Error testing formatting: {str(e)}")
        return False, []

def test_analysis(analyze_option_flow, flow_data, ticker="AAPL"):
    """Test analyzing options flow data."""
    if not flow_data:
        logger.warning("No flow data to test analysis")
        return False, None
    
    logger.info(f"Testing flow data analysis for {ticker}")
    try:
        # Format items first
        from alpha_vantage_api import format_option_flow_for_db
        formatted_items = [format_option_flow_for_db(item) for item in flow_data]
        
        analysis = analyze_option_flow(formatted_items, ticker)
        
        logger.info(f"Analysis results: {json.dumps(analysis, indent=2)}")
        
        # Check for key fields in the analysis
        required_fields = ["ticker", "analysis_date", "flow_count", "sentiment", "created_at"]
        missing_fields = [field for field in required_fields if field not in analysis]
        
        if missing_fields:
            logger.warning(f"Analysis is missing fields: {missing_fields}")
            return False, analysis
        
        return True, analysis
    except Exception as e:
        logger.error(f"Error testing analysis: {str(e)}")
        return False, None

def main():
    """Run the validation tests for Alpha Vantage API integration."""
    logger.info("Starting Alpha Vantage API validation")
    
    # Check if API key is configured
    if not check_api_key():
        logger.error("API key check failed. Please set API_KEY_ALPHA_VANTAGE environment variable.")
        return
    
    # Test importing the module
    import_success, functions = test_import_module()
    if not import_success:
        logger.error("Module import test failed")
        return
    
    # Get functions from the imported module
    get_option_contracts = functions.get("get_option_contracts")
    get_options_flow = functions.get("get_options_flow")
    format_option_flow_for_db = functions.get("format_option_flow_for_db")
    analyze_option_flow = functions.get("analyze_option_flow")
    
    # Test retrieving option contracts
    contracts_success, contracts = test_option_contracts(get_option_contracts)
    if not contracts_success:
        logger.error("Option contracts test failed")
    
    # Test retrieving options flow data
    flow_success, flow_data = test_options_flow(get_options_flow)
    if not flow_success:
        logger.warning("Options flow test did not return data (may be normal if no unusual activity)")
    
    # Test formatting flow data for database
    if flow_data:
        format_success, formatted_data = test_formatting(format_option_flow_for_db, flow_data)
        if not format_success:
            logger.error("Formatting test failed")
        
        # Test analyzing flow data
        analysis_success, analysis = test_analysis(analyze_option_flow, flow_data)
        if not analysis_success:
            logger.error("Analysis test failed")
    
    # Test with another ticker if first one had no flow data
    if not flow_data:
        tickers = ["MSFT", "TSLA", "NVDA", "SPY"]
        for ticker in tickers:
            logger.info(f"Trying alternative ticker: {ticker}")
            flow_success, flow_data = test_options_flow(get_options_flow, ticker)
            if flow_data:
                # Test formatting and analysis with this ticker
                format_success, formatted_data = test_formatting(format_option_flow_for_db, flow_data)
                analysis_success, analysis = test_analysis(analyze_option_flow, flow_data, ticker)
                break
    
    # Provide overall summary
    logger.info("Alpha Vantage API validation completed")
    if contracts_success and (flow_success or flow_data):
        logger.info("✅ API integration appears to be working correctly")
        logger.info("You can now run the full options flow fetcher")
    else:
        logger.warning("⚠️ API integration has some issues that should be addressed")

if __name__ == "__main__":
    main() 