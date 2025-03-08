#!/usr/bin/env python3
"""
Hedge Fund Trades Fetcher
Fetches hedge fund trades from Unusual Whales API
"""

import os
import sys
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from supabase import create_client, Client

# Add the parent directory to the path so we can import unusual_whales_api
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import fixed functions, fallback to original ones if not available
try:
    from fix_institution_tables_minimal import (
        fixed_format_institution_for_db,
        fixed_format_institution_holding_for_db,
        fixed_format_institution_activity_for_db,
        fixed_generate_trades_from_activity
    )
    logging.info("Successfully imported fixed formatter functions (minimal version)")
except ImportError:
    logging.warning("Could not import fixed formatter functions, falling back to local implementations")
    # Define the fixed formatter functions locally
    def fixed_format_institution_for_db(institution):
        """Format institution data for database storage with minimal fields."""
        now = datetime.utcnow().isoformat()
        
        # Generate a UUID for the institution
        institution_id = str(uuid.uuid4())
        
        # Create a minimally formatted institution record with only essential fields
        formatted_institution = {
            "id": institution_id,
            "name": institution.get("name", "Unknown Institution"),
            "created_at": now,
            "updated_at": now
        }
        
        # Add optional fields if they exist
        if "short_name" in institution:
            formatted_institution["short_name"] = institution["short_name"]
        
        if "description" in institution:
            formatted_institution["description"] = institution["description"]
            
        return formatted_institution
    
    def fixed_format_institution_holding_for_db(holding):
        """Format institution holding data for database storage with minimal fields."""
        now = datetime.utcnow().isoformat()
        
        # Generate a UUID for the holding
        holding_id = str(uuid.uuid4())
        
        # Create a minimally formatted holding record with only essential fields
        formatted_holding = {
            "id": holding_id,
            "institution_name": holding.get("institution_name", "Unknown Institution"),
            "ticker": holding.get("ticker", ""),
            "units": holding.get("units", 0),
            "created_at": now,
            "updated_at": now
        }
        
        # Add date only if it's actually a date string
        date_str = holding.get("date")
        if date_str and isinstance(date_str, str):
            formatted_holding["date"] = date_str
            
        return formatted_holding
    
    def fixed_format_institution_activity_for_db(activity):
        """Format institution activity data for database storage with minimal fields."""
        now = datetime.utcnow().isoformat()
        
        # Generate a UUID for the activity
        activity_id = str(uuid.uuid4())
        
        # Create a minimally formatted activity record with only essential fields
        formatted_activity = {
            "id": activity_id,
            "institution_name": activity.get("institution_name", "Unknown Institution"),
            "ticker": activity.get("ticker", ""),
            "units": activity.get("units", 0),
            "units_change": activity.get("units_change", 0),
            "created_at": now,
            "updated_at": now
        }
        
        # Add report_date only if it's actually a date string
        report_date = activity.get("report_date")
        if report_date and isinstance(report_date, str):
            formatted_activity["report_date"] = report_date
            
        return formatted_activity

    def fixed_generate_trades_from_activity(activities, fund_name):
        """
        Generate trades from activity data.
        
        Args:
            activities: List of activity records
            fund_name: Name of the institution/fund
            
        Returns:
            List of trade records
        """
        trades = []
        now = datetime.utcnow().isoformat()
        
        for activity in activities:
            units_change = activity.get("units_change", 0)
            
            # Skip if no change in units
            if units_change == 0:
                continue
                
            # Determine if it's a buy or sell based on units_change
            action = "BUY" if units_change > 0 else "SELL"
            
            # Make units_change positive for SELL actions
            units = abs(units_change)
            
            # Generate trade record with minimal required fields
            trade = {
                "id": str(uuid.uuid4()),
                "institution_name": fund_name,
                "ticker": activity.get("ticker", ""),
                "action": action,
                "units": units,
                "created_at": now,
                "updated_at": now
            }
            
            # Add report_date if available
            report_date = activity.get("report_date")
            if report_date and isinstance(report_date, str):
                trade["report_date"] = report_date
                
            trades.append(trade)
            
        return trades

