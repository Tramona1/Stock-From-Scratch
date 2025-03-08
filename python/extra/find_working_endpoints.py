#!/usr/bin/env python3
"""
Focused Unusual Whales API Endpoint Test

This script tests only the endpoints that showed success in our previous tests
and explores related endpoints for retrieving options flow data.
"""

import os
import json
import logging
import requests
import time
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("api_test")

def get_api_key():
    """Get the Unusual Whales API key from environment variables."""
    # Try different environment variable names
    for key_name in ["API_KEY_UNUSUAL_WHALES", "UNUSUAL_WHALES_API_KEY", "UW_API_KEY"]:
        api_key = os.getenv(key_name)
        if api_key:
            logger.info(f"Found API key in {key_name}")
            return api_key
            
    logger.error("API key not found in any environment variable")
    raise ValueError("API key not found")

def test_endpoint(endpoint, params=None, description=""):
    """Test a specific API endpoint."""
    api_key = get_api_key()
    base_url = "https://api.unusualwhales.com"
    
    # If endpoint doesn't start with '/', add it
    if not endpoint.startswith('/'):
        endpoint = f"/{endpoint}"
        
    url = f"{base_url}{endpoint}"
    
    # Setup headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Default parameters
    if params is None:
        params = {}
    
    logger.info(f"Testing {description}: {url}")
    logger.info(f"Parameters: {params}")
    
    try:
        response = requests.get(url, headers=headers, params=params)
        status = response.status_code
        logger.info(f"Status code: {status}")
        
        # Try to get response as JSON
        try:
            data = response.json()
            logger.info(f"Response is valid JSON")
            
            # Save the response to a file for inspection
            os.makedirs("logs", exist_ok=True)
            filename = f"logs/response_{endpoint.replace('/', '_')}.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Response saved to {filename}")
            
            # Print a sample of the data structure
            if isinstance(data, dict) and "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
                sample = data["data"][0]
                logger.info(f"Sample data structure: {json.dumps(sample, indent=2)[:500]}...")
                
                # Return the data and the status for further processing
                return True, data, status
            else:
                logger.info(f"No data items found in response")
                return True, data, status
        except ValueError:
            logger.info(f"Response is not valid JSON: {response.text[:100]}...")
            return False, response.text, status
            
    except Exception as e:
        logger.error(f"Error testing endpoint: {str(e)}")
        return False, str(e), 0

def extract_contract_id(contract):
    """Extract contract ID from various possible field names in the contract data."""
    for field in ["id", "contractId", "contract_id", "option_id", "symbol", "option_symbol"]:
        if field in contract and contract[field]:
            return contract[field]
    return None

def main():
    """Test working API endpoints based on previous findings."""
    logger.info("Starting focused API endpoint tests")
    
    # Test ticker-specific option contracts endpoint (known to work)
    tickers = ["AAPL", "SPY", "MSFT", "TSLA", "NVDA"]
    all_contracts = {}
    
    for ticker in tickers:
        endpoint = f"/api/stock/{ticker}/option-contracts"
        success, data, status = test_endpoint(endpoint, params={"limit": 10}, 
                                  description=f"Option contracts for {ticker}")
        
        if success and status == 200 and isinstance(data, dict) and "data" in data and data["data"]:
            logger.info(f"✅ Successfully retrieved {len(data['data'])} option contracts for {ticker}")
            all_contracts[ticker] = data["data"]
            
            # Extract first contract ID for flow testing
            first_contract = data["data"][0]
            contract_id = extract_contract_id(first_contract)
            
            if contract_id:
                logger.info(f"Found contract ID: {contract_id} for {ticker}")
                
                # Test option flow endpoints with different patterns
                flow_patterns = [
                    f"/api/stock/{ticker}/option/{contract_id}/flow",
                    f"/api/option/{contract_id}/flow",
                    f"/api/option-contract/{contract_id}/flow",
                    f"/api/option-flow/{contract_id}",
                    f"/api/options/flow/{contract_id}",
                    f"/api/v1/option/{contract_id}/flow", 
                    f"/api/v2/option/{contract_id}/flow",
                    # Try without contract ID, just ticker
                    f"/api/stock/{ticker}/option-flow",
                    f"/api/ticker/{ticker}/option-flow"
                ]
                
                for pattern in flow_patterns:
                    flow_success, flow_data, flow_status = test_endpoint(
                        pattern,
                        params={"limit": 5},
                        description=f"Flow data using pattern {pattern}"
                    )
                    
                    if flow_success and flow_status == 200 and isinstance(flow_data, dict) and "data" in flow_data and flow_data["data"]:
                        logger.info(f"✅ WORKING FLOW ENDPOINT: {pattern}")
                    
                    # Add slight delay to avoid rate limiting
                    time.sleep(1)
            else:
                logger.warning(f"Could not extract contract ID from the first contract for {ticker}")
        
        # Slight delay to avoid rate limiting
        time.sleep(2)
    
    # Test general flow endpoints that don't require a specific contract
    general_patterns = [
        "/api/option-flow",
        "/api/options/flow", 
        "/api/option/flow",
        "/api/flow/recent",
        "/api/flow/latest",
        "/api/unusual-options",
        "/api/unusual/options",
        "/api/unusual_options"
    ]
    
    for pattern in general_patterns:
        success, data, status = test_endpoint(
            pattern,
            params={"limit": 5, "days": 1},
            description=f"General flow data using pattern {pattern}"
        )
        
        if success and status == 200 and isinstance(data, dict) and "data" in data and data["data"]:
            logger.info(f"✅ WORKING GENERAL FLOW ENDPOINT: {pattern}")
        
        # Slight delay to avoid rate limiting
        time.sleep(1)
    
    logger.info("Completed focused API endpoint tests")

if __name__ == "__main__":
    main() 