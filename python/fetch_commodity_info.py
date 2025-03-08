#!/usr/bin/env python3
"""
Commodity Info Fetcher
Fetches commodity price information from Alpha Vantage API
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
from python.alpha_vantage_api import get_commodity_info, format_commodity_info_for_db

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/commodity_info_fetcher.log")
    ]
)
logger = logging.getLogger("commodity_info_fetcher")

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
COMMODITY_INFO_TABLE = "commodity_info"
UPDATE_INTERVAL_DAYS = 1  # Update commodity info daily
MAX_COMMODITIES_PER_RUN = 5  # Limit to avoid API rate limits

# Default commodities to track
DEFAULT_COMMODITIES = [
    "WTI",             # Crude Oil (West Texas Intermediate)
    "BRENT",           # Crude Oil (Brent)
    "NATURAL_GAS",     # Natural Gas
    "COPPER",          # Copper
    "ALUMINUM"         # Aluminum
]

# All available commodities
ALL_COMMODITIES = [
    "WTI",             # Crude Oil (West Texas Intermediate)
    "BRENT",           # Crude Oil (Brent)
    "NATURAL_GAS",     # Natural Gas
    "COPPER",          # Copper
    "ALUMINUM",        # Aluminum
    "WHEAT",           # Wheat
    "CORN",            # Corn
    "COTTON",          # Cotton
    "SUGAR",           # Sugar
    "COFFEE",          # Coffee
    "ALL_COMMODITIES"  # Global Price Index of All Commodities
]


class CommodityInfoFetcher:
    def __init__(self):
        """Initialize the commodity info fetcher."""
        self.last_api_call = 0
        self.min_api_interval = 12.1  # seconds between API calls (Alpha Vantage rate limit is 5 calls per minute for free tier)
        
        # Verify Alpha Vantage API key exists
        if not ALPHA_VANTAGE_API_KEY:
            logger.error("API_KEY_ALPHA_VANTAGE environment variable not set")
            raise ValueError("API_KEY_ALPHA_VANTAGE must be set in environment")
    
    def should_update_commodity_info(self, commodity: str) -> bool:
        """
        Check if a commodity's info should be updated.
        
        Args:
            commodity: The commodity function name
            
        Returns:
            True if the commodity's info should be updated, False otherwise
        """
        try:
            # Check if we have recent data for this commodity
            response = supabase.table(COMMODITY_INFO_TABLE) \
                .select("fetched_at") \
                .eq("function", commodity) \
                .execute()
            
            # If no data exists, we should definitely update
            if not response.data or len(response.data) == 0:
                return True
            
            # Check if data is older than our update interval
            fetched_at = response.data[0].get("fetched_at")
            if fetched_at:
                fetched_date = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
                update_threshold = datetime.now() - timedelta(days=UPDATE_INTERVAL_DAYS)
                
                # If data is older than the threshold, update it
                if fetched_date < update_threshold:
                    logger.info(f"Commodity info for {commodity} is outdated, last update: {fetched_date}")
                    return True
                else:
                    logger.info(f"Commodity info for {commodity} is recent, skipping update")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error checking update status for {commodity}: {str(e)}")
            return True  # Default to updating if we hit an error
    
    def process_commodity(self, commodity: str) -> bool:
        """
        Process a single commodity, fetching and storing its info.
        
        Args:
            commodity: The commodity function name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if we should update this commodity
            if not self.should_update_commodity_info(commodity):
                return True
            
            logger.info(f"Processing commodity {commodity}")
            
            # Apply rate limiting
            current_time = time.time()
            time_since_last_call = current_time - self.last_api_call
            if time_since_last_call < self.min_api_interval:
                sleep_time = self.min_api_interval - time_since_last_call
                logger.info(f"Rate limiting: Sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
            
            # Get commodity info from API
            commodity_info = get_commodity_info(commodity)
            self.last_api_call = time.time()
            
            if not commodity_info:
                logger.warning(f"No data returned for {commodity}")
                return False
            
            # Format the data for the database
            formatted_info = format_commodity_info_for_db(commodity_info)
            
            # Debug output
            logger.info(f"Formatted data for {commodity}: {json.dumps(formatted_info, indent=2)}")
            
            # Upsert to database
            response = supabase.table(COMMODITY_INFO_TABLE) \
                .upsert(formatted_info, on_conflict="function") \
                .execute()
            
            logger.info(f"Successfully updated commodity info for {commodity}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing commodity {commodity}: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def run(self, commodities=None):
        """
        Run the commodity info fetcher.
        
        Args:
            commodities: Optional list of commodity function names to process. If None, use defaults.
            
        Returns:
            Dictionary with results summary
        """
        logger.info("Starting commodity info fetcher")
        
        try:
            # Get commodities to process
            if commodities is None:
                commodities = DEFAULT_COMMODITIES
            
            # Validate commodity names
            validated_commodities = []
            for commodity in commodities:
                if commodity in ALL_COMMODITIES:
                    validated_commodities.append(commodity)
                else:
                    logger.warning(f"Invalid commodity name: {commodity}")
            
            # Limit the number of commodities to avoid API rate limits
            validated_commodities = validated_commodities[:MAX_COMMODITIES_PER_RUN]
                
            if not validated_commodities:
                logger.warning("No valid commodities found to process")
                return {"status": "success", "commodities_processed": 0, "message": "No valid commodities found"}
                
            logger.info(f"Processing {len(validated_commodities)} commodities: {', '.join(validated_commodities)}")
            
            # Process commodities sequentially
            results = {"success": 0, "failure": 0}
            
            for commodity in validated_commodities:
                success = self.process_commodity(commodity)
                if success:
                    results["success"] += 1
                else:
                    results["failure"] += 1
                
                # Add a small delay between processing commodities
                time.sleep(0.1)
            
            logger.info(f"Commodity info fetcher completed - Processed {len(validated_commodities)} commodities")
            logger.info(f"Results: {results['success']} successful, {results['failure']} failed")
            
            return {
                "status": "success",
                "commodities_processed": len(validated_commodities),
                "successful": results["success"],
                "failed": results["failure"]
            }
            
        except Exception as e:
            logger.error(f"Error running commodity info fetcher: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "error": str(e)
            }

def main():
    """Run the commodity info fetcher as a standalone script."""
    parser = argparse.ArgumentParser(description='Fetch commodity price information from Alpha Vantage API')
    parser.add_argument('--commodities', help='Comma-separated list of commodity function names to process')
    parser.add_argument('--all', action='store_true', help='Process all available commodities')
    args = parser.parse_args()
    
    commodities = None
    if args.all:
        commodities = ALL_COMMODITIES
    elif args.commodities:
        commodities = args.commodities.split(',')
    
    fetcher = CommodityInfoFetcher()
    result = fetcher.run(commodities)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main() 