from unusual_whales_api import (
    get_institutions, 
    get_institution_holdings, 
    get_institution_activity,
    get_latest_filings
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("hedge_fund_fetcher.log")
    ]
)
logger = logging.getLogger("hedge_fund_fetcher")

# Load environment variables
load_dotenv()

class HedgeFundTradesFetcher:
    def __init__(self, funds_limit: int = 50):
        self.funds_limit = funds_limit
        self.supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase credentials")
            
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        
    async def run(self):
        """Run the hedge fund trades fetcher"""
        logger.info("Starting hedge fund trades fetcher")
        
        try:
            await self.fetch_from_unusual_whales()
            logger.info("Successfully fetched hedge fund trades")
            return True
        except Exception as e:
            logger.error(f"Error fetching hedge fund trades: {str(e)}")
            return False
    
    async def fetch_from_unusual_whales(self):
        """Fetch hedge fund data from Unusual Whales API"""
        logger.info(f"Fetching up to {self.funds_limit} hedge funds from Unusual Whales API")
        
        try:
            # Get the list of institutions
            institutions = get_institutions(limit=self.funds_limit)
            logger.info(f"Fetched {len(institutions)} institutions")
            
            # Save institutions to database
            await self._save_institutions_to_database(institutions)
            
            # Process each fund
            for institution in institutions:
                fund_name = institution["name"]
                await self._process_fund_data(fund_name)
                
            return True
        except Exception as e:
            logger.error(f"Error fetching from Unusual Whales API: {str(e)}")
            return False
    
    async def _process_fund_data(self, fund_name):
        """Process data for a single fund"""
        logger.info(f"Processing data for fund: {fund_name}")
        
        try:
            # Get holdings for the fund
            holdings = get_institution_holdings(fund_name, limit=500)
            logger.info(f"Fetched {len(holdings)} holdings for {fund_name}")
            
            # Save holdings to database
            await self._save_holdings_to_database(holdings, fund_name)
            
            # Get activity for the fund
            activities = get_institution_activity(fund_name, limit=500)
            logger.info(f"Fetched {len(activities)} activity records for {fund_name}")
            
            # Save activity to database
            await self._save_activity_to_database(activities, fund_name)
            
            # Generate trades from activity
            trades = fixed_generate_trades_from_activity(activities, fund_name)
            logger.info(f"Generated {len(trades)} trades from activity for {fund_name}")
            
            # Save trades to database
            await self._save_trades_to_database(trades)
            
            return True
        except Exception as e:
            logger.error(f"Error processing fund {fund_name}: {str(e)}")
            return False
    
    async def _save_institutions_to_database(self, institutions):
        """Save institutions to database"""
        try:
            # Format institutions for database
            formatted_institutions = []
            for institution in institutions:
                formatted_institution = fixed_format_institution_for_db(institution)
                formatted_institutions.append(formatted_institution)
            
            if not formatted_institutions:
                logger.warning("No institutions to save")
                return False
                
            # Insert institutions into database - simple insert, no on_conflict
            logger.info(f"Saving {len(formatted_institutions)} institutions to database")
            result = self.supabase.table("institutions").insert(
                formatted_institutions
            ).execute()
            
            logger.info(f"Saved {len(formatted_institutions)} institutions to database")
            return True
        except Exception as e:
            logger.error(f"Error saving institutions to database: {str(e)}")
            return False
    
    async def _save_holdings_to_database(self, holdings, fund_name):
        """Save holdings to database"""
        try:
            # Format holdings for database
            formatted_holdings = []
            for holding in holdings:
                # Add fund name to holding
                holding["institution_name"] = fund_name
                formatted_holding = fixed_format_institution_holding_for_db(holding)
                formatted_holdings.append(formatted_holding)
            
            if not formatted_holdings:
                logger.warning(f"No holdings to save for {fund_name}")
                return False
                
            # Insert holdings into database - simple insert, no on_conflict
            logger.info(f"Saving {len(formatted_holdings)} holdings to database for {fund_name}")
            result = self.supabase.table("institution_holdings").insert(
                formatted_holdings
            ).execute()
            
            logger.info(f"Saved {len(formatted_holdings)} holdings to database for {fund_name}")
            return True
        except Exception as e:
            logger.error(f"Error saving holdings to database for {fund_name}: {str(e)}")
            return False
    
    async def _save_activity_to_database(self, activities, fund_name):
        """Save activity to database"""
        try:
            # Format activity for database
            formatted_activities = []
            for activity in activities:
                # Add fund name to activity
                activity["institution_name"] = fund_name
                formatted_activity = fixed_format_institution_activity_for_db(activity)
                formatted_activities.append(formatted_activity)
            
            if not formatted_activities:
                logger.warning(f"No activity to save for {fund_name}")
                return False
                
            # Insert activity into database - simple insert, no on_conflict
            logger.info(f"Saving {len(formatted_activities)} activity records to database for {fund_name}")
            result = self.supabase.table("institution_activity").insert(
                formatted_activities
            ).execute()
            
            logger.info(f"Saved {len(formatted_activities)} activity records to database for {fund_name}")
            return True
        except Exception as e:
            logger.error(f"Error saving activity to database for {fund_name}: {str(e)}")
            return False
    
    async def _save_trades_to_database(self, trades):
        """Save trades to database"""
        try:
            if not trades:
                logger.warning("No trades to save")
                return False
                
            # Insert trades into database - simple insert, no on_conflict
            logger.info(f"Saving {len(trades)} trades to database")
            result = self.supabase.table("hedge_fund_trades").insert(
                trades
            ).execute()
            
            logger.info(f"Saved {len(trades)} trades to database")
            return True
        except Exception as e:
            logger.error(f"Error saving trades to database: {str(e)}")
            return False
    
    async def fetch_for_watchlist(self, watchlist_symbols, limit=200):
        """Fetch hedge fund data for watchlist symbols"""
        logger.info(f"Fetching hedge fund data for {len(watchlist_symbols)} watchlist symbols")
        
        all_trades = []
        institutions_seen = set()
        
        try:
            for ticker in watchlist_symbols:
                logger.info(f"Processing watchlist ticker: {ticker}")
                
                # Get ownership data for the ticker
                try:
                    # This endpoint supports ownership data for a ticker
                    from unusual_whales_api import get_ticker_ownership
                    ownership_data = get_ticker_ownership(ticker, limit=limit)
                    logger.info(f"Fetched {len(ownership_data)} ownership records for {ticker}")
                    
                    # Process each institution that owns this ticker
                    for ownership in ownership_data:
                        institution_name = ownership.get("name")
                        if not institution_name:
                            continue
                            
                        # Skip if we've already seen this institution
                        if institution_name in institutions_seen:
                            continue
                            
                        institutions_seen.add(institution_name)
                        
                        # Process this institution
                        await self._process_fund_data(institution_name)
                except Exception as e:
                    logger.error(f"Error fetching ownership data for {ticker}: {str(e)}")
                
                # Sleep to avoid rate limiting
                time.sleep(1)
                
            logger.info(f"Processed {len(institutions_seen)} unique institutions for watchlist")
            return True
        except Exception as e:
            logger.error(f"Error fetching hedge fund data for watchlist: {str(e)}")
            return False

async def main():
    """Main function"""
    logger.info("Starting hedge fund trades fetcher")
    
    try:
        fetcher = HedgeFundTradesFetcher()
        await fetcher.run()
        logger.info("Hedge fund trades fetcher completed successfully")
    except Exception as e:
        logger.error(f"Error running hedge fund trades fetcher: {str(e)}")
    
if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 