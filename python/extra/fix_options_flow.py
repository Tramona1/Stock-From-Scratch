#!/usr/bin/env python3
"""
Options Flow API Fix

This script provides fixed versions of the Unusual Whales API functions
for options flow data retrieval, based on the updated API documentation.
"""

import os
import sys
import json
import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("fix_options_flow")

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load API key from environment
UW_API_KEY = os.getenv("UNUSUAL_WHALES_API_KEY") or os.getenv("UW_API_KEY")
UW_API_BASE_URL = "https://api.unusualwhales.com/api"

def get_ticker_option_contracts(ticker: str, **kwargs) -> List[Dict[str, Any]]:
    """
    Get option contracts for a specific ticker.
    
    Args:
        ticker: Ticker symbol
        **kwargs: Additional parameters like exclude_zero_vol_chains, vol_greater_oi, etc.
        
    Returns:
        List of option contracts
    """
    if not ticker or not isinstance(ticker, str):
        logger.error(f"Invalid ticker provided: {ticker}")
        return []
    
    url = f"{UW_API_BASE_URL}/stock/{ticker}/option-contracts"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {UW_API_KEY}"
    }
    
    # Add optional query parameters
    params = {}
    if 'exclude_zero_vol_chains' in kwargs:
        params['exclude_zero_vol_chains'] = kwargs['exclude_zero_vol_chains']
    if 'vol_greater_oi' in kwargs:
        params['vol_greater_oi'] = kwargs['vol_greater_oi']
    if 'limit' in kwargs:
        params['limit'] = kwargs['limit']
    if 'option_type' in kwargs:
        params['option_type'] = kwargs['option_type']
    
    try:
        logger.info(f"Fetching option contracts for {ticker}")
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        if "data" in data:
            contracts = data["data"]
            logger.info(f"Retrieved {len(contracts)} option contracts for {ticker}")
            return contracts
        else:
            logger.warning(f"Unexpected response format for {ticker} option contracts")
            return []
    except Exception as e:
        logger.error(f"Error fetching option contracts for {ticker}: {str(e)}")
        if hasattr(response, 'text'):
            logger.error(f"Response: {response.text}")
        return []

def get_option_contract_flow(option_symbol: str, **kwargs) -> List[Dict[str, Any]]:
    """
    Get flow data for a specific option contract.
    
    Args:
        option_symbol: The option symbol in ISO format (e.g., AAPL230526P00167500)
        **kwargs: Additional parameters like min_premium, side, limit, etc.
        
    Returns:
        List of option flow data
    """
    if not option_symbol or not isinstance(option_symbol, str):
        logger.error(f"Invalid option symbol provided: {option_symbol}")
        return []
    
    url = f"{UW_API_BASE_URL}/option-contract/{option_symbol}/flow"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {UW_API_KEY}"
    }
    
    # Add optional query parameters
    params = {}
    if 'min_premium' in kwargs:
        params['min_premium'] = kwargs['min_premium']
    if 'side' in kwargs:
        params['side'] = kwargs['side']
    if 'limit' in kwargs:
        params['limit'] = kwargs['limit']
    if 'date' in kwargs:
        params['date'] = kwargs['date']
    
    try:
        logger.info(f"Fetching flow data for option contract {option_symbol}")
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        if "data" in data:
            flow_data = data["data"]
            logger.info(f"Retrieved {len(flow_data)} flow data points for {option_symbol}")
            return flow_data
        else:
            logger.warning(f"Unexpected response format for option contract {option_symbol} flow")
            return []
    except Exception as e:
        logger.error(f"Error fetching flow for option contract {option_symbol}: {str(e)}")
        if hasattr(response, 'text'):
            logger.error(f"Response: {response.text}")
        return []

