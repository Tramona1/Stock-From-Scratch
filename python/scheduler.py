#!/usr/bin/env python3
"""
Data Fetcher Scheduler
Manages the scheduling of all data fetching scripts while respecting API rate limits.
"""

import os
import sys
import subprocess
import logging
import threading
import time
import json
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
import argparse
from typing import Dict, List, Any, Optional, Set, Tuple
import pytz  # Add this import for timezone support
import traceback

# Configure logging with more detailed format and separate failure log
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/scheduler.log")
    ]
)
logger = logging.getLogger("scheduler")

# Create a special logger for failures
failure_logger = logging.getLogger("scheduler_failures")
failure_handler = logging.FileHandler("logs/scheduler_failures.log")
failure_handler.setLevel(logging.ERROR)
failure_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
failure_logger.addHandler(failure_handler)
failure_logger.setLevel(logging.ERROR)
failure_logger.propagate = False  # Don't propagate to parent logger

# API Rate Limits (requests per minute)
ALPHA_VANTAGE_RATE_LIMIT = 75  # Premium tier limit (5 for free tier)
UNUSUAL_WHALES_RATE_LIMIT = 120  # Based on the 120 requests per minute limit

# API Request Tracking
alpha_vantage_requests = defaultdict(int)
unusual_whales_requests = defaultdict(int)
last_minute_timestamp = datetime.now().replace(second=0, microsecond=0)

# Script API Mapping (which script uses which API)
SCRIPT_API_MAPPING = {
    # Alpha Vantage API scripts
    "fetch_stock_info_alpha.py": "alpha_vantage",
    "fetch_technical_indicators.py": "alpha_vantage",
    "fetch_options_flow_alpha.py": "alpha_vantage",
    "fetch_crypto_info.py": "alpha_vantage",
    "fetch_forex_info.py": "alpha_vantage",
    "fetch_commodity_info.py": "alpha_vantage",
    
    # Unusual Whales API scripts
    "fetch_stock_info.py": "unusual_whales",
    "fetch_stock_details.py": "unusual_whales",
    "fetch_options_flow.py": "unusual_whales",
    "fetch_dark_pool_data.py": "unusual_whales",
    "fetch_insider_trades.py": "unusual_whales",
    "insider_trades_fetcher.py": "unusual_whales",
    "fetch_political_trades.py": "unusual_whales",
    "fetch_analyst_ratings.py": "unusual_whales",
    "hedge_fund_fetcher.py": "unusual_whales",
    
    # Other scripts (no API rate limits)
    "fetch_market_news.py": "other",
    "fetch_economic_reports.py": "other",
    "economic_indicators_fetcher.py": "other",
    "fetch_fda_calendar.py": "other",
    "fetch_for_watchlist.py": "other"
}

# Script Priority Levels (1 is highest, 5 is lowest)
SCRIPT_PRIORITY = {
    # Critical data - highest priority
    "fetch_stock_info_alpha.py": 1,
    "fetch_options_flow.py": 1,
    "fetch_options_flow_alpha.py": 1,
    "fetch_crypto_info.py": 1,
    
    # Important data - high priority
    "fetch_technical_indicators.py": 2,
    "fetch_dark_pool_data.py": 2,
    "fetch_forex_info.py": 2,
    "fetch_commodity_info.py": 2,
    
    # Regular updates - medium priority
    "fetch_market_news.py": 3,
    "fetch_analyst_ratings.py": 3,
    "fetch_insider_trades.py": 3,
    "insider_trades_fetcher.py": 3,
    
    # Background data - lower priority
    "fetch_political_trades.py": 4,
    "economic_indicators_fetcher.py": 4,
    "fetch_economic_reports.py": 4,
    "fetch_fda_calendar.py": 4,
    
    # Infrequent updates - lowest priority
    "fetch_stock_info.py": 5,
    "fetch_stock_details.py": 5,
    "hedge_fund_fetcher.py": 5
}

