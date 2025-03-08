#!/usr/bin/env python3
"""
Template Data Fetcher

This is a template script for fetching financial data from external APIs.
It's designed to be customized for different data types (insider trades, analyst ratings, etc.)
while maintaining a consistent structure and interface.

Usage:
  python fetch_template.py [--tickers TICKER1,TICKER2,...] [--days DAYS] [--limit LIMIT]

Options:
  --tickers TICKERS    Comma-separated list of stock tickers to fetch data for
  --days DAYS          Number of days of historical data to fetch [default: 30]
  --limit LIMIT        Maximum number of records to fetch [default: 500]
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Local imports for utility functions
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from python.utils import create_supabase_client, setup_logging
except ImportError:
    # Fallback for direct execution
    from supabase import create_client

# Environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
API_KEY = os.environ.get("API_KEY_TEMPLATE")  # Replace with actual API key env variable
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# API configuration
API_BASE_URL = "https://api.example.com/v1"  # Replace with actual API URL
API_ENDPOINT = f"{API_BASE_URL}/data"  # Replace with actual endpoint
TABLE_NAME = "template_data"  # Replace with actual Supabase table name

# Set up logging
logger = logging.getLogger("fetch_template")
logger.setLevel(getattr(logging, LOG_LEVEL))
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Also log to file
os.makedirs("logs", exist_ok=True)
file_handler = logging.FileHandler("logs/fetch_template.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class TemplateFetcher:
    """Template class for fetching financial data"""
    
    def __init__(self):
        """Initialize the fetcher with API credentials and Supabase connection"""
        self.headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        self.supabase = self._connect_to_supabase()
        
    def _connect_to_supabase(self):
        """Establish connection to Supabase"""
        try:
            if hasattr(sys.modules.get('python.utils', None), 'create_supabase_client'):
                # Use the utility function if available
                return create_supabase_client()
            else:
                # Direct connection
                return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            raise
            
    def get_last_data_date(self, ticker: Optional[str] = None) -> Optional[datetime]:
        """
        Get the date of the most recent data in the database
        
        Args:
            ticker: Optional ticker symbol to filter by
            
        Returns:
            The datetime of the most recent record, or None if no records exist
        """
        try:
            query = self.supabase.table(TABLE_NAME).select("date").order("date", desc=True).limit(1)
            
            if ticker:
                query = query.eq("ticker", ticker)
                
            result = query.execute()
            
            if result.data and len(result.data) > 0:
                return datetime.fromisoformat(result.data[0]["date"].replace("Z", "+00:00"))
            return None
        except Exception as e:
            logger.error(f"Error getting last data date: {e}")
            return None
    
    def fetch(self, tickers: Optional[List[str]] = None, days: int = 30, limit: int = 500) -> List[Dict[str, Any]]:
        """
        Fetch data from the API
        
        Args:
            tickers: List of ticker symbols to fetch data for
            days: Number of days of historical data to fetch
            limit: Maximum number of records to fetch
            
        Returns:
            List of raw data records from the API
        """
        try:
            logger.info(f"Fetching data for {len(tickers) if tickers else 'all'} tickers, {days} days history, {limit} limit")
            
            # Calculate the date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Prepare API parameters
            params = {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "limit": limit
            }
            
            # Add tickers parameter if provided
            if tickers:
                params["symbols"] = ",".join(tickers)
                
            # Fetch data from API
            import requests  # Import here to avoid dependency issues
            response = requests.get(API_ENDPOINT, params=params, headers=self.headers)
            
            # Check for errors
            if response.status_code != 200:
                logger.error(f"API request failed with status {response.status_code}: {response.text}")
                return []
                
            # Parse the response
            data = response.json()
            
            if "data" in data:
                logger.info(f"Successfully fetched {len(data['data'])} records")
                return data["data"]
            else:
                logger.warning("API response contained no data")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return []
    
    def process(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process and normalize the raw API data
        
        Args:
            raw_data: Raw data records from the API
            
        Returns:
            Processed and normalized data ready for database insertion
        """
        try:
            logger.info(f"Processing {len(raw_data)} raw records")
            
            processed_data = []
            
            for item in raw_data:
                # Extract and transform fields as needed
                processed_item = {
                    "id": item.get("id"),
                    "ticker": item.get("symbol"),
                    "company_name": item.get("company_name"),
                    "date": item.get("date"),
                    "value": float(item.get("value", 0)),
                    "type": item.get("type"),
                    "source": item.get("source"),
                    "url": item.get("url"),
                    "created_at": datetime.now().isoformat()
                }
                
                processed_data.append(processed_item)
                
            logger.info(f"Processed {len(processed_data)} records")
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing data: {e}")
            return []
    
    def store(self, processed_data: List[Dict[str, Any]]) -> int:
        """
        Store the processed data in Supabase
        
        Args:
            processed_data: Processed data records
            
        Returns:
            Number of records successfully stored
        """
        try:
            if not processed_data:
                logger.info("No data to store")
                return 0
                
            logger.info(f"Storing {len(processed_data)} records in Supabase")
            
            # Use batch inserts for efficiency
            batch_size = 100
            stored_count = 0
            
            for i in range(0, len(processed_data), batch_size):
                batch = processed_data[i:i+batch_size]
                
                # Use upsert to avoid duplicates
                result = self.supabase.table(TABLE_NAME).upsert(batch).execute()
                
                if hasattr(result, 'data'):
                    stored_count += len(result.data)
                
                # Add a small delay between batches
                if i + batch_size < len(processed_data):
                    time.sleep(0.5)
            
            logger.info(f"Successfully stored {stored_count} records")
            return stored_count
            
        except Exception as e:
            logger.error(f"Error storing data: {e}")
            return 0
    
    def run(self, tickers: Optional[List[str]] = None, days: int = 30, limit: int = 500) -> bool:
        """
        Run the complete fetch-process-store pipeline
        
        Args:
            tickers: List of ticker symbols to fetch data for
            days: Number of days of historical data to fetch
            limit: Maximum number of records to fetch
            
        Returns:
            True if the pipeline executed successfully, False otherwise
        """
        try:
            logger.info(f"Starting data collection for {len(tickers) if tickers else 'all'} tickers")
            
            # Fetch raw data
            raw_data = self.fetch(tickers, days, limit)
            
            if not raw_data:
                logger.warning("No data fetched, ending pipeline")
                return False
                
            # Process the data
            processed_data = self.process(raw_data)
            
            if not processed_data:
                logger.warning("No data processed, ending pipeline")
                return False
                
            # Store the data
            stored_count = self.store(processed_data)
            
            success = stored_count > 0
            logger.info(f"Data collection {'completed successfully' if success else 'failed'}")
            return success
            
        except Exception as e:
            logger.error(f"Error running data pipeline: {e}")
            return False


def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description="Fetch financial data from API")
    parser.add_argument("--tickers", help="Comma-separated list of tickers to fetch data for")
    parser.add_argument("--days", type=int, default=30, help="Number of days of historical data to fetch")
    parser.add_argument("--limit", type=int, default=500, help="Maximum number of records to fetch")
    
    args = parser.parse_args()
    
    # Parse tickers if provided
    tickers = None
    if args.tickers:
        tickers = [ticker.strip().upper() for ticker in args.tickers.split(",") if ticker.strip()]
        
    # Create and run the fetcher
    fetcher = TemplateFetcher()
    success = fetcher.run(tickers=tickers, days=args.days, limit=args.limit)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 