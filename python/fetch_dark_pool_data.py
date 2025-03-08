#!/usr/bin/env python3
"""
Dark Pool Data Fetcher
Fetches dark pool trading data from Unusual Whales API and stores in Supabase
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
from unusual_whales_api import (
    get_dark_pool_recent,
    get_ticker_dark_pool,
    format_dark_pool_trade_for_db
)

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/dark_pool_fetcher.log")
    ]
)
logger = logging.getLogger("dark_pool_fetcher")

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
DARK_POOL_TABLE = "dark_pool_data"


class DarkPoolDataFetcher:
    def __init__(self):
        """Initialize the dark pool data fetcher."""
        self.last_api_call = 0
        self.min_api_interval = 0.5  # seconds between API calls to avoid rate limiting
        
    def fetch_dark_pool_data_for_ticker(self, ticker, limit=500):
        """
        Fetch dark pool data for a specific ticker from the Unusual Whales API.
        """
        try:
            # Apply rate limiting
            current_time = time.time()
            time_since_last_call = current_time - self.last_api_call
            if time_since_last_call < self.min_api_interval:
                time.sleep(self.min_api_interval - time_since_last_call)
            
            logger.info(f"Fetching dark pool data for {ticker}")
            data = get_ticker_dark_pool(
                ticker=ticker,
                limit=limit
            )
            
            self.last_api_call = time.time()
            
            if not data:
                logger.warning(f"No dark pool data returned for {ticker}")
                return []
                
            logger.info(f"Successfully fetched {len(data)} dark pool trades for {ticker}")
            return data
        except Exception as e:
            logger.error(f"Error fetching dark pool data for {ticker}: {str(e)}")
            return []
    
    def fetch_recent_dark_pool_trades(self, limit=500):
        """
        Fetch recent dark pool trades across all tickers.
        """
        try:
            # Apply rate limiting
            current_time = time.time()
            time_since_last_call = current_time - self.last_api_call
            if time_since_last_call < self.min_api_interval:
                time.sleep(self.min_api_interval - time_since_last_call)
            
            logger.info(f"Fetching recent dark pool trades")
            data = get_dark_pool_recent(limit=limit)
            
            self.last_api_call = time.time()
            
            if not data:
                logger.warning("No recent dark pool trades returned")
                return []
                
            logger.info(f"Successfully fetched {len(data)} recent dark pool trades")
            return data
        except Exception as e:
            logger.error(f"Error fetching recent dark pool trades: {str(e)}")
            return []
    
    def analyze_dark_pool_data(self, data, ticker=None):
        """
        Analyze dark pool data to identify patterns or significant activity.
        """
        if not data or len(data) == 0:
            logger.warning("No dark pool data to analyze")
            return None
        
        try:
            # Use the ticker from the first trade if not provided
            if not ticker and data:
                ticker = data[0].get("ticker", "UNKNOWN")
                
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            # Calculate total volume and premium
            total_volume = sum(trade.get("size", 0) for trade in data)
            total_premium = sum(float(trade.get("premium", 0)) for trade in data if trade.get("premium"))
            
            # Identify largest trades (by size)
            sorted_by_size = sorted(data, key=lambda x: x.get("size", 0), reverse=True)
            largest_trades = sorted_by_size[:5] if len(sorted_by_size) >= 5 else sorted_by_size
            
            # Calculate average price
            prices = [float(trade.get("price", 0)) for trade in data if trade.get("price")]
            avg_price = sum(prices) / len(prices) if prices else 0
            
            # Get most recent trade
            most_recent = data[0]  # Assuming data is sorted by executed_at descending
            
            # Prepare data for DB storage
            analysis = {
                "id": f"{ticker}-{current_date}",
                "symbol": ticker,
                "volume": total_volume,
                "price": avg_price,
                "timestamp": datetime.now().isoformat(),
                "blocks_count": len(data),
                "total_premium": total_premium,
                "largest_block_size": largest_trades[0].get("size", 0) if largest_trades else 0,
                "largest_block_price": float(largest_trades[0].get("price", 0)) if largest_trades else 0,
                "largest_block_premium": float(largest_trades[0].get("premium", 0)) if largest_trades else 0,
                "most_recent_executed_at": most_recent.get("executed_at", ""),
                "data_date": current_date,
                # Store raw data for reference
                "raw_data": json.dumps([format_dark_pool_trade_for_db(trade) for trade in data])
            }
            
            logger.info(f"Analyzed dark pool data for {ticker}")
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing dark pool data: {str(e)}")
            return None

    def store_dark_pool_data(self, analysis):
        """
        Store dark pool analysis in Supabase database.
        """
        if not analysis:
            return False
        
        try:
            logger.info(f"Storing dark pool analysis for {analysis.get('symbol')}")
            
            # Check if entry for this ticker and date already exists
            existing = supabase.table(DARK_POOL_TABLE) \
                .select("id") \
                .eq("symbol", analysis["symbol"]) \
                .eq("id", analysis["id"]) \
                .execute()
            
            if not existing.data or len(existing.data) == 0:
                # Insert new analysis
                response = supabase.table(DARK_POOL_TABLE).insert(analysis).execute()
                logger.info(f"Inserted new dark pool analysis for {analysis['symbol']}")
            else:
                # Update existing analysis
                response = supabase.table(DARK_POOL_TABLE) \
                    .update(analysis) \
                    .eq("id", analysis["id"]) \
                    .execute()
                logger.info(f"Updated dark pool analysis for {analysis['symbol']}")
                
            # Generate alerts for significant dark pool activity
            self.generate_dark_pool_alerts(analysis)
                
            return True
        except Exception as e:
            logger.error(f"Error storing dark pool analysis: {str(e)}")
            return False
    
    def generate_dark_pool_alerts(self, analysis):
        """Generate alerts for significant dark pool activity."""
        try:
            ticker = analysis.get("symbol")
            if not ticker:
                return
                
            # Only generate alerts for tickers in watchlists
            if not self.is_in_watchlist(ticker):
                return
                
            alerts = []
            
            # Alert for unusually large blocks (more than $10M)
            if analysis.get("largest_block_premium", 0) > 10000000:  # $10M+
                alerts.append({
                    "id": f"dark_pool_{ticker}_{datetime.now().strftime('%Y%m%d')}_large",
                    "title": f"Large Dark Pool Trade: {ticker}",
                    "message": f"Unusually large dark pool trade of ${analysis['largest_block_premium']/1000000:.1f}M detected in {ticker}",
                    "type": "dark_pool",
                    "subtype": "large_trade",
                    "importance": "high",
                    "related_ticker": ticker,
                    "created_at": datetime.now().isoformat(),
                    "meta": json.dumps({
                        "price": analysis.get("largest_block_price"),
                        "size": analysis.get("largest_block_size"),
                        "premium": analysis.get("largest_block_premium"),
                        "blocks_count": analysis.get("blocks_count")
                    })
                })
                
            # Alert for high volume (more than 5% of average daily volume)
            # This would need average daily volume data, which we may not have
            
            # Store alerts in database
            if alerts:
                for alert in alerts:
                    response = supabase.table("alerts").upsert(
                        alert,
                        on_conflict=["id"]
                    ).execute()
                
                logger.info(f"Created {len(alerts)} dark pool alerts for {ticker}")
                
        except Exception as e:
            logger.error(f"Error generating dark pool alerts: {str(e)}")
    
    def is_in_watchlist(self, ticker):
        """Check if a ticker is in any user's watchlist."""
        try:
            # First check if watchlists table exists
            response = supabase.table("watchlists").select("id").limit(1).execute()
            
            # If we reach here without error, the table exists
            # Check if the ticker is in any watchlist
            response = supabase.table("watchlists").select("id").filter("tickers", "cs", f"{{{ticker}}}").execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error checking if {ticker} is in watchlist: {str(e)}")
            # In case of error, default to True to avoid missing important data
            return True
    
    def run(self, watchlist_only=False, days=30, limit=500, tickers=None):
        """
        Run the dark pool data fetcher.
        
        Args:
            watchlist_only: If True, only fetch data for tickers in watchlists
            days: Number of days to look back for data
            limit: Maximum number of trades to fetch per request
            tickers: Optional list of specific tickers to process
            
        Returns:
            Dictionary with results summary
        """
        logger.info(f"Running dark pool data fetcher (watchlist_only={watchlist_only}, days={days}, limit={limit})")
        
        try:
            # Get symbols to process
            if tickers is not None:
                symbols = tickers
                logger.info(f"Processing {len(symbols)} provided tickers")
            elif watchlist_only:
                symbols = self.get_watchlist_tickers()
                logger.info(f"Processing {len(symbols)} watchlist tickers")
            else:
                # Fetch recent dark pool trades to get active tickers
                recent_trades = self.fetch_recent_dark_pool_trades(limit=limit)
                # Extract unique tickers
                symbols = list(set(trade.get("ticker") for trade in recent_trades if trade.get("ticker")))
                logger.info(f"Processing {len(symbols)} active tickers from recent dark pool trades")
                
                # Process the recent trades first (they're already fetched)
                if recent_trades:
                    analysis = self.analyze_dark_pool_data(recent_trades)
                    if analysis:
                        self.store_dark_pool_data(analysis)
            
            # Fetch and process data for each ticker
            for ticker in symbols:
                try:
                    # Fetch dark pool data for this ticker
                    dark_pool_data = self.fetch_dark_pool_data_for_ticker(ticker, limit=limit)
                    
                    if dark_pool_data:
                        # Analyze and store the data
                        analysis = self.analyze_dark_pool_data(dark_pool_data, ticker)
                        if analysis:
                            self.store_dark_pool_data(analysis)
                    
                    # Add a small delay between API calls
                    time.sleep(0.5)
                except Exception as e:
                    logger.error(f"Error processing dark pool data for {ticker}: {str(e)}")
            
            logger.info("Dark pool data fetcher completed successfully")
            return {"status": "success", "symbols_processed": len(symbols)}
            
        except Exception as e:
            logger.error(f"Error running dark pool data fetcher: {str(e)}")
            logger.error(traceback.format_exc())
            return {"status": "error", "error": str(e)}
    
    def get_watchlist_tickers(self):
        """Get all tickers from user watchlists."""
        try:
            response = supabase.table("watchlists").select("tickers").execute()
            
            all_tickers = set()
            for watchlist in response.data:
                tickers = watchlist.get("tickers", [])
                all_tickers.update(tickers)
            
            return list(all_tickers)
        except Exception as e:
            logger.error(f"Error getting watchlist tickers: {str(e)}")
            return []


def main():
    """Run the dark pool data fetcher as a standalone script."""
    fetcher = DarkPoolDataFetcher()
    result = fetcher.run()
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main() 