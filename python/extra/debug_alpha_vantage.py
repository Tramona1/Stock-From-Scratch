#!/usr/bin/env python3
"""
Alpha Vantage API Debug Script

This script makes a direct API call to Alpha Vantage's options data endpoint
and prints the full response for debugging purposes.
"""

import os
import json
import requests
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("alpha_vantage_debug")

def get_api_key():
    """Get the Alpha Vantage API key from environment variables."""
    api_key = os.getenv("API_KEY_ALPHA_VANTAGE")
    if not api_key:
        logger.error("No Alpha Vantage API key found in environment variables")
        return None
    
    logger.info(f"Alpha Vantage API key found: {api_key[:4]}...{api_key[-4:]}")
    return api_key

def test_options_endpoint(ticker="AAPL"):
    """Test the options endpoint directly."""
    api_key = get_api_key()
    if not api_key:
        return
    
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "REALTIME_OPTIONS",
        "symbol": ticker,
        "apikey": api_key
    }
    
    logger.info(f"Making request to {url} for {ticker} options data")
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Print the raw response
        logger.info("API Response:")
        print(json.dumps(data, indent=4))
        
        # Check for common issues
        if "Error Message" in data:
            logger.error(f"API Error: {data['Error Message']}")
        elif "Information" in data:
            logger.warning(f"API Information: {data['Information']}")
        elif "Note" in data:
            logger.warning(f"API Note: {data['Note']}")
        
        # Check if options data is present
        if "options" in data:
            logger.info(f"Found {len(data['options'])} option expirations")
            for expiration in data["options"]:
                logger.info(f"Expiration {expiration.get('expiration_date')}: {len(expiration.get('options', []))} contracts")
        else:
            logger.warning("No options data found in the response")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error making request: {str(e)}")

def test_time_series_endpoint(ticker="AAPL"):
    """Test a basic endpoint to verify API key works."""
    api_key = get_api_key()
    if not api_key:
        return
    
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": ticker,
        "outputsize": "compact",
        "apikey": api_key
    }
    
    logger.info(f"Making request to {url} for basic {ticker} daily data")
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for common issues
        if "Error Message" in data:
            logger.error(f"API Error: {data['Error Message']}")
            return
        elif "Information" in data:
            logger.warning(f"API Information: {data['Information']}")
        elif "Note" in data:
            logger.warning(f"API Note: {data['Note']}")
        
        # Check if time series data is present
        if "Time Series (Daily)" in data:
            dates = list(data["Time Series (Daily)"].keys())
            logger.info(f"API key is working! Found daily data for {len(dates)} days.")
            logger.info(f"Most recent date: {dates[0]}")
        else:
            logger.warning("No time series data found in the response")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error making request: {str(e)}")

def main():
    """Run the debug tests."""
    logger.info("Starting Alpha Vantage API debug")
    
    # First test a basic endpoint to verify the API key works
    test_time_series_endpoint()
    
    # Then test the options endpoint
    test_options_endpoint("AAPL")
    
    # Try with another popular ticker
    test_options_endpoint("SPY")
    
    logger.info("Debug tests completed")

if __name__ == "__main__":
    main() 