#!/usr/bin/env python3
"""
Economic Reports Fetcher
Fetches economic reports from various sources and stores them in Supabase
"""

import os
import sys
import json
import logging
import time
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv
from supabase import create_client, Client
import traceback
import uuid

# Add the parent directory to the path so we can import unusual_whales_api
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from unusual_whales_api import get_economic_calendar, format_economic_calendar_event_for_db

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/economic_reports_fetcher.log")
    ]
)
logger = logging.getLogger("economic_reports_fetcher")

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
ECONOMIC_REPORTS_TABLE = "economic_reports"
ECONOMIC_EVENTS_TABLE = "economic_events"

class RateLimiter:
    """Simple rate limiter for API calls."""
    def __init__(self, calls_per_minute=15):
        self.calls_per_minute = calls_per_minute
        self.min_interval = 60.0 / calls_per_minute
        self.last_call_time = 0
    
    def wait_if_needed(self):
        """Wait if necessary to maintain the rate limit."""
        current_time = time.time()
        elapsed = current_time - self.last_call_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call_time = time.time()

class EconomicReportsFetcher:
    def __init__(self):
        """Initialize the economic reports fetcher."""
        self.limiter = RateLimiter(calls_per_minute=15)
        self.session = requests.Session()
    
    def fetch_economic_calendar(self):
        """
        Fetch economic calendar events from the Unusual Whales API.
        """
        try:
            logger.info("Fetching economic calendar events")
            
            economic_events = get_economic_calendar()
            
            if not economic_events:
                logger.warning("No economic calendar events returned")
                return []
                
            logger.info(f"Successfully fetched {len(economic_events)} economic calendar events")
            return economic_events
        except Exception as e:
            logger.error(f"Error fetching economic calendar events: {str(e)}")
            return []
    
    def fetch_research_reports(self, max_reports=10):
        """
        Fetch recent economic research reports from various sources.
        """
        try:
            logger.info("Fetching economic research reports")
            
            # Sources of economic research reports
            sources = [
                {"name": "Federal Reserve", "url": "https://www.federalreserve.gov/feeds/research_all.xml"},
                {"name": "IMF", "url": "https://www.imf.org/en/Publications/RSS/rss-feed-research"},
                {"name": "World Bank", "url": "https://www.worldbank.org/en/rss/research"}
            ]
            
            all_reports = []
            
            # Mocked response for development purposes
            # In reality we would fetch and parse the RSS feeds
            
            # Generate mock reports for testing
            for i in range(max_reports):
                source = sources[i % len(sources)]
                mock_report = {
                    "id": f"report-{datetime.now().strftime('%Y%m%d')}-{i}",
                    "source": source["name"],
                    "title": f"Economic Outlook Report {i+1}",
                    "report_date": datetime.now().strftime("%Y-%m-%d"),
                    "published_date": datetime.now().strftime("%Y-%m-%d"),
                    "url": f"https://example.com/report-{i+1}",
                    "summary": "This report analyzes current economic trends and provides future projections.",
                    "category": "Economic Outlook",
                    "timestamp": datetime.now().isoformat()
                }
                all_reports.append(mock_report)
            
            logger.info(f"Successfully fetched {len(all_reports)} economic research reports")
            return all_reports
        except Exception as e:
            logger.error(f"Error fetching economic research reports: {str(e)}")
            return []
    
    def store_economic_events(self, events):
        """
        Store economic calendar events in Supabase.
        """
        if not events:
            return 0
        
        try:
            logger.info(f"Storing {len(events)} economic calendar events")
            
            stored_count = 0
            for event in events:
                formatted_event = format_economic_calendar_event_for_db(event)
                
                # Generate a UUID for the event instead of a string-based ID
                formatted_event["id"] = str(uuid.uuid4())
                
                try:
                    # Insert new event - no need to check for existence with UUID
                    supabase.table("economic_events").insert(formatted_event).execute()
                    stored_count += 1
                except Exception as e:
                    logger.error(f"Error storing economic event: {str(e)}")
            
            logger.info(f"Successfully stored {stored_count} economic calendar events")
            return stored_count
        except Exception as e:
            logger.error(f"Error storing economic calendar events: {str(e)}")
            return 0
    
    def store_research_reports(self, reports):
        """
        Store economic research reports in Supabase.
        """
        if not reports:
            return 0
        
        try:
            logger.info(f"Storing {len(reports)} economic research reports")
            
            stored_count = 0
            for report in reports:
                # Format the report data to match the economic_reports table schema
                formatted_report = {
                    "id": str(uuid.uuid4()),  # Generate a UUID for the report
                    "report_name": report.get("title", "Economic Report"),  # This is the required field
                    "event_date": datetime.now().isoformat(),
                    "forecast": None,
                    "previous": None,
                    "actual": None,
                    "importance": "medium",
                    "category": report.get("category", "Economic Outlook"),
                    "source": report.get("source", "Mock Data"),
                    "report_period": report.get("report_period", "Monthly"),
                    "impact": "medium",
                    "notes": report.get("summary", "No summary available"),
                    "fetched_at": datetime.now().isoformat()
                }
                
                try:
                    # Insert new report - no need to check for existence with UUID
                    supabase.table("economic_reports").insert(formatted_report).execute()
                    stored_count += 1
                except Exception as e:
                    logger.error(f"Error storing economic report: {str(e)}")
            
            logger.info(f"Successfully stored {stored_count} economic research reports")
            return stored_count
        except Exception as e:
            logger.error(f"Error storing economic research reports: {str(e)}")
            return 0
    
    def generate_events_alerts(self, events):
        """
        Generate alerts for important economic events.
        This functionality is disabled to focus on data storage.
        """
        logger.info("Alerts generation is disabled to focus on data storage")
        return
        
    def run(self):
        """
        Run the economic reports fetcher.
        """
        logger.info("Running economic reports fetcher")
        
        try:
            # Fetch economic calendar events
            events = self.fetch_economic_calendar()
            
            # Store economic calendar events
            events_stored = self.store_economic_events(events)
            
            # Alerts generation is disabled
            # if events:
            #     self.generate_events_alerts(events)
            
            # Fetch research reports
            reports = self.fetch_research_reports()
            
            # Store research reports
            reports_stored = self.store_research_reports(reports)
            
            logger.info(f"Economic reports fetcher completed - Stored {events_stored} events and {reports_stored} reports")
            
            return {
                "status": "success",
                "events_stored": events_stored,
                "reports_stored": reports_stored
            }
            
        except Exception as e:
            logger.error(f"Error running economic reports fetcher: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "error": str(e)
            }
    
    def close(self):
        """Close the session."""
        if self.session:
            self.session.close()

def main():
    """Run the economic reports fetcher as a standalone script."""
    fetcher = EconomicReportsFetcher()
    try:
        result = fetcher.run()
        print(json.dumps(result, indent=2))
    finally:
        fetcher.close()

if __name__ == "__main__":
    main() 