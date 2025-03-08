#!/usr/bin/env python3
"""
Script to fetch detailed stock information from Unusual Whales API and store it in the database.
This script provides comprehensive company information from the Unusual Whales API.
"""

import os
import sys
import logging
import time
import argparse
import asyncio
from datetime import datetime, timezone
import json
from typing import Dict, List, Any, Optional, Union

import httpx
from dotenv import load_dotenv

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/stock_details_fetcher.log")
    ]
)
logger = logging.getLogger("stock_details_fetcher")

# Add the parent directory to the path so we can import unusual_whales_api
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
UW_API_KEY = os.getenv("API_KEY_UNUSUAL_WHALES")
UW_API_BASE_URL = "https://api.unusualwhales.com/api"

# API request settings
MAX_RETRIES = 3  # Maximum number of retry attempts
INITIAL_BACKOFF = 1  # Initial backoff in seconds
MAX_BACKOFF = 10  # Maximum backoff in seconds

def make_api_request(url, headers, params=None, max_retries=MAX_RETRIES):
    """
    Make an API request with retry logic and exponential backoff.
    
    Args:
        url: API endpoint URL
        headers: Request headers
        params: Query parameters
        max_retries: Maximum retry attempts
        
    Returns:
        API response JSON
    """
    retry_count = 0
    backoff = INITIAL_BACKOFF
    
    while retry_count <= max_retries:
        try:
            logger.info(f"Making request to {url}")
            if params:
                logger.info(f"Making request to {url} with params {params}")
            
            response = httpx.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            # If we get here, request was successful
            return response.json()
            
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            logger.error(f"HTTP error: {status_code} - {e.response.text}")
            
            # Don't retry client errors except rate limit errors
            if status_code >= 400 and status_code < 500 and status_code != 429:
                break
                
            # For 429 (rate limit) or 5xx errors, retry with backoff
            retry_count += 1
            
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout) as e:
            logger.error(f"Connection error: {str(e)}")
            retry_count += 1
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            retry_count += 1
        
        # If we've reached max retries, break
        if retry_count > max_retries:
            logger.error(f"Max retries reached for {url}")
            break
            
        # Exponential backoff with jitter
        sleep_time = min(backoff * (2 ** (retry_count - 1)), MAX_BACKOFF)
        logger.info(f"Retrying in {sleep_time} seconds...")
        time.sleep(sleep_time)
    
    # If we get here, all retries failed
    return None

def get_stock_info(ticker):
    """
    Get detailed stock information for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Stock info data or None if request failed
    """
    url = f"{UW_API_BASE_URL}/stock/{ticker}/info"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {UW_API_KEY}"
    }
    
    response_data = make_api_request(url, headers)
    if response_data:
        logger.info(f"API Response for {ticker}: {json.dumps(response_data, indent=2)}")
        return response_data["data"]
    return None

