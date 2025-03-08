#!/usr/bin/env python3
"""
Forex Info Fetcher
Fetches foreign exchange (FX) rate information from Alpha Vantage API
"""

import os
import sys
import json
import logging
import time
import argparse
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
from supabase import create_client, Client
import traceback

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from python.alpha_vantage_api import get_forex_info, format_forex_info_for_db

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/forex_info_fetcher.log")
    ]
)
logger = logging.getLogger("forex_info_fetcher")

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
FOREX_INFO_TABLE = "forex_info"
UPDATE_INTERVAL_HOURS = 1  # Update forex info hourly
MAX_PAIRS_PER_RUN = 5  # Limit to avoid API rate limits

# Default forex pairs to track
DEFAULT_FOREX_PAIRS = [
    ("EUR", "USD"),  # Euro to US Dollar
    ("USD", "JPY"),  # US Dollar to Japanese Yen
    ("GBP", "USD"),  # British Pound to US Dollar
    ("USD", "CAD"),  # US Dollar to Canadian Dollar
    ("AUD", "USD")   # Australian Dollar to US Dollar
]


class ForexInfoFetcher:
    def __init__(self):
        """Initialize the forex info fetcher."""
        self.last_api_call = 0
        self.min_api_interval = 12.1  # seconds between API calls (Alpha Vantage rate limit is 5 calls per minute for free tier)
        
        # Verify Alpha Vantage API key exists
        if not ALPHA_VANTAGE_API_KEY:
            logger.error("API_KEY_ALPHA_VANTAGE environment variable not set")
            raise ValueError("API_KEY_ALPHA_VANTAGE must be set in environment")
    
    def should_update_forex_info(self, from_currency: str, to_currency: str) -> bool:
        """
        Check if a forex pair's info should be updated.
        
        Args:
            from_currency: The source currency
            to_currency: The target currency
            
        Returns:
            True if the forex pair's info should be updated, False otherwise
        """
        try:
            # Check if we have recent data for this forex pair
            response = supabase.table(FOREX_INFO_TABLE) \
                .select("fetched_at") \
                .eq("from_currency", from_currency) \
                .eq("to_currency", to_currency) \
                .execute()
            
            # If no data exists, we should definitely update
            if not response.data or len(response.data) == 0:
                return True
            
            # Check if data is older than our update interval
            fetched_at = response.data[0].get("fetched_at")
            if fetched_at:
                fetched_date = datetime.fromisoformat(fetched_at.replace("Z", "+00:00")).replace(tzinfo=timezone.utc)
                update_threshold = datetime.now(timezone.utc) - timedelta(hours=UPDATE_INTERVAL_HOURS)
                
                # If data is older than the threshold, update it
                if fetched_date < update_threshold:
                    logger.info(f"Forex info for {from_currency}/{to_currency} is outdated, last update: {fetched_date}")
                    return True
                else:
                    logger.info(f"Forex info for {from_currency}/{to_currency} is recent, skipping update")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error checking update status for {from_currency}/{to_currency}: {str(e)}")
            return True  # Default to updating if we hit an error
    
    def process_forex_pair(self, from_currency: str, to_currency: str) -> bool:
        """
        Process a single forex pair, fetching and storing its info.
        
        Args:
            from_currency: The source currency
            to_currency: The target currency
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if we should update this forex pair
            if not self.should_update_forex_info(from_currency, to_currency):
                return True
            
            logger.info(f"Processing forex pair {from_currency}/{to_currency}")
            
            # Apply rate limiting
            current_time = time.time()
            time_since_last_call = current_time - self.last_api_call
            if time_since_last_call < self.min_api_interval:
                sleep_time = self.min_api_interval - time_since_last_call
                logger.info(f"Rate limiting: Sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
            
            # Get forex info from API
            forex_info = get_forex_info(from_currency, to_currency)
            self.last_api_call = time.time()
            
            if not forex_info:
                logger.warning(f"No data returned for {from_currency}/{to_currency}")
                return False
            
            # Format the data for the database
            formatted_info = format_forex_info_for_db(forex_info)
            
            # Debug output
            logger.info(f"Formatted data for {from_currency}/{to_currency}: {json.dumps(formatted_info, indent=2)}")
            
            # Upsert to database
            response = supabase.table(FOREX_INFO_TABLE) \
                .upsert(formatted_info, on_conflict="from_currency,to_currency") \
                .execute()
            
            logger.info(f"Successfully updated forex info for {from_currency}/{to_currency}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing forex pair {from_currency}/{to_currency}: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def run(self, forex_pairs=None):
        """
        Run the forex info fetcher.
        
        Args:
            forex_pairs: Optional list of forex pairs to process. If None, use defaults.
            
        Returns:
            Dictionary with results summary
        """
        logger.info("Starting forex info fetcher")
        
        try:
            # Get forex pairs to process
            if forex_pairs is None:
                forex_pairs = DEFAULT_FOREX_PAIRS
            
            # Limit the number of pairs to avoid API rate limits
            forex_pairs = forex_pairs[:MAX_PAIRS_PER_RUN]
                
            if not forex_pairs:
                logger.warning("No forex pairs found to process")
                return {"status": "success", "pairs_processed": 0, "message": "No forex pairs found"}
                
            logger.info(f"Processing {len(forex_pairs)} forex pairs")
            
            # Process forex pairs sequentially
            results = {"success": 0, "failure": 0}
            
            for from_currency, to_currency in forex_pairs:
                success = self.process_forex_pair(from_currency, to_currency)
                if success:
                    results["success"] += 1
                else:
                    results["failure"] += 1
                
                # Add a small delay between processing pairs
                time.sleep(0.1)
            
            logger.info(f"Forex info fetcher completed - Processed {len(forex_pairs)} forex pairs")
            logger.info(f"Results: {results['success']} successful, {results['failure']} failed")
            
            return {
                "status": "success",
                "pairs_processed": len(forex_pairs),
                "successful": results["success"],
                "failed": results["failure"]
            }
            
        except Exception as e:
            logger.error(f"Error running forex info fetcher: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "error": str(e)
            }

def main():
    """Run the forex info fetcher as a standalone script."""
    parser = argparse.ArgumentParser(description='Fetch forex (FX) information from Alpha Vantage API')
    parser.add_argument('--pairs', help='Comma-separated list of forex pairs in format FROM:TO (e.g., EUR:USD,GBP:USD)')
    args = parser.parse_args()
    
    forex_pairs = None
    if args.pairs:
        try:
            # Parse the pairs from the command line
            pairs_list = args.pairs.split(',')
            forex_pairs = []
            for pair in pairs_list:
                from_currency, to_currency = pair.split(':')
                forex_pairs.append((from_currency, to_currency))
        except Exception as e:
            logger.error(f"Error parsing forex pairs: {str(e)}")
            logger.error("Format should be FROM:TO,FROM:TO (e.g., EUR:USD,GBP:USD)")
            sys.exit(1)
    
    fetcher = ForexInfoFetcher()
    result = fetcher.run(forex_pairs)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main() 