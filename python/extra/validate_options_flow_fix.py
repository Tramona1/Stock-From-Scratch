#!/usr/bin/env python3
"""
Options Flow Fix Validation Script

This script tests the minimal fix for options flow by:
1. Importing the minimal options flow functions
2. Making test API calls
3. Formatting the data for database insertion
4. Testing database insertion if API calls are successful
"""

import os
import sys
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables first
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("validate_options_flow")

# Add the parent directory to the path so we can import our fix modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import fixed functions
try:
    from fix_options_flow_minimal import (
        get_ticker_option_contracts,
        get_option_contract_flow,
        format_option_flow_for_db,
        analyze_option_flow
    )
    logger.info("Successfully imported minimal options flow fix functions")
except ImportError:
    logger.error("Failed to import minimal options flow fix functions")
    sys.exit(1)

def initialize_supabase() -> Client:
    """Initialize Supabase client"""
    # Environment variables already loaded at the top
    
    supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("Supabase URL or key not found in environment variables")
        sys.exit(1)
    
    return create_client(supabase_url, supabase_key)

def test_api_calls():
    """Test API calls to get options flow data"""
    logger.info("Testing API calls...")
    
    # Check if API key is set
    api_key = os.getenv("API_KEY_UNUSUAL_WHALES") or os.getenv("UNUSUAL_WHALES_API_KEY") or os.getenv("UW_API_KEY")
    if not api_key:
        logger.error("API key not found in environment variables")
        return None, None
    
    # Test ticker
    test_ticker = "AAPL"
    
    try:
        # Get option contracts
        logger.info(f"Getting option contracts for {test_ticker}")
        contracts = get_ticker_option_contracts(test_ticker)
        
        if not contracts or len(contracts) == 0:
            logger.warning(f"No option contracts found for {test_ticker}")
            return None, None
        
        logger.info(f"Found {len(contracts)} option contracts for {test_ticker}")
        
        # Get flow data for the first contract
        contract_id = contracts[0].get('option_symbol')
        if not contract_id:
            logger.warning("option_symbol not found in contract response")
            return None, None
        
        logger.info(f"Getting flow data for option symbol: {contract_id}")
        flow_data = get_option_contract_flow(contract_id)
        
        if not flow_data:
            logger.warning(f"No flow data found for option symbol: {contract_id}")
            return None, None
            
        logger.info(f"Successfully retrieved flow data")
        
        return contracts, flow_data
    
    except Exception as e:
        logger.error(f"Error testing API calls: {str(e)}")
        return None, None

def test_data_formatting(contracts, flow_data):
    """Test formatting flow data for database insertion"""
    logger.info("Testing data formatting...")
    
    if not contracts or not flow_data:
        logger.warning("No data to format")
        return None
    
    try:
        formatted_data = []
        
        # Format each flow item
        if isinstance(flow_data, list):
            for item in flow_data:
                formatted = format_option_flow_for_db(item)
                formatted_data.append(formatted)
        else:
            # If flow_data is a single dict, format it
            formatted = format_option_flow_for_db(flow_data)
            formatted_data.append(formatted)
        
        logger.info(f"Successfully formatted {len(formatted_data)} flow items")
        
        # Test analysis function
        test_ticker = "AAPL"
        analysis = analyze_option_flow(formatted_data, test_ticker)
        logger.info(f"Successfully analyzed flow data: {json.dumps(analysis, indent=2)}")
        
        return formatted_data
    
    except Exception as e:
        logger.error(f"Error formatting data: {str(e)}")
        return None

def test_database_insertion(formatted_data):
    """Test inserting formatted data into the database"""
    logger.info("Testing database insertion...")
    
    if not formatted_data:
        logger.warning("No formatted data to insert")
        return
    
    try:
        supabase = initialize_supabase()
        
        # Test insertion into options_flow table (raw flow data)
        logger.info("Testing insertion into options_flow table")
        test_item = formatted_data[0]
        
        # Add a unique ID to avoid conflicts
        test_item['id'] = str(uuid.uuid4())
        
        # Try to insert the item
        logger.info(f"Inserting test item into options_flow table")
        result = supabase.table("options_flow").insert(test_item).execute()
        
        # Check result
        if result.data:
            logger.info("Successfully inserted test item into options_flow table")
        else:
            logger.error(f"Failed to insert test item into options_flow table: {result.error}")
        
        # Test insertion into option_flow_data table (analysis)
        logger.info("Testing insertion into option_flow_data table")
        
        # Generate analysis for the test data
        test_ticker = "AAPL"
        analysis = analyze_option_flow(formatted_data, test_ticker)
        
        # Try to insert the analysis
        logger.info(f"Inserting analysis into option_flow_data table")
        result = supabase.table("option_flow_data").insert(analysis).execute()
        
        # Check result
        if result.data:
            logger.info("Successfully inserted analysis into option_flow_data table")
        else:
            logger.error(f"Failed to insert analysis into option_flow_data table: {result.error}")
            
    except Exception as e:
        logger.error(f"Error inserting data: {str(e)}")

def main():
    """Main function"""
    logger.info("Starting options flow fix validation")
    
    # Test API calls
    contracts, flow_data = test_api_calls()
    
    # Test data formatting
    if contracts is not None and flow_data is not None:
        formatted_data = test_data_formatting(contracts, flow_data)
        
        # Test database insertion
        if formatted_data:
            test_database_insertion(formatted_data)
    
    logger.info("Options flow fix validation complete")

if __name__ == "__main__":
    main() 