def format_option_flow_for_db(flow_item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format option flow data for database storage.
    
    Args:
        flow_item: Raw option flow data item from the API
        
    Returns:
        Formatted option flow data ready for DB insertion
    """
    if not flow_item:
        return {}
    
    try:
        # Format using the fields from the API documentation
        formatted = {
            "id": flow_item.get("id", ""),
            "ticker": flow_item.get("underlying_symbol", ""),
            "date": flow_item.get("executed_at", datetime.now().isoformat()),
            "contract_id": flow_item.get("option_chain_id", ""),
            "strike_price": float(flow_item.get("strike", 0)),
            "expiration_date": flow_item.get("expiry", ""),
            "option_type": flow_item.get("option_type", ""),
            "sentiment": flow_item.get("sentiment", "neutral"),
            "volume": int(flow_item.get("volume", 0)),
            "open_interest": int(flow_item.get("open_interest", 0)),
            "implied_volatility": float(flow_item.get("implied_volatility", 0)),
            "premium": float(flow_item.get("premium", 0)),
            "unusual_score": 0,  # Not provided in the API response
            "trade_type": "",  # Not provided in the API response
            "raw_data": json.dumps(flow_item),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        return formatted
    except Exception as e:
        logger.error(f"Error formatting option flow data: {str(e)}")
        return {}

def analyze_option_flow(flow_data: List[Dict], ticker: str) -> Dict:
    """
    Analyze option flow data to identify patterns and sentiment.
    
    Args:
        flow_data: List of flow data items
        ticker: Ticker symbol
        
    Returns:
        Analysis summary
    """
    if not flow_data:
        return {
            "ticker": ticker,
            "analysis_date": datetime.now().isoformat(),
            "flow_count": 0,
            "sentiment": "neutral",
            "total_premium": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    # Count bullish vs bearish flow
    bullish_count = 0
    bearish_count = 0
    total_premium = 0
    bullish_premium = 0
    bearish_premium = 0
    
    for item in flow_data:
        premium = float(item.get("premium", 0))
        total_premium += premium
        
        tags = item.get("tags", [])
        if "bullish" in tags:
            bullish_count += 1
            bullish_premium += premium
        elif "bearish" in tags:
            bearish_count += 1
            bearish_premium += premium
    
    # Determine overall sentiment
    sentiment = "neutral"
    if bullish_count > bearish_count and bullish_premium > bearish_premium:
        sentiment = "bullish"
    elif bearish_count > bullish_count and bearish_premium > bullish_premium:
        sentiment = "bearish"
    
    analysis = {
        "ticker": ticker,
        "analysis_date": datetime.now().isoformat(),
        "flow_count": len(flow_data),
        "bullish_count": bullish_count,
        "bearish_count": bearish_count,
        "sentiment": sentiment,
        "total_premium": total_premium,
        "bullish_premium": bullish_premium,
        "bearish_premium": bearish_premium,
        "raw_data": json.dumps({"flow_samples": flow_data[:5]}),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    return analysis

def print_usage():
    """Print usage instructions for this script."""
    print("""
Usage: python fix_options_flow.py

This script provides fixed functions for the Unusual Whales API options flow endpoints.
To use these functions, import them into fetch_options_flow.py:

from fix_options_flow import (
    get_ticker_option_contracts, 
    get_option_contract_flow,
    format_option_flow_for_db,
    analyze_option_flow
)

Then update the fetch_option_flow method in the OptionsFlowFetcher class to use these functions.
""")

def main():
    """Main function to demonstrate usage."""
    if not UW_API_KEY:
        logger.error("UNUSUAL_WHALES_API_KEY environment variable is not set")
        print("Please set the UNUSUAL_WHALES_API_KEY environment variable")
        return
    
    print_usage()
    
    # Test a simple API call if the key is available
    ticker = "AAPL"
    try:
        contracts = get_ticker_option_contracts(
            ticker=ticker, 
            exclude_zero_vol_chains=True, 
            limit=5
        )
        
        if contracts:
            logger.info(f"Successfully retrieved {len(contracts)} contracts for {ticker}")
            
            # Try to get flow data for the first contract
            if len(contracts) > 0:
                contract = contracts[0]
                option_symbol = contract.get("option_symbol")
                
                if option_symbol:
                    flow_data = get_option_contract_flow(
                        option_symbol=option_symbol,
                        limit=5,
                        min_premium=10000
                    )
                    
                    if flow_data:
                        logger.info(f"Successfully retrieved {len(flow_data)} flow data points")
                        
                        # Format a sample
                        if len(flow_data) > 0:
                            formatted = format_option_flow_for_db(flow_data[0])
                            logger.info(f"Sample formatted data: {formatted}")
                    else:
                        logger.info(f"No flow data found for {option_symbol}")
        else:
            logger.info(f"No contracts found for {ticker}")
            
    except Exception as e:
        logger.error(f"Error testing API: {str(e)}")

if __name__ == "__main__":
    main() 