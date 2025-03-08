#!/usr/bin/env python3
"""
Options Flow Fetcher (Alpha Vantage)
Fetches options flow data from Alpha Vantage API and stores in Supabase
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client
import time
import traceback

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/options_flow_alpha.log")
    ]
)
logger = logging.getLogger("options_flow_alpha")

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
ALPHA_VANTAGE_KEY = os.getenv("API_KEY_ALPHA_VANTAGE")

# Try to import Alpha Vantage API functions, fallback to fallbacks if not available
try:
    from alpha_vantage_api import (
        get_option_contracts,
        get_options_flow,
        format_option_flow_for_db,
        analyze_option_flow
    )
    logger.info("Successfully imported Alpha Vantage API functions")
except ImportError:
    logger.warning("Could not import Alpha Vantage API functions, using fallbacks")
    
    # Define fallback functions in case the import fails
    def fallback_get_option_contracts(ticker, **kwargs):
        """Fallback function to get option contracts."""
        logger.error(f"Using fallback for get_option_contracts, but API key may be missing")
        return []
        
    def fallback_get_options_flow(ticker, **kwargs):
        """Fallback function to get options flow."""
        logger.error(f"Using fallback for get_options_flow, but API key may be missing")
        return []
        
    def fallback_format_option_flow_for_db(flow_item):
        """Fallback function to format option flow for DB."""
        logger.error(f"Using fallback for format_option_flow_for_db")
        now = datetime.now().isoformat()
        import uuid
        return {
            "id": str(uuid.uuid4()),
            "ticker": flow_item.get("ticker", ""),
            "date": now,
            "created_at": now,
            "updated_at": now,
            "raw_data": json.dumps(flow_item)
        }
        
    def fallback_analyze_option_flow(flow_data, ticker):
        """Fallback function to analyze option flow."""
        logger.error(f"Using fallback for analyze_option_flow")
        now = datetime.now().isoformat()
        today = datetime.now().date().isoformat()
        import uuid
        return {
            "id": str(uuid.uuid4()),
            "ticker": ticker,
            "analysis_date": today,
            "flow_count": len(flow_data),
            "sentiment": "neutral",
            "created_at": now,
            "updated_at": now,
            "raw_data": json.dumps({"sample": flow_data[:1] if flow_data else []})
        }
    
    # Assign fallbacks
    get_option_contracts = fallback_get_option_contracts
    get_options_flow = fallback_get_options_flow
    format_option_flow_for_db = fallback_format_option_flow_for_db
    analyze_option_flow = fallback_analyze_option_flow
    logger.info("Using fallback options flow API functions")

# Initialize Supabase client
supabase = None
try:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Successfully initialized Supabase client")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {str(e)}")
    sys.exit(1)

# Constants
OPTION_FLOW_TABLE = "options_flow"
OPTION_FLOW_DATA_TABLE = "option_flow_data"

class OptionsFlowFetcher:
    def __init__(self):
        """Initialize the options flow fetcher."""
        self.last_api_call = 0
        self.min_api_interval = 12  # seconds between API calls to avoid rate limiting
        
    async def fetch_option_flow(self, ticker, min_volume=50, min_premium=10000):
        """
        Fetch option flow data for a specific ticker using Alpha Vantage API.
        
        Args:
            ticker: The ticker symbol to fetch data for
            min_volume: Minimum volume to consider
            min_premium: Minimum premium amount in USD to filter trades
            
        Returns:
            List of option flow data items
        """
        logger.info(f"Fetching option flow data for {ticker}")
        
        try:
            # Apply rate limiting
            current_time = time.time()
            time_since_last_call = current_time - self.last_api_call
            if time_since_last_call < self.min_api_interval:
                await asyncio.sleep(self.min_api_interval - time_since_last_call)
            
            # Get options flow for this ticker
            flow_data = get_options_flow(
                ticker=ticker,
                min_volume=min_volume,
                min_premium=min_premium
            )
            
            self.last_api_call = time.time()
            
            if not flow_data:
                logger.warning(f"No option flow data found for {ticker}")
                return []
                
            logger.info(f"Found {len(flow_data)} option flow data points for {ticker}")
            
            # Format each flow item for database storage
            formatted_flow_items = [format_option_flow_for_db(item) for item in flow_data]
            
            logger.info(f"Formatted {len(formatted_flow_items)} flow data items for {ticker}")
            return formatted_flow_items
            
        except Exception as e:
            logger.error(f"Error fetching option flow data for {ticker}: {str(e)}")
            logger.error(traceback.format_exc())
            return []
            
    def analyze_option_flow(self, data, ticker):
        """
        Analyze the option flow data to identify patterns and unusual activity.
        
        Args:
            data: List of option flow data items
            ticker: Ticker symbol
            
        Returns:
            Dictionary with analysis results
        """
        return analyze_option_flow(data, ticker)
    
    async def store_option_flow(self, flow_items):
        """
        Store formatted option flow items in the database.
        
        Args:
            flow_items: List of formatted option flow items
            
        Returns:
            Boolean indicating success
        """
        if not flow_items:
            logger.warning("No option flow items to store")
            return False
            
        try:
            # Insert option flow items
            result = supabase.table(OPTION_FLOW_TABLE).insert(flow_items).execute()
            
            inserted_count = len(result.data) if hasattr(result, 'data') else 0
            logger.info(f"Successfully stored {inserted_count} option flow items")
            return True
            
        except Exception as e:
            logger.error(f"Error storing option flow: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    async def store_option_flow_analysis(self, analysis):
        """
        Store option flow analysis in the database.
        
        Args:
            analysis: Dictionary with analysis results
            
        Returns:
            Boolean indicating success
        """
        try:
            # Check if we have data to store
            if not analysis:
                logger.warning("No option flow analysis to store")
                return False
                
            # Insert the analysis
            result = supabase.table(OPTION_FLOW_DATA_TABLE).insert(analysis).execute()
            
            # Log success
            logger.info(f"Successfully stored option flow analysis for {analysis.get('ticker')}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing option flow analysis: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    async def create_flow_alerts(self, data):
        """
        Create alerts for significant option flow activity.
        
        Args:
            data: Dictionary with analysis results
        """
        try:
            ticker = data.get("ticker")
            if not ticker:
                return
                
            # Only generate alerts for tickers in watchlists to reduce noise
            if not await self.is_in_watchlist(ticker):
                return
            
            alerts = []
            
            # Check for significant bullish activity
            if (data.get("bullish_count", 0) >= 8 and data.get("sentiment") == "bullish" and 
                    data.get("total_premium", 0) >= 500000):
                alerts.append({
                    "id": f"flow_alert_{ticker}_{datetime.now().strftime('%Y%m%d')}",
                    "title": f"Bullish Option Flow: {ticker}",
                    "message": f"Significant bullish option activity detected for {ticker} with {data['bullish_count']} bullish trades totaling ${data['bullish_premium']/1000:.1f}k in premium",
                    "type": "option_flow",
                    "subtype": "bullish",
                    "importance": "high",
                    "related_ticker": ticker,
                    "created_at": datetime.now().isoformat(),
                    "meta": json.dumps({
                        "bullish_count": data.get("bullish_count", 0),
                        "bearish_count": data.get("bearish_count", 0),
                        "bullish_premium": data.get("bullish_premium", 0),
                        "bearish_premium": data.get("bearish_premium", 0),
                        "total_premium": data.get("total_premium", 0),
                        "sentiment": data.get("sentiment", "neutral")
                    })
                })
                
            # Check for significant bearish activity
            if (data.get("bearish_count", 0) >= 8 and data.get("sentiment") == "bearish" and 
                    data.get("total_premium", 0) >= 500000):
                alerts.append({
                    "id": f"flow_alert_{ticker}_{datetime.now().strftime('%Y%m%d')}_bear",
                    "title": f"Bearish Option Flow: {ticker}",
                    "message": f"Significant bearish option activity detected for {ticker} with {data['bearish_count']} bearish trades totaling ${data['bearish_premium']/1000:.1f}k in premium",
                    "type": "option_flow",
                    "subtype": "bearish",
                    "importance": "high",
                    "related_ticker": ticker,
                    "created_at": datetime.now().isoformat(),
                    "meta": json.dumps({
                        "bullish_count": data.get("bullish_count", 0),
                        "bearish_count": data.get("bearish_count", 0),
                        "bullish_premium": data.get("bullish_premium", 0),
                        "bearish_premium": data.get("bearish_premium", 0),
                        "total_premium": data.get("total_premium", 0),
                        "sentiment": data.get("sentiment", "neutral")
                    })
                })
            
            # Store alerts in database
            if alerts:
                for alert in alerts:
                    result = supabase.table("alerts").insert(alert).execute()
                logger.info(f"Created {len(alerts)} option flow alerts for {ticker}")
                
        except Exception as e:
            logger.error(f"Error creating flow alerts for {ticker}: {str(e)}")
            logger.error(traceback.format_exc())

    async def is_in_watchlist(self, ticker):
        """
        Check if a ticker is in any user's watchlist.
        
        Args:
            ticker: Ticker symbol to check
            
        Returns:
            Boolean indicating if the ticker is in any watchlist
        """
        try:
            # First check if the watchlists table exists and has data
            response = supabase.table("watchlists").select("*").limit(1).execute()
            
            if not response.data:
                logger.info(f"No watchlists found, treating {ticker} as if it's in a watchlist")
                return True  # If no watchlists, assume all tickers are "in watchlist"
            
            # Try different column names that might contain tickers
            for column_name in ["tickers", "ticker", "symbols", "stocks"]:
                try:
                    # Try to use contains operator on this column
                    query = supabase.table("watchlists").select("id").filter(column_name, "cs", f"{{{ticker}}}")
                    response = query.execute()
                    
                    if response.data and len(response.data) > 0:
                        logger.info(f"Found {ticker} in watchlist using column '{column_name}'")
                        return True
                except Exception:
                    # If this column doesn't exist, try the next one
                    continue
            
            # If we get here, we tried all possible columns and didn't find the ticker
            logger.info(f"Ticker {ticker} not found in any watchlist")
            return False
            
        except Exception as e:
            logger.error(f"Error checking if {ticker} is in watchlist: {str(e)}")
            logger.error("Assuming ticker is in watchlist due to error")
            return True  # Default to True on error to not miss important data
    
    async def get_watchlist_tickers(self):
        """
        Get all tickers from user watchlists.
        
        Returns:
            List of ticker symbols
        """
        try:
            # First check if the watchlists table exists and has data
            test_response = supabase.table("watchlists").select("*").limit(1).execute()
            
            if not test_response.data:
                logger.warning("No watchlists found, returning default tickers")
                # Return default popular tickers as fallback
                return ["AAPL", "MSFT", "TSLA", "AMZN", "NVDA", "GOOGL", "META", "AMD", "NFLX", "SPY", "QQQ"]
            
            all_tickers = set()
            
            # Try different column names that might contain tickers
            for column_name in ["tickers", "ticker", "symbols", "stocks"]:
                try:
                    # Try to select this column
                    response = supabase.table("watchlists").select(column_name).execute()
                    
                    if not response.data:
                        continue
                        
                    # Process the response based on the type of data
                    for watchlist in response.data:
                        if column_name not in watchlist:
                            continue
                            
                        value = watchlist[column_name]
                        
                        # Handle different possible formats (array, string, comma-separated)
                        if isinstance(value, list):
                            all_tickers.update(value)
                        elif isinstance(value, str):
                            if value.startswith('[') and value.endswith(']'):
                                # Try to parse as JSON array
                                try:
                                    tickers_list = json.loads(value)
                                    all_tickers.update(tickers_list)
                                except:
                                    # If can't parse, treat as single ticker
                                    all_tickers.add(value)
                            elif ',' in value:
                                # Comma-separated string
                                tickers_list = [t.strip() for t in value.split(',')]
                                all_tickers.update(tickers_list)
                            else:
                                # Single ticker
                                all_tickers.add(value)
                    
                    # If we found any tickers, return them
                    if all_tickers:
                        logger.info(f"Found {len(all_tickers)} tickers in watchlists using column '{column_name}'")
                        return list(all_tickers)
                        
                except Exception as e:
                    logger.debug(f"Error trying to get tickers from column '{column_name}': {str(e)}")
                    continue
            
            # If we get here, we tried all possible columns and didn't find any tickers
            logger.warning("No tickers found in watchlists, returning default tickers")
            # Return default popular tickers as fallback
            return ["AAPL", "MSFT", "TSLA", "AMZN", "NVDA", "GOOGL", "META", "AMD", "NFLX", "SPY", "QQQ"]
            
        except Exception as e:
            logger.error(f"Error getting watchlist tickers: {str(e)}")
            logger.warning("Returning default tickers due to error")
            # Return default popular tickers as fallback
            return ["AAPL", "MSFT", "TSLA", "AMZN", "NVDA", "GOOGL", "META", "AMD", "NFLX", "SPY", "QQQ"]

    async def run(self, watchlist_only=False, tickers=None):
        """
        Run the options flow fetcher.
        
        Args:
            watchlist_only: If True, only process tickers in user watchlists
            tickers: Optional list of specific tickers to process
            
        Returns:
            Dictionary with results summary
        """
        logger.info(f"Running options flow fetcher (watchlist_only={watchlist_only})")
        
        try:
            # Get the tickers to process
            if tickers is not None:
                # Use provided tickers
                process_tickers = tickers
                logger.info(f"Processing {len(process_tickers)} provided tickers")
            elif watchlist_only:
                process_tickers = await self.get_watchlist_tickers()
                logger.info(f"Processing {len(process_tickers)} watchlist tickers")
            else:
                # Default tickers - most active options symbols
                process_tickers = ["AAPL", "MSFT", "TSLA", "AMZN", "NVDA", "GOOGL", "META", "AMD", "NFLX", "SPY", "QQQ"]
                logger.info(f"Processing {len(process_tickers)} default active tickers")
            
            # Process each ticker
            analyses = {}
            tickers_processed = 0
            all_flow_items = []
            
            for ticker in process_tickers:
                try:
                    # Fetch option flow data for this ticker
                    flow_data = await self.fetch_option_flow(ticker, min_volume=50, min_premium=10000)
                    
                    # If we got data, store it and analyze it
                    if flow_data:
                        # Store individual flow items
                        all_flow_items.extend(flow_data)
                        
                        # Only store a batch of 100 items at a time to avoid hitting limits
                        if len(all_flow_items) >= 100:
                            await self.store_option_flow(all_flow_items[:100])
                            all_flow_items = all_flow_items[100:]
                        
                        # Analyze flow data
                        analysis = self.analyze_option_flow(flow_data, ticker)
                        analyses[ticker] = analysis
                        
                        # Store the analysis
                        await self.store_option_flow_analysis(analysis)
                        
                        # Generate alerts
                        await self.create_flow_alerts(analysis)
                        
                        tickers_processed += 1
                    
                    # Add a small delay to avoid overwhelming the API
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.error(f"Error processing option flow for {ticker}: {str(e)}")
                    logger.error(traceback.format_exc())
            
            # Store any remaining flow items
            if all_flow_items:
                await self.store_option_flow(all_flow_items)
            
            logger.info(f"Completed option flow processing for {tickers_processed} tickers")
            return {
                "status": "success", 
                "tickers_processed": tickers_processed,
                "total_tickers": len(process_tickers)
            }
            
        except Exception as e:
            logger.error(f"Error running options flow fetcher: {str(e)}")
            logger.error(traceback.format_exc())
            return {"status": "error", "error": str(e)}

async def main():
    """Run the options flow fetcher as a standalone script."""
    # Check for required environment variables
    if not ALPHA_VANTAGE_KEY:
        logger.error("API_KEY_ALPHA_VANTAGE environment variable is not set")
        logger.error("Please set API_KEY_ALPHA_VANTAGE to your Alpha Vantage API key")
        sys.exit(1)
    
    fetcher = OptionsFlowFetcher()
    
    # Start with a few major tickers instead of all to avoid hitting API limits
    test_tickers = ["SPY", "AAPL", "MSFT", "TSLA", "NVDA"]
    result = await fetcher.run(tickers=test_tickers)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main()) 