#!/usr/bin/env python3
"""
Insider Trades Fetcher Service
Fetches insider trading data from Unusual Whales API and stores in Supabase
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client
import time
import random
import traceback

# Add the parent directory to the path so we can import unusual_whales_api
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from unusual_whales_api import get_insider_trades, format_insider_trade_for_db

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/insider_trades_fetcher.log")
    ]
)
logger = logging.getLogger("insider_trades_fetcher")

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

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


class InsiderTradesFetcher:
    def __init__(self):
        self.table_name = "insider_trades"
    
    def fetch(self, days=7, limit=200, symbols=None, min_value=None):
        """Fetch insider trades from the Unusual Whales API."""
        logger.info(f"Fetching insider trades for the past {days} days (limit: {limit})...")
        
        try:
            trades = get_insider_trades(
                days=days, 
                limit=limit,
                symbols=symbols,
                min_value=min_value
            )
            logger.info(f"Successfully fetched {len(trades)} insider trades")
            return trades
        
        except Exception as e:
            logger.error(f"Error fetching insider trades: {e}")
            logger.error(traceback.format_exc())
            return []
    
    def process(self, trades):
        """Process the fetched insider trades data."""
        logger.info("Processing insider trades data...")
        
        processed_trades = []
        for trade in trades:
            try:
                # Process using the helper function from unusual_whales_api
                processed_trade = format_insider_trade_for_db(trade)
                processed_trades.append(processed_trade)
            except Exception as e:
                logger.error(f"Error processing trade: {e}")
                logger.error(traceback.format_exc())
                continue
        
        logger.info(f"Processed {len(processed_trades)} insider trades")
        return processed_trades
    
    def store(self, processed_trades):
        """Store the processed insider trades in Supabase."""
        if not processed_trades:
            logger.warning("No trades to store")
            return
        
        logger.info(f"Storing {len(processed_trades)} insider trades in Supabase...")
        
        try:
            # Get existing trades from the last 30 days to avoid duplicates
            thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            existing_trades = supabase.table(self.table_name) \
                .select("filing_id, symbol, insider_name, transaction_date") \
                .gte("transaction_date", thirty_days_ago) \
                .execute()
            
            # Create a set of existing trades for efficient lookup
            existing_set = set()
            for item in existing_trades.data:
                key = (
                    item.get("filing_id", ""),
                    item["symbol"],
                    item["insider_name"],
                    item["transaction_date"]
                )
                existing_set.add(key)
            
            # Filter out duplicates
            new_trades = []
            for trade in processed_trades:
                key = (
                    trade.get("filing_id", ""),
                    trade["symbol"],
                    trade["insider_name"],
                    trade["transaction_date"]
                )
                
                if key not in existing_set:
                    # Supabase table schema matches the processed data, so no need to rename fields
                    new_trades.append(trade)
            
            logger.info(f"Found {len(processed_trades) - len(new_trades)} duplicate trades")
            
            if not new_trades:
                logger.info("No new trades to insert")
                return
            
            # Insert data in batches to avoid hitting API limits
            batch_size = 50
            for i in range(0, len(new_trades), batch_size):
                batch = new_trades[i:i+batch_size]
                response = supabase.table(self.table_name).insert(batch).execute()
                
                if hasattr(response, 'error') and response.error:
                    logger.error(f"Error inserting batch {i//batch_size + 1}: {response.error}")
                else:
                    logger.info(f"Successfully inserted batch {i//batch_size + 1} ({len(batch)} trades)")
                
                # Add a small delay between batches to avoid rate limiting
                if i + batch_size < len(new_trades):
                    time.sleep(random.uniform(0.5, 1.5))
            
            logger.info(f"Successfully stored {len(new_trades)} new insider trades")
        
        except Exception as e:
            logger.error(f"Error storing insider trades: {e}")
            logger.error(traceback.format_exc())
    
    def run(self, days=7, limit=200, symbols=None, min_value=None):
        """Run the full fetcher process."""
        logger.info("Starting Insider Trades Fetcher...")
        
        try:
            trades = self.fetch(days, limit, symbols, min_value)
            processed_trades = self.process(trades)
            self.store(processed_trades)
            logger.info("Insider Trades Fetcher completed successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error running Insider Trades Fetcher: {e}")
            logger.error(traceback.format_exc())
            return False

    def fetch_for_watchlist(self, watchlist_symbols, days=30, limit=500):
        """Fetch insider trades specifically for watchlisted symbols."""
        if not watchlist_symbols:
            logger.warning("No watchlist symbols provided, skipping")
            return []

        logger.info(f"Fetching insider trades for {len(watchlist_symbols)} watchlisted symbols...")
        
        try:
            # Fetch watchlist-specific trades with a higher limit since we care about these
            trades = get_insider_trades(
                days=days,
                limit=limit,
                symbols=watchlist_symbols
            )
            logger.info(f"Successfully fetched {len(trades)} insider trades for watchlisted stocks")
            return trades
        except Exception as e:
            logger.error(f"Error fetching watchlist insider trades: {e}")
            return []


if __name__ == "__main__":
    # Parse command line arguments
    days = 7
    limit = 200
    min_value = None
    symbols_arg = None
    
    # Run the fetcher
    fetcher = InsiderTradesFetcher()
    
    # Check if we should fetch watchlist data
    try:
        # Try to get watchlist symbols from Supabase
        watchlist_result = supabase.table("watchlists").select("ticker").execute()
        if watchlist_result.data:
            watchlist_symbols = [item.get("ticker") for item in watchlist_result.data]
            if watchlist_symbols:
                logger.info(f"Found {len(watchlist_symbols)} symbols in watchlist")
                # First fetch watchlist-specific trades with higher days and limit
                success = fetcher.run(days=30, limit=500, symbols=watchlist_symbols)
    except Exception as e:
        logger.error(f"Error fetching watchlist data: {e}")
    
    # Then run for general market data
    success = fetcher.run(days, limit, symbols_arg, min_value)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1) 