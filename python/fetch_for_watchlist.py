import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("watchlist_fetcher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("watchlist_fetcher")

# Ensure the scripts directory is in the path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

# Try to import fetcher classes
try:
    from fetch_analyst_ratings import AnalystRatingsFetcher
    from fetch_insider_trades import InsiderTradesFetcher
    # Import other fetchers as they become available
    FETCHERS_AVAILABLE = True
except ImportError as e:
    logger.error(f"Error importing fetchers: {e}")
    FETCHERS_AVAILABLE = False

def get_supabase_client():
    """Get Supabase credentials from environment"""
    supabase_url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("Supabase credentials not found in environment")
        return None, None
    
    return supabase_url, supabase_key

def get_all_watchlist_symbols():
    """Fetch all unique symbols from the watchlists table in Supabase"""
    try:
        # Get Supabase credentials
        supabase_url, supabase_key = get_supabase_client()
        if not supabase_url or not supabase_key:
            return []
        
        # Make request to Supabase REST API
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{supabase_url}/rest/v1/watchlists?select=ticker",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            # Extract unique tickers
            unique_tickers = set(item['ticker'] for item in data if 'ticker' in item)
            logger.info(f"Found {len(unique_tickers)} unique tickers in watchlists")
            return list(unique_tickers)
        else:
            logger.error(f"Failed to fetch watchlist symbols: {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error fetching watchlist symbols: {str(e)}")
        return []

def get_user_watchlist_symbols(user_id):
    """Fetch symbols for a specific user's watchlist"""
    try:
        # Get Supabase credentials
        supabase_url, supabase_key = get_supabase_client()
        if not supabase_url or not supabase_key:
            return []
        
        # Make request to Supabase REST API
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{supabase_url}/rest/v1/watchlists?select=ticker&user_id=eq.{user_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            tickers = [item['ticker'] for item in data if 'ticker' in item]
            logger.info(f"Found {len(tickers)} tickers in user {user_id}'s watchlist")
            return tickers
        else:
            logger.error(f"Failed to fetch user watchlist symbols: {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error fetching user watchlist symbols: {str(e)}")
        return []

def fetch_insider_trades(symbols, days=30):
    """Fetch insider trades for the specified symbols"""
    try:
        if not symbols:
            logger.info("No symbols provided for insider trades fetching")
            return False
            
        logger.info(f"Fetching insider trades for {len(symbols)} symbols")
        fetcher = InsiderTradesFetcher()
        
        # Use special method for watchlist
        if hasattr(fetcher, 'fetch_for_watchlist'):
            fetcher.fetch_for_watchlist(symbols, days=days)
        else:
            # Fallback to standard fetch with symbols filter
            fetcher.run(days=days, symbols=symbols)
            
        logger.info(f"Successfully fetched insider trades for watchlist symbols")
        return True
    except Exception as e:
        logger.error(f"Error fetching insider trades: {str(e)}")
        return False

def fetch_analyst_ratings(symbols, days=30):
    """Fetch analyst ratings for the specified symbols"""
    try:
        if not symbols:
            logger.info("No symbols provided for analyst ratings fetching")
            return False
            
        logger.info(f"Fetching analyst ratings for {len(symbols)} symbols")
        fetcher = AnalystRatingsFetcher()
        
        # Check if the fetcher has a watchlist-specific method
        if hasattr(fetcher, 'fetch_for_watchlist'):
            fetcher.fetch_for_watchlist(symbols, days=days)
        else:
            # Use standard fetch method with symbols parameter
            fetcher.run(days=days, symbols=symbols)
            
        logger.info(f"Successfully fetched analyst ratings for watchlist symbols")
        return True
    except Exception as e:
        logger.error(f"Error fetching analyst ratings: {str(e)}")
        return False

def fetch_data_for_watchlist(symbols, days=30, data_types=None):
    """Fetch all relevant data for the provided symbols"""
    if not symbols:
        logger.warning("No symbols provided, skipping data fetch")
        return
    
    logger.info(f"Fetching data for {len(symbols)} symbols: {', '.join(symbols[:5])}...")
    
    # Use all data types if none specified
    if data_types is None:
        data_types = ['insider_trades', 'analyst_ratings']
    
    success_count = 0
    
    try:
        # Fetch insider trades if requested
        if 'insider_trades' in data_types:
            if fetch_insider_trades(symbols, days):
                success_count += 1
        
        # Fetch analyst ratings if requested
        if 'analyst_ratings' in data_types:
            if fetch_analyst_ratings(symbols, days):
                success_count += 1
        
        # Add other data types as they become available
        
        logger.info(f"Successfully fetched {success_count} data types for watchlist symbols")
        return success_count > 0
    except Exception as e:
        logger.error(f"Error during watchlist data fetch: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Fetch financial data for watchlist symbols')
    parser.add_argument('--user', help='Specific user ID to fetch data for')
    parser.add_argument('--days', type=int, default=30, help='Number of days of data to fetch')
    parser.add_argument('--symbols', help='Comma-separated list of symbols to fetch data for')
    parser.add_argument('--data-types', help='Comma-separated list of data types to fetch')
    args = parser.parse_args()
    
    symbols = []
    
    # Check if the required fetchers are available
    if not FETCHERS_AVAILABLE:
        logger.error("Fetcher classes not available. Check imports.")
        sys.exit(1)
    
    # Get symbols based on input method
    if args.symbols:
        symbols = args.symbols.split(',')
        logger.info(f"Using provided symbols: {', '.join(symbols)}")
    elif args.user:
        symbols = get_user_watchlist_symbols(args.user)
        logger.info(f"Using symbols from user {args.user}'s watchlist: {len(symbols)} symbols")
    else:
        symbols = get_all_watchlist_symbols()
        logger.info(f"Using symbols from all watchlists: {len(symbols)} symbols")
    
    # Parse data types if provided
    data_types = None
    if args.data_types:
        data_types = args.data_types.split(',')
        logger.info(f"Fetching specific data types: {', '.join(data_types)}")
    
    # Fetch data for symbols
    success = fetch_data_for_watchlist(symbols, days=args.days, data_types=data_types)
    
    if success:
        logger.info("Data fetch completed successfully")
    else:
        logger.error("Data fetch completed with errors")
        sys.exit(1)

if __name__ == "__main__":
    main() 