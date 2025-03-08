#!/usr/bin/env python3
"""
Economic Indicators Fetcher Service
Fetches economic data from FRED and Alpha Vantage APIs and stores in Supabase
"""

import os
import sys
import json
import logging
import asyncio
import time
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from supabase import create_client, Client
import traceback

# # Optional: Google AI for summaries if available
# try:
#     import google.generativeai as genai
#     HAS_GEMINI = True
# except ImportError:
    HAS_GEMINI = False

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/economic_indicators_fetcher.log")
    ]
)
logger = logging.getLogger("economic_indicators_fetcher")

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
ALPHA_VANTAGE_API_KEY = os.getenv("API_KEY_ALPHA_VANTAGE")
FRED_API_KEY = os.getenv("FRED_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Google Gemini API if available
if HAS_GEMINI and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

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

# Constants for tables
ECONOMIC_INDICATORS_TABLE = "economic_indicators"
ECONOMIC_NEWS_TABLE = "economic_news"
FRED_OBSERVATION_TABLE = "fred_observations"
FRED_METADATA_TABLE = "fred_metadata"
FRED_USER_SERIES_TABLE = "fred_user_series"
FRED_ECONOMIC_EVENTS_TABLE = "fred_economic_events"

# FRED API Configuration
FRED_BASE_URL = "https://api.stlouisfed.org/fred/"


class EconomicIndicatorFetcher:
    def __init__(self):
        """Initialize the economic indicators fetcher."""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Stock Analytics Dashboard - Financial Data Pipeline"
        })
        
        # FRED rate limiting
        self.fred_rate_limit = 120  # Requests per minute
        self.fred_requests_made = 0
        self.last_reset_time = time.time()
        
        # Alpha Vantage rate limiting
        self.alpha_vantage_min_interval = 12  # Wait at least 12 seconds between requests (5 per minute limit)
        self.last_alpha_vantage_request = 0
        
        # Default series to track
        self.default_series = {
            "GDPC1": "Real GDP",
            "CPIAUCSL": "Consumer Price Index (CPI)",
            "UNRATE": "Unemployment Rate", 
            "FEDFUNDS": "Federal Funds Rate",
            "RSXFS": "Retail Sales",
            "INDPRO": "Industrial Production Index",
            "HOUST": "Housing Starts",
            "DCOILWTICO": "Crude Oil Prices",
            "DGS10": "10-Year Treasury Rate",
            "VIXCLS": "CBOE Volatility Index (VIX)",
            "PAYEMS": "Nonfarm Payroll",
            "PCE": "Personal Consumption Expenditures",
            "UMCSENT": "Consumer Sentiment"
        }
    
    async def run(self, user_id=None):
        """Run the economic indicator fetcher to collect all data."""
        logger.info("Running economic indicator fetcher")
        
        try:
            # Collect indicators from Alpha Vantage
            indicators = {}
            
            # Fetch GDP data
            if ALPHA_VANTAGE_API_KEY:
                logger.info("Fetching economic indicators from Alpha Vantage")
                
                # GDP
                gdp_data = await self.fetch_gdp()
                if gdp_data:
                    indicators["gdp"] = gdp_data
                await asyncio.sleep(self.alpha_vantage_min_interval)
                
                # Inflation
                inflation_data = await self.fetch_inflation()
                if inflation_data:
                    indicators["inflation"] = inflation_data
                await asyncio.sleep(self.alpha_vantage_min_interval)
                
                # Unemployment
                unemployment_data = await self.fetch_unemployment()
                if unemployment_data:
                    indicators["unemployment"] = unemployment_data
                await asyncio.sleep(self.alpha_vantage_min_interval)
                
                # Interest rates
                interest_rate_data = await self.fetch_interest_rates()
                if interest_rate_data:
                    indicators["interest_rates"] = interest_rate_data
                await asyncio.sleep(self.alpha_vantage_min_interval)
                
                # Retail sales
                retail_sales_data = await self.fetch_retail_sales()
                if retail_sales_data:
                    indicators["retail_sales"] = retail_sales_data
                await asyncio.sleep(self.alpha_vantage_min_interval)
                
                # Economic news
                economic_news = await self.fetch_economic_news()
                if economic_news:
                    await self.insert_news(economic_news)
            else:
                logger.warning("Alpha Vantage API key not set, skipping Alpha Vantage data fetching")
            
            # FRED indicators
            if FRED_API_KEY:
                logger.info("Fetching FRED economic data")
                
                # Get series for the specified user or default series
                series_ids = await self.get_user_series(user_id) if user_id else self.default_series
                
                # Fetch FRED data
                fred_indicators = await self.fetch_fred_indicators(series_ids)
                
                # Insert FRED data into its tables
                if fred_indicators:
                    await self.insert_fred_data(fred_indicators)
                
                # Check for updates on existing series
                await self.check_series_updates()
                
                # Check for upcoming economic data releases
                await self.fetch_release_dates()
            else:
                logger.warning("FRED API key not set, skipping FRED data fetching")
            
            # Insert Alpha Vantage indicators
            if indicators:
                await self.insert_indicators(indicators)
            
            logger.info("Economic indicator fetcher completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error running economic indicator fetcher: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    async def alpha_vantage_request(self, function, params=None):
        """Make a rate-limited request to Alpha Vantage API."""
        if not ALPHA_VANTAGE_API_KEY:
            logger.error("Alpha Vantage API key not set")
            return None
            
        if params is None:
            params = {}
            
        # Add API key and function to params
        params["apikey"] = ALPHA_VANTAGE_API_KEY
        params["function"] = function
        
        # Ensure we don't exceed rate limits
        current_time = time.time()
        time_since_last_request = current_time - self.last_alpha_vantage_request
        
        if time_since_last_request < self.alpha_vantage_min_interval:
            wait_time = self.alpha_vantage_min_interval - time_since_last_request
            logger.debug(f"Rate limiting Alpha Vantage: waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)
        
        # Make the request
        try:
            url = "https://www.alphavantage.co/query"
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            # Update last request time
            self.last_alpha_vantage_request = time.time()
            
            # Check if we've hit the API rate limit
            if "Note" in response.json() and "API call frequency" in response.json()["Note"]:
                logger.warning("Alpha Vantage rate limit hit, waiting and retrying")
                await asyncio.sleep(60)  # Wait a minute for the limit to reset
                return await self.alpha_vantage_request(function, params)
                
            return response.json()
        except Exception as e:
            logger.error(f"Error making Alpha Vantage request for {function}: {str(e)}")
            return None
    
    async def fred_request(self, endpoint, params=None):
        """Make a rate-limited request to FRED API."""
        if not FRED_API_KEY:
            logger.error("FRED API key not set")
            return None
            
        if params is None:
            params = {}
            
        # Add API key to params
        params["api_key"] = FRED_API_KEY
        params["file_type"] = "json"
        
        # Ensure we don't exceed rate limits (120 requests per minute)
        current_time = time.time()
        
        # Reset counter if a minute has passed
        if current_time - self.last_reset_time >= 60:
            self.fred_requests_made = 0
            self.last_reset_time = current_time
            
        # If we've hit the limit, wait until the minute is up
        if self.fred_requests_made >= self.fred_rate_limit:
            wait_time = 60 - (current_time - self.last_reset_time)
            if wait_time > 0:
                logger.debug(f"Rate limiting FRED: waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
                self.fred_requests_made = 0
                self.last_reset_time = time.time()
        
        # Make the request
        try:
            url = f"{FRED_BASE_URL}{endpoint}"
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            # Increment request counter
            self.fred_requests_made += 1
            
            # Handle rate limiting headers if present
            if response.status_code == 429:
                wait_time = int(response.headers.get("Retry-After", 60))
                logger.warning(f"FRED rate limit hit, waiting {wait_time} seconds")
                await asyncio.sleep(wait_time)
                return await self.fred_request(endpoint, params)
                
            return response.json()
        except Exception as e:
            logger.error(f"Error making FRED request for {endpoint}: {str(e)}")
            return None
    
    async def check_series_updates(self):
        """Check for recently updated series and trigger fetches for new data."""
        if not FRED_API_KEY:
            logger.warning("No FRED API key provided, skipping series updates")
            return
            
        logger.info("Checking for recently updated series from FRED")
        
        try:
            params = {
                "realtime_start": (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d"),
                "realtime_end": datetime.now().strftime("%Y-%m-%d"),
                "limit": 1000
            }
            
            response = await self.fred_request("series/updates", params)
            
            if not response or "seriess" not in response or not response["seriess"]:
                logger.warning("No recently updated series found")
                return
                
            for series in response["seriess"]:
                series_id = series["id"]
                
                # Only process series that are in our default set or user-selected
                if series_id in self.default_series or await self.is_user_selected_series(series_id):
                    last_updated = datetime.strptime(series["last_updated"], "%Y-%m-%d %H:%M:%S-05")
                    last_fetch_time = await self.get_last_fetch_time(series_id)
                    
                    if last_fetch_time is None or last_updated > last_fetch_time:
                        logger.info(f"Fetching updated series: {series_id}")
                        await self.fetch_single_series(series_id)
                        await self.update_last_fetch_time(series_id, datetime.now())
                        
                        # Create an economic event for the update
                        await self.create_economic_event(
                            series_id=series_id, 
                            title=f"{self.default_series.get(series_id, series_id)} Updated",
                            event_type="data_update",
                            content=f"New economic data available for {self.default_series.get(series_id, series_id)}"
                        )
        except Exception as e:
            logger.error(f"Error checking series updates: {str(e)}")
            logger.error(traceback.format_exc())
    
    async def is_user_selected_series(self, series_id):
        """Check if a series is selected by any user."""
        try:
            result = supabase.table(FRED_USER_SERIES_TABLE).select("series_id").eq("series_id", series_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error checking user series: {str(e)}")
            return False
    
    async def get_last_fetch_time(self, series_id):
        """Retrieve the last fetch time for a series from Supabase."""
        try:
            result = supabase.table(FRED_METADATA_TABLE).select("last_fetch_time").eq("series_id", series_id).execute()
            if result.data:
                return datetime.fromisoformat(result.data[0]["last_fetch_time"].replace("Z", "+00:00"))
            return None
        except Exception as e:
            logger.error(f"Error getting last fetch time: {str(e)}")
            return None
    
    async def update_last_fetch_time(self, series_id, fetch_time):
        """Update the last fetch time for a series in Supabase."""
        try:
            data = {
                "series_id": series_id,
                "last_fetch_time": fetch_time.isoformat()
            }
            supabase.table(FRED_METADATA_TABLE).upsert(data).execute()
        except Exception as e:
            logger.error(f"Error updating last fetch time: {str(e)}")
    
    async def fetch_release_dates(self):
        """Fetch upcoming release dates for economic data."""
        if not FRED_API_KEY:
            logger.warning("No FRED API key provided, skipping release dates")
            return
            
        logger.info("Fetching upcoming economic data release dates")
        
        try:
            params = {
                "realtime_start": datetime.now().strftime("%Y-%m-%d"),
                "realtime_end": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "limit": 1000,
                "include_release_dates_with_no_data": "true"
            }
            
            response = await self.fred_request("releases/dates", params)
            
            if not response or "release_dates" not in response:
                logger.warning("No upcoming release dates found")
                return
                
            for release in response["release_dates"]:
                release_date = datetime.strptime(release["date"], "%Y-%m-%d")
                release_id = release["release_id"]
                release_name = release.get("name", f"Economic Release {release_id}")
                
                # Only process if the release is in the future
                if release_date > datetime.now():
                    # Create an economic event for the upcoming release
                    await self.create_economic_event(
                        series_id=None,
                        title=f"Upcoming Economic Release: {release_name}",
                        event_type="upcoming_release",
                        content=f"Economic data release scheduled for {release_date.strftime('%Y-%m-%d')}"
                    )
                    
                    logger.info(f"Added event for upcoming release {release_name} on {release_date}")
        except Exception as e:
            logger.error(f"Error fetching release dates: {str(e)}")
            logger.error(traceback.format_exc())
    
    async def fetch_single_series(self, series_id):
        """Fetch data for a single FRED series."""
        if not FRED_API_KEY:
            logger.warning("No FRED API key provided, skipping single series fetch")
            return
            
        logger.info(f"Fetching single FRED series: {series_id}")
        
        try:
            # Get series description
            description = self.default_series.get(series_id, "Custom Series")
            
            # Define the date range - get observations since the last observation
            last_observation_date = await self.get_last_observation_date(series_id)
            if last_observation_date:
                # Start from the day after the last observation
                observation_start = (datetime.fromisoformat(last_observation_date.replace("Z", "+00:00")) + timedelta(days=1)).strftime("%Y-%m-%d")
            else:
                # If no previous observations, get all data
                observation_start = "1776-07-04"  # FRED's earliest possible date
                
            # Current date for end of range
            observation_end = datetime.now().strftime("%Y-%m-%d")
            
            # Fetch observations
            params = {
                "series_id": series_id,
                "observation_start": observation_start,
                "observation_end": observation_end,
                "sort_order": "asc"  # Oldest first
            }
            
            response = await self.fred_request("series/observations", params)
            
            if not response or "observations" not in response or not response["observations"]:
                logger.info(f"No new observations for series {series_id}")
                return
                
            observations = response["observations"]
            logger.info(f"Found {len(observations)} new observations for series {series_id}")
            
            # Save observations to database
            for obs in observations:
                observation_data = {
                    "series_id": series_id,
                    "date": obs["date"],
                    "value": float(obs["value"]) if obs["value"] != "." else None,
                    "vintage_date": datetime.now().strftime("%Y-%m-%d"),  # Current date as vintage
                    "revision_timestamp": datetime.now().isoformat()
                }
                
                supabase.table(FRED_OBSERVATION_TABLE).upsert(observation_data, on_conflict=["series_id", "date"]).execute()
            
            logger.info(f"Successfully saved {len(observations)} observations for series {series_id}")
            
            # Generate AI summary if available
            if HAS_GEMINI and GEMINI_API_KEY and len(observations) > 0:
                await self.generate_indicator_summary(series_id, description, observations)
                
        except Exception as e:
            logger.error(f"Error fetching single series {series_id}: {str(e)}")
            logger.error(traceback.format_exc())
    
    async def get_last_observation_date(self, series_id):
        """Get the most recent observation date for a series from Supabase."""
        try:
            result = supabase.table(FRED_OBSERVATION_TABLE).select("date").eq("series_id", series_id).order("date", desc=True).limit(1).execute()
            return result.data[0]["date"] if result.data else None
        except Exception as e:
            logger.error(f"Error getting last observation date: {str(e)}")
            return None
    
    async def fetch_fred_indicators(self, series_ids=None):
        """Fetch economic indicators from FRED API."""
        if not FRED_API_KEY:
            logger.warning("No FRED API key provided, skipping FRED indicators")
            return {}
            
        logger.info("Fetching FRED economic indicators")
        
        if series_ids is None:
            series_ids = self.default_series
            
        indicators = {}
        
        for series_id, description in series_ids.items():
            try:
                # Fetch the series metadata
                metadata_params = {
                    "series_id": series_id
                }
                
                metadata = await self.fred_request("series", metadata_params)
                
                if not metadata or "seriess" not in metadata or not metadata["seriess"]:
                    logger.warning(f"Could not fetch metadata for series {series_id}")
                    continue
                    
                series_info = metadata["seriess"][0]
                
                # Check if we already have the most recent data
                last_updated = datetime.strptime(series_info["last_updated"], "%Y-%m-%d %H:%M:%S-05")
                stored_last_updated = await self.get_stored_last_updated(series_id)
                
                if stored_last_updated and last_updated <= stored_last_updated:
                    logger.info(f"Series {series_id} is already up to date")
                    continue
                
                # Get the latest observations
                last_observation_date = await self.get_last_observation_date(series_id)
                if last_observation_date:
                    # Start from the day after the last observation
                    observation_start = (datetime.fromisoformat(last_observation_date.replace("Z", "+00:00")) + timedelta(days=1)).strftime("%Y-%m-%d")
                else:
                    # If no previous observations, get all data
                    observation_start = "1776-07-04"  # FRED's earliest possible date
                    
                params = {
                    "series_id": series_id,
                    "observation_start": observation_start,
                    "observation_end": datetime.now().strftime("%Y-%m-%d"),
                    "sort_order": "asc"  # Oldest first
                }
                
                response = await self.fred_request("series/observations", params)
                
                if not response or "observations" not in response:
                    logger.warning(f"Could not fetch observations for series {series_id}")
                    continue
                    
                observations = response["observations"]
                
                if not observations:
                    logger.info(f"No new observations for series {series_id}")
                    continue
                    
                indicators[series_id] = {
                    "description": description,
                    "observations": observations,
                    "last_updated": last_updated.isoformat()
                }
                
                # Update the stored last updated timestamp
                await self.update_stored_last_updated(series_id, last_updated)
                
                logger.info(f"Successfully fetched {len(observations)} new observations for series {series_id}")
                
                # Generate AI summary if available
                if HAS_GEMINI and GEMINI_API_KEY and len(observations) > 0:
                    await self.generate_indicator_summary(series_id, description, observations)
                    
            except Exception as e:
                logger.error(f"Error fetching FRED indicators for series {series_id}: {str(e)}")
                logger.error(traceback.format_exc())
                continue
                
            # Add a small delay between requests to avoid overwhelming the API
            await asyncio.sleep(0.5)
            
        return indicators
    
    async def get_user_series(self, user_id):
        """Retrieve user-selected series from Supabase."""
        try:
            result = supabase.table(FRED_USER_SERIES_TABLE).select("series_id, description").eq("user_id", user_id).execute()
            return {row["series_id"]: row["description"] for row in result.data} if result.data else self.default_series
        except Exception as e:
            logger.error(f"Error getting user series: {str(e)}")
            return self.default_series
    
    async def get_stored_last_updated(self, series_id):
        """Get the last updated timestamp for a series from Supabase."""
        try:
            result = supabase.table(FRED_METADATA_TABLE).select("last_updated").eq("series_id", series_id).execute()
            if result.data and result.data[0]["last_updated"]:
                return datetime.fromisoformat(result.data[0]["last_updated"].replace("Z", "+00:00"))
            return None
        except Exception as e:
            logger.error(f"Error getting stored last updated: {str(e)}")
            return None
    
    async def update_stored_last_updated(self, series_id, last_updated):
        """Update the last updated timestamp for a series in Supabase."""
        try:
            data = {
                "series_id": series_id,
                "last_updated": last_updated.isoformat()
            }
            supabase.table(FRED_METADATA_TABLE).upsert(data).execute()
        except Exception as e:
            logger.error(f"Error updating stored last updated: {str(e)}")
    
    async def insert_fred_data(self, indicators):
        """Insert fetched indicators into Supabase."""
        for series_id, data in indicators.items():
            for obs in data["observations"]:
                try:
                    # Get the value, handling missing values
                    value = float(obs["value"]) if obs["value"] != "." else None
                    
                    # Prepare the observation data
                    observation_data = {
                        "series_id": series_id,
                        "date": obs["date"],
                        "value": value,
                        "vintage_date": datetime.now().strftime("%Y-%m-%d"),  # Current date as vintage
                        "revision_timestamp": data["last_updated"]
                    }
                    
                    # Insert or update the observation
                    supabase.table(FRED_OBSERVATION_TABLE).upsert(observation_data, on_conflict=["series_id", "date"]).execute()
                    
                except Exception as e:
                    logger.error(f"Error inserting observation for {series_id}: {str(e)}")
    
    async def generate_indicator_summary(self, series_id, description, observations):
        """Generate an AI summary of the economic indicator data."""
        if not HAS_GEMINI or not GEMINI_API_KEY or not observations:
            return
            
        try:
            # Get the most recent observations (last 12 or all if fewer)
            recent_obs = observations[-12:] if len(observations) > 12 else observations
            
            # Prepare data for the AI model
            data_text = "\n".join([f"Date: {obs['date']}, Value: {obs['value']}" for obs in recent_obs])
            
            prompt = f"""Analyze the following economic data for {description} ({series_id}) and provide a concise summary 
            of the current trend, any notable changes, and potential market impact. Keep your response under 100 words.
            
            Recent Data:
            {data_text}
            """
            
            # Generate the summary using Gemini
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            
            if response and hasattr(response, 'text'):
                summary = response.text.strip()
                
                # Create an economic event with the AI summary
                await self.create_economic_event(
                    series_id=series_id,
                    title=f"{description} Update",
                    event_type="ai_analysis",
                    content=summary
                )
                
                logger.info(f"Generated AI summary for {series_id}")
        except Exception as e:
            logger.error(f"Error generating AI summary for {series_id}: {str(e)}")
    
    async def create_economic_event(self, series_id, title, event_type, content):
        """Create an economic event record in the database."""
        try:
            event_data = {
                "series_id": series_id,
                "title": title,
                "event_type": event_type,
                "content": content,
                "created_at": datetime.now().isoformat()
            }
            
            supabase.table(FRED_ECONOMIC_EVENTS_TABLE).insert(event_data).execute()
            logger.info(f"Created economic event: {title}")
        except Exception as e:
            logger.error(f"Error creating economic event: {str(e)}")
    
    async def fetch_gdp(self):
        """Fetch GDP data from Alpha Vantage."""
        logger.info("Fetching GDP data")
        
        try:
            params = {
                "interval": "quarterly"
            }
            
            data = await self.alpha_vantage_request("REAL_GDP", params)
            
            if not data or "data" not in data or not data["data"]:
                logger.warning("No GDP data available")
                return None
                
            return {
                "name": "GDP",
                "description": "Gross Domestic Product (GDP)",
                "unit": data.get("unit", ""),
                "data": data.get("data", [])[:12]  # Last 3 years quarterly
            }
        except Exception as e:
            logger.error(f"Error fetching GDP data: {str(e)}")
            return None
    
    async def fetch_inflation(self):
        """Fetch inflation (CPI) data from Alpha Vantage."""
        logger.info("Fetching inflation data")
        
        try:
            params = {
                "interval": "monthly"
            }
            
            data = await self.alpha_vantage_request("CPI", params)
            
            if not data or "data" not in data or not data["data"]:
                logger.warning("No inflation (CPI) data available")
                return None
                
            return {
                "name": "CPI",
                "description": "Consumer Price Index (Inflation)",
                "unit": data.get("unit", ""),
                "data": data.get("data", [])[:12]  # Last 12 months
            }
        except Exception as e:
            logger.error(f"Error fetching inflation data: {str(e)}")
            return None
    
    async def fetch_unemployment(self):
        """Fetch unemployment data from Alpha Vantage."""
        logger.info("Fetching unemployment data")
        
        try:
            params = {}
            
            data = await self.alpha_vantage_request("UNEMPLOYMENT", params)
            
            if not data or "data" not in data or not data["data"]:
                logger.warning("No unemployment data available")
                return None
                
            return {
                "name": "UNEMPLOYMENT",
                "description": "Unemployment Rate",
                "unit": data.get("unit", ""),
                "data": data.get("data", [])[:12]  # Last 12 months
            }
        except Exception as e:
            logger.error(f"Error fetching unemployment data: {str(e)}")
            return None
    
    async def fetch_interest_rates(self):
        """Fetch interest rate data from Alpha Vantage."""
        logger.info("Fetching interest rate data")
        
        try:
            params = {
                "interval": "monthly"
            }
            
            data = await self.alpha_vantage_request("FEDERAL_FUNDS_RATE", params)
            
            if not data or "data" not in data or not data["data"]:
                logger.warning("No interest rate data available")
                return None
                
            return {
                "name": "FEDERAL_FUNDS_RATE",
                "description": "Federal Funds Rate",
                "unit": data.get("unit", ""),
                "data": data.get("data", [])[:12]  # Last 12 months
            }
        except Exception as e:
            logger.error(f"Error fetching interest rate data: {str(e)}")
            return None
    
    async def fetch_retail_sales(self):
        """Fetch retail sales data from Alpha Vantage."""
        logger.info("Fetching retail sales data")
        
        try:
            params = {}
            
            data = await self.alpha_vantage_request("RETAIL_SALES", params)
            
            if not data or "data" not in data or not data["data"]:
                logger.warning("No retail sales data available")
                return None
                
            return {
                "name": "RETAIL_SALES",
                "description": "Retail Sales",
                "unit": data.get("unit", ""),
                "data": data.get("data", [])[:12]  # Last 12 months
            }
        except Exception as e:
            logger.error(f"Error fetching retail sales data: {str(e)}")
            return None
    
    async def fetch_economic_news(self):
        """Fetch economic news from Alpha Vantage."""
        logger.info("Fetching economic news")
        
        try:
            params = {
                "topics": "economy,economic,inflation,fed,interest_rates,gdp"
            }
            
            data = await self.alpha_vantage_request("NEWS_SENTIMENT", params)
            
            if not data or "feed" not in data or not data["feed"]:
                logger.warning("No economic news available")
                return None
                
            # Process news and add sentiment analysis
            processed_news = []
            for item in data.get("feed", [])[:20]:  # Process top 20 news items
                try:
                    title = item.get("title", "")
                    
                    # Extract sentiment from Alpha Vantage if available
                    overall_sentiment = item.get("overall_sentiment_score", 0)
                    sentiment_label = item.get("overall_sentiment_label", "neutral")
                    
                    if not overall_sentiment and HAS_GEMINI and GEMINI_API_KEY:
                        # Use Google AI for sentiment if available
                        model = genai.GenerativeModel('gemini-pro')
                        prompt = f"Analyze the sentiment of this news headline and provide a sentiment score between -1 (very negative) and 1 (very positive): \"{title}\". Return just the score."
                        response = model.generate_content(prompt)
                        if response and hasattr(response, 'text'):
                            try:
                                overall_sentiment = float(response.text.strip())
                                sentiment_label = "positive" if overall_sentiment > 0.1 else "negative" if overall_sentiment < -0.1 else "neutral"
                            except ValueError:
                                overall_sentiment = 0
                                sentiment_label = "neutral"
                    
                    processed_news.append({
                        "title": title,
                        "url": item.get("url", ""),
                        "time_published": item.get("time_published", ""),
                        "authors": item.get("authors", []),
                        "summary": item.get("summary", ""),
                        "source": item.get("source", ""),
                        "sentiment_score": overall_sentiment,
                        "sentiment_label": sentiment_label
                    })
                except Exception as e:
                    logger.error(f"Error processing news item: {str(e)}")
                    continue
            
            return processed_news
        except Exception as e:
            logger.error(f"Error fetching economic news: {str(e)}")
            return None
    
    async def insert_indicators(self, indicators):
        """Insert indicators into Supabase table."""
        if not indicators:
            logger.warning("No indicators to insert")
            return
            
        timestamp = datetime.now().isoformat()
        
        try:
            data_to_insert = {
                "indicators": indicators,
                "timestamp": timestamp
            }
            
            # Check if we should update or insert
            result = supabase.table(ECONOMIC_INDICATORS_TABLE).select("id").limit(1).execute()
            
            if result.data:
                # Update the existing record
                record_id = result.data[0]["id"]
                supabase.table(ECONOMIC_INDICATORS_TABLE).update(data_to_insert).eq("id", record_id).execute()
                logger.info(f"Updated economic indicators record (id: {record_id})")
            else:
                # Insert new record
                supabase.table(ECONOMIC_INDICATORS_TABLE).insert(data_to_insert).execute()
                logger.info("Inserted new economic indicators record")
                
            return True
        except Exception as e:
            logger.error(f"Error inserting indicators: {str(e)}")
            return False
    
    async def insert_news(self, news):
        """Insert news into Supabase table."""
        if not news:
            logger.warning("No news to insert")
            return
            
        timestamp = datetime.now().isoformat()
        
        try:
            data_to_insert = {
                "news": news,
                "timestamp": timestamp
            }
            
            # We'll always create a new record for news since it's time-dependent
            supabase.table(ECONOMIC_NEWS_TABLE).insert(data_to_insert).execute()
            logger.info("Inserted new economic news record")
                
            return True
        except Exception as e:
            logger.error(f"Error inserting news: {str(e)}")
            return False


async def main():
    """Main function to run the economic indicator fetcher."""
    # Parse command line args if needed
    # Here we could add argparse support for user_id, etc.
    
    # Create and run the fetcher
    fetcher = EconomicIndicatorFetcher()
    success = await fetcher.run()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())