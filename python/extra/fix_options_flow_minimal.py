#!/usr/bin/env python3
"""
Minimal version of options flow fetcher functions.

This module provides minimal implementations of functions for fetching and
formatting options flow data from the Unusual Whales API. It focuses on
using only essential fields that are guaranteed to be in the schema.
"""

import os
import sys
import json
import time
import logging
import requests
import uuid
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def get_api_key() -> str:
    """Get the Unusual Whales API key from environment variables."""
    api_key = os.getenv("API_KEY_UNUSUAL_WHALES") or os.getenv("UNUSUAL_WHALES_API_KEY") or os.getenv("UW_API_KEY")
    if not api_key:
        logger.error("Unusual Whales API key not found in environment variables")
        raise ValueError("API key not found. Set API_KEY_UNUSUAL_WHALES environment variable")
    return api_key

def make_api_request(endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make a request to the Unusual Whales API."""
    api_key = get_api_key()
    base_url = "https://api.unusualwhales.com/api"
    url = f"{base_url}/{endpoint}"
    
    # Setup headers with Bearer token
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Ensure params is initialized
    if params is None:
        params = {}
    
    logger.info(f"Making request to {url}")
    
    retries = 3
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if attempt < retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Request failed with {e}, retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Error making request to {url}: {e}")
                logger.error(f"Response content: {response.text}")
                raise
        except Exception as e:
            logger.error(f"Error making request to {url}: {e}")
            if attempt < retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise

def get_ticker_option_contracts(ticker: str, **kwargs) -> List[Dict[str, Any]]:
    """
    Get option contracts for a specific ticker.
    
    Args:
        ticker: The ticker symbol
        **kwargs: Additional parameters to pass to the API
    
    Returns:
        List of option contracts
    """
    logger.info(f"Fetching option contracts for {ticker}")
    
    # Set defaults for params
    params = {}
    
    # Add any additional params
    for key, value in kwargs.items():
        params[key] = value
    
    try:
        data = make_api_request(f"stock/{ticker}/option-contracts", params)
        contracts = data.get("data", [])
        logger.info(f"Retrieved {len(contracts)} option contracts for {ticker}")
        return contracts
    except Exception as e:
        logger.error(f"Failed to fetch option contracts for {ticker}: {str(e)}")
        return []

def get_option_contract_flow(option_symbol: str, **kwargs) -> List[Dict[str, Any]]:
    """
    Get flow data for a specific option contract.
    
    Args:
        option_symbol: The option contract symbol or ID
        **kwargs: Additional parameters to pass to the API
    
    Returns:
        List of flow data items
    """
    logger.info(f"Fetching flow data for option contract {option_symbol}")
    
    # Set defaults for params
    params = {}
    
    # Add any additional params
    for key, value in kwargs.items():
        params[key] = value
    
    try:
        data = make_api_request(f"option-contract/{option_symbol}/flow", params)
        flow_data = data.get("data", [])
        logger.info(f"Retrieved {len(flow_data)} flow data items for {option_symbol}")
        return flow_data
    except Exception as e:
        logger.error(f"Failed to fetch flow data for {option_symbol}: {str(e)}")
        return []

def format_option_flow_for_db(flow_item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format option flow data for database storage, using only essential fields.
    
    Args:
        flow_item: Raw option flow data
    
    Returns:
        Formatted option flow data that matches the database schema
    """
    now = datetime.now().isoformat()
    
    # Extract basic fields with fallbacks for missing data
    formatted = {
        "id": flow_item.get("id", str(hash(json.dumps(flow_item, sort_keys=True)))),
        "ticker": flow_item.get("ticker", flow_item.get("symbol", flow_item.get("underlying_symbol", ""))),
        "created_at": flow_item.get("created_at", now),
        "updated_at": now
    }
    
    # Add date if available (required by schema)
    if "date" in flow_item:
        formatted["date"] = flow_item["date"]
    elif "executed_at" in flow_item:
        formatted["date"] = flow_item["executed_at"]
    elif "timestamp" in flow_item:
        formatted["date"] = flow_item["timestamp"]
    else:
        formatted["date"] = now
    
    # Optional fields that map directly to the schema
    schema_fields = {
        "contract_id": ["contract_id", "option_id", "id"],
        "strike_price": ["strike_price", "strike"],
        "expiration_date": ["expiration_date", "expiration", "expiry"],
        "option_type": ["option_type", "type", "contract_type"],
        "sentiment": ["sentiment"],
        "volume": ["volume"],
        "open_interest": ["open_interest", "oi"],
        "implied_volatility": ["implied_volatility", "iv"],
        "premium": ["premium", "total_premium"],
        "unusual_score": ["unusual_score", "score"],
        "trade_type": ["trade_type", "type"]
    }
    
    # Map fields from input to schema
    for schema_field, possible_input_fields in schema_fields.items():
        for input_field in possible_input_fields:
            if input_field in flow_item and flow_item[input_field] is not None:
                formatted[schema_field] = flow_item[input_field]
                break
    
    # Include raw data as JSON
    formatted["raw_data"] = json.dumps(flow_item)
    
    logger.info(f"Formatted flow item with ID: {formatted['id']}")
    return formatted

def analyze_option_flow(flow_data: List[Dict], ticker: str) -> Dict[str, Any]:
    """
    Analyze option flow data to identify patterns and sentiment.
    
    Args:
        flow_data: List of option flow data items
        ticker: The ticker symbol
    
    Returns:
        Analysis results for database storage that match the schema
    """
    logger.info(f"Analyzing {len(flow_data)} flow data items for {ticker}")
    
    # Initialize counters
    bullish_count = 0
    bearish_count = 0
    high_premium_count = 0
    pre_earnings_count = 0
    total_premium = 0
    bullish_premium = 0
    bearish_premium = 0
    
    # Analyze each flow item
    for item in flow_data:
        sentiment = item.get("sentiment", "").lower()
        
        # Handle premium which might be string or number
        premium = item.get("premium", 0)
        if isinstance(premium, str) and premium.strip():
            try:
                premium = float(premium.replace(',', '').strip())
            except (ValueError, TypeError):
                premium = 0
        elif not isinstance(premium, (int, float)):
            premium = 0
        
        # Track sentiment counts
        if sentiment == "bullish":
            bullish_count += 1
            bullish_premium += premium
        elif sentiment == "bearish":
            bearish_count += 1
            bearish_premium += premium
        
        # Count trades with premium over $100k
        if premium and premium > 100000:
            high_premium_count += 1
        
        # Count pre-earnings activity (would need more logic in real implementation)
        if "earnings" in str(item.get("tags", "")).lower() or "earnings" in str(item.get("note", "")).lower():
            pre_earnings_count += 1
        
        # Sum up total premium
        if premium:
            total_premium += premium
    
    # Determine overall sentiment
    sentiment = "neutral"
    if bullish_count > bearish_count and bullish_premium > bearish_premium:
        sentiment = "bullish"
    elif bearish_count > bullish_count and bearish_premium > bullish_premium:
        sentiment = "bearish"
    
    # Format the current date properly for database
    today = datetime.now().date().isoformat()
    now = datetime.now().isoformat()
    
    # Generate analysis results matching the schema
    analysis = {
        "id": str(uuid.uuid4()),
        "ticker": ticker,
        "analysis_date": today,
        "flow_count": len(flow_data),
        "bullish_count": bullish_count,
        "bearish_count": bearish_count,
        "high_premium_count": high_premium_count,
        "pre_earnings_count": pre_earnings_count,
        "total_premium": total_premium,
        "bullish_premium": bullish_premium,
        "bearish_premium": bearish_premium,
        "sentiment": sentiment,
        "raw_data": json.dumps({"sample_items": flow_data[:3] if len(flow_data) > 3 else flow_data}),
        "created_at": now,
        "updated_at": now
    }
    
    logger.info(f"Analysis complete: {bullish_count} bullish, {bearish_count} bearish")
    return analysis

def main():
    """Test the functions with a sample ticker."""
    ticker = "AAPL"
    logger.info(f"Testing with ticker: {ticker}")
    
    try:
        # Check if API key is set
        get_api_key()
        
        # Test getting option contracts
        contracts = get_ticker_option_contracts(ticker, limit=10)
        if contracts and len(contracts) > 0:
            logger.info(f"Found {len(contracts)} option contracts")
            
            # Test getting flow data for the first contract
            contract_id = contracts[0].get("contractId", contracts[0].get("id"))
            if contract_id:
                logger.info(f"Getting flow data for contract ID: {contract_id}")
                flow_data = get_option_contract_flow(contract_id, limit=10)
                
                if flow_data and len(flow_data) > 0:
                    logger.info(f"Found {len(flow_data)} flow data items")
                    
                    # Test formatting flow data
                    formatted_data = [format_option_flow_for_db(item) for item in flow_data]
                    logger.info(f"Formatted {len(formatted_data)} flow data items")
                    
                    # Test analyzing flow data
                    analysis = analyze_option_flow(formatted_data, ticker)
                    logger.info(f"Analysis: {json.dumps(analysis, indent=2)}")
                    
                else:
                    logger.warning(f"No flow data found for contract ID: {contract_id}")
            else:
                logger.warning("Contract ID not found in the first contract")
        else:
            logger.warning(f"No option contracts found for {ticker}")
    
    except Exception as e:
        logger.error(f"Error during testing: {str(e)}")

if __name__ == "__main__":
    main() 