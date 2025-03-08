#!/usr/bin/env python3
"""
Simple test script to find working Unusual Whales API endpoints.
"""

import os
import json
import logging
import requests
import time
from dotenv import load_dotenv

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
            filename = f"logs/response_{endpoint.replace('/', '_')}.json"
            os.makedirs("logs", exist_ok=True)
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Response saved to {filename}")
            return True, data
        except ValueError:
            logger.info(f"Response is not valid JSON: {response.text[:100]}...")
            return False, response.text
            
    except Exception as e:
        logger.error(f"Error testing endpoint: {str(e)}")
        return False, str(e)

def main():
    """Test various Unusual Whales API endpoints."""
    logger.info("Starting API endpoint tests")
    
    # Test base API info
    test_endpoint("/api", description="Base API")
    
    # Test common endpoint patterns for option contracts
    tickers = ["AAPL", "SPY"]
    
    for ticker in tickers:
        # Test different patterns for getting option contracts
        patterns = [
            f"/api/stock/{ticker}/option-contracts",
            f"/api/ticker/{ticker}/option-contracts",
            f"/api/v1/stock/{ticker}/option-contracts",
            f"/api/v1/ticker/{ticker}/option-contracts",
            f"/api/v2/stock/{ticker}/option-contracts",
            f"/api/v2/ticker/{ticker}/option-contracts",
            f"/api/options/contracts/{ticker}",
            f"/api/options/{ticker}/contracts",
            f"/api/stock/{ticker}/contracts",
            f"/api/option/chain/{ticker}"
        ]
        
        for pattern in patterns:
            success, data = test_endpoint(pattern, params={"limit": 5}, 
                                       description=f"Option contracts for {ticker}")
            if success and isinstance(data, dict) and data.get("data"):
                logger.info(f"✅ WORKING ENDPOINT FOUND: {pattern}")
                
                # If we found contracts, try to get flow data for the first one
                contracts = data.get("data", [])
                if contracts and len(contracts) > 0:
                    contract = contracts[0]
                    
                    # Try to find ID or symbol from the contract
                    contract_id = None
                    for key in ["id", "contractId", "contract_id", "symbol", "option_symbol"]:
                        if key in contract:
                            contract_id = contract[key]
                            break
                    
                    if contract_id:
                        # Test flow patterns
                        flow_patterns = [
                            f"/api/option-contract/{contract_id}/flow",
                            f"/api/option/{contract_id}/flow",
                            f"/api/v1/option-contract/{contract_id}/flow",
                            f"/api/v1/option/{contract_id}/flow",
                            f"/api/v2/option-contract/{contract_id}/flow",
                            f"/api/v2/option/{contract_id}/flow",
                            f"/api/flow/option/{contract_id}",
                            f"/api/options/flow/{contract_id}"
                        ]
                        
                        for flow_pattern in flow_patterns:
                            success, flow_data = test_endpoint(flow_pattern, params={"limit": 5},
                                                          description=f"Flow data for contract {contract_id}")
                            if success and isinstance(flow_data, dict) and flow_data.get("data"):
                                logger.info(f"✅ WORKING FLOW ENDPOINT FOUND: {flow_pattern}")
            
            # Add a small delay to avoid rate limits
            time.sleep(1)
    
    # Also try general flow endpoints
    flow_patterns = [
        "/api/flow",
        "/api/flows",
        "/api/options-flow",
        "/api/options/flow",
        "/api/v1/flow",
        "/api/v1/options-flow",
        "/api/v2/flow",
        "/api/v2/options-flow"
    ]
    
    for pattern in flow_patterns:
        success, data = test_endpoint(pattern, params={"limit": 5},
                                   description="General flow data")
        if success and isinstance(data, dict) and data.get("data"):
            logger.info(f"✅ WORKING GENERAL FLOW ENDPOINT FOUND: {pattern}")
        
        # Add a small delay to avoid rate limits
        time.sleep(1)
    
    logger.info("Completed API endpoint tests")

if __name__ == "__main__":
    main() 