def format_stock_details_for_db(stock_info, ticker):
    """
    Format the stock info data for database storage.
    
    Args:
        stock_info: Stock info data from API
        ticker: Stock ticker symbol
        
    Returns:
        Formatted data for database
    """
    logger.info(f"Formatting stock info for {ticker}: {json.dumps(stock_info, indent=2)}")
    
    try:
        # Convert market cap to float if possible
        market_cap = 0.0
        if stock_info.get("marketcap"):
            try:
                market_cap = float(stock_info["marketcap"])
            except (ValueError, TypeError):
                logger.warning(f"Could not convert marketcap to float for {ticker}: {stock_info.get('marketcap')}")
        
        # Convert average volume to float if possible
        avg_volume = 0.0
        if stock_info.get("avg30_volume"):
            try:
                avg_volume = float(stock_info["avg30_volume"])
            except (ValueError, TypeError):
                logger.warning(f"Could not convert avg30_volume to float for {ticker}: {stock_info.get('avg30_volume')}")
        
        # Build the data object
        now = datetime.now(timezone.utc).isoformat()
        data = {
            "ticker": ticker,
            "company_name": stock_info.get("full_name", ""),
            "short_name": stock_info.get("short_name", ""),
            "sector": stock_info.get("sector"),
            "market_cap": market_cap,
            "market_cap_size": stock_info.get("marketcap_size"),
            "avg_volume": avg_volume,
            "description": stock_info.get("short_description", ""),
            "logo_url": stock_info.get("logo", ""),
            "issue_type": stock_info.get("issue_type"),
            "has_dividend": stock_info.get("has_dividend", False),
            "has_earnings_history": stock_info.get("has_earnings_history", False),
            "has_investment_arm": stock_info.get("has_investment_arm", False),
            "has_options": stock_info.get("has_options", False),
            "next_earnings_date": stock_info.get("next_earnings_date"),
            "earnings_announce_time": stock_info.get("announce_time"),
            "tags": stock_info.get("uw_tags", []),
            "fetched_at": now
        }
        
        logger.info(f"Formatted data for {ticker}: {json.dumps(data, indent=2)}")
        return data
    except Exception as e:
        logger.error(f"Error formatting data for {ticker}: {str(e)}")
        return None

