#!/usr/bin/env python3
"""
FDA Calendar Fetcher
Fetches FDA calendar events from Unusual Whales API and stores in Supabase
"""

import os
import sys
import json
import logging
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client
import traceback
import uuid  # Add this import for UUID generation

# Add the parent directory to the path so we can import unusual_whales_api
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from unusual_whales_api import get_fda_calendar, format_fda_calendar_event_for_db

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/fda_calendar_fetcher.log")
    ]
)
logger = logging.getLogger("fda_calendar_fetcher")

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

# Constants
FDA_CALENDAR_TABLE = "fda_calendar"


class FDACalendarFetcher:
    def __init__(self):
        """Initialize the FDA calendar fetcher."""
        self.last_api_call = 0
        self.min_api_interval = 0.5  # seconds between API calls
        
    def fetch_fda_calendar(self, days_ahead=180):
        """
        Fetch FDA calendar events from the Unusual Whales API.
        
        Args:
            days_ahead: Number of days ahead to fetch events for
        
        Returns:
            List of FDA calendar events
        """
        try:
            # Apply rate limiting
            current_time = time.time()
            time_since_last_call = current_time - self.last_api_call
            if time_since_last_call < self.min_api_interval:
                time.sleep(self.min_api_interval - time_since_last_call)
            
            logger.info(f"Fetching FDA calendar events for the next {days_ahead} days")
            
            # Define date range for FDA calendar
            target_date_min = datetime.now().strftime("%Y-%m-%d")
            target_date_max = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
            
            # Get FDA calendar events from Unusual Whales API
            fda_events = get_fda_calendar(
                target_date_min=target_date_min,
                target_date_max=target_date_max
            )
            
            self.last_api_call = time.time()
            
            if not fda_events:
                logger.warning("No FDA calendar events found")
                return []
                
            logger.info(f"Successfully fetched {len(fda_events)} FDA calendar events")
            
            # Format events for database
            formatted_events = []
            for event in fda_events:
                try:
                    formatted_event = format_fda_calendar_event_for_db(event)
                    formatted_events.append(formatted_event)
                except Exception as e:
                    logger.error(f"Error formatting FDA event: {str(e)}")
            
            return formatted_events
        except Exception as e:
            logger.error(f"Error fetching FDA calendar: {str(e)}")
            logger.error(traceback.format_exc())
            return []
    
    def store_fda_events(self, events):
        """
        Store FDA calendar events in Supabase.
        
        Args:
            events: List of FDA calendar events to store
            
        Returns:
            Number of events stored
        """
        if not events:
            return 0
        
        try:
            logger.info(f"Storing {len(events)} FDA calendar events")
            
            # Batch insert to avoid request size limits
            batch_size = 20
            stored_count = 0
            
            for i in range(0, len(events), batch_size):
                batch = events[i:i+batch_size]
                
                # Generate UUIDs for each event based on drug and date
                for event in batch:
                    # Create a deterministic ID based on ticker, drug, and date
                    unique_key = f"{event['ticker'] or 'unknown'}-{event['drug'] or 'unknown'}-{event['start_date']}"
                    # Generate UUID using uuid5 with a namespace
                    event["id"] = str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_key))
                
                # Check if events already exist
                existing_ids = []
                for event in batch:
                    result = supabase.table(FDA_CALENDAR_TABLE) \
                        .select("id") \
                        .eq("id", event["id"]) \
                        .execute()
                    
                    if result.data and len(result.data) > 0:
                        existing_ids.append(event["id"])
                
                # Split into new and existing events
                new_events = [e for e in batch if e["id"] not in existing_ids]
                existing_events = [e for e in batch if e["id"] in existing_ids]
                
                # Insert new events
                if new_events:
                    supabase.table(FDA_CALENDAR_TABLE).insert(new_events).execute()
                    stored_count += len(new_events)
                    logger.info(f"Inserted {len(new_events)} new FDA events")
                
                # Update existing events
                for event in existing_events:
                    supabase.table(FDA_CALENDAR_TABLE) \
                        .update(event) \
                        .eq("id", event["id"]) \
                        .execute()
                    stored_count += 1
                
                logger.info(f"Updated {len(existing_events)} existing FDA events")
                
                # Brief pause to avoid overwhelming the database
                time.sleep(0.1)
            
            logger.info(f"Successfully stored {stored_count} FDA calendar events")
            return stored_count
        except Exception as e:
            logger.error(f"Error storing FDA events: {str(e)}")
            logger.error(traceback.format_exc())
            return 0
    
    def generate_fda_alerts(self, events):
        """
        Generate alerts for important FDA calendar events.
        
        Args:
            events: List of FDA calendar events to generate alerts for
        """
        try:
            logger.info(f"Checking {len(events)} FDA events for alerts")
            
            # Filter for important events in the next 30 days
            now = datetime.now()
            upcoming_catalysts = []
            
            for event in events:
                try:
                    # Parse start date 
                    start_date = datetime.strptime(event["start_date"], "%Y-%m-%d")
                    
                    # Check if within 30 days
                    days_until = (start_date - now).days
                    if 0 <= days_until <= 30:
                        # Important catalysts include approvals, phase results, or high market cap
                        is_important = (
                            "approval" in event.get("catalyst", "").lower() or
                            "phase" in event.get("catalyst", "").lower() or
                            "pdufa" in event.get("catalyst", "").lower() or
                            "result" in event.get("catalyst", "").lower() or
                            (event.get("marketcap") and float(event.get("marketcap", 0)) > 1000000000)
                        )
                        
                        if is_important:
                            upcoming_catalysts.append(event)
                except Exception as e:
                    logger.error(f"Error processing FDA event for alerts: {str(e)}")
            
            alerts = []
            for event in upcoming_catalysts:
                try:
                    ticker = event.get("ticker", "")
                    drug = event.get("drug", "Unknown")
                    catalyst = event.get("catalyst", "Unknown Event")
                    start_date = event.get("start_date", "")
                    notes = event.get("notes", "")
                    
                    # Generate a unique key for this alert
                    alert_key = f"fda_{ticker}_{drug}_{start_date}".replace(" ", "_").lower()
                    
                    # Create UUID from the key
                    alert_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, alert_key))
                    
                    alerts.append({
                        "id": alert_id,
                        "title": f"FDA Event: {ticker} - {drug}",
                        "message": f"Upcoming FDA catalyst: {catalyst} for {ticker} ({drug}) on {start_date}. {notes}",
                        "type": "fda",
                        "subtype": "calendar_event",
                        "importance": "high" if "approval" in catalyst.lower() else "medium",
                        "related_ticker": ticker if ticker else None,
                        "created_at": datetime.now().isoformat(),
                        "meta": json.dumps({
                            "drug": drug,
                            "catalyst": catalyst,
                            "date": start_date,
                            "notes": notes
                        })
                    })
                except Exception as e:
                    logger.error(f"Error creating FDA alert: {str(e)}")
            
            # Store alerts in database
            if alerts:
                for alert in alerts:
                    supabase.table("alerts").upsert(
                        alert,
                        on_conflict=["id"]
                    ).execute()
                
                logger.info(f"Created {len(alerts)} FDA event alerts")
                
        except Exception as e:
            logger.error(f"Error generating FDA alerts: {str(e)}")
    
    def get_watchlist_tickers(self):
        """
        Get tickers from all user watchlists.
        
        Returns:
            Set of unique ticker symbols from all watchlists
        """
        try:
            # Query the watchlists table
            response = supabase.table("watchlists").select("tickers").execute()
            
            # Extract unique tickers from all watchlists
            all_tickers = set()
            for watchlist in response.data:
                tickers = watchlist.get("tickers", [])
                all_tickers.update(tickers)
            
            logger.info(f"Found {len(all_tickers)} unique tickers in watchlists")
            return list(all_tickers)
        except Exception as e:
            logger.error(f"Error fetching watchlist tickers: {str(e)}")
            return []
    
    def run(self, days_ahead=180):
        """
        Run the FDA calendar fetcher.
        
        Args:
            days_ahead: Number of days ahead to fetch events for
            
        Returns:
            Dictionary with results summary
        """
        logger.info(f"Running FDA calendar fetcher for the next {days_ahead} days")
        
        try:
            # Fetch FDA calendar events
            events = self.fetch_fda_calendar(days_ahead=days_ahead)
            
            # Store FDA calendar events
            events_stored = self.store_fda_events(events)
            
            # Generate alerts for important events
            if events:
                self.generate_fda_alerts(events)
            
            logger.info(f"FDA calendar fetcher completed - Stored {events_stored} events")
            
            return {
                "status": "success",
                "events_stored": events_stored
            }
            
        except Exception as e:
            logger.error(f"Error running FDA calendar fetcher: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "error": str(e)
            }

def main():
    """Run the FDA calendar fetcher as a standalone script."""
    fetcher = FDACalendarFetcher()
    result = fetcher.run()
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main() 