# Estimated API Calls per Script Execution
ESTIMATED_API_CALLS = {
    # Alpha Vantage scripts
    "fetch_stock_info_alpha.py": 25,  # ~5 API calls per ticker, 5 tickers per run
    "fetch_technical_indicators.py": 20,  # Multiple indicators per ticker
    "fetch_crypto_info.py": 10,  # Multiple API calls per crypto
    "fetch_forex_info.py": 10,  # Currency pair data
    "fetch_commodity_info.py": 5,  # Commodity data
    "fetch_options_flow_alpha.py": 15,  # Options data
    
    # Unusual Whales scripts
    "fetch_stock_info.py": 10,  # One API call per ticker, 10 tickers 
    "fetch_stock_details.py": 10,  # One API call per ticker
    "fetch_options_flow.py": 30,  # Multiple API calls for options chains and flow
    "fetch_dark_pool_data.py": 10,  # Dark pool data
    "fetch_insider_trades.py": 5,  # Insider trading data
    "insider_trades_fetcher.py": 5,  # Additional insider data
    "fetch_political_trades.py": 5,  # Political trading data
    "fetch_analyst_ratings.py": 5,  # Analyst ratings
    "hedge_fund_fetcher.py": 10,  # Hedge fund data
}

# Script to CMD arguments mapping (for custom parameters)
SCRIPT_ARGS = {
    "fetch_stock_info_alpha.py": [],
    "fetch_stock_info.py": [],
    "fetch_options_flow.py": ["--limit", "50"],  # Limit options flow to 50 entries
    "fetch_stock_details.py": [],
}

# Market hours (US Eastern Time)
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 30
MARKET_CLOSE_HOUR = 16
MARKET_CLOSE_MINUTE = 0

# Add holidays list at the top of the file after imports
# US Market Holidays for 2025 (update yearly)
US_MARKET_HOLIDAYS_2025 = [
    datetime(2025, 1, 1).date(),    # New Year's Day
    datetime(2025, 1, 20).date(),   # Martin Luther King Jr. Day
    datetime(2025, 2, 17).date(),   # Presidents' Day
    datetime(2025, 4, 18).date(),   # Good Friday
    datetime(2025, 5, 26).date(),   # Memorial Day
    datetime(2025, 6, 19).date(),   # Juneteenth
    datetime(2025, 7, 4).date(),    # Independence Day
    datetime(2025, 9, 1).date(),    # Labor Day
    datetime(2025, 11, 27).date(),  # Thanksgiving Day
    datetime(2025, 12, 25).date(),  # Christmas Day
]

# Add a list of market-hours only scripts
# Scripts that should only run during market hours
MARKET_HOURS_ONLY_SCRIPTS = [
    "fetch_stock_info_alpha.py",
    "fetch_technical_indicators.py", 
    "fetch_options_flow.py"
]

def is_market_hours() -> bool:
    """Check if current time is during market hours (9:30 AM - 4:00 PM ET)."""
    # Get current time in Eastern Time
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)
    
    # Weekend check (Saturday = 5, Sunday = 6)
    if now.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        return False
    
    # Holiday check
    if now.date() in US_MARKET_HOLIDAYS_2025:
        return False
    
    # Check if time is between 9:30 AM and 4:00 PM ET
    market_open = now.replace(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MINUTE, second=0, microsecond=0)
    market_close = now.replace(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MINUTE, second=0, microsecond=0)
    
    return market_open <= now <= market_close

def update_api_counters():
    """Reset API counters if a minute has passed."""
    global last_minute_timestamp, alpha_vantage_requests, unusual_whales_requests
    
    current_minute = datetime.now().replace(second=0, microsecond=0)
    if current_minute > last_minute_timestamp:
        # Reset counters for the new minute
        alpha_vantage_requests.clear()
        unusual_whales_requests.clear()
        last_minute_timestamp = current_minute
        logger.info(f"API counters reset at {current_minute}")

def can_run_script(script_name: str) -> bool:
    """
    Check if a script can run based on API rate limits.
    Returns True if the script can run, False otherwise.
    """
    update_api_counters()
    
    # Get the API used by this script
    api_used = SCRIPT_API_MAPPING.get(script_name, "other")
    
    # If the script doesn't use a rate-limited API, allow it
    if api_used == "other":
        return True
    
    # Get estimated API calls for this script
    estimated_calls = ESTIMATED_API_CALLS.get(script_name, 1)
    
    # Check if running would exceed rate limits
    if api_used == "alpha_vantage":
        current_usage = sum(alpha_vantage_requests.values())
        return (current_usage + estimated_calls) <= ALPHA_VANTAGE_RATE_LIMIT
    elif api_used == "unusual_whales":
        current_usage = sum(unusual_whales_requests.values())
        return (current_usage + estimated_calls) <= UNUSUAL_WHALES_RATE_LIMIT
    
    # Default to allowing the script to run
    return True

