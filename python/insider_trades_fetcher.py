#!/usr/bin/env python3
"""
Insider Trades Fetcher Service
Fetches insider trading data from Unusual Whales API and stores in Supabase
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
import random
import traceback

# Add the parent directory to the path so we can import unusual_whales_api
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from unusual_whales_api import (
    get_insider_transactions, 
    format_insider_transaction_for_db,
    get_ticker_insider_flow,
    get_ticker_insiders
)

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
    def __init__(self, days_to_fetch: int = 7):
        """Initialize the insider trades fetcher.
        
        Args:
            days_to_fetch: Number of days of data to fetch
        """
        self.days_to_fetch = days_to_fetch
        self.insider_trades_table = "insider_trades"
        self.insider_flow_table = "insider_flow"
        self.insiders_table = "insiders"
        
    async def run(self):
        """Run the complete insider trades fetching process."""
        try:
            logger.info("Starting insider trades fetching process", 
                       extra={"metadata": {"days_to_fetch": self.days_to_fetch}})
            
            # Fetch from UnusualWhales API
            await self.fetch_from_unusual_whales()
            
            logger.info("Completed insider trades fetching process", extra={"metadata": {}})
            return True
        except Exception as e:
            logger.error(f"Error in insider trades fetching process: {str(e)}", 
                       extra={"metadata": {"error": str(e), "traceback": traceback.format_exc()}})
            return False
    
    async def fetch_from_unusual_whales(self):
        """Fetch insider trading data from the UnusualWhales API."""
        try:
            logger.info("Fetching insider trades from UnusualWhales API", 
                       extra={"metadata": {"days": self.days_to_fetch}})
            
            # Get the most recent insider transactions
            transactions = get_insider_transactions()
            
            if not transactions:
                logger.warning("No insider transactions returned from UnusualWhales API", 
                              extra={"metadata": {}})
                return
                
            logger.info(f"Retrieved {len(transactions)} insider transactions from UnusualWhales API", 
                       extra={"metadata": {"count": len(transactions)}})
            
            # Process each transaction
            trades_to_insert = []
            for transaction in transactions:
                # Format the transaction for database insertion
                formatted_trade = format_insider_transaction_for_db(transaction)
                
                # Update field names to match the database schema
                # If 'amount' is used but the table expects 'shares'
                if "amount" in formatted_trade:
                    formatted_trade["shares"] = formatted_trade.pop("amount")
                
                # If 'ticker' is used but the table expects 'symbol'
                if "ticker" in formatted_trade:
                    formatted_trade["symbol"] = formatted_trade.pop("ticker")
                
                # If 'transaction_id' is used but the table expects 'filing_id'
                if "transaction_id" in formatted_trade:
                    formatted_trade["filing_id"] = formatted_trade.pop("transaction_id")
                
                # If 'owner_name' is used but the table expects 'insider_name'
                if "owner_name" in formatted_trade:
                    formatted_trade["insider_name"] = formatted_trade.pop("owner_name")
                
                # Check if this transaction already exists in the database
                if "filing_id" in formatted_trade and formatted_trade["filing_id"]:
                    if await self._trade_exists(formatted_trade["filing_id"]):
                        continue
                
                # Remove any fields that don't exist in the database schema
                keys_to_remove = []
                for key in formatted_trade.keys():
                    if key not in ["filing_id", "symbol", "company_name", "insider_name", "insider_title", 
                                   "transaction_type", "transaction_date", "shares", "price", "total_value", 
                                   "shares_owned_after", "filing_date", "source", "created_at", "updated_at"]:
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    formatted_trade.pop(key, None)
                
                trades_to_insert.append(formatted_trade)
            
            # Insert trades into database
            if trades_to_insert:
                # Insert trades in batches to avoid hitting API limits
                batch_size = 50
                for i in range(0, len(trades_to_insert), batch_size):
                    batch = trades_to_insert[i:i + batch_size]
                    result = supabase.table(self.insider_trades_table).insert(batch).execute()
                    
                    if hasattr(result, 'error') and result.error:
                        logger.error(f"Error inserting insider trades batch: {result.error}", 
                                   extra={"metadata": {"error": str(result.error)}})
                    else:
                        logger.info(f"Successfully inserted {len(batch)} insider trades", 
                                  extra={"metadata": {"count": len(batch)}})
                        
                    # Add a small delay between batches
                    if i + batch_size < len(trades_to_insert):
                        await asyncio.sleep(0.5)
            
            logger.info(f"Inserted {len(trades_to_insert)} new insider trades from UnusualWhales API", 
                      extra={"metadata": {"count": len(trades_to_insert)}})
            
            # Fetch insider flow for specific tickers of interest
            await self.fetch_insider_flow_for_tickers()
            
        except Exception as e:
            logger.error(f"Error fetching insider trades from UnusualWhales API: {str(e)}", 
                       extra={"metadata": {"error": str(e), "traceback": traceback.format_exc()}})
    
    async def fetch_insider_flow_for_tickers(self, tickers=None):
        """
        Fetch insider flow data for specific tickers of interest.
        
        Args:
            tickers: List of ticker symbols to fetch insider flow for. If None, 
                    will use watchlist tickers or a default list of popular stocks.
        """
        try:
            # If no tickers provided, try to get from watchlist
            if not tickers:
                try:
                    # Try to get watchlist symbols from Supabase
                    watchlist_result = supabase.table("watchlists").select("ticker").execute()
                    if watchlist_result.data:
                        tickers = list(set([item.get("ticker") for item in watchlist_result.data if item.get("ticker")]))
                        logger.info(f"Using {len(tickers)} tickers from watchlists")
                except Exception as e:
                    logger.error(f"Error fetching watchlist tickers: {e}", extra={"metadata": {"error": str(e)}})
            
            # Default list of tickers if none provided and couldn't get from watchlist
            if not tickers:
                # Get list of tickers from environment variable or use a default list
                tickers_env = os.getenv("INSIDER_FLOW_TICKERS", "AAPL,MSFT,AMZN,GOOGL,META,TSLA,NVDA,AMD")
                tickers = [t.strip() for t in tickers_env.split(",")]
            
            logger.info(f"Fetching insider flow for {len(tickers)} tickers", 
                       extra={"metadata": {"tickers": tickers}})
            
            flow_data_to_insert = []
            insiders_to_insert = []
            seen_insider_ids = set()
            
            for ticker in tickers:
                try:
                    # Get insider flow data for the ticker
                    flow_data = get_ticker_insider_flow(ticker)
                    
                    if flow_data:
                        logger.info(f"Retrieved {len(flow_data)} insider flow records for {ticker}", 
                                  extra={"metadata": {"ticker": ticker, "count": len(flow_data)}})
                        
                        # Process and prepare for database insertion
                        for flow in flow_data:
                            flow_record = {
                                "ticker": ticker,
                                "date": flow.get("date", ""),
                                "buy_sell": flow.get("buy_sell", ""),
                                "avg_price": float(flow.get("avg_price", 0)),
                                "volume": int(flow.get("volume", 0)),
                                "premium": float(flow.get("premium", 0)),
                                "transactions": int(flow.get("transactions", 0)),
                                "unique_insiders": int(flow.get("uniq_insiders", 0)),
                                "created_at": datetime.now().isoformat(),
                                "updated_at": datetime.now().isoformat()
                            }
                            
                            flow_data_to_insert.append(flow_record)
                    
                    # Get insiders data for the ticker
                    insiders_data = get_ticker_insiders(ticker)
                    
                    if insiders_data:
                        logger.info(f"Retrieved {len(insiders_data)} insiders for {ticker}", 
                                  extra={"metadata": {"ticker": ticker, "count": len(insiders_data)}})
                        
                        # Process and prepare for database insertion
                        for insider in insiders_data:
                            # Skip if we've already seen this insider ID
                            insider_id = insider.get("id")
                            if insider_id in seen_insider_ids:
                                continue
                                
                            seen_insider_ids.add(insider_id)
                            
                            insider_record = {
                                "insider_id": str(insider_id),
                                "ticker": ticker,
                                "name": insider.get("name", ""),
                                "display_name": insider.get("display_name", ""),
                                "is_person": insider.get("is_person", True),
                                "logo_url": insider.get("logo_url", ""),
                                "name_slug": insider.get("name_slug", ""),
                                "social_links": json.dumps(insider.get("social_links", [])),
                                "created_at": datetime.now().isoformat(),
                                "updated_at": datetime.now().isoformat()
                            }
                            
                            insiders_to_insert.append(insider_record)
                    
                    # Sleep briefly to avoid hitting rate limits
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error fetching insider data for {ticker}: {str(e)}", 
                               extra={"metadata": {"ticker": ticker, "error": str(e)}})
            
            # Insert flow data into database
            if flow_data_to_insert:
                # Insert in batches
                batch_size = 50
                for i in range(0, len(flow_data_to_insert), batch_size):
                    batch = flow_data_to_insert[i:i + batch_size]
                    # Use upsert to handle duplicate IDs
                    result = supabase.table(self.insider_flow_table).upsert(batch).execute()
                    
                    if hasattr(result, 'error') and result.error:
                        logger.error(f"Error inserting insider flow batch: {result.error}", 
                                   extra={"metadata": {"error": str(result.error)}})
                    else:
                        logger.info(f"Successfully inserted/updated {len(batch)} insider flow records", 
                                  extra={"metadata": {"count": len(batch)}})
                    
                    # Add a small delay between batches
                    if i + batch_size < len(flow_data_to_insert):
                        await asyncio.sleep(0.5)
            
            # Insert insiders data into database
            if insiders_to_insert:
                # Insert in batches
                batch_size = 50
                for i in range(0, len(insiders_to_insert), batch_size):
                    batch = insiders_to_insert[i:i + batch_size]
                    # Use upsert to handle duplicate insider IDs
                    result = supabase.table(self.insiders_table).upsert(batch).execute()
                    
                    if hasattr(result, 'error') and result.error:
                        logger.error(f"Error inserting insiders batch: {result.error}", 
                                   extra={"metadata": {"error": str(result.error)}})
                    else:
                        logger.info(f"Successfully inserted/updated {len(batch)} insiders", 
                                  extra={"metadata": {"count": len(batch)}})
                    
                    # Add a small delay between batches
                    if i + batch_size < len(insiders_to_insert):
                        await asyncio.sleep(0.5)
            
            logger.info("Completed fetching insider flow data", 
                       extra={"metadata": {"flow_count": len(flow_data_to_insert), "insiders_count": len(insiders_to_insert)}})
                
        except Exception as e:
            logger.error(f"Error fetching insider flow data: {str(e)}", 
                       extra={"metadata": {"error": str(e), "traceback": traceback.format_exc()}})
    
    async def _trade_exists(self, filing_id: str) -> bool:
        """Check if a trade already exists in the database."""
        try:
            result = supabase.table(self.insider_trades_table).select("id").eq("filing_id", filing_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error checking if trade exists: {str(e)}", 
                       extra={"metadata": {"error": str(e)}})
            return False

    async def fetch_for_watchlist(self, watchlist_symbols, days=30, limit=500):
        """Fetch insider trades specifically for watchlisted symbols."""
        if not watchlist_symbols:
            logger.warning("No watchlist symbols provided, skipping")
            return []

        logger.info(f"Fetching insider trades for {len(watchlist_symbols)} watchlisted symbols...")
        
        try:
            # Fetch directly from UnusualWhales API for watchlist stocks
            transactions = get_insider_transactions(
                days=days,
                limit=limit,
                symbols=watchlist_symbols
            )
            
            logger.info(f"Successfully fetched {len(transactions)} insider trades for watchlisted stocks")
            
            # Process these transactions just like the main fetcher
            trades_to_insert = []
            for transaction in transactions:
                formatted_trade = format_insider_transaction_for_db(transaction)
                
                if "filing_id" in formatted_trade and formatted_trade["filing_id"]:
                    if await self._trade_exists(formatted_trade["filing_id"]):
                        continue
                
                trades_to_insert.append(formatted_trade)
            
            # Insert trades into database
            if trades_to_insert:
                batch_size = 50
                for i in range(0, len(trades_to_insert), batch_size):
                    batch = trades_to_insert[i:i + batch_size]
                    result = supabase.table(self.insider_trades_table).insert(batch).execute()
                    
                    if hasattr(result, 'error') and result.error:
                        logger.error(f"Error inserting watchlist insider trades batch: {result.error}")
                    else:
                        logger.info(f"Successfully inserted {len(batch)} watchlist insider trades")
                    
                    # Add a small delay between batches
                    if i + batch_size < len(trades_to_insert):
                        await asyncio.sleep(0.5)
            
            return transactions
        except Exception as e:
            logger.error(f"Error fetching watchlist insider trades: {e}")
            logger.error(traceback.format_exc())
            return []

async def main():
    """Main function to run the insider trades fetcher."""
    # Get days to fetch from environment or use default
    days_to_fetch = int(os.getenv("INSIDER_TRADES_DAYS", "7"))
    
    # Create and run the fetcher
    fetcher = InsiderTradesFetcher(days_to_fetch=days_to_fetch)
    success = await fetcher.run()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main()) 