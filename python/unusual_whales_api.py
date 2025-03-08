#!/usr/bin/env python3
"""
Unusual Whales API Integration Module
Provides functions for fetching data from the Unusual Whales API
for insider trades, political trades, and analyst sentiment.
"""

import os
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import uuid  # Add this import at the top of the file

import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from requests_ratelimiter import LimiterSession
from dotenv import load_dotenv
from diskcache import Cache

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("unusual_whales_api.log")
    ]
)
logger = logging.getLogger("unusual_whales_api")

# API Configuration
API_BASE_URL = "https://api.unusualwhales.com/api"
API_KEY = os.getenv("API_KEY_UNUSUAL_WHALES")

# Setup cache
cache = Cache(".cache")
CACHE_EXPIRY = 3600  # Cache for 1 hour

# Cache directory
# Create rate-limited session (8 requests per minute)
session = LimiterSession(per_second=0.13)

class UnusualWhalesError(Exception):
    """Custom exception for Unusual Whales API errors"""
    pass

def get_headers() -> Dict[str, str]:
    """Return headers for API requests"""
    if not API_KEY:
        raise UnusualWhalesError("API_KEY_UNUSUAL_WHALES environment variable not set")
    
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def make_request(endpoint: str, params: Dict[str, Any] = None) -> Dict:
    """
    Make a request to the Unusual Whales API with retry logic
    
    Args:
        endpoint: API endpoint to query
        params: Query parameters
        
    Returns:
        Dict: API response
    """
    url = f"{API_BASE_URL}/{endpoint}"
    
    # Generate cache key based on endpoint and params
    cache_key = f"{endpoint}-{json.dumps(params or {})}"
    
    # Check cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.info(f"Using cached data for {endpoint}")
        return cached_data
    
    try:
        logger.info(f"Making request to {url} with params {params}")
        response = session.get(url, headers=get_headers(), params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Cache successful response
        cache.set(cache_key, data, expire=CACHE_EXPIRY)
        
        return data
    except requests.RequestException as e:
        logger.error(f"Error making request to {url}: {str(e)}")
        if hasattr(e.response, 'text'):
            logger.error(f"Response content: {e.response.text}")
        raise UnusualWhalesError(f"API request failed: {str(e)}")

def get_insider_trades(
    days: int = 7,
    symbols: Optional[List[str]] = None,
    transaction_type: Optional[str] = None,
    min_value: Optional[int] = None,
    limit: int = 100
) -> List[Dict]:
    """
    Fetch insider trading data from Unusual Whales
    
    Args:
        days: Number of days to look back
        symbols: List of ticker symbols to filter by
        transaction_type: Filter by transaction type (Purchase, Sale)
        min_value: Minimum transaction value in dollars
        limit: Maximum number of records to return
        
    Returns:
        List[Dict]: List of insider trades
    """
    params = {"days": days, "limit": limit}
    
    if symbols:
        params["symbols"] = ",".join(symbols)
    if transaction_type:
        params["type"] = transaction_type
    if min_value:
        params["min_value"] = min_value
        
    try:
        response = make_request("insider/trades", params)
        return response.get("data", [])
    except Exception as e:
        logger.error(f"Failed to fetch insider trades: {str(e)}")
        raise

def get_political_trades(
    days: int = 30,
    symbols: Optional[List[str]] = None,
    politician: Optional[str] = None,
    party: Optional[str] = None,
    limit: int = 100
) -> List[Dict]:
    """
    Fetch congressional trading data from Unusual Whales
    
    Args:
        days: Number of days to look back
        symbols: List of ticker symbols to filter by
        politician: Filter by politician name
        party: Filter by political party (Democratic, Republican, Independent)
        limit: Maximum number of records to return (max 200)
        
    Returns:
        List[Dict]: List of political trades
    """
    # Convert days to a date for the API
    if days:
        date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    else:
        date = None
    
    # API has a maximum limit of 200
    if limit > 200:
        limit = 200
        logger.warning(f"Political trades API limit capped at 200 (requested {limit})")
    
    params = {"limit": limit}
    
    if date:
        params["date"] = date
    
    if symbols and len(symbols) == 1:
        # API only supports filtering by a single ticker
        params["ticker"] = symbols[0]
    
    if politician:
        # Use the congress-trader endpoint for specific politicians
        params["name"] = politician
        try:
            response = make_request("congress/congress-trader", params)
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Failed to fetch political trades for {politician}: {str(e)}")
            raise
    else:
        # Use the recent-trades endpoint for all trades
        try:
            response = make_request("congress/recent-trades", params)
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Failed to fetch political trades: {str(e)}")
            raise

def get_analyst_ratings(
    days: int = 14,
    symbols: Optional[List[str]] = None,
    action: Optional[str] = None,
    recommendation: Optional[str] = None,
    limit: int = 500
) -> List[Dict]:
    """
    Fetch analyst ratings from the Unusual Whales API
    
    Args:
        days: Number of days to look back (used to filter data after fetching)
        symbols: List of ticker symbols to filter by
        action: Filter by action (initiated, reiterated, downgraded, upgraded, maintained)
        recommendation: Filter by recommendation (buy, hold, sell)
        limit: Maximum number of records to return (max 500)
        
    Returns:
        List[Dict]: List of analyst ratings
    """
    # The new endpoint doesn't accept days parameter directly
    # We'll filter by timestamp after receiving the data
    params = {"limit": min(limit, 500)}  # Ensure limit doesn't exceed API maximum
    
    if symbols and len(symbols) == 1:
        # API only accepts a single ticker
        params["ticker"] = symbols[0]
    
    if action and action.lower() in ["initiated", "reiterated", "downgraded", "upgraded", "maintained"]:
        params["action"] = action.lower()
        
    if recommendation and recommendation.lower() in ["buy", "hold", "sell"]:
        params["recommendation"] = recommendation.lower()
        
    try:
        response = make_request("screener/analysts", params)
        data = response.get("data", [])
        
        # If days parameter was provided, filter by timestamp
        if days > 0:
            cutoff_date = datetime.now() - timedelta(days=days)
            filtered_data = []
            
            for item in data:
                try:
                    timestamp = datetime.strptime(item["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
                    if timestamp >= cutoff_date:
                        filtered_data.append(item)
                except (ValueError, KeyError):
                    # If we can't parse the timestamp, include the item anyway
                    filtered_data.append(item)
                    
            return filtered_data
        
        return data
    except Exception as e:
        logger.error(f"Failed to fetch analyst ratings: {str(e)}")
        raise

def get_unusual_options(
    days: int = 1,
    symbols: Optional[List[str]] = None,
    sentiment: Optional[str] = None,
    min_premium: Optional[int] = None,
    limit: int = 100
) -> List[Dict]:
    """
    Fetch unusual options activity from Unusual Whales
    
    Args:
        days: Number of days to look back
        symbols: List of ticker symbols to filter by
        sentiment: Filter by sentiment (bullish, bearish)
        min_premium: Minimum premium paid in dollars
        limit: Maximum number of records to return
        
    Returns:
        List[Dict]: List of unusual options activity
    """
    params = {"days": days, "limit": limit}
    
    if symbols:
        params["symbols"] = ",".join(symbols)
    if sentiment:
        params["sentiment"] = sentiment
    if min_premium:
        params["min_premium"] = min_premium
        
    try:
        response = make_request("options/unusual", params)
        return response.get("data", [])
    except Exception as e:
        logger.error(f"Failed to fetch unusual options: {str(e)}")
        raise

def get_earnings_data(
    days_forward: int = 7,
    days_backward: int = 7,
    symbols: Optional[List[str]] = None,
    limit: int = 100
) -> List[Dict]:
    """
    Fetch earnings announcements data
    
    Args:
        days_forward: Number of days to look forward for upcoming earnings
        days_backward: Number of days to look back for past earnings
        symbols: List of ticker symbols to filter by
        limit: Maximum number of records to return
        
    Returns:
        List[Dict]: List of earnings announcements
    """
    params = {
        "days_forward": days_forward,
        "days_backward": days_backward,
        "limit": limit
    }
    
    if symbols:
        params["symbols"] = ",".join(symbols)
        
    try:
        response = make_request("earnings/calendar", params)
        return response.get("data", [])
    except Exception as e:
        logger.error(f"Failed to fetch earnings data: {str(e)}")
        raise

def get_market_sentiment() -> Dict:
    """
    Fetch overall market sentiment and indicators
    
    Returns:
        Dict: Market sentiment data
    """
    try:
        response = make_request("market/sentiment")
        return response.get("data", {})
    except Exception as e:
        logger.error(f"Failed to fetch market sentiment: {str(e)}")
        raise

def format_insider_trade_for_db(trade: Dict) -> Dict:
    """Format insider trade data for database insertion"""
    return {
        "filing_id": trade.get("filing_id", ""),
        "symbol": trade.get("symbol", ""),
        "company_name": trade.get("company_name", ""),
        "insider_name": trade.get("insider_name", ""),
        "insider_title": trade.get("insider_title", ""),
        "transaction_type": trade.get("transaction_type", ""),
        "transaction_date": trade.get("transaction_date", ""),
        "shares": trade.get("shares", 0),
        "price": trade.get("price", 0.0),
        "total_value": trade.get("total_value", 0.0),
        "shares_owned_after": trade.get("shares_owned_after", 0),
        "filing_date": trade.get("filing_date", ""),
        "source": "Unusual Whales"
    }

def format_political_trade_for_db(trade: Dict) -> Dict:
    """Format political trade data for database insertion"""
    # Create a unique string for UUID generation
    politician = trade.get("reporter", "")
    ticker = trade.get("ticker", "")
    date = trade.get("transaction_date", "")
    txn_type = trade.get("txn_type", "")
    
    # Create a unique key for UUID generation
    unique_key = f"{politician}-{ticker}-{date}-{txn_type}"
    
    # Generate UUID using uuid5 with a namespace
    unique_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_key))
    
    # Map member_type to politician_type
    member_type = trade.get("member_type", "")
    if member_type == "house":
        politician_type = "Representative"
    elif member_type == "senate":
        politician_type = "Senator"
    else:
        politician_type = member_type
    
    return {
        "id": unique_id,
        "politician_name": trade.get("reporter", ""),
        "politician_type": politician_type,
        "party": "",  # Not provided in new API
        "state": "",  # Not provided in new API
        "district": "",  # Not provided in new API
        "symbol": trade.get("ticker", ""),
        "company_name": "",  # Not provided in new API
        "transaction_date": trade.get("transaction_date", ""),
        "transaction_type": trade.get("txn_type", ""),
        "asset_type": "",  # Not provided in new API
        "asset_description": trade.get("notes", ""),
        "amount_range": trade.get("amounts", ""),
        "estimated_value": 0,  # Would need to parse from amounts
        "filing_date": trade.get("filed_at_date", ""),
        "source": "Unusual Whales",
        "notes": f"Issuer: {trade.get('issuer', '')}"  # Add issuer to notes field
    }

def format_analyst_rating_for_db(rating: Dict) -> Dict:
    """Format analyst rating data for database insertion"""
    # Convert timestamp to date format if present
    date = ""
    if "timestamp" in rating:
        try:
            date_obj = datetime.strptime(rating["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
            date = date_obj.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            date = datetime.now().strftime("%Y-%m-%d")
    
    # Extract numeric price target if present
    price_target = 0.0
    if "target" in rating:
        try:
            price_target = float(rating["target"])
        except (ValueError, TypeError):
            price_target = 0.0
    
    return {
        "symbol": rating.get("ticker", ""),
        "company_name": "",  # Not provided in new API
        "analyst_firm": rating.get("firm", ""),
        "analyst_name": rating.get("analyst_name", ""),
        "rating": rating.get("recommendation", ""),
        "previous_rating": "",  # Not provided in new API
        "rating_change": rating.get("action", ""),
        "price_target": price_target,
        "previous_price_target": 0.0,  # Not provided in new API
        "date": date,
        "notes": "",  # Not provided in new API
        "sector": rating.get("sector", ""),  # New field in API
        "source": "Unusual Whales"
    }

def get_dark_pool_recent(
    date: Optional[str] = None,
    limit: int = 100,
    min_premium: Optional[int] = None,
    max_premium: Optional[int] = None,
    min_size: Optional[int] = None,
    max_size: Optional[int] = None,
    min_volume: Optional[int] = None,
    max_volume: Optional[int] = None
) -> List[Dict]:
    """
    Fetch recent dark pool trades from Unusual Whales
    
    Args:
        date: Trading date in format YYYY-MM-DD (defaults to last trading day)
        limit: Maximum number of records to return (max 200)
        min_premium: Minimum premium of trades
        max_premium: Maximum premium of trades
        min_size: Minimum size of trades
        max_size: Maximum size of trades
        min_volume: Minimum volume of trades
        max_volume: Maximum volume of trades
        
    Returns:
        List[Dict]: List of dark pool trades
    """
    params = {"limit": min(limit, 200)}  # Ensure limit doesn't exceed API maximum
    
    if date:
        params["date"] = date
    if min_premium is not None:
        params["min_premium"] = min_premium
    if max_premium is not None:
        params["max_premium"] = max_premium
    if min_size is not None:
        params["min_size"] = min_size
    if max_size is not None:
        params["max_size"] = max_size
    if min_volume is not None:
        params["min_volume"] = min_volume
    if max_volume is not None:
        params["max_volume"] = max_volume
        
    try:
        response = make_request("darkpool/recent", params)
        return response.get("data", [])
    except Exception as e:
        logger.error(f"Failed to fetch recent dark pool trades: {str(e)}")
        raise

def get_ticker_dark_pool(
    ticker: str,
    date: Optional[str] = None,
    limit: int = 500,
    min_premium: Optional[int] = None,
    max_premium: Optional[int] = None,
    min_size: Optional[int] = None,
    max_size: Optional[int] = None,
    min_volume: Optional[int] = None,
    max_volume: Optional[int] = None,
    newer_than: Optional[str] = None,
    older_than: Optional[str] = None
) -> List[Dict]:
    """
    Fetch dark pool trades for a specific ticker
    
    Args:
        ticker: Stock ticker symbol
        date: Trading date in format YYYY-MM-DD (defaults to last trading day)
        limit: Maximum number of records to return (max 500)
        min_premium: Minimum premium of trades
        max_premium: Maximum premium of trades
        min_size: Minimum size of trades
        max_size: Maximum size of trades
        min_volume: Minimum volume of trades
        max_volume: Maximum volume of trades
        newer_than: Unix timestamp or ISO date for pagination
        older_than: Unix timestamp or ISO date for pagination
        
    Returns:
        List[Dict]: List of dark pool trades for the specified ticker
    """
    params = {"limit": min(limit, 500)}  # Ensure limit doesn't exceed API maximum
    
    if date:
        params["date"] = date
    if min_premium is not None:
        params["min_premium"] = min_premium
    if max_premium is not None:
        params["max_premium"] = max_premium
    if min_size is not None:
        params["min_size"] = min_size
    if max_size is not None:
        params["max_size"] = max_size
    if min_volume is not None:
        params["min_volume"] = min_volume
    if max_volume is not None:
        params["max_volume"] = max_volume
    if newer_than is not None:
        params["newer_than"] = newer_than
    if older_than is not None:
        params["older_than"] = older_than
        
    try:
        response = make_request(f"darkpool/{ticker}", params)
        return response.get("data", [])
    except Exception as e:
        logger.error(f"Failed to fetch dark pool trades for {ticker}: {str(e)}")
        raise

def format_dark_pool_trade_for_db(trade: Dict) -> Dict:
    """Format dark pool trade data for database insertion"""
    # Convert timestamp to date format if present
    executed_at = ""
    if "executed_at" in trade:
        try:
            date_obj = datetime.strptime(trade["executed_at"], "%Y-%m-%dT%H:%M:%SZ")
            executed_at = date_obj.isoformat()
        except (ValueError, TypeError):
            executed_at = datetime.now().isoformat()
    
    # Extract numeric values if present
    premium = 0.0
    if "premium" in trade:
        try:
            premium = float(trade["premium"])
        except (ValueError, TypeError):
            premium = 0.0
            
    price = 0.0
    if "price" in trade:
        try:
            price = float(trade["price"])
        except (ValueError, TypeError):
            price = 0.0
            
    size = 0
    if "size" in trade:
        try:
            size = int(trade["size"])
        except (ValueError, TypeError):
            size = 0
            
    volume = 0
    if "volume" in trade:
        try:
            volume = int(trade["volume"])
        except (ValueError, TypeError):
            volume = 0
            
    return {
        "ticker": trade.get("ticker", ""),
        "executed_at": executed_at,
        "price": price,
        "size": size,
        "premium": premium,
        "volume": volume,
        "market_center": trade.get("market_center", ""),
        "ext_hour_sold_codes": trade.get("ext_hour_sold_codes", ""),
        "sale_cond_codes": trade.get("sale_cond_codes", ""),
        "trade_code": trade.get("trade_code", ""),
        "trade_settlement": trade.get("trade_settlement", ""),
        "canceled": trade.get("canceled", False),
        "tracking_id": trade.get("tracking_id", ""),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

def get_ticker_insider_flow(ticker: str) -> List[Dict]:
    """
    Fetch aggregated insider trading flow for a specific ticker
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        List[Dict]: Aggregated buy/sell insider flow for the ticker
    """
    try:
        response = make_request(f"insider/{ticker}/ticker-flow")
        return response.get("data", [])
    except Exception as e:
        logger.error(f"Failed to fetch insider flow for {ticker}: {str(e)}")
        raise

def get_ticker_insiders(ticker: str) -> List[Dict]:
    """
    Fetch list of insiders for a specific ticker
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        List[Dict]: List of insiders associated with the ticker
    """
    try:
        response = make_request(f"insider/{ticker}")
        return response.get("data", [])
    except Exception as e:
        logger.error(f"Failed to fetch insiders for {ticker}: {str(e)}")
        raise

def get_insider_transactions(
    ticker_symbol: Optional[str] = None,
    common_stock_only: Optional[str] = None,
    transaction_codes: Optional[str] = None,
    is_director: Optional[str] = None,
    is_officer: Optional[str] = None,
    is_ten_percent_owner: Optional[str] = None,
    min_marketcap: Optional[int] = None,
    max_marketcap: Optional[int] = None,
    min_amount: Optional[str] = None,
    max_amount: Optional[str] = None,
    min_price: Optional[str] = None,
    max_price: Optional[str] = None,
    owner_name: Optional[str] = None,
    sectors: Optional[str] = None,
    industries: Optional[str] = None
) -> List[Dict]:
    """
    Fetch insider transactions from the Unusual Whales API
    
    Args:
        ticker_symbol: Comma-separated list of tickers to include or exclude (prefix with - to exclude)
        common_stock_only: Filter for common stock only
        transaction_codes: Filter by transaction codes
        is_director: Filter for directors
        is_officer: Filter for officers
        is_ten_percent_owner: Filter for 10% owners
        min_marketcap: Minimum market cap
        max_marketcap: Maximum market cap
        min_amount: Minimum transaction amount
        max_amount: Maximum transaction amount
        min_price: Minimum price
        max_price: Maximum price
        owner_name: Filter by owner name
        sectors: Filter by sectors
        industries: Filter by industries
        
    Returns:
        List[Dict]: List of insider transactions
    """
    params = {}
    
    if ticker_symbol:
        params["ticker_symbol"] = ticker_symbol
    if common_stock_only:
        params["common_stock_only"] = common_stock_only
    if transaction_codes:
        params["transaction_codes"] = transaction_codes
    if is_director:
        params["is_director"] = is_director
    if is_officer:
        params["is_officer"] = is_officer
    if is_ten_percent_owner:
        params["is_ten_percent_owner"] = is_ten_percent_owner
    if min_marketcap is not None:
        params["min_marketcap"] = min_marketcap
    if max_marketcap is not None:
        params["max_marketcap"] = max_marketcap
    if min_amount:
        params["min_amount"] = min_amount
    if max_amount:
        params["max_amount"] = max_amount
    if min_price:
        params["min_price"] = min_price
    if max_price:
        params["max_price"] = max_price
    if owner_name:
        params["owner_name"] = owner_name
    if sectors:
        params["sectors"] = sectors
    if industries:
        params["industries"] = industries
        
    try:
        response = make_request("insider/transactions", params)
        return response.get("data", [])
    except Exception as e:
        logger.error(f"Failed to fetch insider transactions: {str(e)}")
        raise

def format_insider_transaction_for_db(transaction: Dict) -> Dict:
    """Format insider transaction data for database insertion"""
    # Convert string dates to proper format
    filing_date = ""
    if "filing_date" in transaction:
        try:
            date_obj = datetime.strptime(transaction["filing_date"], "%Y-%m-%d")
            filing_date = date_obj.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            filing_date = datetime.now().strftime("%Y-%m-%d")
            
    transaction_date = ""
    if "transaction_date" in transaction:
        try:
            date_obj = datetime.strptime(transaction["transaction_date"], "%Y-%m-%d")
            transaction_date = date_obj.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            transaction_date = datetime.now().strftime("%Y-%m-%d")
    
    # Extract numeric values
    price = 0.0
    if "price" in transaction:
        try:
            price = float(transaction["price"])
        except (ValueError, TypeError):
            price = 0.0
            
    amount = 0
    if "amount" in transaction:
        try:
            amount = int(transaction["amount"])
        except (ValueError, TypeError):
            amount = 0
            
    shares_owned_before = 0
    if "shares_owned_before" in transaction:
        try:
            shares_owned_before = int(transaction["shares_owned_before"])
        except (ValueError, TypeError):
            shares_owned_before = 0
            
    shares_owned_after = 0
    if "shares_owned_after" in transaction:
        try:
            shares_owned_after = int(transaction["shares_owned_after"])
        except (ValueError, TypeError):
            shares_owned_after = 0
    
    return {
        "transaction_id": transaction.get("id", ""),
        "ticker": transaction.get("ticker", ""),
        "owner_name": transaction.get("owner_name", ""),
        "transaction_date": transaction_date,
        "filing_date": filing_date,
        "transaction_type": transaction.get("transaction_code", ""),
        "is_purchase": transaction.get("transaction_code", "") in ["P", "A"],
        "is_sale": transaction.get("transaction_code", "") in ["S", "D"],
        "price": price,
        "amount": amount,
        "value": price * amount if price and amount else 0,
        "shares_owned_before": shares_owned_before,
        "shares_owned_after": shares_owned_after,
        "is_director": transaction.get("is_director", False),
        "is_officer": transaction.get("is_officer", False),
        "is_ten_percent_owner": transaction.get("is_ten_percent_owner", False),
        "officer_title": transaction.get("officer_title", ""),
        "form_type": transaction.get("formtype", ""),
        "security_title": transaction.get("security_title", ""),
        "source": "Unusual Whales",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

def clear_cache() -> None:
    """Clear the API response cache"""
    cache.clear()
    logger.info("Cache cleared")

def get_economic_calendar() -> List[Dict]:
    """
    Fetches the economic calendar data from UnusualWhales API.
    
    Returns:
        List[Dict]: A list of economic calendar events including fed speakers, 
                    FOMC meetings, and economic reports.
    
    Each event contains:
        - event: The event/reason (e.g., "PCE index")
        - forecast: The forecast if the event is an economic report/indicator
        - prev: The previous value of the preceding period
        - reported_period: The period for which the report is being reported
        - time: The time at which the event will start (UTC timestamp)
        - type: The type of the event (fed-speaker, fomc, report)
    """
    try:
        response = make_request("market/economic-calendar")
        if not response or "data" not in response:
            logger.warning("No data found in economic calendar response")
            return []
        
        # Return all the economic events
        return response.get("data", [])
    except Exception as e:
        logger.error(f"Error fetching economic calendar: {str(e)}")
        return []

def get_fda_calendar(
    ticker: Optional[str] = None,
    drug: Optional[str] = None,
    target_date_min: Optional[str] = None,
    target_date_max: Optional[str] = None,
    announced_date_min: Optional[str] = None,
    announced_date_max: Optional[str] = None,
    limit: int = 100
) -> List[Dict]:
    """
    Fetches FDA calendar data from UnusualWhales API with filtering options.
    
    The FDA calendar contains information about:
    - PDUFA (Prescription Drug User Fee Act) dates
    - Advisory Committee Meetings
    - FDA Decisions
    - Clinical Trial Results
    - New Drug Applications
    - Biologics License Applications
    
    Args:
        ticker: Filter by ticker symbol (comma-separated for multiple)
        drug: Filter by drug name (partial match)
        target_date_min: Minimum target date (supports Q1-Q4, H1-H2, MID, LATE formats)
        target_date_max: Maximum target date (supports Q1-Q4, H1-H2, MID, LATE formats)
        announced_date_min: Minimum announced date (YYYY-MM-DD)
        announced_date_max: Maximum announced date (YYYY-MM-DD)
        limit: Maximum number of results to return (1-200, default 100)
    
    Returns:
        List[Dict]: A list of FDA calendar events.
    """
    params = {"limit": min(200, max(1, limit))}
    
    if ticker:
        params["ticker"] = ticker
    if drug:
        params["drug"] = drug
    if target_date_min:
        params["target_date_min"] = target_date_min
    if target_date_max:
        params["target_date_max"] = target_date_max
    if announced_date_min:
        params["announced_date_min"] = announced_date_min
    if announced_date_max:
        params["announced_date_max"] = announced_date_max
    
    try:
        # Updated endpoint to use the market prefix
        response = make_request("market/fda-calendar", params)
        if not response or "data" not in response:
            logger.warning("No data found in FDA calendar response")
            return []
        return response.get("data", [])
    except Exception as e:
        logger.error(f"Error fetching FDA calendar: {str(e)}")
        return []

def format_economic_calendar_event_for_db(event: Dict) -> Dict:
    """
    Formats an economic calendar event for database insertion.
    
    Args:
        event (Dict): Raw economic calendar event from the API
        
    Returns:
        Dict: Formatted event ready for database insertion
    """
    # Extract date from the event_time field if available
    event_time_value = None
    if "time" in event and event["time"]:
        try:
            # Parse the ISO format time
            event_time_value = event["time"]
        except (ValueError, TypeError):
            # If parsing fails, keep as is
            pass
    
    formatted_event = {
        "event": event.get("event", "Unknown Economic Event"),  # This is the required field
        "event_time": event_time_value,
        "forecast": event.get("forecast"),
        "previous": event.get("prev"),
        "reported_period": event.get("reported_period"),
        "type": event.get("type", "report"),
        "importance": "medium",  # Default importance level
        "notes": f"Event Type: {event.get('type', 'Unknown')}",
        "fetched_at": datetime.now().isoformat()
    }
    
    return formatted_event

def format_fda_calendar_event_for_db(event: Dict) -> Dict:
    """
    Formats an FDA calendar event for database insertion.
    
    Args:
        event (Dict): Raw FDA calendar event from the API
        
    Returns:
        Dict: Formatted event ready for database insertion
    """
    # Convert marketcap to number if possible
    marketcap = event.get("marketcap")
    if marketcap and isinstance(marketcap, str) and marketcap.isdigit():
        marketcap = int(marketcap)
    
    formatted_event = {
        "catalyst": event.get("catalyst"),
        "description": event.get("description"),
        "drug": event.get("drug"),
        "end_date": event.get("end_date"),
        "has_options": event.get("has_options"),
        "indication": event.get("indication"),
        "marketcap": marketcap,
        "notes": event.get("notes"),
        "outcome": event.get("outcome"),
        "outcome_brief": event.get("outcome_brief"),
        "source_link": event.get("source_link"),
        "start_date": event.get("start_date"),
        "status": event.get("status"),
        "ticker": event.get("ticker"),
        "fetched_at": datetime.now().isoformat(),
    }
    
    return formatted_event

def get_institution_activity(
    name: str, 
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    date: Optional[str] = None,
    limit: int = 500,
    page: Optional[int] = None
) -> List[Dict]:
    """
    Get the trading activities for a specific institution from UnusualWhales API.
    
    Args:
        name: Institution name or CIK (e.g., "VANGUARD GROUP INC")
        start_date: Start date to filter institutional data (YYYY-MM-DD)
        end_date: End date to filter institutional data (YYYY-MM-DD)
        date: Specific date to filter institutional data (YYYY-MM-DD)
        limit: Number of results to return (max 500)
        page: Page number for pagination
        
    Returns:
        List[Dict]: Institution activity data
    """
    try:
        endpoint = f"institution/{name}/activity"
        
        # Construct parameters dictionary
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if date:
            params["date"] = date
        if limit:
            params["limit"] = min(max(1, limit), 500)  # Ensure limit is between 1 and 500
        if page is not None:
            params["page"] = page
            
        response = make_request(endpoint, params)
        return response.get("data", [])
    
    except Exception as e:
        logger.error(f"Failed to fetch institution activity for {name}: {str(e)}", extra={"metadata": {}})
        return []


def get_institution_holdings(
    name: str,
    date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    security_types: Optional[List[str]] = None,
    order: Optional[str] = None,
    order_direction: str = "desc",
    limit: int = 500,
    page: Optional[int] = None
) -> List[Dict]:
    """
    Get the holdings for a specific institution from UnusualWhales API.
    
    Args:
        name: Institution name or CIK (e.g., "VANGUARD GROUP INC")
        date: Specific date to filter holdings (YYYY-MM-DD)
        start_date: Start date to filter holdings (YYYY-MM-DD)
        end_date: End date to filter holdings (YYYY-MM-DD)
        security_types: List of security types to filter (e.g., ["Share"])
        order: Column to order results by
        order_direction: Sort direction ("desc" or "asc")
        limit: Number of results to return (max 500)
        page: Page number for pagination
        
    Returns:
        List[Dict]: Institution holdings data
    """
    try:
        endpoint = f"institution/{name}/holdings"
        
        # Construct parameters dictionary
        params = {}
        if date:
            params["date"] = date
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if security_types:
            params["security_types"] = security_types
        if order:
            params["order"] = order
        if order_direction:
            params["order_direction"] = order_direction
        if limit:
            params["limit"] = min(max(1, limit), 500)  # Ensure limit is between 1 and 500
        if page is not None:
            params["page"] = page
            
        response = make_request(endpoint, params)
        return response.get("data", [])
    
    except Exception as e:
        logger.error(f"Failed to fetch institution holdings for {name}: {str(e)}", extra={"metadata": {}})
        return []


def get_ticker_ownership(
    ticker: str,
    date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    tags: Optional[List[str]] = None,
    order: Optional[str] = None,
    order_direction: str = "desc",
    limit: int = 500,
    page: Optional[int] = None
) -> List[Dict]:
    """
    Get the institutional ownership of a specific ticker from UnusualWhales API.
    
    Args:
        ticker: Ticker symbol (e.g., "AAPL")
        date: Specific report date to filter (YYYY-MM-DD)
        start_date: Start date to filter ownership (YYYY-MM-DD)
        end_date: End date to filter ownership (YYYY-MM-DD)
        tags: List of institution tags to filter (e.g., ["activist"])
        order: Column to order results by
        order_direction: Sort direction ("desc" or "asc")
        limit: Number of results to return (max 500)
        page: Page number for pagination
        
    Returns:
        List[Dict]: Institutional ownership data for the ticker
    """
    try:
        endpoint = f"institution/{ticker}/ownership"
        
        # Construct parameters dictionary
        params = {}
        if date:
            params["date"] = date
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if tags:
            params["tags"] = tags
        if order:
            params["order"] = order
        if order_direction:
            params["order_direction"] = order_direction
        if limit:
            params["limit"] = min(max(1, limit), 500)  # Ensure limit is between 1 and 500
        if page is not None:
            params["page"] = page
            
        response = make_request(endpoint, params)
        return response.get("data", [])
    
    except Exception as e:
        logger.error(f"Failed to fetch institutional ownership for {ticker}: {str(e)}", extra={"metadata": {}})
        return []


def get_institutions(
    name: Optional[str] = None,
    tags: Optional[List[str]] = None,
    min_total_value: Optional[str] = None,
    max_total_value: Optional[str] = None,
    min_share_value: Optional[str] = None,
    max_share_value: Optional[str] = None,
    order: Optional[str] = None,
    order_direction: str = "desc",
    limit: int = 500,
    page: Optional[int] = None
) -> List[Dict]:
    """
    Get a list of institutions from UnusualWhales API.
    
    Args:
        name: Filter by institution name
        tags: List of institution tags to filter (e.g., ["activist"])
        min_total_value: Minimum total portfolio value
        max_total_value: Maximum total portfolio value
        min_share_value: Minimum share portfolio value
        max_share_value: Maximum share portfolio value
        order: Column to order results by
        order_direction: Sort direction ("desc" or "asc")
        limit: Number of results to return (max 500)
        page: Page number for pagination
        
    Returns:
        List[Dict]: List of institutions
    """
    try:
        endpoint = "institutions"
        
        # Construct parameters dictionary
        params = {}
        if name:
            params["name"] = name
        if tags:
            params["tags"] = tags
        if min_total_value:
            params["min_total_value"] = min_total_value
        if max_total_value:
            params["max_total_value"] = max_total_value
        if min_share_value:
            params["min_share_value"] = min_share_value
        if max_share_value:
            params["max_share_value"] = max_share_value
        if order:
            params["order"] = order
        if order_direction:
            params["order_direction"] = order_direction
        if limit:
            params["limit"] = min(max(1, limit), 500)  # Ensure limit is between 1 and 500
        if page is not None:
            params["page"] = page
            
        response = make_request(endpoint, params)
        return response.get("data", [])
    
    except Exception as e:
        logger.error(f"Failed to fetch institutions: {str(e)}", extra={"metadata": {}})
        return []


def get_latest_filings(
    date: Optional[str] = None,
    name: Optional[str] = None,
    order: Optional[str] = None,
    order_direction: str = "desc",
    limit: int = 500,
    page: Optional[int] = None
) -> List[Dict]:
    """
    Get the latest institutional filings from UnusualWhales API.
    
    Args:
        date: Filter by filing date (YYYY-MM-DD)
        name: Filter by institution name
        order: Column to order results by
        order_direction: Sort direction ("desc" or "asc")
        limit: Number of results to return (max 500)
        page: Page number for pagination
        
    Returns:
        List[Dict]: Latest institutional filings
    """
    try:
        endpoint = "institutions/latest_filings"
        
        # Construct parameters dictionary
        params = {}
        if date:
            params["date"] = date
        if name:
            params["name"] = name
        if order:
            params["order"] = order
        if order_direction:
            params["order_direction"] = order_direction
        if limit:
            params["limit"] = min(max(1, limit), 500)  # Ensure limit is between 1 and 500
        if page is not None:
            params["page"] = page
            
        response = make_request(endpoint, params)
        return response.get("data", [])
    
    except Exception as e:
        logger.error(f"Failed to fetch latest filings: {str(e)}", extra={"metadata": {}})
        return []


def format_institution_activity_for_db(activity: Dict) -> Dict:
    """
    Format institution activity data for database insertion.
    
    Args:
        activity: Raw institution activity data from API
        
    Returns:
        Dict: Formatted activity data for database
    """
    # Try to convert string values to numeric where appropriate
    avg_price = activity.get("avg_price")
    if avg_price and isinstance(avg_price, str):
        try:
            avg_price = float(avg_price)
        except ValueError:
            pass
            
    buy_price = activity.get("buy_price")
    if buy_price and isinstance(buy_price, str):
        try:
            buy_price = float(buy_price)
        except ValueError:
            pass
            
    sell_price = activity.get("sell_price")
    if sell_price and isinstance(sell_price, str):
        try:
            sell_price = float(sell_price)
        except ValueError:
            pass
            
    close = activity.get("close")
    if close and isinstance(close, str):
        try:
            close = float(close)
        except ValueError:
            pass
            
    price_on_filing = activity.get("price_on_filing")
    if price_on_filing and isinstance(price_on_filing, str):
        try:
            price_on_filing = float(price_on_filing)
        except ValueError:
            pass
            
    price_on_report = activity.get("price_on_report")
    if price_on_report and isinstance(price_on_report, str):
        try:
            price_on_report = float(price_on_report)
        except ValueError:
            pass
            
    shares_outstanding = activity.get("shares_outstanding")
    if shares_outstanding and isinstance(shares_outstanding, str):
        try:
            shares_outstanding = float(shares_outstanding)
        except ValueError:
            pass
    
    # Format the activity data
    formatted_activity = {
        "ticker": activity.get("ticker"),
        "filing_date": activity.get("filing_date"),
        "report_date": activity.get("report_date"),
        "security_type": activity.get("security_type"),
        "put_call": activity.get("put_call"),
        "units": activity.get("units"),
        "units_change": activity.get("units_change"),
        "avg_price": avg_price,
        "buy_price": buy_price,
        "sell_price": sell_price,
        "close": close,
        "price_on_filing": price_on_filing,
        "price_on_report": price_on_report,
        "shares_outstanding": shares_outstanding,
        "timestamp": datetime.now().isoformat(),
    }
    
    return formatted_activity


def format_institution_holding_for_db(holding: Dict) -> Dict:
    """
    Format institution holding data for database insertion.
    
    Args:
        holding: Raw institution holding data from API
        
    Returns:
        Dict: Formatted holding data for database
    """
    # Try to convert string values to numeric where appropriate
    avg_price = holding.get("avg_price")
    if avg_price and isinstance(avg_price, str):
        try:
            avg_price = float(avg_price)
        except ValueError:
            pass
            
    close = holding.get("close")
    if close and isinstance(close, str):
        try:
            close = float(close)
        except ValueError:
            pass
            
    price_first_buy = holding.get("price_first_buy")
    if price_first_buy and isinstance(price_first_buy, str):
        try:
            price_first_buy = float(price_first_buy)
        except ValueError:
            pass
            
    shares_outstanding = holding.get("shares_outstanding")
    if shares_outstanding and isinstance(shares_outstanding, str):
        try:
            shares_outstanding = float(shares_outstanding)
        except ValueError:
            pass
    
    # Format the holding data
    formatted_holding = {
        "ticker": holding.get("ticker"),
        "date": holding.get("date"),
        "full_name": holding.get("full_name"),
        "security_type": holding.get("security_type"),
        "put_call": holding.get("put_call"),
        "units": holding.get("units"),
        "units_change": holding.get("units_change"),
        "value": holding.get("value"),
        "avg_price": avg_price,
        "close": close,
        "first_buy": holding.get("first_buy"),
        "price_first_buy": price_first_buy,
        "sector": holding.get("sector"),
        "shares_outstanding": shares_outstanding,
        "historical_units": holding.get("historical_units"),
        "timestamp": datetime.now().isoformat(),
    }
    
    return formatted_holding


def format_ticker_ownership_for_db(ownership: Dict) -> Dict:
    """
    Format ticker ownership data for database insertion.
    
    Args:
        ownership: Raw ticker ownership data from API
        
    Returns:
        Dict: Formatted ownership data for database
    """
    # Try to convert string values to numeric where appropriate
    avg_price = ownership.get("avg_price")
    if avg_price and isinstance(avg_price, str):
        try:
            avg_price = float(avg_price)
        except ValueError:
            pass
            
    inst_share_value = ownership.get("inst_share_value")
    if inst_share_value and isinstance(inst_share_value, str):
        try:
            inst_share_value = float(inst_share_value)
        except ValueError:
            pass
            
    inst_value = ownership.get("inst_value")
    if inst_value and isinstance(inst_value, str):
        try:
            inst_value = float(inst_value)
        except ValueError:
            pass
            
    shares_outstanding = ownership.get("shares_outstanding")
    if shares_outstanding and isinstance(shares_outstanding, str):
        try:
            shares_outstanding = float(shares_outstanding)
        except ValueError:
            pass
            
    value = ownership.get("value")
    if value and isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            pass
    
    # Format the ownership data
    formatted_ownership = {
        "name": ownership.get("name"),
        "short_name": ownership.get("short_name"),
        "filing_date": ownership.get("filing_date"),
        "report_date": ownership.get("report_date"),
        "first_buy": ownership.get("first_buy"),
        "units": ownership.get("units"),
        "units_change": ownership.get("units_change"),
        "value": value,
        "avg_price": avg_price,
        "inst_share_value": inst_share_value,
        "inst_value": inst_value,
        "shares_outstanding": shares_outstanding,
        "historical_units": ownership.get("historical_units"),
        "people": ownership.get("people"),
        "tags": ownership.get("tags"),
        "timestamp": datetime.now().isoformat(),
    }
    
    return formatted_ownership


def format_institution_for_db(institution: Dict) -> Dict:
    """
    Format institution data for database insertion.
    
    Args:
        institution: Raw institution data from API
        
    Returns:
        Dict: Formatted institution data for database
    """
    # Try to convert string values to numeric where appropriate
    def convert_to_float(value):
        if value and isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return value
        return value
    
    # Format the institution data
    formatted_institution = {
        "name": institution.get("name"),
        "short_name": institution.get("short_name"),
        "cik": institution.get("cik"),
        "date": institution.get("date"),
        "filing_date": institution.get("filing_date"),
        "is_hedge_fund": institution.get("is_hedge_fund"),
        "description": institution.get("description"),
        "website": institution.get("website"),
        "logo_url": institution.get("logo_url"),
        "founder_img_url": institution.get("founder_img_url"),
        "people": institution.get("people"),
        "tags": institution.get("tags"),
        "buy_value": convert_to_float(institution.get("buy_value")),
        "sell_value": convert_to_float(institution.get("sell_value")),
        "share_value": convert_to_float(institution.get("share_value")),
        "put_value": convert_to_float(institution.get("put_value")),
        "call_value": convert_to_float(institution.get("call_value")),
        "warrant_value": convert_to_float(institution.get("warrant_value")),
        "fund_value": convert_to_float(institution.get("fund_value")),
        "pfd_value": convert_to_float(institution.get("pfd_value")),
        "debt_value": convert_to_float(institution.get("debt_value")),
        "total_value": convert_to_float(institution.get("total_value")),
        "share_holdings": convert_to_float(institution.get("share_holdings")),
        "put_holdings": convert_to_float(institution.get("put_holdings")),
        "call_holdings": convert_to_float(institution.get("call_holdings")),
        "warrant_holdings": convert_to_float(institution.get("warrant_holdings")),
        "fund_holdings": convert_to_float(institution.get("fund_holdings")),
        "pfd_holdings": convert_to_float(institution.get("pfd_holdings")),
        "debt_holdings": convert_to_float(institution.get("debt_holdings")),
        "total_holdings": convert_to_float(institution.get("total_holdings")),
        "timestamp": datetime.now().isoformat(),
    }
    
    return formatted_institution

def get_alerts(
    config_ids: Optional[List[str]] = None,
    intraday_only: bool = True,
    limit: int = 100,
    noti_types: Optional[List[str]] = None,
    page: int = 0,
    ticker_symbols: Optional[str] = None
) -> List[Dict]:
    """
    Fetches alerts that have been triggered for the user from UnusualWhales API.
    
    Args:
        config_ids: Optional list of alert configuration IDs to filter by
        intraday_only: Whether to return only intraday alerts (default True)
        limit: Number of alerts to return (max 200)
        noti_types: Optional list of notification types to filter by
        page: Page number for pagination
        ticker_symbols: Optional comma-separated list of tickers to filter by
        
    Returns:
        List of alert dictionaries
        
    Raises:
        UnusualWhalesError: If the API request fails
    """
    endpoint = "alerts"
    params = {
        "limit": min(limit, 200),
        "page": max(page, 0),
        "intraday_only": intraday_only
    }
    
    if config_ids:
        params["config_ids[]"] = config_ids
    
    if noti_types:
        params["noti_types[]"] = noti_types
        
    if ticker_symbols:
        params["ticker_symbols"] = ticker_symbols
    
    try:
        response = make_request(endpoint, params)
        if "data" in response:
            return response["data"]
        return []
    except Exception as e:
        logger.error(f"Failed to fetch alerts: {str(e)}")
        raise UnusualWhalesError(f"Failed to fetch alerts: {str(e)}")

def get_alert_configurations() -> List[Dict]:
    """
    Fetches all alert configurations created by the user from UnusualWhales API.
    
    Returns:
        List of alert configuration dictionaries
        
    Raises:
        UnusualWhalesError: If the API request fails
    """
    endpoint = "alerts/configuration"
    
    try:
        response = make_request(endpoint)
        if "data" in response:
            return response["data"]
        return []
    except Exception as e:
        logger.error(f"Failed to fetch alert configurations: {str(e)}")
        raise UnusualWhalesError(f"Failed to fetch alert configurations: {str(e)}")

def format_alert_for_db(alert: Dict) -> Dict:
    """
    Formats an alert from the UnusualWhales API for database insertion.
    
    Args:
        alert: The alert data from the API
        
    Returns:
        Formatted alert dictionary ready for database insertion
    """
    formatted_alert = {
        "alert_id": alert.get("id"),
        "name": alert.get("name"),
        "symbol": alert.get("symbol"),
        "symbol_type": alert.get("symbol_type", "stock"),
        "notification_type": alert.get("noti_type"),
        "created_at": alert.get("created_at"),
        "tape_time": alert.get("tape_time"),
        "config_id": alert.get("user_noti_config_id"),
        "meta": json.dumps(alert.get("meta", {})),
        "processed": False,
        "created_at_ts": datetime.now().isoformat()
    }
    
    return formatted_alert

def get_stock_screener(
    ticker: Optional[str] = None,
    sectors: Optional[List[str]] = None,
    issue_types: Optional[List[str]] = None,
    min_marketcap: Optional[int] = None,
    max_marketcap: Optional[int] = None,
    min_volume: Optional[int] = None,
    max_volume: Optional[int] = None,
    min_implied_move_perc: Optional[float] = None,
    max_implied_move_perc: Optional[float] = None,
    min_iv_rank: Optional[float] = None,
    max_iv_rank: Optional[float] = None,
    min_put_call_ratio: Optional[float] = None,
    max_put_call_ratio: Optional[float] = None,
    order: Optional[str] = "premium",
    order_direction: str = "desc",
    limit: int = 100,
    is_s_p_500: bool = False,
    has_dividends: bool = False
) -> List[Dict]:
    """
    Fetches stock screening data from UnusualWhales API.
    
    Args:
        ticker: Comma-separated list of tickers, prefix with - to exclude
        sectors: List of sectors to filter by
        issue_types: Types of issues (Common Stock, ETF, Index, ADR)
        min_marketcap/max_marketcap: Market cap range
        min_volume/max_volume: Options volume range
        min_implied_move_perc/max_implied_move_perc: Implied move percentage range
        min_iv_rank/max_iv_rank: IV rank range (0-100)
        min_put_call_ratio/max_put_call_ratio: Put/call ratio range
        order: Field to order by (premium, marketcap, etc.)
        order_direction: Direction to sort (asc, desc)
        limit: Maximum number of results to return
        is_s_p_500: Filter to only S&P 500 stocks
        has_dividends: Filter to only stocks with dividends
        
    Returns:
        List of stock data dictionaries
    """
    endpoint = "screener/stocks"
    params = {}
    
    if ticker:
        params["ticker"] = ticker
    if sectors:
        params["sectors[]"] = sectors
    if issue_types:
        params["issue_types[]"] = issue_types
    if min_marketcap:
        params["min_marketcap"] = min_marketcap
    if max_marketcap:
        params["max_marketcap"] = max_marketcap
    if min_volume:
        params["min_volume"] = min_volume
    if max_volume:
        params["max_volume"] = max_volume
    if min_implied_move_perc:
        params["min_implied_move_perc"] = min_implied_move_perc
    if max_implied_move_perc:
        params["max_implied_move_perc"] = max_implied_move_perc
    if min_iv_rank:
        params["min_iv_rank"] = min_iv_rank
    if max_iv_rank:
        params["max_iv_rank"] = max_iv_rank
    if min_put_call_ratio:
        params["min_put_call_ratio"] = min_put_call_ratio
    if max_put_call_ratio:
        params["max_put_call_ratio"] = max_put_call_ratio
    if order:
        params["order"] = order
    if order_direction:
        params["order_direction"] = order_direction
    if limit:
        params["limit"] = limit
    if is_s_p_500:
        params["is_s_p_500"] = "true"
    if has_dividends:
        params["has_dividends"] = "true"
    
    data = make_request(endpoint, params)
    return data.get("data", [])

def get_earnings_afterhours(
    date: Optional[str] = None,
    limit: int = 50,
    page: Optional[int] = None
) -> List[Dict]:
    """
    Fetches afterhours earnings data for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format (defaults to last trading day)
        limit: Number of results to return (max 100)
        page: Page number for pagination
        
    Returns:
        List of earnings data dictionaries
    """
    endpoint = "earnings/afterhours"
    params = {"limit": limit}
    
    if date:
        params["date"] = date
    if page is not None:
        params["page"] = page
    
    data = make_request(endpoint, params)
    return data.get("data", [])

def get_earnings_premarket(
    date: Optional[str] = None,
    limit: int = 50,
    page: Optional[int] = None
) -> List[Dict]:
    """
    Fetches premarket earnings data for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format (defaults to last trading day)
        limit: Number of results to return (max 100)
        page: Page number for pagination
        
    Returns:
        List of earnings data dictionaries
    """
    endpoint = "earnings/premarket"
    params = {"limit": limit}
    
    if date:
        params["date"] = date
    if page is not None:
        params["page"] = page
    
    data = make_request(endpoint, params)
    return data.get("data", [])

def format_stock_screener_data_for_db(stock_data: Dict) -> Dict:
    """
    Formats stock screener data for database storage.
    
    Args:
        stock_data: Stock data from the UnusualWhales API
        
    Returns:
        Formatted data for database insertion
    """
    # Convert string numeric values to appropriate types
    for key, value in stock_data.items():
        if isinstance(value, str) and value.replace('.', '', 1).isdigit():
            try:
                if '.' in value:
                    stock_data[key] = float(value)
                else:
                    stock_data[key] = int(value)
            except (ValueError, TypeError):
                pass  # Keep as string if conversion fails
    
    # Add timestamp for when this data was retrieved
    stock_data['retrieved_at'] = datetime.now().isoformat()
    
    return stock_data

def format_earnings_data_for_db(earnings_data: Dict) -> Dict:
    """
    Formats earnings data for database storage.
    
    Args:
        earnings_data: Earnings data from the UnusualWhales API
        
    Returns:
        Formatted data for database insertion
    """
    # Create a new dict to avoid modifying the original
    formatted_data = earnings_data.copy()
    
    # Convert string numeric values to appropriate types
    for key, value in formatted_data.items():
        if isinstance(value, str) and value.replace('.', '', 1).replace('-', '', 1).isdigit():
            try:
                if '.' in value:
                    formatted_data[key] = float(value)
                else:
                    formatted_data[key] = int(value)
            except (ValueError, TypeError):
                pass  # Keep as string if conversion fails
    
    # Add timestamp for when this data was retrieved
    formatted_data['retrieved_at'] = datetime.now().isoformat()
    
    return formatted_data

def get_stock_info(ticker: str) -> Dict:
    """
    Get detailed information about a stock from UnusualWhales API.
    
    Args:
        ticker: The ticker symbol to get information for
        
    Returns:
        Dictionary containing stock information including sector, market cap, 
        logo URL, company description, earnings data, etc.
    """
    endpoint = f"stock/{ticker}/info"
    try:
        logger.info(f"Making request to {API_BASE_URL}/{endpoint}")
        response = make_request(endpoint)
        
        # Debug: Print the response data
        logger.info(f"API Response for {ticker}: {json.dumps(response, indent=2)}")
        
        return response.get('data', {})
    except Exception as e:
        logger.error(f"Error fetching stock info for {ticker}: {str(e)}")
        return {}

def get_stock_state(ticker: str) -> Dict:
    """
    Get the latest stock state (price, volume, etc.) from UnusualWhales API.
    
    Args:
        ticker: The ticker symbol to get stock state for
        
    Returns:
        Dictionary containing latest stock state including open, close, high, low,
        volume and market time.
    """
    endpoint = f"stock/{ticker}/stock-state"
    try:
        response = make_request(endpoint)
        return response.get('data', {})
    except Exception as e:
        logger.error(f"Error fetching stock state for {ticker}: {str(e)}")
        return {}

def format_stock_info_for_db(info: Dict, ticker: str) -> Dict:
    """
    Format stock information for database storage.
    
    Args:
        info: The stock information from the API
        ticker: The ticker symbol
        
    Returns:
        Formatted dictionary ready for database storage
    """
    now = datetime.utcnow().isoformat()
    
    # Debug: Print the input data
    logger.info(f"Formatting stock info for {ticker}: {json.dumps(info, indent=2)}")
    
    formatted_data = {
        "ticker": ticker,
        "company_name": info.get("full_name", ""),
        "sector": info.get("sector", ""),
        "market_cap": float(info.get("marketcap", 0)) if info.get("marketcap") else 0,
        "avg_volume": float(info.get("avg30_volume", 0)) if info.get("avg30_volume") else 0,
        "description": info.get("short_description", ""),
        "logo_url": info.get("logo", ""),
        "current_price": float(info.get("price", 0)) if info.get("price") else 0,
        "price_updated_at": datetime.utcnow().isoformat(),
        "fetched_at": now
    }
    
    # Debug: Print the formatted data
    logger.info(f"Formatted data for {ticker}: {json.dumps(formatted_data, indent=2)}")
    
    return formatted_data

# Define the Unusual Whales API URL
UW_API_BASE_URL = "https://api.unusualwhales.com/api"
UW_API_KEY = os.getenv("API_KEY_UNUSUAL_WHALES")

# Cache configuration
CACHE_DIR = Path("./cache")
CACHE_DIR.mkdir(exist_ok=True)
cache = Cache(str(CACHE_DIR))

# Initialize a rate-limited session
limiter_session = LimiterSession(per_second=5)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_ticker_option_contracts(symbol: str) -> List[Dict[str, Any]]:
    """
    Fetch option contracts for a specific ticker from the Unusual Whales API
    
    Args:
        symbol: The stock symbol to fetch option contracts for
        
    Returns:
        List of option contract data
    """
    if not symbol or not isinstance(symbol, str):
        logger.error(f"Invalid symbol provided to get_ticker_option_contracts: {symbol}")
        return []
        
    url = f"{UW_API_BASE_URL}/options/contracts/{symbol}"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {UW_API_KEY}"
    }
    
    # Check cache first
    cache_key = f"option_contracts_{symbol}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    try:
        response = limiter_session.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if "data" in data and "contracts" in data["data"]:
            contracts = data["data"]["contracts"]
            # Cache for 1 hour
            cache.set(cache_key, contracts, expire=3600)
            return contracts
        else:
            logger.warning(f"Unexpected response format for {symbol} option contracts")
            return []
    except Exception as e:
        logger.error(f"Error fetching option contracts for {symbol}: {str(e)}")
        return []

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_option_contract_flow(contract_id: str) -> Dict[str, Any]:
    """
    Fetch flow data for a specific option contract from the Unusual Whales API
    
    Args:
        contract_id: The option contract ID
        
    Returns:
        Option flow data for the specified contract
    """
    url = f"{UW_API_BASE_URL}/options/flow/{contract_id}"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {UW_API_KEY}"
    }
    
    # Check cache first
    cache_key = f"option_flow_{contract_id}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    try:
        response = limiter_session.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if "data" in data and "flow" in data["data"]:
            flow = data["data"]["flow"]
            # Cache for 30 minutes
            cache.set(cache_key, flow, expire=1800)
            return flow
        else:
            logger.warning(f"Unexpected response format for option contract {contract_id} flow")
            return {}
    except Exception as e:
        logger.error(f"Error fetching flow for option contract {contract_id}: {str(e)}")
        return {}

def format_option_flow_for_db(flow_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format option flow data for database storage
    
    Args:
        flow_data: Raw option flow data from the API
        
    Returns:
        Formatted option flow data ready for DB insertion
    """
    if not flow_data:
        return {}
    
    try:
        # Extract and format the relevant fields
        formatted_data = {
            "ticker": flow_data.get("symbol", ""),
            "date": datetime.now().isoformat(),
            "contract_id": flow_data.get("contract_id", ""),
            "strike_price": float(flow_data.get("strike", 0)),
            "expiration_date": flow_data.get("expiration", ""),
            "option_type": flow_data.get("type", ""),  # 'call' or 'put'
            "sentiment": flow_data.get("sentiment", "neutral"),
            "volume": int(flow_data.get("volume", 0)),
            "open_interest": int(flow_data.get("open_interest", 0)),
            "implied_volatility": float(flow_data.get("iv", 0)),
            "premium": float(flow_data.get("premium", 0)),
            "unusual_score": float(flow_data.get("unusual_score", 0)),
            "trade_type": flow_data.get("trade_type", ""),
            "raw_data": json.dumps(flow_data)
        }
        
        return formatted_data
    except Exception as e:
        logger.error(f"Error formatting option flow data: {str(e)}")
        return {}

if __name__ == "__main__":
    # Example usage
    try:
        print("Fetching insider trades...")
        insider_trades = get_insider_trades(days=14, limit=5)
        for trade in insider_trades:
            print(f"{trade['insider_name']} - {trade['symbol']} - {trade['transaction_type']} - ${trade['total_value']:,.2f}")
        
        print("\nFetching political trades...")
        political_trades = get_political_trades(days=30, limit=5)
        for trade in political_trades:
            print(f"{trade['politician_name']} ({trade['party']}) - {trade['symbol']} - {trade['transaction_type']} - {trade['amount_range']}")
        
        print("\nFetching analyst ratings...")
        ratings = get_analyst_ratings(days=7, limit=5)
        for rating in ratings:
            print(f"{rating['firm']} - {rating['symbol']} - {rating['rating_change']} - PT: ${rating['price_target']}")
            
        print("\nFetching market sentiment...")
        sentiment = get_market_sentiment()
        print(f"Overall: {sentiment.get('overall_sentiment', 'N/A')}")
        print(f"VIX: {sentiment.get('vix', 'N/A')}")
        print(f"SPY: {sentiment.get('spy_change', 'N/A')}")
        
    except UnusualWhalesError as e:
        print(f"API Error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}") 