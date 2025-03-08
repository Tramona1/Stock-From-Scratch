#!/usr/bin/env python3
"""
Fetch and store technical indicators for stocks and cryptocurrencies.
"""

import os
import sys
import logging
import argparse
import time
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from dotenv import load_dotenv
import supabase

# Add the directory containing the script to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python.alpha_vantage_api import get_technical_indicators, format_technical_indicators_for_db

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/fetch_technical_indicators.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

# Constants
TECH_INDICATORS_TABLE = "technical_indicators"
UPDATE_INTERVAL_HOURS = 6  # Update technical indicators every 6 hours
MAX_SYMBOLS_PER_RUN = 5  # Limit to 5 symbols per run to avoid API rate limits
DELAY_BETWEEN_REQUESTS = 15  # Seconds between API requests to avoid rate limiting

class TechnicalIndicatorsFetcher:
    """Fetch and store technical indicators for financial instruments."""
    
    def __init__(self):
        """Initialize the fetcher."""
        logger.info("Initializing TechnicalIndicatorsFetcher")
        
        # Initialize Supabase client
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.error("Supabase URL or key not found in environment variables")
            raise ValueError("Supabase URL or key not found")
        
        self.supabase = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)
        self.current_time = datetime.now(timezone.utc)
        
        logger.info("TechnicalIndicatorsFetcher initialized")
    
    def should_update_indicators(self, symbol: str, interval: str = "daily") -> bool:
        """
        Check if technical indicators for the symbol need updating.
        
        Args:
            symbol: The ticker symbol
            interval: The time interval
            
        Returns:
            True if indicators need updating
        """
        logger.info(f"Checking if indicators for {symbol} ({interval}) need updating")
        
        try:
            # Query the latest record for this symbol and interval
            response = self.supabase.table(TECH_INDICATORS_TABLE) \
                .select("*") \
                .eq("symbol", symbol) \
                .eq("interval", interval) \
                .order("fetched_at", desc=True) \
                .limit(1) \
                .execute()
            
            records = response.data
            
            if not records:
                logger.info(f"No existing indicators found for {symbol}, will fetch new data")
                return True
            
            # Check if the last update was more than UPDATE_INTERVAL_HOURS ago
            last_updated_str = records[0]["fetched_at"].replace("Z", "+00:00")
            last_updated = datetime.fromisoformat(last_updated_str)
            
            # Ensure last_updated is timezone-aware
            if last_updated.tzinfo is None:
                last_updated = last_updated.replace(tzinfo=timezone.utc)
            
            time_diff = self.current_time - last_updated
            
            if time_diff > timedelta(hours=UPDATE_INTERVAL_HOURS):
                logger.info(f"Indicators for {symbol} were last updated {time_diff.total_seconds() / 3600:.2f} hours ago, will update")
                return True
            else:
                logger.info(f"Indicators for {symbol} were updated recently ({time_diff.total_seconds() / 3600:.2f} hours ago), skipping")
                return False
        
        except Exception as e:
            logger.error(f"Error checking update status for {symbol}: {str(e)}")
            # In case of error, assume we should update
            return True
    
    def process_symbol(self, symbol: str, interval: str = "daily") -> Optional[Dict]:
        """
        Fetch and store technical indicators for a symbol.
        
        Args:
            symbol: The ticker symbol
            interval: The time interval
            
        Returns:
            The processed data, or None if failed
        """
        logger.info(f"Processing technical indicators for {symbol} ({interval})")
        
        try:
            # Check if we should update this symbol
            if not self.should_update_indicators(symbol, interval):
                return None
            
            # Fetch technical indicators
            indicators_data = get_technical_indicators(symbol, interval)
            
            if not indicators_data:
                logger.warning(f"No technical indicators data returned for {symbol}, creating placeholder record")
                # Create a placeholder record with default values
                indicators_data = {
                    "symbol": symbol,
                    "interval": interval,
                    "date": datetime.utcnow().isoformat(),
                    "macd": 0,
                    "macd_signal": 0,
                    "macd_hist": 0,
                    "rsi": 0,
                    "fetched_at": datetime.utcnow().isoformat()
                }
            
            # Format data for database
            formatted_data = format_technical_indicators_for_db(indicators_data)
            
            # Store data in Supabase
            logger.info(f"Storing technical indicators for {symbol} in Supabase")
            response = self.supabase.table(TECH_INDICATORS_TABLE) \
                .upsert(formatted_data) \
                .execute()
            
            if response.data:
                logger.info(f"Successfully stored technical indicators for {symbol}")
                return formatted_data
            else:
                logger.warning(f"No data returned from Supabase when storing indicators for {symbol}")
                return None
        
        except Exception as e:
            logger.error(f"Error processing technical indicators for {symbol}: {str(e)}")
            return None
    
    def run(self, symbols: List[str] = None, interval: str = "daily") -> List[Dict]:
        """
        Run the technical indicators fetcher for a list of symbols.
        
        Args:
            symbols: List of symbols to process, or None to use default/watchlist
            interval: The time interval
            
        Returns:
            List of processed data
        """
        logger.info("Starting technical indicators fetcher run")
        
        if not symbols:
            # Get symbols from the stock_info table and crypto_info table
            try:
                stock_response = self.supabase.table("stock_info") \
                    .select("symbol") \
                    .execute()
                
                crypto_response = self.supabase.table("crypto_info") \
                    .select("symbol") \
                    .execute()
                
                stock_symbols = [record["symbol"] for record in stock_response.data]
                crypto_symbols = [record["symbol"] for record in crypto_response.data]
                
                # Combine symbols
                all_symbols = stock_symbols + crypto_symbols
                symbols = list(set(all_symbols))  # Remove duplicates
                
                logger.info(f"Found {len(symbols)} symbols in database")
            except Exception as e:
                logger.error(f"Error fetching symbols from database: {str(e)}")
                symbols = []
        
        # Limit the number of symbols to process
        symbols = symbols[:MAX_SYMBOLS_PER_RUN]
        
        logger.info(f"Processing technical indicators for {len(symbols)} symbols: {symbols}")
        
        results = []
        for i, symbol in enumerate(symbols):
            # Process the symbol
            result = self.process_symbol(symbol, interval)
            if result:
                results.append(result)
            
            # Add delay between API calls to avoid rate limiting
            if i < len(symbols) - 1:  # Don't delay after the last symbol
                logger.info(f"Waiting {DELAY_BETWEEN_REQUESTS} seconds before next API call...")
                time.sleep(DELAY_BETWEEN_REQUESTS)
        
        logger.info(f"Technical indicators fetcher run completed. Processed {len(results)} symbols")
        return results

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Fetch technical indicators for financial instruments")
    parser.add_argument("-s", "--symbols", nargs="+", help="Symbols to fetch data for")
    parser.add_argument("-i", "--interval", default="daily", 
                        choices=["1min", "5min", "15min", "30min", "60min", "daily", "weekly", "monthly"],
                        help="Time interval between data points")
    args = parser.parse_args()
    
    try:
        # Create directories if they don't exist
        os.makedirs("logs", exist_ok=True)
        
        logger.info("Starting technical indicators fetcher")
        fetcher = TechnicalIndicatorsFetcher()
        fetcher.run(symbols=args.symbols, interval=args.interval)
        logger.info("Technical indicators fetcher completed successfully")
    
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 