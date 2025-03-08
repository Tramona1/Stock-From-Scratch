#!/usr/bin/env python3
"""
Political Trades Fetcher
Fetches congressional trading data from Unusual Whales API
"""

import os
import sys
import json
import logging
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client
import traceback

# Add the parent directory to the path so we can import unusual_whales_api
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from unusual_whales_api import get_political_trades, format_political_trade_for_db

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/political_trades_fetcher.log")
    ]
)
logger = logging.getLogger("political_trades_fetcher")

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

# Constants
POLITICAL_TRADES_TABLE = "political_trades"


class PoliticalTradesFetcher:
    def __init__(self):
        """Initialize the political trades fetcher."""
        self.last_api_call = 0
        self.min_api_interval = 0.5  # seconds between API calls
        
    def fetch_political_trades(self, days=30, limit=500):
        """
        Fetch political trades from Unusual Whales API.
        
        Args:
            days: Number of days to look back
            limit: Maximum number of trades to fetch
            
        Returns:
            List of political trades
        """
        try:
            # Apply rate limiting
            current_time = time.time()
            time_since_last_call = current_time - self.last_api_call
            if time_since_last_call < self.min_api_interval:
                time.sleep(self.min_api_interval - time_since_last_call)
            
            logger.info(f"Fetching political trades for the past {days} days (limit: {limit})")
            
            # Get political trades from Unusual Whales API using the correct parameters
            political_trades = get_political_trades(
                days=days,
                limit=limit
            )
            
            self.last_api_call = time.time()
            
            if not political_trades:
                logger.warning("No political trades found")
                return []
            
            logger.info(f"Successfully fetched {len(political_trades)} political trades")
            
            # Format trades for database
            formatted_trades = [format_political_trade_for_db(trade) for trade in political_trades]
            
            return formatted_trades
        except Exception as e:
            logger.error(f"Error fetching political trades: {str(e)}")
            logger.error(traceback.format_exc())
            return []
            
    def fetch_political_trades_for_ticker(self, ticker, days=180, limit=100):
        """
        Fetch political trades for a specific ticker.
        
        Args:
            ticker: Ticker symbol to fetch trades for
            days: Number of days to look back
            limit: Maximum number of trades to fetch
            
        Returns:
            List of political trades for the specified ticker
        """
        try:
            # Apply rate limiting
            current_time = time.time()
            time_since_last_call = current_time - self.last_api_call
            if time_since_last_call < self.min_api_interval:
                time.sleep(self.min_api_interval - time_since_last_call)
            
            logger.info(f"Fetching political trades for {ticker} over the past {days} days")
            
            # Get political trades for the specific ticker
            political_trades = get_political_trades(
                days=days,
                symbols=[ticker],
                limit=limit
            )
            
            self.last_api_call = time.time()
            
            if not political_trades:
                logger.warning(f"No political trades found for {ticker}")
                return []
            
            logger.info(f"Successfully fetched {len(political_trades)} political trades for {ticker}")
            
            # Format trades for database
            formatted_trades = [format_political_trade_for_db(trade) for trade in political_trades]
            
            return formatted_trades
        except Exception as e:
            logger.error(f"Error fetching political trades for {ticker}: {str(e)}")
            logger.error(traceback.format_exc())
            return []
    
    def store_political_trades(self, trades):
        """
        Store political trades in Supabase.
        
        Args:
            trades: List of political trades to store
            
        Returns:
            Number of trades stored
        """
        if not trades:
            return 0
        
        try:
            logger.info(f"Storing {len(trades)} political trades")
            
            # Remove duplicates based on the id field
            unique_trades = {}
            for trade in trades:
                trade_id = trade.get("id")
                if trade_id and trade_id not in unique_trades:
                    unique_trades[trade_id] = trade
            
            deduped_trades = list(unique_trades.values())
            logger.info(f"Deduped trades from {len(trades)} to {len(deduped_trades)}")
            
            # Batch insert to avoid request size limits
            batch_size = 50
            stored_count = 0
            
            for i in range(0, len(deduped_trades), batch_size):
                batch = deduped_trades[i:i+batch_size]
                
                try:
                    # Upsert the batch (insert or update if exists)
                    supabase.table(POLITICAL_TRADES_TABLE).upsert(
                        batch,
                        on_conflict=["id"]
                    ).execute()
                    
                    stored_count += len(batch)
                    logger.info(f"Stored batch of {len(batch)} political trades (total: {stored_count})")
                except Exception as e:
                    logger.error(f"Error storing batch of political trades: {str(e)}")
                
                # Brief pause to avoid overwhelming the database
                time.sleep(0.1)
            
            logger.info(f"Successfully stored {stored_count} political trades")
            return stored_count
        except Exception as e:
            logger.error(f"Error storing political trades: {str(e)}")
            logger.error(traceback.format_exc())
            return 0
    
    def generate_political_trade_alerts(self, trades):
        """
        Generate alerts for significant political trades.
        
        Args:
            trades: List of political trades to process
        """
        try:
            logger.info(f"Checking {len(trades)} political trades for alerts")
            
            # Filter for significant trades (large size or interesting patterns)
            significant_trades = []
            
            for trade in trades:
                # Large trades are significant
                value = trade.get("value")
                if value:
                    # Convert value ranges to numbers for comparison
                    if isinstance(value, str):
                        if "-" in value:
                            # Range like "$1,000,001 - $5,000,000"
                            upper_value = value.split("-")[1].strip()
                            # Extract digits only
                            upper_value = ''.join(c for c in upper_value if c.isdigit())
                            if upper_value and int(upper_value) >= 100000:  # $100k+
                                significant_trades.append(trade)
                        elif value.replace("$", "").replace(",", "").isdigit():
                            # Single value
                            value_num = int(value.replace("$", "").replace(",", ""))
                            if value_num >= 100000:  # $100k+
                                significant_trades.append(trade)
            
            alerts = []
            for trade in significant_trades:
                politician = trade.get("politician_name", "Unknown")
                ticker = trade.get("symbol", "Unknown")
                transaction_type = trade.get("transaction_type", "Unknown").capitalize()
                transaction_date = trade.get("transaction_date", "Unknown")
                value = trade.get("value", "Unknown")
                
                alert_id = f"political_{politician.lower().replace(' ', '_')}_{ticker.lower()}_{transaction_date}"
                
                alerts.append({
                    "id": alert_id,
                    "title": f"Significant Political Trade: {politician} - {ticker}",
                    "message": f"{politician} reported a {transaction_type} transaction of {value} in {ticker} on {transaction_date}",
                    "type": "political",
                    "subtype": "congress_trade",
                    "importance": "medium",
                    "related_ticker": ticker,
                    "created_at": datetime.now().isoformat(),
                    "meta": json.dumps({
                        "politician": politician,
                        "ticker": ticker,
                        "transaction_type": transaction_type,
                        "transaction_date": transaction_date,
                        "value": value
                    })
                })
            
            # Store alerts in database
            if alerts:
                for alert in alerts:
                    supabase.table("alerts").upsert(
                        alert,
                        on_conflict=["id"]
                    ).execute()
                
                logger.info(f"Created {len(alerts)} political trade alerts")
                
        except Exception as e:
            logger.error(f"Error generating political trade alerts: {str(e)}")
    
    def get_watchlist_tickers(self):
        """
        Get tickers from all user watchlists.
        
        Returns:
            List of unique ticker symbols from all watchlists
        """
        try:
            # Query the watchlists table
            response = supabase.table("watchlists").select("tickers").execute()
            
            # Extract unique tickers from all watchlists
            all_tickers = set()
            for watchlist in response.data:
                tickers = watchlist.get("tickers", [])
                all_tickers.update(tickers)
            
            logger.info(f"Found {len(all_tickers)} unique tickers in watchlists")
            return list(all_tickers)
        except Exception as e:
            logger.error(f"Error fetching watchlist tickers: {str(e)}")
            return []
    
    def run(self, watchlist_only=False, days=30, limit=500):
        """
        Run the political trades fetcher.
        
        Args:
            watchlist_only: If True, only fetch data for tickers in watchlists
            days: Number of days to look back for data
            limit: Maximum number of trades to fetch
            
        Returns:
            Dictionary with results summary
        """
        logger.info(f"Running political trades fetcher (watchlist_only={watchlist_only}, days={days}, limit={limit})")
        
        try:
            if watchlist_only:
                # Get symbols from watchlists
                symbols = self.get_watchlist_tickers()
                logger.info(f"Processing {len(symbols)} watchlist tickers")
                
                all_trades = []
                for ticker in symbols:
                    # Fetch trades for each ticker
                    trades = self.fetch_political_trades_for_ticker(ticker, days=days, limit=limit)
                    if trades:
                        all_trades.extend(trades)
                        
                    # Add a small delay between API calls
                    time.sleep(0.5)
            else:
                # Fetch all political trades
                all_trades = self.fetch_political_trades(days=days, limit=limit)
            
            # Store the trades in the database
            stored_count = self.store_political_trades(all_trades)
            
            # Generate alerts for significant trades
            if all_trades:
                self.generate_political_trade_alerts(all_trades)
            
            logger.info(f"Political trades fetcher completed - Stored {stored_count} trades")
            
            return {
                "status": "success",
                "trades_stored": stored_count
            }
        except Exception as e:
            logger.error(f"Error running political trades fetcher: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "error": str(e)
            }

def main():
    """Run the political trades fetcher as a standalone script."""
    fetcher = PoliticalTradesFetcher()
    result = fetcher.run()
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main() 