class StockDetailsFetcher:
    """Class to fetch and store detailed stock information."""
    
    def __init__(self):
        """Initialize the fetcher with Supabase client."""
        try:
            self.supabase_url = SUPABASE_URL
            self.supabase_key = SUPABASE_KEY
            self.headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }
            logger.info("Successfully initialized Supabase client")
        except Exception as e:
            logger.error(f"Error initializing Supabase client: {str(e)}")
            raise
    
    async def is_in_watchlist(self, ticker):
        """Check if a ticker is in the user's watchlist."""
        try:
            url = f"{self.supabase_url}/rest/v1/watchlists"
            params = {"ticker": f"eq.{ticker}", "select": "id"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                return len(data) > 0
        except Exception as e:
            logger.error(f"Error checking if {ticker} is in watchlist: {str(e)}")
            return False
    
    async def fetch_watchlist_tickers(self):
        """Fetch all tickers from the user's watchlist."""
        tickers = []
        try:
            # Fetch watchlist tickers
            url = f"{self.supabase_url}/rest/v1/watchlists"
            params = {"select": "ticker"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Extract tickers from response
                for item in data:
                    if "ticker" in item and item["ticker"]:
                        tickers.append(item["ticker"])
                
                # Try to fetch portfolio tickers too
                try:
                    url = f"{self.supabase_url}/rest/v1/portfolios"
                    params = {"select": "ticker"}
                    
                    response = await client.get(url, headers=self.headers, params=params)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Extract tickers from response
                    for item in data:
                        if "ticker" in item and item["ticker"]:
                            tickers.append(item["ticker"])
                except Exception as e:
                    logger.warning(f"Error fetching portfolio tickers: {str(e)}")
        except Exception as e:
            logger.error(f"Error fetching watchlist tickers: {str(e)}")
        
        # If no tickers found, use default tickers
        if not tickers:
            logger.warning("No tickers found in database, using default tickers")
            tickers = ["AAPL", "MSFT", "GOOG", "AMZN", "META", "TSLA", "NVDA", "AMD", "SPY", "QQQ"]
        
        # Remove duplicates and return
        return list(set(tickers))
    
    async def needs_update(self, ticker):
        """Check if a ticker needs updating (update every 7 days by default)."""
        try:
            url = f"{self.supabase_url}/rest/v1/stock_details"
            params = {"select": "fetched_at", "ticker": f"eq.{ticker}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                if not data:
                    # No existing data, needs update
                    return True
                
                # Check if data is older than 7 days
                fetched_at = data[0].get("fetched_at")
                if not fetched_at:
                    return True
                
                try:
                    fetched_time = datetime.fromisoformat(fetched_at.replace('Z', '+00:00'))
                    now = datetime.now(timezone.utc)
                    age = now - fetched_time
                    
                    # Update if data is older than 7 days
                    return age.days >= 7
                except Exception as e:
                    logger.error(f"Error checking update status for {ticker}: {str(e)}")
                    return True
        except Exception as e:
            logger.error(f"Error checking if {ticker} needs update: {str(e)}")
            return True
    
    async def process_ticker(self, ticker):
        """Process a single ticker to fetch and store its details."""
        try:
            # Check if ticker needs updating
            needs_update = await self.needs_update(ticker)
            if not needs_update:
                logger.info(f"Ticker {ticker} already up to date, skipping")
                return True
            
            logger.info(f"Processing ticker {ticker}")
            
            # Get stock info
            stock_info = get_stock_info(ticker)
            if not stock_info:
                logger.error(f"Failed to get stock info for {ticker}")
                return False
            
            # Format data for database
            formatted_data = format_stock_details_for_db(stock_info, ticker)
            if not formatted_data:
                logger.error(f"Failed to format stock info for {ticker}")
                return False
            
            # Store data
            success = await self.store_stock_details(formatted_data)
            return success
        except Exception as e:
            logger.error(f"Error processing ticker {ticker}: {str(e)}")
            return False
    
    async def store_stock_details(self, data):
        """Store stock details in the database."""
        try:
            url = f"{self.supabase_url}/rest/v1/stock_details"
            params = {"on_conflict": "ticker"}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, 
                    headers=self.headers, 
                    params=params,
                    json=data
                )
                response.raise_for_status()
                
                logger.info(f"Successfully updated stock details for {data['ticker']}")
                return True
        except Exception as e:
            logger.error(f"Error storing stock details for {data['ticker']}: {str(e)}")
            return False
    
    async def run(self, tickers=None, watchlist_only=False):
        """Run the stock details fetcher."""
        logger.info("Starting stock details fetcher")
        
        # Fetch tickers
        if tickers:
            # Convert to list if string
            if isinstance(tickers, str):
                tickers = [ticker.strip() for ticker in tickers.split(",")]
            logger.info(f"Using provided tickers: {tickers}")
        else:
            # Fetch watchlist tickers
            tickers = await self.fetch_watchlist_tickers()
            
            # Filter to watchlist only if requested
            if watchlist_only:
                watchlist_tickers = []
                for ticker in tickers:
                    if await self.is_in_watchlist(ticker):
                        watchlist_tickers.append(ticker)
                tickers = watchlist_tickers
                logger.info(f"Filtered to {len(tickers)} watchlist tickers")
        
        logger.info(f"Found {len(tickers)} unique tickers to process")
        
        # Process tickers
        success_count = 0
        fail_count = 0
        
        logger.info(f"Processing {len(tickers)} tickers")
        for ticker in tickers:
            # Add a small delay between requests to avoid rate limiting
            if success_count + fail_count > 0:
                time.sleep(0.5)
                
            success = await self.process_ticker(ticker)
            if success:
                success_count += 1
            else:
                fail_count += 1
        
        logger.info(f"Stock details fetcher completed - Processed {len(tickers)} tickers")
        logger.info(f"Results: {success_count} successful, {fail_count} failed")
        
        return {
            "status": "success" if fail_count == 0 else "partial_success" if success_count > 0 else "failure",
            "tickers_processed": len(tickers),
            "successful": success_count,
            "failed": fail_count
        }

async def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Fetch detailed stock information")
    parser.add_argument("--tickers", help="Comma-separated list of tickers to process")
    parser.add_argument("--watchlist-only", action="store_true", help="Only process tickers in the watchlist")
    args = parser.parse_args()
    
    # Initialize fetcher
    fetcher = StockDetailsFetcher()
    
    # Run fetcher
    result = await fetcher.run(tickers=args.tickers, watchlist_only=args.watchlist_only)
    
    # Print result as JSON
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    asyncio.run(main()) 