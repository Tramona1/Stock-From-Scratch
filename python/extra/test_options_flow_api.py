#!/usr/bin/env python3
"""
Options Flow API Test Script

This script tries different approaches to fetch options flow data from
the Unusual Whales API to find a reliable method that doesn't hit 500 errors.
"""

import os
import sys
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("options_flow_test")

def get_api_key() -> str:
    """Get the Unusual Whales API key from environment variables."""
    api_key = os.getenv("API_KEY_UNUSUAL_WHALES")
    if not api_key:
        logger.error("API key not found in environment variables")
        sys.exit(1)
    return api_key

def make_request(url: str, params: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Optional[Dict]:
    """
    Make a request to the API with retries and better error handling.
    
    Args:
        url: The URL to make the request to
        params: Query parameters
        headers: Headers for the request
        
    Returns:
        The JSON response or None if the request failed
    """
    if not headers:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {get_api_key()}"
        }
    
    if not params:
        params = {}
    
    logger.info(f"Making request to {url}")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            # Log the full URL for debugging
            logger.info(f"Full URL: {response.url}")
            
            # If we get a 500 error, try with different parameters
            if response.status_code == 500 and "min_premium" in params:
                logger.warning("Got a 500 error, trying without min_premium")
                params_copy = params.copy()
                del params_copy["min_premium"]
                return make_request(url, params_copy, headers)
            
            # Check if we got a successful response
            response.raise_for_status()
            
            # Parse and return the JSON response
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            if 400 <= response.status_code < 500:
                # Client error, log and return None
                logger.error(f"Client error: {e}")
                logger.error(f"Response content: {response.text}")
                return None
            
            if attempt < max_retries - 1:
                # Server error, retry with exponential backoff
                wait_time = 2 ** attempt
                logger.warning(f"Server error: {e}, retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                # Max retries reached, log and return None
                logger.error(f"Max retries reached for {url}: {e}")
                logger.error(f"Response content: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            # Network error, retry with exponential backoff
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Network error: {e}, retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                # Max retries reached, log and return None
                logger.error(f"Network error for {url}: {e}")
                return None
    
    return None

def test_unusual_options_endpoint():
    """Test the unusual options endpoint which might give us flow data."""
    logger.info("Testing unusual options endpoint")
    
    base_url = "https://api.unusualwhales.com/api"
    endpoint = "unusual_options"
    
    url = f"{base_url}/{endpoint}"
    
    params = {
        "days": 1,
        "limit": 10
    }
    
    response = make_request(url, params)
    
    if response:
        logger.info("Successfully retrieved unusual options data")
        logger.info(f"Response structure: {list(response.keys())}")
        
        if "data" in response:
            if isinstance(response["data"], list):
                logger.info(f"Found {len(response['data'])} unusual options")
                if response["data"]:
                    # Log the first item's structure
                    logger.info("First item structure:")
                    for key, value in response["data"][0].items():
                        logger.info(f"  {key}: {value}")
            else:
                logger.info(f"Data is not a list: {type(response['data'])}")
        
        # Save the response for further inspection
        with open("unusual_options_response.json", "w") as f:
            json.dump(response, f, indent=2)
        logger.info("Saved response to unusual_options_response.json")
    else:
        logger.error("Failed to retrieve unusual options data")

def test_ticker_options_flow_endpoint(ticker="AAPL"):
    """
    Test fetching options flow directly for a ticker.
    This is an alternative approach to fetch flow data without going through contracts.
    """
    logger.info(f"Testing ticker options flow endpoint for {ticker}")
    
    base_url = "https://api.unusualwhales.com/api"
    # Try both with and without 's' at the end
    endpoints = [
        f"ticker/{ticker}/options-flow",
        f"ticker/{ticker}/options_flow",
        f"stock/{ticker}/options-flow",
        f"stock/{ticker}/options_flow"
    ]
    
    params = {
        "days": 1,
        "limit": 10
    }
    
    for endpoint in endpoints:
        logger.info(f"Trying endpoint: {endpoint}")
        url = f"{base_url}/{endpoint}"
        response = make_request(url, params)
        
        if response:
            logger.info(f"Successfully retrieved options flow data from {endpoint}")
            logger.info(f"Response structure: {list(response.keys())}")
            
            # Save the response for further inspection
            with open(f"{ticker}_options_flow_response_{endpoint.replace('/', '_')}.json", "w") as f:
                json.dump(response, f, indent=2)
            logger.info(f"Saved response to {ticker}_options_flow_response_{endpoint.replace('/', '_')}.json")
            
            # No need to try other endpoints if this one worked
            return
    
    logger.error(f"Failed to retrieve options flow data for {ticker} from any endpoint")

def test_get_flow_endpoint():
    """Test the flow endpoint which might provide recent options flow data."""
    logger.info("Testing flow endpoint")
    
    base_url = "https://api.unusualwhales.com/api"
    endpoints = ["flow", "flows", "options-flow", "options_flow"]
    
    params = {
        "days": 1,
        "limit": 10
    }
    
    for endpoint in endpoints:
        logger.info(f"Trying endpoint: {endpoint}")
        url = f"{base_url}/{endpoint}"
        response = make_request(url, params)
        
        if response:
            logger.info(f"Successfully retrieved flow data from {endpoint}")
            logger.info(f"Response structure: {list(response.keys())}")
            
            # Save the response for further inspection
            with open(f"flow_response_{endpoint}.json", "w") as f:
                json.dump(response, f, indent=2)
            logger.info(f"Saved response to flow_response_{endpoint}.json")
            
            # No need to try other endpoints if this one worked
            return
    
    logger.error("Failed to retrieve flow data from any endpoint")

def main():
    """Run various tests to find a reliable way to get options flow data."""
    logger.info("Starting options flow API tests")
    
    # Test getting unusual options
    test_unusual_options_endpoint()
    
    # Test getting ticker-specific options flow
    test_ticker_options_flow_endpoint("AAPL")
    test_ticker_options_flow_endpoint("SPY")
    
    # Test getting general flow data
    test_get_flow_endpoint()
    
    logger.info("Completed options flow API tests")

if __name__ == "__main__":
    main() 