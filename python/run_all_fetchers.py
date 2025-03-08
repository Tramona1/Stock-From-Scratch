#!/usr/bin/env python3
"""
Data Fetchers Runner Script
Runs all data fetchers in sequence to update our financial data
"""

import os
import sys
import asyncio
import logging
import argparse
from datetime import datetime

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/data_fetchers_{datetime.now().strftime('%Y%m%d')}.log")
    ]
)
logger = logging.getLogger("data_fetchers_runner")

async def run_insider_trades_fetcher():
    """Run the insider trades fetcher."""
    try:
        logger.info("Starting insider trades fetcher")
        from insider_trades_fetcher import InsiderTradesFetcher
        
        fetcher = InsiderTradesFetcher()
        success = await fetcher.run()
        
        if success:
            logger.info("Insider trades fetcher completed successfully")
        else:
            logger.error("Insider trades fetcher failed")
            
        return success
    except Exception as e:
        logger.error(f"Error running insider trades fetcher: {str(e)}")
        return False

async def run_hedge_fund_fetcher():
    """Run the hedge fund trades fetcher."""
    try:
        logger.info("Starting hedge fund fetcher")
        from hedge_fund_fetcher import HedgeFundTradesFetcher
        
        fetcher = HedgeFundTradesFetcher()
        success = await fetcher.run()
        
        if success:
            logger.info("Hedge fund fetcher completed successfully")
        else:
            logger.error("Hedge fund fetcher failed")
            
        return success
    except Exception as e:
        logger.error(f"Error running hedge fund fetcher: {str(e)}")
        return False

async def run_economic_indicators_fetcher():
    """Run the economic indicators fetcher."""
    try:
        logger.info("Starting economic indicators fetcher")
        from economic_indicators_fetcher import EconomicIndicatorFetcher
        
        fetcher = EconomicIndicatorFetcher()
        success = await fetcher.run()
        
        if success:
            logger.info("Economic indicators fetcher completed successfully")
        else:
            logger.error("Economic indicators fetcher failed")
            
        return success
    except Exception as e:
        logger.error(f"Error running economic indicators fetcher: {str(e)}")
        return False

async def run_market_data_fetcher():
    """Run the market data fetcher."""
    try:
        logger.info("Starting market data fetcher")
        from market_data_fetcher import MarketDataFetcher
        
        # Default tickers for market data
        default_tickers = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA", "SPY"]
        
        # Get tickers from environment variable or use defaults
        tickers_env = os.getenv("TRACKED_TICKERS")
        tickers = tickers_env.split(",") if tickers_env else default_tickers
        
        fetcher = MarketDataFetcher()
        
        # Run trader (higher frequency) first
        logger.info("Running trader frequency data collection")
        success_trader = await fetcher.run_trader(tickers)
        
        # Then run investor (lower frequency)
        logger.info("Running investor frequency data collection")
        success_investor = await fetcher.run_investor(tickers)
        
        if success_trader and success_investor:
            logger.info("Market data fetcher completed successfully")
        else:
            logger.error("Market data fetcher partially failed")
            
        return success_trader and success_investor
    except Exception as e:
        logger.error(f"Error running market data fetcher: {str(e)}")
        return False

async def run_fetchers_for_watchlist():
    """Run fetchers specifically for watchlisted stocks."""
    try:
        # Import utilities
        from dotenv import load_dotenv
        from supabase import create_client
        
        # Load environment variables
        load_dotenv()
        
        # Initialize Supabase client
        supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("Supabase credentials not available, skipping watchlist fetches")
            return False
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Get watchlist symbols
        try:
            result = supabase.table("watchlists").select("ticker").execute()
            watchlist_symbols = list(set(item.get("ticker") for item in result.data if item.get("ticker")))
            
            if not watchlist_symbols:
                logger.info("No watchlist symbols found, skipping watchlist fetchers")
                return True
                
            logger.info(f"Found {len(watchlist_symbols)} watchlist symbols: {', '.join(watchlist_symbols[:5])}...")
            
            # Run insider trades fetcher for watchlist
            from insider_trades_fetcher import InsiderTradesFetcher
            insider_fetcher = InsiderTradesFetcher()
            await insider_fetcher.fetch_for_watchlist(watchlist_symbols)
            
            # Run hedge fund fetcher for watchlist
            from hedge_fund_fetcher import HedgeFundTradesFetcher
            hedge_fund_fetcher = HedgeFundTradesFetcher()
            await hedge_fund_fetcher.fetch_for_watchlist(watchlist_symbols)
            
            # Run market data fetcher for watchlist
            from market_data_fetcher import MarketDataFetcher
            market_fetcher = MarketDataFetcher()
            await market_fetcher.run_trader(watchlist_symbols)
            
            logger.info("Successfully ran fetchers for watchlist stocks")
            return True
            
        except Exception as e:
            logger.error(f"Error getting watchlist symbols: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"Error running fetchers for watchlist: {str(e)}")
        return False

async def main():
    """Main function to run all data fetchers."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run financial data fetchers")
    parser.add_argument("--only", choices=["insider", "hedge_fund", "economic", "market", "watchlist", "all"],
                      default="all", help="Run only a specific fetcher")
    args = parser.parse_args()
    
    logger.info(f"Starting data fetchers runner with mode: {args.only}")
    
    # Run the selected fetcher(s)
    if args.only == "insider" or args.only == "all":
        await run_insider_trades_fetcher()
        
    if args.only == "hedge_fund" or args.only == "all":
        await run_hedge_fund_fetcher()
        
    if args.only == "economic" or args.only == "all":
        await run_economic_indicators_fetcher()
        
    if args.only == "market" or args.only == "all":
        await run_market_data_fetcher()
        
    if args.only == "watchlist" or args.only == "all":
        await run_fetchers_for_watchlist()
    
    logger.info("Data fetchers runner completed")

if __name__ == "__main__":
    asyncio.run(main()) 