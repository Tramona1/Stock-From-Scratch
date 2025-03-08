#!/usr/bin/env python3
"""
Alpha Vantage API Integration Module
Provides functions for fetching stock market data from the Alpha Vantage API
"""

import os
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
from diskcache import Cache

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("alpha_vantage_api.log")
    ]
)
logger = logging.getLogger("alpha_vantage_api")

# API Configuration
API_BASE_URL = "https://www.alphavantage.co/query"
API_KEY = os.getenv("API_KEY_ALPHA_VANTAGE")

# Setup cache
cache = Cache(".cache")
CACHE_EXPIRY = 3600  # Cache for 1 hour

class AlphaVantageError(Exception):
    """Custom exception for Alpha Vantage API errors"""
    pass

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def make_request(function: str, params: Dict[str, Any] = None) -> Dict:
    """
    Make a request to the Alpha Vantage API with retry logic
    
    Args:
        function: API function to call
        params: Additional query parameters
        
    Returns:
        Dict: API response
    """
    if params is None:
        params = {}
    
    # Add required parameters
    params["function"] = function
    params["apikey"] = API_KEY
    
    # Generate cache key based on function and params
    cache_key = f"{function}-{json.dumps(params)}"
    
    # Check cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.info(f"Using cached data for {function}")
        return cached_data
    
    try:
        logger.info(f"Making request to Alpha Vantage: {function} with params {params}")
        response = requests.get(API_BASE_URL, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for error messages in the response
        if "Error Message" in data:
            logger.error(f"Alpha Vantage API error: {data['Error Message']}")
            raise AlphaVantageError(data["Error Message"])
        
        if "Information" in data:
            logger.warning(f"Alpha Vantage API information: {data['Information']}")
            # Still return the data as it might contain partial results
        
        # Cache successful response
        cache.set(cache_key, data, expire=CACHE_EXPIRY)
        
        return data
    except requests.RequestException as e:
        logger.error(f"Error making request to Alpha Vantage: {str(e)}")
        if hasattr(e.response, 'text'):
            logger.error(f"Response content: {e.response.text}")
        raise AlphaVantageError(f"API request failed: {str(e)}")

def get_stock_quote(ticker: str) -> Dict:
    """
    Get the latest stock quote data from Alpha Vantage
    
    Args:
        ticker: The ticker symbol to get information for
        
    Returns:
        Dictionary containing latest quote information
    """
    try:
        logger.info(f"Fetching stock quote for {ticker}")
        response = make_request("GLOBAL_QUOTE", {"symbol": ticker})
        
        # Debug: Print the response data
        logger.info(f"API Response for {ticker}: {json.dumps(response, indent=2)}")
        
        if "Global Quote" in response and response["Global Quote"]:
            return response["Global Quote"]
        else:
            logger.warning(f"No quote data found for {ticker}")
            return {}
    except Exception as e:
        logger.error(f"Error fetching stock quote for {ticker}: {str(e)}")
        return {}

def get_daily_time_series(ticker: str, outputsize: str = "compact") -> Dict:
    """
    Get daily time series data from Alpha Vantage
    
    Args:
        ticker: The ticker symbol to get information for
        outputsize: 'compact' for last 100 data points, 'full' for 20+ years of data
        
    Returns:
        Dictionary containing daily time series data
    """
    try:
        logger.info(f"Fetching daily time series for {ticker}")
        response = make_request("TIME_SERIES_DAILY", {
            "symbol": ticker,
            "outputsize": outputsize
        })
        
        # Debug: Print the response data
        logger.debug(f"API Response for {ticker}: {json.dumps(response, indent=2)}")
        
        if "Time Series (Daily)" in response:
            return response["Time Series (Daily)"]
        else:
            logger.warning(f"No daily time series data found for {ticker}")
            return {}
    except Exception as e:
        logger.error(f"Error fetching daily time series for {ticker}: {str(e)}")
        return {}

def get_intraday_time_series(ticker: str, interval: str = "5min", outputsize: str = "compact") -> Dict:
    """
    Get intraday time series data from Alpha Vantage
    
    Args:
        ticker: The ticker symbol to get information for
        interval: Time interval between data points (1min, 5min, 15min, 30min, 60min)
        outputsize: 'compact' for last 100 data points, 'full' for extended data
        
    Returns:
        Dictionary containing intraday time series data
    """
    try:
        logger.info(f"Fetching intraday time series for {ticker}")
        response = make_request("TIME_SERIES_INTRADAY", {
            "symbol": ticker,
            "interval": interval,
            "outputsize": outputsize
        })
        
        # Debug: Print the response data
        logger.debug(f"API Response for {ticker}: {json.dumps(response, indent=2)}")
        
        key = f"Time Series ({interval})"
        if key in response:
            return response[key]
        else:
            logger.warning(f"No intraday time series data found for {ticker}")
            return {}
    except Exception as e:
        logger.error(f"Error fetching intraday time series for {ticker}: {str(e)}")
        return {}

def get_weekly_time_series(ticker: str) -> Dict:
    """
    Get weekly time series data from Alpha Vantage
    
    Args:
        ticker: The ticker symbol to get information for
        
    Returns:
        Dictionary containing weekly time series data
    """
    try:
        logger.info(f"Fetching weekly time series for {ticker}")
        response = make_request("TIME_SERIES_WEEKLY", {
            "symbol": ticker
        })
        
        # Debug: Print the response data
        logger.debug(f"API Response for {ticker}: {json.dumps(response, indent=2)}")
        
        if "Weekly Time Series" in response:
            return response["Weekly Time Series"]
        else:
            logger.warning(f"No weekly time series data found for {ticker}")
            return {}
    except Exception as e:
        logger.error(f"Error fetching weekly time series for {ticker}: {str(e)}")
        return {}

def get_monthly_time_series(ticker: str) -> Dict:
    """
    Get monthly time series data from Alpha Vantage
    
    Args:
        ticker: The ticker symbol to get information for
        
    Returns:
        Dictionary containing monthly time series data
    """
    try:
        logger.info(f"Fetching monthly time series for {ticker}")
        response = make_request("TIME_SERIES_MONTHLY", {
            "symbol": ticker
        })
        
        # Debug: Print the response data
        logger.debug(f"API Response for {ticker}: {json.dumps(response, indent=2)}")
        
        if "Monthly Time Series" in response:
            return response["Monthly Time Series"]
        else:
            logger.warning(f"No monthly time series data found for {ticker}")
            return {}
    except Exception as e:
        logger.error(f"Error fetching monthly time series for {ticker}: {str(e)}")
        return {}

def search_ticker(keywords: str) -> List[Dict]:
    """
    Search for ticker symbols based on keywords
    
    Args:
        keywords: Search keywords
        
    Returns:
        List of matching ticker information
    """
    try:
        logger.info(f"Searching for ticker with keywords: {keywords}")
        response = make_request("SYMBOL_SEARCH", {
            "keywords": keywords
        })
        
        # Debug: Print the response data
        logger.debug(f"API Response for search '{keywords}': {json.dumps(response, indent=2)}")
        
        if "bestMatches" in response:
            return response["bestMatches"]
        else:
            logger.warning(f"No matches found for {keywords}")
            return []
    except Exception as e:
        logger.error(f"Error searching for ticker {keywords}: {str(e)}")
        return []

def get_market_status() -> Dict:
    """
    Get global market open/close status
    
    Returns:
        Dictionary containing market status information
    """
    try:
        logger.info("Fetching market status")
        response = make_request("MARKET_STATUS")
        
        # Debug: Print the response data
        logger.debug(f"API Response for market status: {json.dumps(response, indent=2)}")
        
        if "markets" in response:
            return response
        else:
            logger.warning("No market status data found")
            return {}
    except Exception as e:
        logger.error(f"Error fetching market status: {str(e)}")
        return {}

def get_stock_info(ticker: str) -> Dict:
    """
    Get comprehensive stock information combining multiple endpoints
    
    Args:
        ticker: The ticker symbol to get information for
        
    Returns:
        Dictionary containing combined stock information
    """
    logger.info(f"Getting comprehensive stock info for {ticker}")
    
    # Get quote data first (basic info)
    quote_data = get_stock_quote(ticker)
    
    # Get latest daily data
    try:
        daily_data = get_daily_time_series(ticker)
        latest_date = list(daily_data.keys())[0] if daily_data else None
        latest_daily = daily_data.get(latest_date, {}) if latest_date else {}
    except (IndexError, KeyError):
        logger.warning(f"Could not extract latest daily data for {ticker}")
        latest_date = None
        latest_daily = {}
    
    # Get monthly data for longer-term metrics
    try:
        monthly_data = get_monthly_time_series(ticker)
        monthly_dates = list(monthly_data.keys())
        current_month = monthly_dates[0] if monthly_dates else None
        last_month = monthly_dates[1] if len(monthly_dates) > 1 else None
        
        current_month_data = monthly_data.get(current_month, {}) if current_month else {}
        last_month_data = monthly_data.get(last_month, {}) if last_month else {}
    except (IndexError, KeyError):
        logger.warning(f"Could not extract monthly data for {ticker}")
        current_month_data = {}
        last_month_data = {}
    
    # Search for company information
    search_results = search_ticker(ticker)
    company_info = search_results[0] if search_results else {}
    
    # Compile the data
    result = {
        "ticker": ticker,
        "price": float(quote_data.get("05. price", 0)),
        "change_percent": quote_data.get("10. change percent", "0%"),
        "volume": int(quote_data.get("06. volume", 0)),
        "latest_trading_day": quote_data.get("07. latest trading day", ""),
        "previous_close": float(quote_data.get("08. previous close", 0)),
        "change": float(quote_data.get("09. change", 0)),
        "open": float(latest_daily.get("1. open", 0)),
        "high": float(latest_daily.get("2. high", 0)),
        "low": float(latest_daily.get("3. low", 0)),
        "close": float(latest_daily.get("4. close", 0)),
        "daily_volume": int(latest_daily.get("5. volume", 0)),
        "monthly_high": float(current_month_data.get("2. high", 0)),
        "monthly_low": float(current_month_data.get("3. low", 0)),
        "prev_month_high": float(last_month_data.get("2. high", 0)),
        "prev_month_low": float(last_month_data.get("3. low", 0)),
        "name": company_info.get("2. name", ""),
        "type": company_info.get("3. type", ""),
        "region": company_info.get("4. region", ""),
        "currency": company_info.get("8. currency", "USD"),
        "fetched_at": datetime.utcnow().isoformat()
    }
    
    logger.info(f"Compiled stock info for {ticker}")
    return result

def format_stock_info_for_db(info: Dict, ticker: str) -> Dict:
    """
    Format stock information for database storage.
    
    Args:
        info: The stock information 
        ticker: The ticker symbol
        
    Returns:
        Formatted dictionary ready for database storage
    """
    # Debug: Print the input data
    logger.info(f"Formatting stock info for {ticker}")
    
    now = datetime.utcnow().isoformat()
    
    formatted_data = {
        "ticker": ticker,
        "company_name": info.get("name", ""),
        "sector": info.get("type", ""),  # Using type as sector for now
        "market_cap": 0,  # Not available in the free API
        "avg_volume": info.get("volume", 0),
        "description": "",  # Not available in the current API calls
        "logo_url": "",  # Not available in the current API calls
        "current_price": info.get("price", 0),
        "open_price": info.get("open", 0),
        "daily_high": info.get("high", 0),
        "daily_low": info.get("low", 0),
        "daily_volume": info.get("daily_volume", 0),
        "fifty_two_week_high": max(info.get("monthly_high", 0), info.get("prev_month_high", 0)),
        "fifty_two_week_low": min(info.get("monthly_low", 0) if info.get("monthly_low", 0) > 0 else float('inf'), 
                                info.get("prev_month_low", 0) if info.get("prev_month_low", 0) > 0 else float('inf')),
        "pe_ratio": 0,  # Not available in the free API
        "eps": 0,  # Not available in the free API
        "price_updated_at": datetime.utcnow().isoformat(),
        "fetched_at": now
    }
    
    # Debug: Print the formatted data
    logger.info(f"Formatted data for {ticker}")
    
    return formatted_data

# Clear cache function
def clear_cache() -> None:
    """Clear the API cache"""
    cache.clear()
    logger.info("Cache cleared")

# Add new functions for cryptocurrency data

def get_crypto_exchange_rate(from_currency: str, to_currency: str) -> Dict:
    """
    Get the current exchange rate for a cryptocurrency to fiat currency pair
    
    Args:
        from_currency: The source currency (e.g., 'BTC')
        to_currency: The target currency (e.g., 'USD')
        
    Returns:
        Dictionary containing exchange rate information
    """
    try:
        logger.info(f"Fetching crypto exchange rate for {from_currency} to {to_currency}")
        response = make_request("CURRENCY_EXCHANGE_RATE", {
            "from_currency": from_currency,
            "to_currency": to_currency
        })
        
        # Debug: Print the response data
        logger.debug(f"API Response for {from_currency} to {to_currency}: {json.dumps(response, indent=2)}")
        
        if "Realtime Currency Exchange Rate" in response:
            return response["Realtime Currency Exchange Rate"]
        else:
            logger.warning(f"No exchange rate data found for {from_currency} to {to_currency}")
            return {}
    except Exception as e:
        logger.error(f"Error fetching crypto exchange rate for {from_currency} to {to_currency}: {str(e)}")
        return {}

def get_digital_currency_daily(symbol: str, market: str = "USD") -> Dict:
    """
    Get daily time series for a digital currency
    
    Args:
        symbol: The digital/crypto currency symbol (e.g., 'BTC')
        market: The market to convert to (e.g., 'USD')
        
    Returns:
        Dictionary containing daily time series data
    """
    try:
        logger.info(f"Fetching daily time series for {symbol} in {market}")
        response = make_request("DIGITAL_CURRENCY_DAILY", {
            "symbol": symbol,
            "market": market
        })
        
        # Debug: Print the response data
        logger.debug(f"API Response for {symbol} in {market}: {json.dumps(response, indent=2)}")
        
        key = f"Time Series (Digital Currency Daily)"
        if key in response:
            return response[key]
        else:
            logger.warning(f"No daily time series data found for {symbol} in {market}")
            return {}
    except Exception as e:
        logger.error(f"Error fetching daily time series for {symbol} in {market}: {str(e)}")
        return {}

def get_digital_currency_weekly(symbol: str, market: str = "USD") -> Dict:
    """
    Get weekly time series for a digital currency
    
    Args:
        symbol: The digital/crypto currency symbol (e.g., 'BTC')
        market: The market to convert to (e.g., 'USD')
        
    Returns:
        Dictionary containing weekly time series data
    """
    try:
        logger.info(f"Fetching weekly time series for {symbol} in {market}")
        response = make_request("DIGITAL_CURRENCY_WEEKLY", {
            "symbol": symbol,
            "market": market
        })
        
        # Debug: Print the response data
        logger.debug(f"API Response for {symbol} in {market}: {json.dumps(response, indent=2)}")
        
        key = f"Time Series (Digital Currency Weekly)"
        if key in response:
            return response[key]
        else:
            logger.warning(f"No weekly time series data found for {symbol} in {market}")
            return {}
    except Exception as e:
        logger.error(f"Error fetching weekly time series for {symbol} in {market}: {str(e)}")
        return {}

def get_digital_currency_monthly(symbol: str, market: str = "USD") -> Dict:
    """
    Get monthly time series for a digital currency
    
    Args:
        symbol: The digital/crypto currency symbol (e.g., 'BTC')
        market: The market to convert to (e.g., 'USD')
        
    Returns:
        Dictionary containing monthly time series data
    """
    try:
        logger.info(f"Fetching monthly time series for {symbol} in {market}")
        response = make_request("DIGITAL_CURRENCY_MONTHLY", {
            "symbol": symbol,
            "market": market
        })
        
        # Debug: Print the response data
        logger.debug(f"API Response for {symbol} in {market}: {json.dumps(response, indent=2)}")
        
        key = f"Time Series (Digital Currency Monthly)"
        if key in response:
            return response[key]
        else:
            logger.warning(f"No monthly time series data found for {symbol} in {market}")
            return {}
    except Exception as e:
        logger.error(f"Error fetching monthly time series for {symbol} in {market}: {str(e)}")
        return {}

# Add new functions for forex (FX) data

def get_forex_exchange_rate(from_currency: str, to_currency: str) -> Dict:
    """
    Get the current exchange rate for a forex currency pair
    
    Args:
        from_currency: The source currency (e.g., 'EUR')
        to_currency: The target currency (e.g., 'USD')
        
    Returns:
        Dictionary containing exchange rate information
    """
    try:
        logger.info(f"Fetching forex exchange rate for {from_currency} to {to_currency}")
        response = make_request("CURRENCY_EXCHANGE_RATE", {
            "from_currency": from_currency,
            "to_currency": to_currency
        })
        
        # Debug: Print the response data
        logger.debug(f"API Response for {from_currency} to {to_currency}: {json.dumps(response, indent=2)}")
        
        if "Realtime Currency Exchange Rate" in response:
            return response["Realtime Currency Exchange Rate"]
        else:
            logger.warning(f"No exchange rate data found for {from_currency} to {to_currency}")
            return {}
    except Exception as e:
        logger.error(f"Error fetching forex exchange rate for {from_currency} to {to_currency}: {str(e)}")
        return {}

def get_forex_daily(from_symbol: str, to_symbol: str, outputsize: str = "compact") -> Dict:
    """
    Get daily time series for a forex currency pair
    
    Args:
        from_symbol: The source currency (e.g., 'EUR')
        to_symbol: The target currency (e.g., 'USD')
        outputsize: 'compact' for last 100 data points, 'full' for full data
        
    Returns:
        Dictionary containing daily time series data
    """
    try:
        logger.info(f"Fetching daily time series for {from_symbol} to {to_symbol}")
        response = make_request("FX_DAILY", {
            "from_symbol": from_symbol,
            "to_symbol": to_symbol,
            "outputsize": outputsize
        })
        
        # Debug: Print the response data
        logger.debug(f"API Response for {from_symbol} to {to_symbol}: {json.dumps(response, indent=2)}")
        
        key = f"Time Series FX (Daily)"
        if key in response:
            return response[key]
        else:
            logger.warning(f"No daily time series data found for {from_symbol} to {to_symbol}")
            return {}
    except Exception as e:
        logger.error(f"Error fetching daily time series for {from_symbol} to {to_symbol}: {str(e)}")
        return {}

def get_forex_weekly(from_symbol: str, to_symbol: str) -> Dict:
    """
    Get weekly time series for a forex currency pair
    
    Args:
        from_symbol: The source currency (e.g., 'EUR')
        to_symbol: The target currency (e.g., 'USD')
        
    Returns:
        Dictionary containing weekly time series data
    """
    try:
        logger.info(f"Fetching weekly time series for {from_symbol} to {to_symbol}")
        response = make_request("FX_WEEKLY", {
            "from_symbol": from_symbol,
            "to_symbol": to_symbol
        })
        
        # Debug: Print the response data
        logger.debug(f"API Response for {from_symbol} to {to_symbol}: {json.dumps(response, indent=2)}")
        
        key = f"Time Series FX (Weekly)"
        if key in response:
            return response[key]
        else:
            logger.warning(f"No weekly time series data found for {from_symbol} to {to_symbol}")
            return {}
    except Exception as e:
        logger.error(f"Error fetching weekly time series for {from_symbol} to {to_symbol}: {str(e)}")
        return {}

def get_forex_monthly(from_symbol: str, to_symbol: str) -> Dict:
    """
    Get monthly time series for a forex currency pair
    
    Args:
        from_symbol: The source currency (e.g., 'EUR')
        to_symbol: The target currency (e.g., 'USD')
        
    Returns:
        Dictionary containing monthly time series data
    """
    try:
        logger.info(f"Fetching monthly time series for {from_symbol} to {to_symbol}")
        response = make_request("FX_MONTHLY", {
            "from_symbol": from_symbol,
            "to_symbol": to_symbol
        })
        
        # Debug: Print the response data
        logger.debug(f"API Response for {from_symbol} to {to_symbol}: {json.dumps(response, indent=2)}")
        
        key = f"Time Series FX (Monthly)"
        if key in response:
            return response[key]
        else:
            logger.warning(f"No monthly time series data found for {from_symbol} to {to_symbol}")
            return {}
    except Exception as e:
        logger.error(f"Error fetching monthly time series for {from_symbol} to {to_symbol}: {str(e)}")
        return {}

# Add new functions for commodity data

def get_commodity_data(commodity: str, interval: str = "monthly") -> Dict:
    """
    Get time series data for a commodity
    
    Args:
        commodity: The commodity function name (e.g., 'WTI', 'BRENT', 'NATURAL_GAS', etc.)
        interval: Time interval (daily, weekly, monthly, quarterly, annual)
        
    Returns:
        Dictionary containing time series data
    """
    try:
        logger.info(f"Fetching {interval} time series for {commodity}")
        response = make_request(commodity, {
            "interval": interval
        })
        
        # Debug: Print the response data
        logger.debug(f"API Response for {commodity} ({interval}): {json.dumps(response, indent=2)}")
        
        if "data" in response:
            return response["data"]
        else:
            logger.warning(f"No {interval} time series data found for {commodity}")
            return {}
    except Exception as e:
        logger.error(f"Error fetching {interval} time series for {commodity}: {str(e)}")
        return {}

def get_crypto_info(symbol: str, market: str = "USD") -> Dict:
    """
    Get comprehensive cryptocurrency information
    
    Args:
        symbol: The cryptocurrency symbol (e.g., 'BTC')
        market: The market currency (e.g., 'USD')
        
    Returns:
        Dictionary containing combined cryptocurrency information
    """
    logger.info(f"Getting comprehensive crypto info for {symbol} in {market}")
    
    # Get current exchange rate
    exchange_rate_data = get_crypto_exchange_rate(symbol, market)
    
    # Get daily data for recent price info
    try:
        daily_data = get_digital_currency_daily(symbol, market)
        latest_date = list(daily_data.keys())[0] if daily_data else None
        latest_daily = daily_data.get(latest_date, {}) if latest_date else {}
    except (IndexError, KeyError):
        logger.warning(f"Could not extract latest daily data for {symbol}")
        latest_date = None
        latest_daily = {}
    
    # Get monthly data for longer-term metrics
    try:
        monthly_data = get_digital_currency_monthly(symbol, market)
        monthly_dates = list(monthly_data.keys())
        current_month = monthly_dates[0] if monthly_dates else None
        last_month = monthly_dates[1] if len(monthly_dates) > 1 else None
        
        current_month_data = monthly_data.get(current_month, {}) if current_month else {}
        last_month_data = monthly_data.get(last_month, {}) if last_month else {}
    except (IndexError, KeyError):
        logger.warning(f"Could not extract monthly data for {symbol}")
        current_month_data = {}
        last_month_data = {}
    
    # Compile the data
    result = {
        "symbol": symbol,
        "market": market,
        "price": float(exchange_rate_data.get("5. Exchange Rate", 0)),
        "price_updated_at": exchange_rate_data.get("6. Last Refreshed", ""),
        "bid_price": float(exchange_rate_data.get("8. Bid Price", 0)),
        "ask_price": float(exchange_rate_data.get("9. Ask Price", 0)),
        "open": float(latest_daily.get(f"1a. open ({market})", 0)),
        "high": float(latest_daily.get(f"2a. high ({market})", 0)),
        "low": float(latest_daily.get(f"3a. low ({market})", 0)),
        "close": float(latest_daily.get(f"4a. close ({market})", 0)),
        "volume": float(latest_daily.get(f"5. volume", 0)),
        "market_cap": float(latest_daily.get(f"6. market cap ({market})", 0)),
        "monthly_high": float(current_month_data.get(f"2a. high ({market})", 0)),
        "monthly_low": float(current_month_data.get(f"3a. low ({market})", 0)),
        "prev_month_high": float(last_month_data.get(f"2a. high ({market})", 0)),
        "prev_month_low": float(last_month_data.get(f"3a. low ({market})", 0)),
        "latest_trading_day": latest_date,
        "fetched_at": datetime.utcnow().isoformat()
    }
    
    logger.info(f"Compiled crypto info for {symbol}")
    return result

def format_crypto_info_for_db(info: Dict, symbol: str) -> Dict:
    """
    Format cryptocurrency information for database storage.
    
    Args:
        info: The cryptocurrency information 
        symbol: The cryptocurrency symbol
        
    Returns:
        Formatted dictionary ready for database storage
    """
    logger.info(f"Formatting crypto info for {symbol}")
    
    now = datetime.utcnow().isoformat()
    
    formatted_data = {
        "symbol": symbol,
        "market": info.get("market", "USD"),
        "name": symbol,  # We don't get the full name from this API
        "current_price": info.get("price", 0),
        "bid_price": info.get("bid_price", 0),
        "ask_price": info.get("ask_price", 0),
        "open_price": info.get("open", 0),
        "daily_high": info.get("high", 0),
        "daily_low": info.get("low", 0),
        "daily_volume": info.get("volume", 0),
        "market_cap": info.get("market_cap", 0),
        "price_change_24h": 0,  # Not directly available
        "price_change_percentage_24h": 0,  # Not directly available
        "market_cap_rank": 0,  # Not available
        "price_updated_at": info.get("price_updated_at", now),
        "fetched_at": now
    }
    
    logger.info(f"Formatted data for {symbol}")
    return formatted_data

def get_forex_info(from_currency: str, to_currency: str) -> Dict:
    """
    Get comprehensive forex information
    
    Args:
        from_currency: The source currency (e.g., 'EUR')
        to_currency: The target currency (e.g., 'USD')
        
    Returns:
        Dictionary containing combined forex information
    """
    logger.info(f"Getting comprehensive forex info for {from_currency}/{to_currency}")
    
    # Get current exchange rate
    exchange_rate_data = get_forex_exchange_rate(from_currency, to_currency)
    
    # Get daily data for recent price info
    try:
        daily_data = get_forex_daily(from_currency, to_currency)
        latest_date = list(daily_data.keys())[0] if daily_data else None
        latest_daily = daily_data.get(latest_date, {}) if latest_date else {}
    except (IndexError, KeyError):
        logger.warning(f"Could not extract latest daily data for {from_currency}/{to_currency}")
        latest_date = None
        latest_daily = {}
    
    # Get weekly data
    try:
        weekly_data = get_forex_weekly(from_currency, to_currency)
        latest_week = list(weekly_data.keys())[0] if weekly_data else None
        latest_weekly = weekly_data.get(latest_week, {}) if latest_week else {}
    except (IndexError, KeyError):
        logger.warning(f"Could not extract latest weekly data for {from_currency}/{to_currency}")
        latest_weekly = {}
    
    # Compile the data
    result = {
        "from_currency": from_currency,
        "to_currency": to_currency,
        "exchange_rate": float(exchange_rate_data.get("5. Exchange Rate", 0)),
        "bid_price": float(exchange_rate_data.get("8. Bid Price", 0)),
        "ask_price": float(exchange_rate_data.get("9. Ask Price", 0)),
        "updated_at": exchange_rate_data.get("6. Last Refreshed", ""),
        "open": float(latest_daily.get("1. open", 0)),
        "high": float(latest_daily.get("2. high", 0)),
        "low": float(latest_daily.get("3. low", 0)),
        "close": float(latest_daily.get("4. close", 0)),
        "weekly_open": float(latest_weekly.get("1. open", 0)),
        "weekly_high": float(latest_weekly.get("2. high", 0)),
        "weekly_low": float(latest_weekly.get("3. low", 0)),
        "weekly_close": float(latest_weekly.get("4. close", 0)),
        "latest_trading_day": latest_date,
        "fetched_at": datetime.utcnow().isoformat()
    }
    
    logger.info(f"Compiled forex info for {from_currency}/{to_currency}")
    return result

def format_forex_info_for_db(info: Dict) -> Dict:
    """
    Format forex information for database storage.
    
    Args:
        info: The forex information
        
    Returns:
        Formatted dictionary ready for database storage
    """
    logger.info(f"Formatting forex info for {info.get('from_currency')}/{info.get('to_currency')}")
    
    now = datetime.utcnow().isoformat()
    
    formatted_data = {
        "from_currency": info.get("from_currency", ""),
        "to_currency": info.get("to_currency", ""),
        "currency_pair": f"{info.get('from_currency')}/{info.get('to_currency')}",
        "exchange_rate": info.get("exchange_rate", 0),
        "bid_price": info.get("bid_price", 0),
        "ask_price": info.get("ask_price", 0),
        "open_price": info.get("open", 0),
        "daily_high": info.get("high", 0),
        "daily_low": info.get("low", 0),
        "daily_close": info.get("close", 0),
        "weekly_open": info.get("weekly_open", 0),
        "weekly_high": info.get("weekly_high", 0),
        "weekly_low": info.get("weekly_low", 0),
        "weekly_close": info.get("weekly_close", 0),
        "last_refreshed": info.get("updated_at", ""),
        "price_updated_at": info.get("updated_at", now),
        "fetched_at": now
    }
    
    logger.info(f"Formatted data for {info.get('from_currency')}/{info.get('to_currency')}")
    return formatted_data

def get_commodity_info(commodity: str) -> Dict:
    """
    Get comprehensive commodity information
    
    Args:
        commodity: The commodity function name (e.g., 'WTI', 'BRENT', 'NATURAL_GAS', etc.)
        
    Returns:
        Dictionary containing combined commodity information
    """
    logger.info(f"Getting comprehensive commodity info for {commodity}")
    
    # Get data for different intervals
    daily_data = get_commodity_data(commodity, "daily") if commodity in ["WTI", "BRENT", "NATURAL_GAS"] else {}
    weekly_data = get_commodity_data(commodity, "weekly") if commodity in ["WTI", "BRENT", "NATURAL_GAS"] else {}
    monthly_data = get_commodity_data(commodity, "monthly")
    
    # Get the latest data points
    try:
        latest_daily = daily_data[0] if daily_data else None
        latest_weekly = weekly_data[0] if weekly_data else None
        latest_monthly = monthly_data[0] if monthly_data else None
    except (IndexError, KeyError):
        logger.warning(f"Could not extract latest data for {commodity}")
        latest_daily = None
        latest_weekly = None
        latest_monthly = None
    
    # Map commodity function to display name
    commodity_names = {
        "WTI": "Crude Oil WTI",
        "BRENT": "Crude Oil Brent",
        "NATURAL_GAS": "Natural Gas",
        "COPPER": "Copper",
        "ALUMINUM": "Aluminum",
        "WHEAT": "Wheat",
        "CORN": "Corn",
        "COTTON": "Cotton",
        "SUGAR": "Sugar",
        "COFFEE": "Coffee",
        "ALL_COMMODITIES": "All Commodities Index"
    }
    
    # Compile the data
    result = {
        "function": commodity,
        "name": commodity_names.get(commodity, commodity),
        "daily_value": float(latest_daily["value"]) if latest_daily else 0,
        "daily_date": latest_daily["date"] if latest_daily else "",
        "weekly_value": float(latest_weekly["value"]) if latest_weekly else 0,
        "weekly_date": latest_weekly["date"] if latest_weekly else "",
        "monthly_value": float(latest_monthly["value"]) if latest_monthly else 0,
        "monthly_date": latest_monthly["date"] if latest_monthly else "",
        "unit": "USD per barrel" if commodity in ["WTI", "BRENT"] else 
                "USD per million BTU" if commodity == "NATURAL_GAS" else
                "USD per metric ton" if commodity in ["COPPER", "ALUMINUM"] else
                "USD per bushel" if commodity in ["WHEAT", "CORN"] else
                "USD per pound" if commodity in ["COTTON", "SUGAR"] else
                "Index" if commodity == "ALL_COMMODITIES" else "USD",
        "fetched_at": datetime.utcnow().isoformat()
    }
    
    logger.info(f"Compiled commodity info for {commodity}")
    return result

def format_commodity_info_for_db(info: Dict) -> Dict:
    """
    Format commodity information for database storage.
    
    Args:
        info: The commodity information
        
    Returns:
        Formatted dictionary ready for database storage
    """
    logger.info(f"Formatting commodity info for {info.get('function')}")
    
    now = datetime.utcnow().isoformat()
    
    formatted_data = {
        "function": info.get("function", ""),
        "name": info.get("name", ""),
        "daily_value": info.get("daily_value", 0),
        "daily_date": info.get("daily_date", ""),
        "weekly_value": info.get("weekly_value", 0),
        "weekly_date": info.get("weekly_date", ""),
        "monthly_value": info.get("monthly_value", 0),
        "monthly_date": info.get("monthly_date", ""),
        "unit": info.get("unit", ""),
        "fetched_at": now
    }
    
    logger.info(f"Formatted data for {info.get('function')}")
    return formatted_data

# Add functions for technical indicators

def get_technical_indicator(function: str, symbol: str, interval: str, 
                          series_type: str, **kwargs) -> Dict:
    """
    Get technical indicator data from Alpha Vantage API
    
    Args:
        function: The technical indicator function (e.g., 'MACD', 'RSI', 'MACDEXT')
        symbol: The ticker symbol to get information for
        interval: Time interval (1min, 5min, 15min, 30min, 60min, daily, weekly, monthly)
        series_type: Price type (close, open, high, low)
        **kwargs: Additional parameters specific to each indicator
        
    Returns:
        Dictionary containing technical indicator data
    """
    try:
        logger.info(f"Fetching {function} for {symbol} ({interval}, {series_type})")
        
        # Prepare API parameters
        params = {
            "symbol": symbol,
            "interval": interval,
            "series_type": series_type
        }
        
        # Add optional parameters
        params.update(kwargs)
        
        # Make the API request
        response = make_request(function, params)
        
        # Debug: Print the response data
        logger.debug(f"API Response for {function} ({symbol}): {json.dumps(response, indent=2)}")
        
        # Check for premium API message
        if "Information" in response and "premium" in response["Information"].lower():
            logger.warning(f"Premium API required for {function}: {response['Information']}")
            return {}
        
        # Check for other error messages
        if "Error Message" in response:
            logger.error(f"API Error for {function}: {response['Error Message']}")
            return {}
        
        # Filter out metadata keys
        data_keys = [key for key in response.keys() if key not in 
                    ["Meta Data", "Information", "Error Message", "Note"]]
        
        if not data_keys:
            logger.warning(f"No data keys found in {function} response for {symbol}")
            return {}
            
        # Extract the technical indicator data - handle different response structures
        if len(data_keys) > 0:
            key = data_keys[0]  # Use the first data key
            if isinstance(response[key], dict):
                return response[key]
            else:
                logger.warning(f"Unexpected data format for {function}: {key} is not a dictionary")
                return {}
        
        logger.warning(f"No {function} data found for {symbol}. Keys in response: {list(response.keys())}")
        return {}
    except Exception as e:
        logger.error(f"Error fetching {function} for {symbol}: {str(e)}")
        return {}

def get_macd(symbol: str, interval: str = "daily", series_type: str = "close", 
            fastperiod: int = 12, slowperiod: int = 26, signalperiod: int = 9, 
            month: str = None) -> Dict:
    """
    Get MACD (Moving Average Convergence/Divergence) values
    
    Args:
        symbol: The ticker symbol
        interval: Time interval between data points
        series_type: Price type (close, open, high, low)
        fastperiod: Fast period
        slowperiod: Slow period
        signalperiod: Signal period
        month: Specific month for intraday data (YYYY-MM format)
        
    Returns:
        Dictionary containing MACD data
    """
    params = {
        "fastperiod": fastperiod,
        "slowperiod": slowperiod,
        "signalperiod": signalperiod
    }
    
    # Add month parameter only for intraday intervals
    if month and interval in ["1min", "5min", "15min", "30min", "60min"]:
        params["month"] = month
    
    return get_technical_indicator("MACD", symbol, interval, series_type, **params)

def get_rsi(symbol: str, interval: str = "daily", time_period: int = 14, 
           series_type: str = "close", month: str = None) -> Dict:
    """
    Get RSI (Relative Strength Index) values
    
    Args:
        symbol: The ticker symbol
        interval: Time interval between data points
        time_period: Number of data points used to calculate each RSI value
        series_type: Price type (close, open, high, low)
        month: Specific month for intraday data (YYYY-MM format)
        
    Returns:
        Dictionary containing RSI data
    """
    params = {
        "time_period": time_period
    }
    
    # Add month parameter only for intraday intervals
    if month and interval in ["1min", "5min", "15min", "30min", "60min"]:
        params["month"] = month
    
    return get_technical_indicator("RSI", symbol, interval, series_type, **params)

def get_macdext(symbol: str, interval: str = "daily", series_type: str = "close", 
               fastperiod: int = 12, slowperiod: int = 26, signalperiod: int = 9,
               fastmatype: int = 0, slowmatype: int = 0, signalmatype: int = 0,
               month: str = None) -> Dict:
    """
    Get MACDEXT (Extended MACD with controllable MA type) values
    
    Args:
        symbol: The ticker symbol
        interval: Time interval between data points
        series_type: Price type (close, open, high, low)
        fastperiod: Fast period
        slowperiod: Slow period
        signalperiod: Signal period
        fastmatype: Moving average type for fast MA (0-8)
        slowmatype: Moving average type for slow MA (0-8)
        signalmatype: Moving average type for signal MA (0-8)
        month: Specific month for intraday data (YYYY-MM format)
        
    Returns:
        Dictionary containing MACDEXT data
    """
    params = {
        "fastperiod": fastperiod,
        "slowperiod": slowperiod,
        "signalperiod": signalperiod,
        "fastmatype": fastmatype,
        "slowmatype": slowmatype,
        "signalmatype": signalmatype
    }
    
    # Add month parameter only for intraday intervals
    if month and interval in ["1min", "5min", "15min", "30min", "60min"]:
        params["month"] = month
    
    return get_technical_indicator("MACDEXT", symbol, interval, series_type, **params)

def get_technical_indicators(symbol: str, interval: str = "daily") -> Dict:
    """
    Get a set of common technical indicators for a symbol
    
    Args:
        symbol: The ticker symbol
        interval: Time interval between data points
        
    Returns:
        Dictionary containing various technical indicators
    """
    logger.info(f"Fetching technical indicators for {symbol} ({interval})")
    
    # Get common technical indicators
    macd_data = get_macd(symbol, interval)
    rsi_data = get_rsi(symbol, interval)
    
    # Log what we received for debugging
    logger.info(f"MACD data keys received: {list(macd_data.keys())[:5] if macd_data else 'None'}")
    logger.info(f"RSI data keys received: {list(rsi_data.keys())[:5] if rsi_data else 'None'}")
    
    # Extract the latest data points
    try:
        # Handle MACD data
        if macd_data and len(macd_data) > 0:
            latest_date = list(macd_data.keys())[0]
            latest_macd = macd_data.get(latest_date, {})
            logger.info(f"Latest MACD data for {symbol} ({latest_date}): {latest_macd}")
        else:
            logger.warning(f"No MACD data found for {symbol}")
            latest_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            latest_macd = {}
        
        # Handle RSI data
        if rsi_data and len(rsi_data) > 0:
            latest_rsi_date = list(rsi_data.keys())[0]
            latest_rsi = rsi_data.get(latest_rsi_date, {})
            logger.info(f"Latest RSI data for {symbol} ({latest_rsi_date}): {latest_rsi}")
        else:
            logger.warning(f"No RSI data found for {symbol}")
            latest_rsi_date = latest_date  # Use MACD date or current date
            latest_rsi = {}
    except (IndexError, KeyError) as e:
        logger.warning(f"Could not extract latest technical data for {symbol}: {str(e)}")
        latest_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        latest_macd = {}
        latest_rsi = {}
    
    # Extract values with better error handling
    try:
        macd_value = float(latest_macd.get("MACD", 0))
    except (ValueError, TypeError):
        logger.warning(f"Invalid MACD value for {symbol}: {latest_macd.get('MACD')}")
        macd_value = 0
        
    try:
        macd_signal = float(latest_macd.get("MACD_Signal", 0))
    except (ValueError, TypeError):
        logger.warning(f"Invalid MACD_Signal value for {symbol}: {latest_macd.get('MACD_Signal')}")
        macd_signal = 0
        
    try:
        macd_hist = float(latest_macd.get("MACD_Hist", 0))
    except (ValueError, TypeError):
        logger.warning(f"Invalid MACD_Hist value for {symbol}: {latest_macd.get('MACD_Hist')}")
        macd_hist = 0
        
    try:
        rsi_value = float(latest_rsi.get("RSI", 0))
    except (ValueError, TypeError):
        logger.warning(f"Invalid RSI value for {symbol}: {latest_rsi.get('RSI')}")
        rsi_value = 0
    
    # Compile the data
    result = {
        "symbol": symbol,
        "interval": interval,
        "date": latest_date,
        "macd": macd_value,
        "macd_signal": macd_signal,
        "macd_hist": macd_hist,
        "rsi": rsi_value,
        "fetched_at": datetime.now(timezone.utc).isoformat()
    }
    
    logger.info(f"Compiled technical indicators for {symbol}: {result}")
    return result

def format_technical_indicators_for_db(info: Dict) -> Dict:
    """
    Format technical indicators for database storage.
    
    Args:
        info: The technical indicators data
        
    Returns:
        Formatted dictionary ready for database storage
    """
    logger.info(f"Formatting technical indicators for {info.get('symbol')}")
    
    now = datetime.now(timezone.utc).isoformat()
    
    formatted_data = {
        "symbol": info.get("symbol", ""),
        "interval": info.get("interval", "daily"),
        "date": info.get("date", ""),
        "macd": info.get("macd", 0),
        "macd_signal": info.get("macd_signal", 0),
        "macd_hist": info.get("macd_hist", 0),
        "rsi": info.get("rsi", 0),
        "fetched_at": info.get("fetched_at", now)
    }
    
    logger.info(f"Formatted data for {info.get('symbol')}")
    return formatted_data 