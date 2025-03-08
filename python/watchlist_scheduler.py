#!/usr/bin/env python3
"""
Watchlist-Driven Data Scheduler

This script implements an intelligent data collection system that:
1. Monitors the watchlist table for new ticker additions
2. Maintains a registry of active tickers to collect data for
3. Schedules data collection at appropriate intervals based on data type
4. Immediately collects data for new ticker additions
5. Cleans up inactive tickers (no longer in any watchlist)

Usage:
  python watchlist_scheduler.py [--once] [--run SCRIPT]

Options:
  --once                Run all fetchers once and exit
  --run SCRIPT          Run a specific fetcher script
"""

import os
import sys
import time
import logging
import argparse
import json
import subprocess
import datetime
import schedule
from typing import List, Dict, Set, Optional
from datetime import datetime, timedelta
import random

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
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scheduler_state.json")

# Set up logging
logger = logging.getLogger("watchlist_scheduler")
logger.setLevel(getattr(logging, LOG_LEVEL))
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Also log to file
file_handler = logging.FileHandler("logs/watchlist_scheduler.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Data collection configuration
DATA_COLLECTION_CONFIG = {
    "stock_prices": {
        "script": "fetch_stock_prices.py",
        "frequency_minutes": 5,
        "priority": 1,
        "time_of_day": None,  # Collect throughout the day
        "requires_market_hours": True
    },
    "options_flow": {
        "script": "fetch_options_flow.py",
        "frequency_minutes": 15,
        "priority": 2,
        "time_of_day": None,
        "requires_market_hours": True
    },
    "dark_pool": {
        "script": "fetch_dark_pool.py",
        "frequency_minutes": 60,
        "priority": 3,
        "time_of_day": None,
        "requires_market_hours": True
    },
    "analyst_ratings": {
        "script": "fetch_analyst_ratings.py",
        "frequency_minutes": 24 * 60,  # Daily
        "priority": 4,
        "time_of_day": "08:00",  # Run at 8 AM
        "requires_market_hours": False
    },
    "insider_trades": {
        "script": "fetch_insider_trades.py",
        "frequency_minutes": 24 * 60,  # Daily
        "priority": 4,
        "time_of_day": "09:00",  # Run at 9 AM
        "requires_market_hours": False
    },
    "financial_news": {
        "script": "fetch_financial_news.py",
        "frequency_minutes": 60,
        "priority": 3,
        "time_of_day": None,
        "requires_market_hours": False
    },
    "hedge_fund_holdings": {
        "script": "fetch_hedge_fund_holdings.py",
        "frequency_minutes": 24 * 60 * 7,  # Weekly
        "priority": 5,
        "time_of_day": "10:00",  # Run at 10 AM
        "requires_market_hours": False
    },
    "economic_indicators": {
        "script": "fetch_economic_indicators.py",
        "frequency_minutes": 24 * 60 * 14,  # Bi-weekly
        "priority": 5,
        "time_of_day": "07:00",  # Run at 7 AM
        "requires_market_hours": False
    }
}

class WatchlistScheduler:
    def __init__(self):
        self.supabase = None
        self.last_processed_timestamp = None
        self.load_state()
        self.connect_to_supabase()
        
    def connect_to_supabase(self):
        """Establish connection to Supabase"""
        try:
            logger.info("Connecting to Supabase...")
            
            if hasattr(sys.modules.get('python.utils', None), 'create_supabase_client'):
                # Use the utility function if available
                self.supabase = create_supabase_client()
            else:
                # Direct connection
                self.supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
                
            logger.info("Connected to Supabase")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            raise
            
    def load_state(self):
        """Load the scheduler state from file"""
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, 'r') as f:
                    state = json.load(f)
                    self.last_processed_timestamp = state.get('last_processed_timestamp')
                    logger.info(f"Loaded state: last processed timestamp = {self.last_processed_timestamp}")
            else:
                self.last_processed_timestamp = None
                logger.info("No previous state found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            self.last_processed_timestamp = None
            
    def save_state(self):
        """Save the current scheduler state to file"""
        try:
            os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
            with open(STATE_FILE, 'w') as f:
                json.dump({
                    'last_processed_timestamp': self.last_processed_timestamp
                }, f)
            logger.debug(f"Saved state: last processed timestamp = {self.last_processed_timestamp}")
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def monitor_watchlist_changes(self):
        """Check for new watchlist entries and trigger data collection"""
        try:
            logger.info("Checking for new watchlist entries...")
            
            # Query for new watchlist entries
            query = self.supabase.table('watchlists').select('ticker,user_id,created_at')
            
            if self.last_processed_timestamp:
                query = query.gt('created_at', self.last_processed_timestamp)
                
            result = query.order('created_at').execute()
            
            # Process new tickers
            new_tickers = set()
            latest_timestamp = self.last_processed_timestamp
            
            for item in result.data:
                ticker = item['ticker']
                new_tickers.add(ticker)
                timestamp = item['created_at']
                
                # Keep track of the latest timestamp
                if not latest_timestamp or timestamp > latest_timestamp:
                    latest_timestamp = timestamp
            
            # Trigger data collection for new tickers
            if new_tickers:
                logger.info(f"Found {len(new_tickers)} new ticker(s): {', '.join(new_tickers)}")
                self.trigger_immediate_data_collection(list(new_tickers))
            else:
                logger.info("No new watchlist entries found")
                
            # Update the last processed timestamp
            if latest_timestamp and (not self.last_processed_timestamp or latest_timestamp > self.last_processed_timestamp):
                self.last_processed_timestamp = latest_timestamp
                self.save_state()
                
        except Exception as e:
            logger.error(f"Error monitoring watchlist changes: {e}")
    
    def update_ticker_registry(self, tickers: List[str], activation_reason: str = "watchlist"):
        """Add or update tickers in the registry for scheduled collection"""
        try:
            for ticker in tickers:
                # Check if ticker already exists
                result = self.supabase.table('ticker_registry').select('ticker,watchlist_count').eq('ticker', ticker).execute()
                
                if not result.data:
                    # Add new ticker to registry
                    logger.info(f"Adding new ticker to registry: {ticker}")
                    self.supabase.table('ticker_registry').insert({
                        'ticker': ticker,
                        'is_active': True,
                        'first_added': datetime.now().isoformat(),
                        'last_updated': datetime.now().isoformat(),
                        'activation_reason': activation_reason,
                        'watchlist_count': 1
                    }).execute()
                else:
                    # Update existing ticker
                    current_count = result.data[0].get('watchlist_count', 0)
                    logger.info(f"Updating existing ticker in registry: {ticker} (count: {current_count} -> {current_count + 1})")
                    
                    self.supabase.table('ticker_registry').update({
                        'is_active': True,
                        'last_updated': datetime.now().isoformat(),
                        'watchlist_count': current_count + 1
                    }).eq('ticker', ticker).execute()
                    
        except Exception as e:
            logger.error(f"Error updating ticker registry: {e}")
    
    def get_active_tickers_from_registry(self) -> List[str]:
        """Get the list of active tickers from the registry"""
        try:
            result = self.supabase.table('ticker_registry').select('ticker').eq('is_active', True).execute()
            tickers = [item['ticker'] for item in result.data]
            logger.info(f"Found {len(tickers)} active tickers in registry")
            return tickers
        except Exception as e:
            logger.error(f"Error getting active tickers: {e}")
            return []
    
    def get_all_watchlist_tickers(self) -> Set[str]:
        """Get all tickers currently in any user's watchlist"""
        try:
            result = self.supabase.table('watchlists').select('ticker').execute()
            tickers = {item['ticker'] for item in result.data}
            return tickers
        except Exception as e:
            logger.error(f"Error getting watchlist tickers: {e}")
            return set()
    
    def deactivate_ticker(self, ticker: str):
        """Mark a ticker as inactive in the registry"""
        try:
            logger.info(f"Deactivating ticker: {ticker}")
            self.supabase.table('ticker_registry').update({
                'is_active': False,
                'last_updated': datetime.now().isoformat(),
                'watchlist_count': 0
            }).eq('ticker', ticker).execute()
        except Exception as e:
            logger.error(f"Error deactivating ticker {ticker}: {e}")
    
    def cleanup_inactive_tickers(self):
        """Remove tickers from active collection when no longer in any watchlist"""
        try:
            logger.info("Running cleanup of inactive tickers...")
            
            # Get current watchlist tickers
            current_watchlist_tickers = self.get_all_watchlist_tickers()
            
            # Get all active registry tickers
            active_tickers = self.get_active_tickers_from_registry()
            
            # Find tickers in registry but not in any watchlist
            inactive_tickers = [t for t in active_tickers if t not in current_watchlist_tickers]
            
            if inactive_tickers:
                logger.info(f"Found {len(inactive_tickers)} inactive tickers to deactivate: {', '.join(inactive_tickers)}")
                
                # Deactivate these tickers
                for ticker in inactive_tickers:
                    self.deactivate_ticker(ticker)
            else:
                logger.info("No inactive tickers found for cleanup")
                
        except Exception as e:
            logger.error(f"Error during inactive ticker cleanup: {e}")
    
    def trigger_immediate_data_collection(self, tickers: List[str]):
        """Trigger immediate data collection for new tickers"""
        try:
            logger.info(f"Triggering immediate data collection for tickers: {', '.join(tickers)}")
            
            # Update the registry first
            self.update_ticker_registry(tickers, "new_watchlist_addition")
            
            # Run each data fetcher for these specific tickers
            for data_type, config in DATA_COLLECTION_CONFIG.items():
                script = config['script']
                self.run_fetcher_for_tickers(script, tickers)
                
        except Exception as e:
            logger.error(f"Error triggering immediate data collection: {e}")
    
    def run_fetcher_for_tickers(self, script_name: str, tickers: List[str]):
        """Run a specific fetcher script for a list of tickers"""
        try:
            if not tickers:
                logger.info(f"No tickers to process for {script_name}")
                return
                
            logger.info(f"Running {script_name} for {len(tickers)} ticker(s)")
            
            # Construct the command
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
            
            # Check if script exists
            if not os.path.exists(script_path):
                logger.error(f"Fetcher script not found: {script_path}")
                return
                
            # Run the script with ticker arguments
            tickers_arg = ",".join(tickers)
            cmd = [sys.executable, script_path, "--tickers", tickers_arg]
            
            logger.debug(f"Executing command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Successfully ran {script_name}")
                logger.debug(f"Output: {result.stdout.strip()}")
            else:
                logger.error(f"Error running {script_name}: {result.stderr.strip()}")
                
            # Update the last_collected field in ticker_registry
            current_time = datetime.now().isoformat()
            for ticker in tickers:
                # Get current last_collected data
                result = self.supabase.table('ticker_registry').select('last_collected').eq('ticker', ticker).execute()
                if result.data:
                    last_collected = result.data[0].get('last_collected', {})
                    if isinstance(last_collected, str):
                        last_collected = json.loads(last_collected)
                    
                    # Update with this collection
                    script_key = os.path.splitext(script_name)[0]  # Remove .py extension
                    last_collected[script_key] = current_time
                    
                    # Save back to database
                    self.supabase.table('ticker_registry').update({
                        'last_collected': last_collected
                    }).eq('ticker', ticker).execute()
                
        except Exception as e:
            logger.error(f"Error running fetcher for tickers: {e}")
    
    def run_fetcher_for_active_tickers(self, script_name: str):
        """Run a fetcher script for all active tickers"""
        active_tickers = self.get_active_tickers_from_registry()
        
        if not active_tickers:
            logger.info(f"No active tickers to process for {script_name}")
            return
            
        # Process in batches to avoid overwhelming API limits
        batch_size = 20  # Adjust based on API limits
        for i in range(0, len(active_tickers), batch_size):
            batch = active_tickers[i:i+batch_size]
            self.run_fetcher_for_tickers(script_name, batch)
            
            # Add a small delay between batches
            if i + batch_size < len(active_tickers):
                delay = random.uniform(1, 5)  # Random delay between 1-5 seconds
                logger.debug(f"Sleeping for {delay:.2f} seconds between batches...")
                time.sleep(delay)
    
    def is_market_open(self) -> bool:
        """Check if the US stock market is currently open"""
        # This is a simplified version - in production use a more accurate check
        now = datetime.now()
        
        # Check if it's a weekday
        if now.weekday() >= 5:  # 5 is Saturday, 6 is Sunday
            return False
            
        # Check if it's between 9:30 AM and 4:00 PM Eastern Time
        # Note: This is simplified and doesn't account for holidays or timezone differences
        # In production, use a proper market calendar library
        hour = now.hour
        minute = now.minute
        
        if (hour < 9) or (hour == 9 and minute < 30) or (hour > 16):
            return False
            
        return True
    
    def schedule_data_collection(self):
        """Set up the scheduler with appropriate frequencies for different data types"""
        logger.info("Setting up data collection schedules...")
        
        for data_type, config in DATA_COLLECTION_CONFIG.items():
            script = config['script']
            frequency = config['frequency_minutes']
            time_of_day = config.get('time_of_day')
            
            # Schedule based on type
            if time_of_day:
                # Run at a specific time each day
                schedule.every().day.at(time_of_day).do(
                    lambda s=script: self.run_fetcher_for_active_tickers(s)
                )
                logger.info(f"Scheduled {data_type} ({script}) to run daily at {time_of_day}")
            else:
                # Run at regular intervals
                minutes = frequency
                
                if minutes < 60:
                    # Add a small random offset to avoid all fetchers starting at the same time
                    offset = random.randint(1, min(10, minutes-1))
                    schedule.every(minutes).minutes.do(
                        lambda s=script: self.run_fetcher_for_active_tickers(s)
                    )
                    logger.info(f"Scheduled {data_type} ({script}) to run every {minutes} minutes")
                elif minutes < 24*60:
                    # Hours-based schedule
                    hours = minutes // 60
                    schedule.every(hours).hours.do(
                        lambda s=script: self.run_fetcher_for_active_tickers(s)
                    )
                    logger.info(f"Scheduled {data_type} ({script}) to run every {hours} hours")
                else:
                    # Days-based schedule
                    days = minutes // (24*60)
                    schedule.every(days).days.do(
                        lambda s=script: self.run_fetcher_for_active_tickers(s)
                    )
                    logger.info(f"Scheduled {data_type} ({script}) to run every {days} days")
                    
        # Schedule watchlist monitoring every minute
        schedule.every(1).minutes.do(self.monitor_watchlist_changes)
        logger.info("Scheduled watchlist monitoring to run every 1 minute")
        
        # Schedule inactive ticker cleanup daily
        schedule.every().day.at("02:00").do(self.cleanup_inactive_tickers)
        logger.info("Scheduled inactive ticker cleanup to run daily at 02:00")
        
        logger.info("All schedules have been set up")
    
    def run_all_once(self):
        """Run all data fetchers once for active tickers"""
        logger.info("Running all data fetchers once...")
        
        # First check for new watchlist changes
        self.monitor_watchlist_changes()
        
        # Then run all the fetchers
        for data_type, config in DATA_COLLECTION_CONFIG.items():
            script = config['script']
            self.run_fetcher_for_active_tickers(script)
            
        # Finally clean up inactive tickers
        self.cleanup_inactive_tickers()
        
        logger.info("Completed one-time run of all fetchers")
        
    def run_specific_fetcher(self, script_name: str):
        """Run a specific fetcher script once"""
        logger.info(f"Running specific fetcher: {script_name}")
        
        # First check for new watchlist changes
        self.monitor_watchlist_changes()
        
        # Run the specific fetcher
        self.run_fetcher_for_active_tickers(script_name)
        
        logger.info(f"Completed running {script_name}")
    
    def run_continuously(self):
        """Run the scheduler continuously"""
        logger.info("Starting watchlist-driven scheduler in continuous mode...")
        
        # Set up the schedules
        self.schedule_data_collection()
        
        # Initial run of watchlist monitoring to catch any additions while the service was down
        self.monitor_watchlist_changes()
        
        # Run the scheduler loop
        while True:
            try:
                schedule.run_pending()
                time.sleep(10)  # Check every 10 seconds
            except KeyboardInterrupt:
                logger.info("Scheduler interrupted, shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)  # Wait a minute before retrying after an error


def main():
    """Main entry point for the scheduler"""
    parser = argparse.ArgumentParser(description="Watchlist-driven data collection scheduler")
    parser.add_argument("--once", action="store_true", help="Run all fetchers once and exit")
    parser.add_argument("--run", metavar="SCRIPT", help="Run a specific fetcher script")
    
    args = parser.parse_args()
    
    # Create scheduler instance
    scheduler = WatchlistScheduler()
    
    if args.once:
        # Run all fetchers once and exit
        scheduler.run_all_once()
    elif args.run:
        # Run a specific fetcher
        scheduler.run_specific_fetcher(args.run)
    else:
        # Run continuously
        scheduler.run_continuously()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Unhandled exception in main: {e}", exc_info=True)
        sys.exit(1) 