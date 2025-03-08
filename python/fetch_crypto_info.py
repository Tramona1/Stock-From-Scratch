#!/usr/bin/env python3
"""
Crypto Info Fetcher
Fetches cryptocurrency information from Alpha Vantage API
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
from python.alpha_vantage_api import get_crypto_info, format_crypto_info_for_db

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/crypto_info_fetcher.log")
    ]
)
logger = logging.getLogger("crypto_info_fetcher")

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
CRYPTO_INFO_TABLE = "crypto_info"
UPDATE_INTERVAL_HOURS = 1  # Update crypto info hourly
MAX_CRYPTOS_PER_RUN = 5  # Limit to avoid API rate limits
DEFAULT_CRYPTOS = ["BTC", "ETH", "XRP", "LTC", "SOL"]


class CryptoInfoFetcher:
    def __init__(self):
        """Initialize the crypto info fetcher."""
        self.last_api_call = 0
        self.min_api_interval = 12.1  # seconds between API calls (Alpha Vantage rate limit is 5 calls per minute for free tier)
        
        # Verify Alpha Vantage API key exists
        if not ALPHA_VANTAGE_API_KEY:
            logger.error("API_KEY_ALPHA_VANTAGE environment variable not set")
            raise ValueError("API_KEY_ALPHA_VANTAGE must be set in environment")
    
    def should_update_crypto_info(self, symbol: str, market: str = "USD") -> bool:
        """
        Check if a cryptocurrency's info should be updated.
        
        Args:
            symbol: The cryptocurrency symbol to check
            market: The market currency
            
        Returns:
            True if the crypto's info should be updated, False otherwise
        """
        try:
            # Check if we have recent data for this crypto
            response = supabase.table(CRYPTO_INFO_TABLE) \
                .select("fetched_at") \
                .eq("symbol", symbol) \
                .eq("market", market) \
                .execute()
            
            # If no data exists, we should definitely update
            if not response.data or len(response.data) == 0:
                return True
            
            # Check if data is older than our update interval
            fetched_at = response.data[0].get("fetched_at")
            if fetched_at:
                fetched_date = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
                update_threshold = datetime.now() - timedelta(hours=UPDATE_INTERVAL_HOURS)
                
                # If data is older than the threshold, update it
                if fetched_date < update_threshold:
                    logger.info(f"Crypto info for {symbol}/{market} is outdated, last update: {fetched_date}")
                    return True
                else:
                    logger.info(f"Crypto info for {symbol}/{market} is recent, skipping update")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error checking update status for {symbol}/{market}: {str(e)}")
            return True  # Default to updating if we hit an error
    
    def process_crypto(self, symbol: str, market: str = "USD") -> bool:
        """
        Process a single cryptocurrency, fetching and storing its info.
        
        Args:
            symbol: The cryptocurrency symbol to process
            market: The market currency
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if we should update this crypto
            if not self.should_update_crypto_info(symbol, market):
                return True
            
            logger.info(f"Processing cryptocurrency {symbol}/{market}")
            
            # Apply rate limiting
            current_time = time.time()
            time_since_last_call = current_time - self.last_api_call
            if time_since_last_call < self.min_api_interval:
                sleep_time = self.min_api_interval - time_since_last_call
                logger.info(f"Rate limiting: Sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
            
            # Get crypto info from API
            crypto_info = get_crypto_info(symbol, market)
            self.last_api_call = time.time()
            
            if not crypto_info:
                logger.warning(f"No data returned for {symbol}/{market}")
                return False
            
            # Format the data for the database
            formatted_info = format_crypto_info_for_db(crypto_info, symbol)
            
            # Debug output
            logger.info(f"Formatted data for {symbol}/{market}: {json.dumps(formatted_info, indent=2)}")
            
            # Upsert to database
            response = supabase.table(CRYPTO_INFO_TABLE) \
                .upsert(formatted_info, on_conflict=["symbol", "market"]) \
                .execute()
            
            logger.info(f"Successfully updated crypto info for {symbol}/{market}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing cryptocurrency {symbol}/{market}: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def run(self, cryptos=None, market: str = "USD"):
        """
        Run the crypto info fetcher.
        
        Args:
            cryptos: Optional list of crypto symbols to process. If None, use defaults.
            market: The market currency
            
        Returns:
            Dictionary with results summary
        """
        logger.info("Starting crypto info fetcher")
        
        try:
            # Get cryptos to process
            if cryptos is None:
                cryptos = DEFAULT_CRYPTOS
            
            # Limit the number of cryptos to avoid API rate limits
            cryptos = cryptos[:MAX_CRYPTOS_PER_RUN]
                
            if not cryptos:
                logger.warning("No cryptocurrencies found to process")
                return {"status": "success", "cryptos_processed": 0, "message": "No cryptocurrencies found"}
                
            logger.info(f"Processing {len(cryptos)} cryptocurrencies: {', '.join(cryptos)}")
            
            # Process cryptos sequentially
            results = {"success": 0, "failure": 0}
            
            for symbol in cryptos:
                success = self.process_crypto(symbol, market)
                if success:
                    results["success"] += 1
                else:
                    results["failure"] += 1
                
                # Add a small delay between processing cryptos
                time.sleep(0.1)
            
            logger.info(f"Crypto info fetcher completed - Processed {len(cryptos)} cryptocurrencies")
            logger.info(f"Results: {results['success']} successful, {results['failure']} failed")
            
            return {
                "status": "success",
                "cryptos_processed": len(cryptos),
                "successful": results["success"],
                "failed": results["failure"]
            }
            
        except Exception as e:
            logger.error(f"Error running crypto info fetcher: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "error": str(e)
            }

def main():
    """Run the crypto info fetcher as a standalone script."""
    parser = argparse.ArgumentParser(description='Fetch cryptocurrency information from Alpha Vantage API')
    parser.add_argument('--cryptos', help='Comma-separated list of cryptocurrency symbols to process')
    parser.add_argument('--market', help='Market currency (default: USD)', default='USD')
    args = parser.parse_args()
    
    cryptos = args.cryptos.split(',') if args.cryptos else None
    
    fetcher = CryptoInfoFetcher()
    result = fetcher.run(cryptos, args.market)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main() 