def update_api_usage(script_name: str):
    """Update the API usage counters after running a script."""
    # Get the API used by this script
    api_used = SCRIPT_API_MAPPING.get(script_name, "other")
    
    # Get estimated API calls for this script
    estimated_calls = ESTIMATED_API_CALLS.get(script_name, 1)
    
    # Update the appropriate counter
    if api_used == "alpha_vantage":
        alpha_vantage_requests[script_name] += estimated_calls
        logger.info(f"Alpha Vantage API usage: {sum(alpha_vantage_requests.values())}/{ALPHA_VANTAGE_RATE_LIMIT} requests this minute")
    elif api_used == "unusual_whales":
        unusual_whales_requests[script_name] += estimated_calls
        logger.info(f"Unusual Whales API usage: {sum(unusual_whales_requests.values())}/{UNUSUAL_WHALES_RATE_LIMIT} requests this minute")

# Add this function to log script details before execution
def log_script_details(script_name: str, args: List[str]):
    """Log detailed information about the script being executed."""
    api_used = SCRIPT_API_MAPPING.get(script_name, "other")
    priority = SCRIPT_PRIORITY.get(script_name, 3)
    estimated_calls = ESTIMATED_API_CALLS.get(script_name, 1)
    
    details = {
        "script": script_name,
        "api": api_used,
        "priority": priority,
        "estimated_api_calls": estimated_calls,
        "arguments": args,
        "timestamp": datetime.now().isoformat(),
        "market_hours": is_market_hours()
    }
    
    logger.info(f"SCRIPT DETAILS: {json.dumps(details, indent=2)}")

