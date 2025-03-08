#!/usr/bin/env python3
"""
Stock Info Fetcher (Alpha Vantage)
Fetches basic information about stocks from Alpha Vantage API
"""

import os
import sys
import json
import logging
import time
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from supabase import create_client, Client
import traceback

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from python.alpha_vantage_api import get_stock_info, format_stock_info_for_db

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/stock_info_alpha_fetcher.log")
    ]
)
logger = logging.getLogger("stock_info_alpha_fetcher")

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
ALPHA_VANTAGE_API_KEY = os.getenv("API_KEY_ALPHA_VANTAGE")

# Initialize Supabase client
supabase: Client = None
try:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Successfully initialized Supabase client")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {str(e)}")
    sys.exit(1)

# Constants
STOCK_INFO_TABLE = "stock_info"
UPDATE_INTERVAL_DAYS = 1  # Update stock info daily
MAX_TICKERS_PER_RUN = 5  # Limit to avoid API rate limits


class StockInfoFetcher:
    def __init__(self):
        """Initialize the stock info fetcher."""
        self.last_api_call = 0
        self.min_api_interval = 12.1  # seconds between API calls (Alpha Vantage rate limit is 5 calls per minute for free tier)
        
        # Verify Alpha Vantage API key exists
        if not ALPHA_VANTAGE_API_KEY:
            logger.error("API_KEY_ALPHA_VANTAGE environment variable not set")
            raise ValueError("API_KEY_ALPHA_VANTAGE must be set in environment")
    
    def fetch_user_tickers(self) -> List[str]:
        """
        Fetch tickers from user watchlists.
        
        Returns:
            List of unique ticker symbols
        """
        try:
            logger.info("Fetching user watchlist tickers")
            
            # Get tickers from watchlists table
            response = supabase.table("watchlists").select("ticker").execute()
            
            all_tickers = set()
            for watchlist in response.data:
                ticker = watchlist.get("ticker")
                if ticker:
                    all_tickers.add(ticker)
            
            # Get any additional tickers from portfolios table if it exists
            try:
                response = supabase.table("portfolios").select("ticker").execute()
                for portfolio in response.data:
                    ticker = portfolio.get("ticker")
                    if ticker:
                        all_tickers.add(ticker)
            except Exception as e:
                logger.warning(f"Error fetching portfolio tickers: {str(e)}")
            
            # If no tickers found, use some default popular tickers
            if not all_tickers:
                logger.warning("No tickers found in database, using default tickers")
                default_tickers = ["AAPL", "MSFT", "GOOG", "AMZN", "META", "TSLA", "NVDA", "AMD", "SPY", "QQQ"]
                all_tickers.update(default_tickers)
            
            logger.info(f"Found {len(all_tickers)} unique tickers to process")
            
            # Limit the number of tickers to avoid exceeding API rate limits
            return list(all_tickers)[:MAX_TICKERS_PER_RUN]
        except Exception as e:
            logger.error(f"Error fetching user tickers: {str(e)}")
            # Return default tickers in case of error
            return ["AAPL", "MSFT", "GOOG", "AMZN", "META"]
    
    def should_update_ticker_info(self, ticker: str) -> bool:
        """
        Check if a ticker's info should be updated.
        
        Args:
            ticker: The ticker symbol to check
            
        Returns:
            True if the ticker's info should be updated, False otherwise
        """
        try:
            # Check if we have recent data for this ticker
            response = supabase.table(STOCK_INFO_TABLE) \
                .select("fetched_at") \
                .eq("ticker", ticker) \
                .execute()
            
            # If no data exists, we should definitely update
            if not response.data or len(response.data) == 0:
                return True
            
            # Check if data is older than our update interval
            fetched_at = response.data[0].get("fetched_at")
            if fetched_at:
                fetched_date = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
                update_threshold = datetime.now() - timedelta(days=UPDATE_INTERVAL_DAYS)
                
                # If data is older than the threshold, update it
                if fetched_date < update_threshold:
                    logger.info(f"Stock info for {ticker} is outdated, last update: {fetched_date}")
                    return True
                else:
                    logger.info(f"Stock info for {ticker} is recent, skipping update")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error checking update status for {ticker}: {str(e)}")
            return True  # Default to updating if we hit an error
    
    def process_ticker(self, ticker: str) -> bool:
        """
        Process a single ticker, fetching and storing its info.
        
        Args:
            ticker: The ticker symbol to process
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if we should update this ticker
            if not self.should_update_ticker_info(ticker):
                return True
            
            logger.info(f"Processing ticker {ticker}")
            
            # Apply rate limiting
            current_time = time.time()
            time_since_last_call = current_time - self.last_api_call
            if time_since_last_call < self.min_api_interval:
                sleep_time = self.min_api_interval - time_since_last_call
                logger.info(f"Rate limiting: Sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
            
            # Get stock info from API
            stock_info = get_stock_info(ticker)
            self.last_api_call = time.time()
            
            if not stock_info:
                logger.warning(f"No data returned for {ticker}")
                return False
            
            # Format the data for the database
            formatted_info = format_stock_info_for_db(stock_info, ticker)
            
            # Debug output
            logger.info(f"Formatted data for {ticker}: {json.dumps(formatted_info, indent=2)}")
            
            # Upsert to database
            response = supabase.table(STOCK_INFO_TABLE) \
                .upsert(formatted_info, on_conflict="ticker") \
                .execute()
            
            logger.info(f"Successfully updated stock info for {ticker}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing ticker {ticker}: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def run(self, tickers=None):
        """
        Run the stock info fetcher.
        
        Args:
            tickers: Optional list of tickers to process. If None, fetch from user watchlists.
            
        Returns:
            Dictionary with results summary
        """
        logger.info("Starting stock info fetcher")
        
        try:
            # Get tickers to process
            if tickers is None:
                tickers = self.fetch_user_tickers()
                
            if not tickers:
                logger.warning("No tickers found to process")
                return {"status": "success", "tickers_processed": 0, "message": "No tickers found"}
                
            logger.info(f"Processing {len(tickers)} tickers: {', '.join(tickers)}")
            
            # Process tickers sequentially
            results = {"success": 0, "failure": 0}
            
            for ticker in tickers:
                success = self.process_ticker(ticker)
                if success:
                    results["success"] += 1
                else:
                    results["failure"] += 1
                
                # Add a small delay between processing tickers
                time.sleep(0.1)
            
            logger.info(f"Stock info fetcher completed - Processed {len(tickers)} tickers")
            logger.info(f"Results: {results['success']} successful, {results['failure']} failed")
            
            return {
                "status": "success",
                "tickers_processed": len(tickers),
                "successful": results["success"],
                "failed": results["failure"]
            }
            
        except Exception as e:
            logger.error(f"Error running stock info fetcher: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "error": str(e)
            }

def main():
    """Run the stock info fetcher as a standalone script."""
    parser = argparse.ArgumentParser(description='Fetch stock information from Alpha Vantage API')
    parser.add_argument('--tickers', help='Comma-separated list of ticker symbols to process')
    args = parser.parse_args()
    
    tickers = args.tickers.split(',') if args.tickers else None
    
    fetcher = StockInfoFetcher()
    result = fetcher.run(tickers)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main() 