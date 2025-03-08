#!/usr/bin/env python3
"""
Options Flow Fetcher
Fetches options flow data from Unusual Whales API and stores in Supabase
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
import requests
import uuid

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/options_flow_fetcher.log")
    ]
)
logger = logging.getLogger("options_flow_fetcher")

# Add the parent directory to the path so we can import unusual_whales_api
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
UW_API_KEY = os.getenv("API_KEY_UNUSUAL_WHALES")
UW_API_BASE_URL = "https://api.unusualwhales.com/api"

# API request settings
MAX_RETRIES = 2  # Maximum number of retry attempts
INITIAL_BACKOFF = 1  # Initial backoff in seconds
MAX_BACKOFF = 8  # Maximum backoff in seconds

def make_api_request(url, headers, params=None, max_retries=MAX_RETRIES):
    """
    Make an API request with retry logic and exponential backoff.
    
    Args:
        url: API endpoint URL
        headers: Request headers
        params: Query parameters
        max_retries: Maximum retry attempts
        
    Returns:
        Response data or empty dict/list on failure
    """
    retry_count = 0
    backoff = INITIAL_BACKOFF
    
    while retry_count <= max_retries:
        try:
            if retry_count > 0:
                logger.info(f"Retry attempt {retry_count}/{max_retries} for {url}")
                
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            # Handle different status codes
            if response.status_code == 200:
                data = response.json()
                return data
            elif response.status_code == 429:  # Rate limited
                logger.warning(f"Rate limited on request to {url}")
                # Always retry rate limiting with longer backoff
                backoff = min(MAX_BACKOFF, backoff * 2) 
            elif response.status_code >= 500:  # Server errors
                logger.error(f"Server error ({response.status_code}) for URL: {url}")
                # Retry server errors
                backoff = min(MAX_BACKOFF, backoff * 2)
            else:  # Other client errors (400, 401, 403, etc.)
                logger.error(f"Client error ({response.status_code}) for URL: {url} - {response.text}")
                # Don't retry client errors except for rate limiting
                break
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception for {url}: {str(e)}")
            # Retry network/timeout errors
            backoff = min(MAX_BACKOFF, backoff * 2)
        
        # Only sleep and retry if we haven't exceeded max retries
        if retry_count < max_retries:
            logger.info(f"Backing off for {backoff} seconds before retry")
            time.sleep(backoff)
            retry_count += 1
        else:
            break
    
    # If we got here, all retries failed
    logger.error(f"All {max_retries} retries failed for {url}")
    return {} if params and params.get("format") == "object" else []

# Define the functions for Unusual Whales API calls based on the documentation
def get_option_chains(ticker, date=None):
    """
    Get option chains for a ticker.
    
    Args:
        ticker: Ticker symbol
        date: Optional trading date in YYYY-MM-DD format
        
    Returns:
        List of option chain symbols
    """
    logger.info(f"Fetching option chains for {ticker}")
    
    url = f"{UW_API_BASE_URL}/stock/{ticker}/option-chains"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {UW_API_KEY}"
    }
    
    # Add optional query parameters
    params = {}
    if date:
        params["date"] = date
    
    try:
        logger.info(f"Making request to {url}")
        
        data = make_api_request(url, headers, params)
        
        if "data" in data:
            chains = data["data"]
            logger.info(f"Retrieved {len(chains)} option chains for {ticker}")
            return chains
        else:
            logger.warning(f"Unexpected response format for {ticker} option chains")
            return []
    except Exception as e:
        logger.error(f"Error fetching option chains for {ticker}: {str(e)}")
        return []

def get_option_contracts(ticker, **kwargs):
    """
    Get option contracts for a ticker.
    
    Args:
        ticker: Ticker symbol
        **kwargs: Additional parameters like limit, exclude_zero_vol_chains, etc.
        
    Returns:
        List of option contracts with details
    """
    logger.info(f"Fetching option contracts for {ticker}")
    
    url = f"{UW_API_BASE_URL}/stock/{ticker}/option-contracts"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {UW_API_KEY}"
    }
    
    # Add optional query parameters
    params = kwargs
    
    try:
        logger.info(f"Making request to {url}")
        
        data = make_api_request(url, headers, params)
        
        if "data" in data:
            contracts = data["data"]
            logger.info(f"Retrieved {len(contracts)} option contracts for {ticker}")
            return contracts
        else:
            logger.warning(f"Unexpected response format for {ticker} option contracts")
            return []
    except Exception as e:
        logger.error(f"Error fetching option contracts for {ticker}: {str(e)}")
        return []

def get_option_flow(option_symbol, date=None, limit=50, min_premium=0, side="ALL"):
    """
    Get flow data for a specific option contract.
    
    Args:
        option_symbol: Option symbol (e.g., AAPL250307C00240000)
        date: Optional trading date in YYYY-MM-DD format
        limit: Maximum number of records to return
        min_premium: Minimum premium for filtering trades
        side: Trade side (ALL, ASK, BID, MID)
        
    Returns:
        List of flow data items
    """
    logger.info(f"Fetching flow data for option contract {option_symbol}")
    
    url = f"{UW_API_BASE_URL}/option-contract/{option_symbol}/flow"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {UW_API_KEY}"
    }
    
    # Add query parameters
    params = {
        "limit": limit,
        "min_premium": min_premium,
        "side": side
    }
    
    if date:
        params["date"] = date
    
    try:
        logger.info(f"Making request to {url}")
        
        data = make_api_request(url, headers, params)
        
        if "data" in data:
            flow_data = data["data"]
            logger.info(f"Retrieved {len(flow_data)} flow data points for {option_symbol}")
            return flow_data
        else:
            logger.warning(f"Unexpected response format for option contract {option_symbol} flow")
            return []
    except Exception as e:
        logger.error(f"Error fetching flow for option contract {option_symbol}: {str(e)}")
        return []

def get_flow_alerts(ticker=None, min_premium=10000, limit=100):
    """
    Get flow alerts for a ticker or all tickers.
    
    Args:
        ticker: Optional ticker symbol to filter alerts
        min_premium: Minimum premium for filtering trades
        limit: Maximum number of records to return
        
    Returns:
        List of flow alerts
    """
    logger.info(f"Fetching flow alerts" + (f" for {ticker}" if ticker else ""))
    
    url = f"{UW_API_BASE_URL}/option-trades/flow-alerts"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {UW_API_KEY}"
    }
    
    # Add query parameters
    params = {
        "limit": limit,
        "min_premium": min_premium
    }
    
    if ticker:
        params["ticker_symbol"] = ticker
    
    try:
        logger.info(f"Making request to {url}")
        
        data = make_api_request(url, headers, params)
        
        if "data" in data:
            alerts = data["data"]
            logger.info(f"Retrieved {len(alerts)} flow alerts" + (f" for {ticker}" if ticker else ""))
            return alerts
        else:
            logger.warning(f"Unexpected response format for flow alerts")
            return []
    except Exception as e:
        logger.error(f"Error fetching flow alerts: {str(e)}")
        return []

def format_option_flow_for_db(flow_item):
    """
    Format option flow data for database storage.
    
    Args:
        flow_item: Raw option flow data item from the API
        
    Returns:
        Formatted option flow data ready for DB insertion
    """
    if not flow_item:
        return {}
    
    try:
        now = datetime.now().isoformat()
        
        # Safely convert values with proper handling for None or missing values
        def safe_float(value, default=0.0):
            """Safely convert value to float, handling None or non-numeric values."""
            if value is None:
                return default
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
                
        def safe_int(value, default=0):
            """Safely convert value to int, handling None or non-numeric values."""
            if value is None:
                return default
            try:
                return int(value)
            except (ValueError, TypeError):
                return default
        
        # Format using the fields from the API documentation
        formatted = {
            "id": flow_item.get("id", str(uuid.uuid4())),
            "ticker": flow_item.get("underlying_symbol", ""),
            "date": flow_item.get("executed_at", now),
            "contract_id": flow_item.get("option_chain_id", ""),
            "strike_price": safe_float(flow_item.get("strike", 0)),
            "expiration_date": flow_item.get("expiry", ""),
            "option_type": flow_item.get("option_type", ""),
            "sentiment": "neutral",
            "volume": safe_int(flow_item.get("volume", 0)),
            "open_interest": safe_int(flow_item.get("open_interest", 0)),
            "implied_volatility": safe_float(flow_item.get("implied_volatility", 0)),
            "premium": safe_float(flow_item.get("premium", 0)),
            "raw_data": json.dumps(flow_item),
            "created_at": now,
            "updated_at": now
        }
        
        # Determine sentiment from tags if available
        if "tags" in flow_item:
            tags = flow_item["tags"]
            if isinstance(tags, list):
                if "bullish" in tags:
                    formatted["sentiment"] = "bullish"
                elif "bearish" in tags:
                    formatted["sentiment"] = "bearish"
        
        return formatted
    except Exception as e:
        logger.error(f"Error formatting option flow data: {str(e)}")
        logger.error(traceback.format_exc())
        # Return a minimal valid record rather than nothing
        return {
            "id": str(uuid.uuid4()),
            "ticker": flow_item.get("underlying_symbol", "unknown"),
            "date": now,
            "sentiment": "neutral",
            "raw_data": json.dumps({"error": "Formatting error", "original": str(flow_item)}),
            "created_at": now,
            "updated_at": now
        }

def analyze_option_flow(flow_data, ticker):
    """
    Analyze option flow data.
    
    Args:
        flow_data: List of flow data items
        ticker: Ticker symbol
        
    Returns:
        Dictionary with analysis results
    """
    logger.info(f"Analyzing {len(flow_data)} option flow data points for {ticker}")
    
    if not flow_data:
        logger.warning(f"No option flow data to analyze for {ticker}")
        return {
            "ticker": ticker,
            "analysis_date": datetime.now().date().isoformat(),
            "flow_count": 0,
            "bullish_count": 0,
            "bearish_count": 0,
            "high_premium_count": 0,
            "pre_earnings_count": 0,
            "sentiment": "neutral",
            "total_premium": 0,
            "bullish_premium": 0,
            "bearish_premium": 0,
            "raw_data": json.dumps({"sample_items": []}),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    total_premium = 0
    bullish_count = 0
    bearish_count = 0
    neutral_count = 0
    bullish_premium = 0
    bearish_premium = 0
    high_premium_count = 0  # Trades with premium > $100,000
    pre_earnings_count = 0  # Trades before earnings
    
    for item in flow_data:
        premium = float(item.get("premium", 0))
        total_premium += premium
        
        # Check for high premium trades
        if premium > 100000:
            high_premium_count += 1
        
        # Check for pre-earnings trades
        if "tags" in item and "earnings_soon" in item["tags"]:
            pre_earnings_count += 1
        
        # Determine sentiment from tags
        if "tags" in item:
            tags = item["tags"]
            if "bullish" in tags:
                bullish_count += 1
                bullish_premium += premium
            elif "bearish" in tags:
                bearish_count += 1
                bearish_premium += premium
            else:
                neutral_count += 1
    
    # Determine overall sentiment
    overall_sentiment = "neutral"
    if bullish_count > bearish_count and bullish_premium > bearish_premium:
        overall_sentiment = "bullish"
    elif bearish_count > bullish_count and bearish_premium > bullish_premium:
        overall_sentiment = "bearish"
    
    analysis = {
        "id": str(uuid.uuid4()),
        "ticker": ticker,
        "analysis_date": datetime.now().date().isoformat(),
        "flow_count": len(flow_data),
        "bullish_count": bullish_count,
        "bearish_count": bearish_count,
        "high_premium_count": high_premium_count,
        "pre_earnings_count": pre_earnings_count,
        "sentiment": overall_sentiment,
        "total_premium": total_premium,
        "bullish_premium": bullish_premium,
        "bearish_premium": bearish_premium,
        "raw_data": json.dumps({"sample_items": flow_data[:5] if flow_data else []}),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    logger.info(f"Analysis complete: {bullish_count} bullish, {bearish_count} bearish")
    return analysis

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
        self.min_api_interval = 1.0  # seconds between API calls
        
    async def is_in_watchlist(self, ticker):
        """
        Check if a ticker is in any user watchlist.
        
        Args:
            ticker: Ticker symbol
            
        Returns:
            Boolean indicating if ticker is in watchlist
        """
        try:
            response = supabase.table("watchlists") \
                .select("id") \
                .eq("ticker", ticker) \
                .execute()
                
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error checking if {ticker} is in watchlist: {str(e)}")
            return False
    
    async def fetch_watchlist_tickers(self):
        """
        Fetch tickers from user watchlists.
        
        Returns:
            List of unique ticker symbols
        """
        try:
            response = supabase.table("watchlists") \
                .select("ticker") \
                .execute()
                
            tickers = set([item.get("ticker") for item in response.data if item.get("ticker")])
            
            if not tickers:
                logger.warning("No tickers found in watchlists, using default set")
                return ["SPY", "QQQ", "AAPL", "MSFT", "TSLA", "NVDA"]
                
            return list(tickers)
        except Exception as e:
            logger.error(f"Error fetching watchlist tickers: {str(e)}")
            return ["SPY", "QQQ", "AAPL", "MSFT", "TSLA"]
    
    async def process_ticker(self, ticker, days=5, limit=20):
        """
        Process a single ticker, fetching and analyzing its options flow.
        
        Args:
            ticker: Ticker symbol
            days: Number of days to look back for expiry filtering
            limit: Maximum number of option contracts to process
            
        Returns:
            Dictionary with processing results
        """
        try:
            logger.info(f"Fetching option flow data for {ticker}")
            
            # Apply rate limiting
            current_time = time.time()
            time_since_last_call = current_time - self.last_api_call
            if time_since_last_call < self.min_api_interval:
                await asyncio.sleep(self.min_api_interval - time_since_last_call)
            
            # Get option contracts for this ticker
            # Focus on contracts with volume > open interest and exclude zero volume chains
            # This helps filter out less active options
            contracts = get_option_contracts(
                ticker, 
                exclude_zero_vol_chains=True,
                vol_greater_oi=True,
                limit=limit
            )
            
            self.last_api_call = time.time()
            
            if not contracts:
                logger.warning(f"No option contracts found for {ticker}")
                return {"ticker": ticker, "processed": False, "flow_items": 0}
            
            logger.info(f"Found {len(contracts)} option contracts for {ticker}")
            
            # Process each contract to get flow data
            all_flow_items = []
            processed_count = 0
            error_count = 0
            # Limit the number of contracts to process to avoid overloading
            max_contracts_to_process = min(10, len(contracts))
            
            # Process contracts with a progress counter
            for i, contract in enumerate(contracts):
                if i >= max_contracts_to_process:
                    logger.info(f"Reached maximum contract limit ({max_contracts_to_process}) for {ticker}, stopping")
                    break
                    
                option_symbol = contract.get("option_symbol")
                if not option_symbol:
                    logger.warning(f"Contract {i+1}/{len(contracts)} missing option_symbol, skipping")
                    continue
                
                # Apply rate limiting
                current_time = time.time()
                time_since_last_call = current_time - self.last_api_call
                if time_since_last_call < self.min_api_interval:
                    await asyncio.sleep(self.min_api_interval - time_since_last_call)
                
                # Get flow data for this contract
                logger.info(f"Fetching flow data for option contract {option_symbol}")
                flow_data = get_option_flow(option_symbol, limit=50, min_premium=1000)
                
                self.last_api_call = time.time()
                
                if flow_data:
                    # Format the flow data for database storage
                    formatted_items = []
                    for item in flow_data:
                        try:
                            formatted_item = format_option_flow_for_db(item)
                            if formatted_item:
                                formatted_items.append(formatted_item)
                        except Exception as e:
                            error_count += 1
                            logger.error(f"Error formatting flow item: {str(e)}")
                    
                    valid_items = [item for item in formatted_items if item]
                    
                    if valid_items:
                        logger.info(f"Processed {len(valid_items)} flow items for contract {option_symbol}")
                        all_flow_items.extend(valid_items)
                        processed_count += 1
                    else:
                        logger.warning(f"No valid flow items for contract {option_symbol} after formatting")
                else:
                    logger.warning(f"No flow data found for contract {option_symbol}")
                
                # Add a small delay between contract processing
                await asyncio.sleep(0.5)
            
            if all_flow_items:
                # Store the flow items in the database
                storage_success = await self.store_option_flow(all_flow_items)
                if not storage_success:
                    logger.error(f"Failed to store flow items for {ticker}")
                    
                # Analyze the flow data
                analysis = analyze_option_flow(all_flow_items, ticker)
                
                # Store the analysis in the database
                analysis_success = await self.store_option_flow_analysis(analysis)
                if not analysis_success:
                    logger.error(f"Failed to store flow analysis for {ticker}")
                    
                # Create alerts for significant activity
                await self.create_flow_alerts(analysis)
                
                logger.info(f"Successfully processed {len(all_flow_items)} flow items for {ticker} from {processed_count} contracts with {error_count} errors")
                return {
                    "ticker": ticker, 
                    "processed": True, 
                    "flow_items": len(all_flow_items),
                    "contracts_processed": processed_count,
                    "errors": error_count
                }
            else:
                logger.warning(f"No flow data found for {ticker}")
                return {"ticker": ticker, "processed": False, "flow_items": 0}
            
        except Exception as e:
            logger.error(f"Error processing ticker {ticker}: {str(e)}")
            logger.error(traceback.format_exc())
            return {"ticker": ticker, "processed": False, "error": str(e)}
    
    async def store_option_flow(self, flow_items):
        """
        Store option flow items in the database.
        
        Args:
            flow_items: List of formatted option flow items
        
        Returns:
            Boolean indicating success
        """
        if not flow_items:
            return False
        
        try:
            # Insert in batches to avoid hitting request size limits
            batch_size = 50
            for i in range(0, len(flow_items), batch_size):
                batch = flow_items[i:i+batch_size]
                # Use upsert instead of insert to handle duplicate IDs
                result = supabase.table(OPTION_FLOW_TABLE).upsert(batch, on_conflict="id").execute()
                logger.info(f"Inserted batch of {len(batch)} flow items")
            
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
        if not analysis:
            return False
        
        try:
            # Check if analysis already exists for this ticker and date
            response = supabase.table(OPTION_FLOW_DATA_TABLE) \
                .select("id") \
                .eq("ticker", analysis["ticker"]) \
                .eq("analysis_date", analysis["analysis_date"]) \
                .execute()
                
            if response.data:
                # Update existing analysis
                result = supabase.table(OPTION_FLOW_DATA_TABLE) \
                    .update(analysis) \
                    .eq("ticker", analysis["ticker"]) \
                    .eq("analysis_date", analysis["analysis_date"]) \
                    .execute()
                logger.info(f"Updated existing analysis for {analysis['ticker']}")
            else:
                # Insert new analysis
                result = supabase.table(OPTION_FLOW_DATA_TABLE) \
                    .insert(analysis) \
                    .execute()
                logger.info(f"Inserted new analysis for {analysis['ticker']}")
            
            return True
        except Exception as e:
            logger.error(f"Error storing option flow analysis: {str(e)}")
            logger.error(traceback.format_exc())
            return False
            
    async def create_flow_alerts(self, analysis):
        """
        Create alerts for significant option flow activity.
        
        Args:
            analysis: Dictionary with analysis results
        """
        try:
            ticker = analysis.get("ticker")
            if not ticker:
                return
            
            # Only generate alerts for tickers in watchlists to reduce noise
            if not await self.is_in_watchlist(ticker):
                logger.info(f"Skipping alerts for {ticker} as it's not in any watchlist")
                return
            
            # Check for significant activity
            flow_count = analysis.get("flow_count", 0)
            bullish_count = analysis.get("bullish_count", 0)
            bearish_count = analysis.get("bearish_count", 0)
            total_premium = analysis.get("total_premium", 0)
            
            # Don't create alerts if there's not enough data
            if flow_count < 5 or total_premium < 50000:
                return
            
            # Determine alert type
            alert_type = None
            message = None
            
            # Strong bullish signal: at least 70% bullish
            if bullish_count > bearish_count * 2 and bullish_count / flow_count >= 0.7:
                alert_type = "bullish"
                message = f"Strong bullish options flow detected for {ticker}: {bullish_count} bullish vs {bearish_count} bearish trades with ${total_premium:,.2f} total premium"
            
            # Strong bearish signal: at least 70% bearish
            elif bearish_count > bullish_count * 2 and bearish_count / flow_count >= 0.7:
                alert_type = "bearish"
                message = f"Strong bearish options flow detected for {ticker}: {bearish_count} bearish vs {bullish_count} bullish trades with ${total_premium:,.2f} total premium"
            
            # Very high activity signal
            elif flow_count > 50 or total_premium > 1000000:
                alert_type = "high_activity"
                message = f"Unusually high options activity for {ticker}: {flow_count} trades with ${total_premium:,.2f} total premium"
            
            if not alert_type or not message:
                return
            
            # Create the alert
            alert = {
                "id": str(uuid.uuid4()),
                "related_ticker": ticker,
                "alert_type": alert_type,
                "message": message,
                "source": "options_flow",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "is_read": False,
                "priority": "medium",
                "expires_at": (datetime.now() + timedelta(days=1)).isoformat()
            }
            
            # Store the alert in the database
            try:
                supabase.table("alerts").insert(alert).execute()
                logger.info(f"Created {alert_type} alert for {ticker}")
            except Exception as e:
                logger.error(f"Error creating alert for {ticker}: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error processing alerts: {str(e)}")
    
    async def run(self, tickers=None, watchlist_only=False, days=5, limit=20):
        """
        Run the options flow fetcher for multiple tickers.
        
        Args:
            tickers: Optional list of tickers to process
            watchlist_only: Whether to only process tickers in user watchlists
            days: Number of days to look back for expiry filtering
            limit: Maximum number of option contracts to process per ticker
            
        Returns:
            Dictionary with results summary
        """
        logger.info(f"Running options flow fetcher (watchlist_only={watchlist_only}, days={days}, limit={limit})")
        
        try:
            # Get tickers to process
            if tickers is None:
                if watchlist_only:
                    tickers = await self.fetch_watchlist_tickers()
                else:
                    # Use a default list of popular tickers
                    tickers = ["SPY", "QQQ", "AAPL", "MSFT", "TSLA"]
            
            if not tickers:
                logger.warning("No tickers to process")
                return {
                    "status": "success",
                    "tickers_processed": 0,
                    "total_tickers": 0
                }
                
            logger.info(f"Processing {len(tickers)} provided tickers")
            
            # Process each ticker
            results = []
            for ticker in tickers:
                result = await self.process_ticker(ticker, days, limit)
                results.append(result)
                
                # Add a small delay between processing tickers
                await asyncio.sleep(0.5)
            
            # Count successful processing
            successful = [r for r in results if r.get("processed", False)]
            
            logger.info(f"Completed option flow processing for {len(successful)} tickers")
            
            return {
                "status": "success",
                "tickers_processed": len(successful),
                "total_tickers": len(tickers)
            }
            
        except Exception as e:
            logger.error(f"Error running options flow fetcher: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "error": str(e)
            }

async def main():
    """Run the options flow fetcher as a standalone script."""
    fetcher = OptionsFlowFetcher()
    result = await fetcher.run(tickers=["SPY", "QQQ"])
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main()) 