def run_script(script_name: str) -> bool:
    """
    Run a data fetching script with proper error handling.
    Returns True if successful, False otherwise.
    """
    logger.info(f"🔍 Preparing to run {script_name}")
    
    # Check if the script exists
    script_path = os.path.join("python", script_name)
    if not os.path.exists(script_path):
        error_msg = f"❌ Script file not found: {script_path}"
        logger.error(error_msg)
        failure_logger.error(error_msg)
        return False
    
    # Check if the script can run based on API limits
    if not can_run_script(script_name):
        logger.warning(f"⚠️ Skipping {script_name} due to API rate limits.")
        return False
    
    # Get any custom arguments for this script
    args = SCRIPT_ARGS.get(script_name, [])
    
    # Skip market-hours only scripts outside market hours
    if (script_name in MARKET_HOURS_ONLY_SCRIPTS and 
        not is_market_hours() and not "--force" in args):
        logger.info(f"⏱️ Skipping {script_name} - outside market hours")
        return False
    
    # For crypto scripts, these can run 24/7 since crypto markets never close
    if script_name == "fetch_crypto_info.py":
        # Always run crypto scripts regardless of market hours
        logger.info(f"🪙 Running crypto script regardless of market hours")
    
    # Log detailed script information before running
    log_script_details(script_name, args)
    
    # Start timing
    start_time = time.time()
    
    try:
        logger.info(f"▶️ Running {script_name} at {datetime.now().isoformat()}")
        cmd = [sys.executable, os.path.join("python", script_name)] + args
        
        # Run the script
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False  # Don't raise exception on non-zero exit
        )
        
        # Check result
        if process.returncode == 0:
            duration = time.time() - start_time
            logger.info(f"✅ Successfully ran {script_name} in {duration:.2f} seconds")
            
            # Log stdout if not empty
            if process.stdout.strip():
                logger.info(f"📄 {script_name} stdout: {process.stdout[:500]}...")
            
            # Update API usage counters
            update_api_usage(script_name)
            
            # Log API usage after script execution
            api_used = SCRIPT_API_MAPPING.get(script_name, "other")
            if api_used == "alpha_vantage":
                logger.info(f"📊 Alpha Vantage API usage after {script_name}: {sum(alpha_vantage_requests.values())}/{ALPHA_VANTAGE_RATE_LIMIT}")
            elif api_used == "unusual_whales":
                logger.info(f"📊 Unusual Whales API usage after {script_name}: {sum(unusual_whales_requests.values())}/{UNUSUAL_WHALES_RATE_LIMIT}")
            
        return True
        else:
            duration = time.time() - start_time
            error_msg = f"❌ Error running {script_name} (Exit code: {process.returncode}). Duration: {duration:.2f}s"
        logger.error(error_msg)
            
            # Log stderr in separate log files
            if process.stderr.strip():
                failure_logger.error(f"SCRIPT FAILED: {script_name}\nExit code: {process.returncode}\nStderr:\n{process.stderr}")
                logger.error(f"Stderr from {script_name}: {process.stderr[:500]}...")
                
                # Also save full stderr to a separate file for debugging
                error_log_dir = os.path.join("logs", "script_errors")
                os.makedirs(error_log_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                error_file = os.path.join(error_log_dir, f"{script_name.replace('.py', '')}_{timestamp}.err")
                with open(error_file, "w") as f:
                    f.write(f"Command: {' '.join(cmd)}\n")
                    f.write(f"Exit code: {process.returncode}\n")
                    f.write(f"Stderr:\n{process.stderr}\n")
                    if process.stdout.strip():
                        f.write(f"\nStdout:\n{process.stdout}\n")
                
        return False
            
    except Exception as e:
        duration = time.time() - start_time
        error_msg = f"❌ Exception running {script_name} after {duration:.2f}s: {str(e)}"
        logger.exception(error_msg)
        
        # Log full exception
        failure_logger.error(f"EXCEPTION IN SCRIPT: {script_name}\n{error_msg}\n{traceback.format_exc()}")
        
        return False

def schedule_runs(scripts_to_run: List[str]) -> None:
    """
    Run the specified scripts, prioritizing by importance and respecting rate limits.
    """
    if not scripts_to_run:
        logger.info("No scripts to run in this cycle")
        return
        
    # Sort scripts by priority
    sorted_scripts = sorted(scripts_to_run, key=lambda s: SCRIPT_PRIORITY.get(s, 3))
    
    # Log the execution plan
    logger.info(f"📋 Execution plan: {len(sorted_scripts)} scripts in priority order")
    for idx, script in enumerate(sorted_scripts):
        priority = SCRIPT_PRIORITY.get(script, 3)
        api_used = SCRIPT_API_MAPPING.get(script, "other")
        logger.info(f"  {idx+1}. {script} (Priority: {priority}, API: {api_used})")
    
    # Run scripts in priority order
    success_count = 0
    failure_count = 0
    
    for script in sorted_scripts:
        success = run_script(script)
        
        if success:
            success_count += 1
        else:
            failure_count += 1
            logger.warning(f"⚠️ Failed to run {script}, will retry in next scheduling cycle")
        
        # Small pause between script runs to prevent system overload
        time.sleep(1)
    
    # Log summary
    logger.info(f"📊 Execution summary: {success_count} successful, {failure_count} failed")

def get_scripts_for_interval(interval_minutes: int) -> List[str]:
    """Get the list of scripts to run at the specified interval."""
    if interval_minutes == 5:
        # 5-minute scripts (high frequency)
        return [
            "fetch_stock_info_alpha.py",
            "fetch_technical_indicators.py",
            "fetch_crypto_info.py"
        ]
    elif interval_minutes == 15:
        # 15-minute scripts (medium frequency)
        return [
            "fetch_options_flow.py",
            "fetch_options_flow_alpha.py", 
            "fetch_forex_info.py",
            "fetch_commodity_info.py"
        ]
    elif interval_minutes == 60:
        # Hourly scripts
        return [
            "fetch_dark_pool_data.py",
            "fetch_market_news.py"
        ]
    elif interval_minutes == 1440:  # 24 hours
        # Daily scripts
        return [
            "fetch_analyst_ratings.py",
            "fetch_insider_trades.py",
            "insider_trades_fetcher.py",
            "economic_indicators_fetcher.py",
            "fetch_economic_reports.py",
            "fetch_fda_calendar.py",
            "fetch_political_trades.py"
        ]
    elif interval_minutes == 10080:  # 7 days
        # Weekly scripts
        return [
            "hedge_fund_fetcher.py"
        ]
    else:
        # Unknown interval
        return []

def print_status() -> None:
    """Print the current status of the scheduler."""
    # Get current time in Eastern Time
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)
    
    market_status = "OPEN" if is_market_hours() else "CLOSED"
    reason = ""
    
    # Add reason for market being closed
    if market_status == "CLOSED":
        if now.weekday() >= 5:
            reason = f" (Weekend - {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][now.weekday()]})"
        elif now.date() in US_MARKET_HOLIDAYS_2025:
            reason = " (Holiday)"
        elif now.hour < MARKET_OPEN_HOUR or (now.hour == MARKET_OPEN_HOUR and now.minute < MARKET_OPEN_MINUTE):
            reason = " (Before hours)"
        elif now.hour > MARKET_CLOSE_HOUR or (now.hour == MARKET_CLOSE_HOUR and now.minute >= MARKET_CLOSE_MINUTE):
            reason = " (After hours)"
    
    print("\n==== SCHEDULER STATUS ====")
    print(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Market hours: {market_status}{reason}")
    print(f"Alpha Vantage API usage: {sum(alpha_vantage_requests.values())}/{ALPHA_VANTAGE_RATE_LIMIT} requests this minute")
    print(f"Unusual Whales API usage: {sum(unusual_whales_requests.values())}/{UNUSUAL_WHALES_RATE_LIMIT} requests this minute")
    print("==========================\n")

def run_scheduler(interval: int = 5, dry_run: bool = False) -> None:
    """
    Main scheduling loop that runs at the specified interval.
    
    Args:
        interval: Minimum interval in minutes between scheduling runs
        dry_run: If True, log what would run but don't actually run scripts
    """
    logger.info(f"🚀 Starting scheduler with {interval} minute interval")
    logger.info(f"📌 Alpha Vantage rate limit: {ALPHA_VANTAGE_RATE_LIMIT} requests/minute")
    logger.info(f"📌 Unusual Whales rate limit: {UNUSUAL_WHALES_RATE_LIMIT} requests/minute")
    
    # Track last run times for different intervals
    last_run = {
        5: datetime.min,     # 5-minute interval
        15: datetime.min,    # 15-minute interval
        60: datetime.min,    # Hourly interval
        1440: datetime.min,  # Daily interval
        10080: datetime.min  # Weekly interval
    }
    
    # Special schedule for company metadata (Mondays and Thursdays at 6:00 AM)
    company_metadata_run_days = [0, 3]  # Monday and Thursday
    company_metadata_hour = 6
    company_metadata_last_run = datetime.min
    
    try:
        while True:
            cycle_start_time = datetime.now()
            logger.info(f"⏰ Starting scheduling cycle at {cycle_start_time.isoformat()}")
            
            now = datetime.now()
            scripts_to_run = []
            
            # Check each interval to see if scripts should run
            for minutes in [5, 15, 60, 1440, 10080]:
                if now - last_run[minutes] >= timedelta(minutes=minutes):
                    interval_scripts = get_scripts_for_interval(minutes)
                    if interval_scripts:
                        logger.info(f"🔄 Adding {len(interval_scripts)} scripts for {minutes}-minute interval")
                        scripts_to_run.extend(interval_scripts)
                        last_run[minutes] = now
            
            # Check if company metadata should run (Mondays and Thursdays at 6:00 AM)
            if (now.weekday() in company_metadata_run_days and 
                now.hour == company_metadata_hour and 
                now.date() > company_metadata_last_run.date()):
                logger.info(f"🔄 Adding company metadata scripts (weekly schedule)")
                scripts_to_run.append("fetch_stock_info.py")
                scripts_to_run.append("fetch_stock_details.py")
                company_metadata_last_run = now
            
            # Remove duplicates while preserving order
            scripts_to_run = list(dict.fromkeys(scripts_to_run))
            
            if scripts_to_run:
                logger.info(f"📋 Scheduling run for {len(scripts_to_run)} scripts: {', '.join(scripts_to_run)}")
                
                if dry_run:
                    logger.info("🔍 DRY RUN - Not actually running scripts")
                else:
                    try:
                        schedule_runs(scripts_to_run)
                    except Exception as e:
                        logger.error(f"❌ Error in schedule_runs: {str(e)}")
                        logger.exception("Exception details:")
            else:
                logger.info("ℹ️ No scripts to run in this cycle")
            
            # Print status every run
            print_status()
            
            # Calculate time spent in this cycle and sleep until next interval
            cycle_duration = (datetime.now() - cycle_start_time).total_seconds()
            logger.info(f"⏱️ Cycle completed in {cycle_duration:.2f} seconds")
            
            sleep_time = max(1, min(60, interval * 60 - cycle_duration))
            logger.info(f"💤 Sleeping for {sleep_time:.2f} seconds until next cycle")
            time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        logger.info("👋 Scheduler stopped by user")
    except Exception as e:
        logger.error(f"❌ Scheduler error: {str(e)}")
        logger.exception("Exception details:")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Data Fetcher Scheduler")
    parser.add_argument("--interval", type=int, default=5, 
                        help="Minimum interval in minutes between scheduling runs (default: 5)")
    parser.add_argument("--dry-run", action="store_true", 
                        help="Log what would run but don't actually run scripts")
    parser.add_argument("--run-now", type=str, 
                        help="Run a specific script immediately and exit")
    args = parser.parse_args()
    
    if args.run_now:
        logger.info(f"Running {args.run_now} immediately")
        run_script(args.run_now)
    else:
        run_scheduler(interval=args.interval, dry_run=args.dry_run) 