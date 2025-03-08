# Stock Data Pipeline Implementation

## Current State Assessment

Based on our existing documentation and code review, we currently have:

1. **User Authentication**: Implemented via Clerk
2. **User-specific Watchlists**: Stored in Supabase `watchlists` table
3. **Data Fetchers**: Functional Python scripts for retrieving financial data:
   - Technical indicators fetcher (MACD, RSI)
   - Forex information fetcher (currency exchange rates)
   - Commodity information fetcher (oil, metals, natural gas)
   - Crypto information fetcher
   - Market news fetcher
4. **Database Structure**: Schema defined and tables created
5. **API Keys**: Alpha Vantage, FRED API, and others are configured in .env
6. **Data Storage**: Supabase integration for storing fetched data

## Implementation Plan

We've established a robust data pipeline to handle real market data, focusing on:
1. Data Collection from external APIs
2. Data Storage in Supabase
3. API Endpoints to serve this data
4. Updates to UI components

## Phase 1: Database Setup (Completed)

### 1. Created Tables

We've set up the following key tables in Supabase:

```sql
-- Stock info table 
CREATE TABLE IF NOT EXISTS public.stock_info (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  ticker TEXT UNIQUE NOT NULL,
  company_name TEXT NOT NULL,
  sector TEXT,
  industry TEXT,
  market_cap DECIMAL(18,2),
  price DECIMAL(10,2) NOT NULL,
  price_change_percent DECIMAL(6,2),
  analyst_rating TEXT,
  volume BIGINT,
  last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Technical indicators table
CREATE TABLE IF NOT EXISTS technical_indicators (
  id SERIAL PRIMARY KEY,
  symbol TEXT NOT NULL,
  interval TEXT NOT NULL DEFAULT 'daily',
  date TEXT,
  macd FLOAT,
  macd_signal FLOAT,
  macd_hist FLOAT,
  rsi FLOAT,
  fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(symbol, interval, date)
);

-- Forex information table
CREATE TABLE IF NOT EXISTS forex_info (
  id SERIAL PRIMARY KEY,
  from_currency TEXT NOT NULL,
  to_currency TEXT NOT NULL,
  currency_pair TEXT,
  exchange_rate FLOAT,
  bid_price FLOAT,
  ask_price FLOAT,
  open_price FLOAT,
  daily_high FLOAT,
  daily_low FLOAT,
  daily_close FLOAT,
  weekly_open FLOAT,
  weekly_high FLOAT,
  weekly_low FLOAT,
  weekly_close FLOAT,
  last_refreshed TEXT,
  price_updated_at TEXT,
  fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(from_currency, to_currency)
);

-- Commodity information table
CREATE TABLE IF NOT EXISTS commodity_info (
  id SERIAL PRIMARY KEY,
  function TEXT NOT NULL,
  unit TEXT,
  daily_value FLOAT,
  daily_date TEXT,
  weekly_value FLOAT,
  weekly_date TEXT,
  monthly_value FLOAT,
  monthly_date TEXT,
  fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(function)
);
```

## Phase 2: Data Collection Pipeline (Completed)

### 1. Technical Indicators Fetcher

We've implemented the technical indicators fetcher to retrieve MACD and RSI data from Alpha Vantage:

```python
class TechnicalIndicatorsFetcher:
    def __init__(self):
        # Initialize Supabase client and API variables
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        self.supabase = create_client(supabase_url, supabase_key)
        self.alpha_vantage_key = os.environ.get("API_KEY_ALPHA_VANTAGE")
        
        # Track API calls for rate limiting
        self.last_api_call = datetime.min.replace(tzinfo=timezone.utc)
        self.min_api_interval = 12.0  # seconds
        
    def should_update_indicators(self, symbol: str, interval: str = "daily") -> bool:
        # Check if indicators need to be updated based on recency
        try:
            result = self.supabase.table("technical_indicators").select("fetched_at").eq("symbol", symbol).eq("interval", interval).limit(1).execute()
            
            if result.data and len(result.data) > 0:
                # Convert fetched_at to a timezone-aware datetime
                fetched_date = datetime.fromisoformat(result.data[0]["fetched_at"]).replace(tzinfo=timezone.utc)
                update_threshold = datetime.now(timezone.utc) - timedelta(hours=4)
                
                if fetched_date > update_threshold:
                    logging.info(f"Technical indicators for {symbol} ({interval}) are recent, skipping update")
                    return False
            
            return True
        except Exception as e:
            logging.error(f"Error checking if {symbol} needs update: {str(e)}")
            return True
            
    def process_symbol(self, symbol: str, interval: str = "daily") -> Optional[Dict]:
        # Process a symbol to fetch and store technical indicators
        try:
            # Get technical indicators from Alpha Vantage
            indicators = alpha_vantage_api.get_technical_indicators(symbol, interval)
            
            # Process and store the data
            if indicators and "data" in indicators:
                success_count = 0
                
                for date, values in indicators["data"].items():
                    # Create record for database
                    record = {
                        "symbol": symbol,
                        "interval": interval,
                        "date": date,
                        "macd": values.get("MACD", None),
                        "macd_signal": values.get("MACD_Signal", None),
                        "macd_hist": values.get("MACD_Hist", None),
                        "rsi": values.get("RSI", None),
                        "fetched_at": datetime.now(timezone.utc).isoformat()
                    }
                    
                    # Insert using upsert to handle duplicates
                    result = self.supabase.table("technical_indicators").upsert(
                        record,
                        on_conflict="symbol,interval,date"
                    ).execute()
                    
                    if result.data:
                        success_count += 1
                
                logging.info(f"Successfully stored {success_count} records for {symbol}")
                return indicators
            else:
                logging.warning(f"No valid technical indicators data for {symbol}")
                return None
        except Exception as e:
            logging.error(f"Error processing {symbol}: {str(e)}")
            return None
    
    def run(self, symbols: List[str] = None, interval: str = "daily") -> List[Dict]:
        # Run the technical indicators fetcher for a list of symbols
        results = []
        
        if not symbols:
            # Default to some major stocks if no symbols provided
            symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
        
        for symbol in symbols:
            if self.should_update_indicators(symbol, interval):
                result = self.process_symbol(symbol, interval)
                if result:
                    results.append({"symbol": symbol, "status": "success"})
                else:
                    results.append({"symbol": symbol, "status": "error"})
        
        return results
```

### 2. Forex Information Fetcher

We've implemented the forex information fetcher to retrieve currency exchange rates:

```python
class ForexInfoFetcher:
    def __init__(self):
        # Initialize Supabase client and API variables
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        self.supabase = create_client(supabase_url, supabase_key)
        
        # Set default forex pairs if none provided
        self.DEFAULT_FOREX_PAIRS = [
            ("EUR", "USD"), ("JPY", "USD"), ("GBP", "USD"), 
            ("AUD", "USD"), ("CAD", "USD"), ("CHF", "USD")
        ]
        
        # Track API calls for rate limiting
        self.last_api_call = datetime.min.replace(tzinfo=timezone.utc)
        self.min_api_interval = 12.0  # seconds
        
    def should_update_forex_info(self, from_currency: str, to_currency: str) -> bool:
        # Check if forex info needs to be updated based on recency
        try:
            result = self.supabase.table("forex_info").select("fetched_at").eq("from_currency", from_currency).eq("to_currency", to_currency).execute()
            
            if result.data and len(result.data) > 0:
                # Convert fetched_at to a timezone-aware datetime
                fetched_date = datetime.fromisoformat(result.data[0]["fetched_at"]).replace(tzinfo=timezone.utc)
                update_threshold = datetime.now(timezone.utc) - timedelta(hours=6)
                
                if fetched_date > update_threshold:
                    logging.info(f"Forex info for {from_currency}/{to_currency} is recent, skipping update")
                    return False
            
            return True
        except Exception as e:
            logging.error(f"Error checking if {from_currency}/{to_currency} needs update: {str(e)}")
            return True
    
    def process_forex_pair(self, from_currency: str, to_currency: str) -> bool:
        # Process a forex pair to fetch and store exchange rate info
        try:
            if not self.should_update_forex_info(from_currency, to_currency):
                return True
                
            # Apply rate limiting
            current_time = datetime.now(timezone.utc)
            time_since_last_call = (current_time - self.last_api_call).total_seconds()
            
            if time_since_last_call < self.min_api_interval:
                sleep_time = self.min_api_interval - time_since_last_call
                logging.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
            
            # Get forex data from Alpha Vantage
            logging.info(f"Processing forex pair {from_currency}/{to_currency}")
            forex_info = alpha_vantage_api.get_forex_info(from_currency, to_currency)
            self.last_api_call = datetime.now(timezone.utc)
            
            if not forex_info:
                logging.warning(f"Failed to get forex info for {from_currency}/{to_currency}")
                return False
            
            # Format the data for storage
            formatted_data = alpha_vantage_api.format_forex_info_for_db(forex_info)
            logging.info(f"Formatted data for {from_currency}/{to_currency}: {json.dumps(formatted_data, indent=2)}")
            
            # Store in Supabase using upsert with the correct format
            result = self.supabase.table("forex_info").upsert(
                formatted_data,
                on_conflict="from_currency,to_currency"
            ).execute()
            
            if result.data:
                logging.info(f"Successfully updated forex info for {from_currency}/{to_currency}")
                return True
            else:
                logging.error(f"Failed to update forex info for {from_currency}/{to_currency}")
                return False
        except Exception as e:
            logging.error(f"Error processing {from_currency}/{to_currency}: {str(e)}")
            return False
    
    def run(self, forex_pairs=None):
        # Run the forex info fetcher for a list of currency pairs
        if not forex_pairs:
            forex_pairs = self.DEFAULT_FOREX_PAIRS
        
        success_count = 0
        fail_count = 0
        
        for from_currency, to_currency in forex_pairs:
            if self.process_forex_pair(from_currency, to_currency):
                success_count += 1
            else:
                fail_count += 1
        
        logging.info(f"Forex info fetcher completed - Processed {len(forex_pairs)} forex pairs")
        logging.info(f"Results: {success_count} successful, {fail_count} failed")
        
        return {
            "status": "success" if fail_count == 0 else "partial_success",
            "pairs_processed": len(forex_pairs),
            "successful": success_count,
            "failed": fail_count
        }
```

### 3. Commodity Information Fetcher

We've implemented the commodity information fetcher to retrieve commodity prices:

```python
class CommodityInfoFetcher:
    def __init__(self):
        # Initialize Supabase client and API variables
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        self.supabase = create_client(supabase_url, supabase_key)
        
        # Set default commodities if none provided
        self.DEFAULT_COMMODITIES = ["WTI", "BRENT", "NATURAL_GAS", "COPPER", "ALUMINUM", "WHEAT"]
        
        # Track API calls for rate limiting
        self.last_api_call = datetime.min.replace(tzinfo=timezone.utc)
        self.min_api_interval = 12.0  # seconds
    
    def should_update_commodity_info(self, commodity: str) -> bool:
        # Check if commodity info needs to be updated based on recency
        try:
            result = self.supabase.table("commodity_info").select("fetched_at").eq("function", commodity).execute()
            
            if result.data and len(result.data) > 0:
                # Convert fetched_at to a timezone-aware datetime
                fetched_date = datetime.fromisoformat(result.data[0]["fetched_at"]).replace(tzinfo=timezone.utc)
                update_threshold = datetime.now(timezone.utc) - timedelta(hours=12)
                
                if fetched_date > update_threshold:
                    logging.info(f"Commodity info for {commodity} is recent, skipping update")
                    return False
            
            return True
        except Exception as e:
            logging.error(f"Error checking if {commodity} needs update: {str(e)}")
            return True
    
    def process_commodity(self, commodity: str) -> bool:
        # Process a commodity to fetch and store price info
        try:
            if not self.should_update_commodity_info(commodity):
                return True
                
            # Apply rate limiting
            current_time = datetime.now(timezone.utc)
            time_since_last_call = (current_time - self.last_api_call).total_seconds()
            
            if time_since_last_call < self.min_api_interval:
                sleep_time = self.min_api_interval - time_since_last_call
                logging.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
            
            # Get commodity data from Alpha Vantage
            logging.info(f"Processing commodity {commodity}")
            commodity_info = alpha_vantage_api.get_commodity_info(commodity)
            self.last_api_call = datetime.now(timezone.utc)
            
            if not commodity_info:
                logging.warning(f"Failed to get info for commodity {commodity}")
                return False
            
            # Format the data for storage
            formatted_data = alpha_vantage_api.format_commodity_info_for_db(commodity_info)
            logging.info(f"Formatted data for {commodity}: {json.dumps(formatted_data, indent=2)}")
            
            # Store in Supabase
            result = self.supabase.table("commodity_info").upsert(
                formatted_data,
                on_conflict="function"
            ).execute()
            
            if result.data:
                logging.info(f"Successfully updated commodity info for {commodity}")
                return True
            else:
                logging.error(f"Failed to update commodity info for {commodity}")
                return False
        except Exception as e:
            logging.error(f"Error processing commodity {commodity}: {str(e)}")
            return False
    
    def run(self, commodities=None):
        # Run the commodity info fetcher for a list of commodities
        if not commodities:
            commodities = self.DEFAULT_COMMODITIES
        
        success_count = 0
        fail_count = 0
        
        for commodity in commodities:
            if self.process_commodity(commodity):
                success_count += 1
            else:
                fail_count += 1
        
        logging.info(f"Commodity info fetcher completed - Processed {len(commodities)} commodities")
        logging.info(f"Results: {success_count} successful, {fail_count} failed")
        
        return {
            "status": "success" if fail_count == 0 else "partial_success",
            "commodities_processed": len(commodities),
            "successful": success_count,
            "failed": fail_count
        }
```

### 4. Run All Fetchers Script (To Be Implemented)

We'll implement a runner script to periodically execute all our data fetchers:

```python
#!/usr/bin/env python3
"""
Data Fetchers Runner Script
Runs all data fetchers in sequence to update our financial data
"""

import os
import sys
import asyncio
import logging
import argparse
from datetime import datetime

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our fetchers
from fetch_technical_indicators import TechnicalIndicatorsFetcher
from fetch_forex_info import ForexInfoFetcher
from fetch_commodity_info import CommodityInfoFetcher
from fetch_market_news import MarketNewsFetcher

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/data_fetchers_{datetime.now().strftime('%Y%m%d')}.log")
    ]
)
logger = logging.getLogger("data_fetchers_runner")

async def run_technical_indicators_fetcher():
    """Run the technical indicators fetcher."""
    try:
        logger.info("Starting technical indicators fetcher")
        
        fetcher = TechnicalIndicatorsFetcher()
        
        # Default tickers for technical indicators
        default_tickers = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA", "SPY"]
        
        # Get tickers from environment variable or use defaults
        tickers_env = os.getenv("TRACKED_TICKERS")
        tickers = tickers_env.split(",") if tickers_env else default_tickers
        
        results = fetcher.run(tickers, "daily")
        
        success_count = sum(1 for r in results if r["status"] == "success")
        logger.info(f"Technical indicators fetcher completed: {success_count} of {len(results)} successful")
        
        return success_count == len(results)
    except Exception as e:
        logger.error(f"Error running technical indicators fetcher: {str(e)}")
        return False

async def run_forex_info_fetcher():
    """Run the forex info fetcher."""
    try:
        logger.info("Starting forex info fetcher")
        
        fetcher = ForexInfoFetcher()
        results = fetcher.run()
        
        if results["successful"] == results["pairs_processed"]:
            logger.info("Forex info fetcher completed successfully")
            return True
        else:
            logger.warning(f"Forex info fetcher completed with {results['failed']} failures")
            return results["failed"] == 0
    except Exception as e:
        logger.error(f"Error running forex info fetcher: {str(e)}")
        return False

async def run_commodity_info_fetcher():
    """Run the commodity info fetcher."""
    try:
        logger.info("Starting commodity info fetcher")
        
        fetcher = CommodityInfoFetcher()
        results = fetcher.run()
        
        if results["successful"] == results["commodities_processed"]:
            logger.info("Commodity info fetcher completed successfully")
            return True
        else:
            logger.warning(f"Commodity info fetcher completed with {results['failed']} failures")
            return results["failed"] == 0
    except Exception as e:
        logger.error(f"Error running commodity info fetcher: {str(e)}")
        return False

async def run_market_news_fetcher():
    """Run the market news fetcher."""
    try:
        logger.info("Starting market news fetcher")
        
        fetcher = MarketNewsFetcher()
        
        # Default tickers for news
        default_tickers = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA", "SPY"]
        
        # Get tickers from environment variable or use defaults
        tickers_env = os.getenv("TRACKED_TICKERS")
        tickers = tickers_env.split(",") if tickers_env else default_tickers
        
        results = fetcher.run(tickers)
        
        logger.info(f"Market news fetcher completed with {results['news_count']} articles")
        return True
    except Exception as e:
        logger.error(f"Error running market news fetcher: {str(e)}")
        return False

async def main():
    """Main function to run all data fetchers."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run financial data fetchers")
    parser.add_argument("--only", choices=["technical", "forex", "commodity", "news", "all"],
                      default="all", help="Run only a specific fetcher")
    args = parser.parse_args()
    
    logger.info(f"Starting data fetchers runner with mode: {args.only}")
    
    # Run the selected fetcher(s)
    if args.only == "technical" or args.only == "all":
        await run_technical_indicators_fetcher()
        
    if args.only == "forex" or args.only == "all":
        await run_forex_info_fetcher()
        
    if args.only == "commodity" or args.only == "all":
        await run_commodity_info_fetcher()
        
    if args.only == "news" or args.only == "all":
        await run_market_news_fetcher()
    
    logger.info("Data fetchers runner completed")

if __name__ == "__main__":
    asyncio.run(main())
```

## Phase 3: API Endpoints

To serve the data to our frontend, we'll implement API endpoints:

1. Technical Indicators API
2. Forex Information API
3. Commodity Information API
4. Market News API

## Phase 4: Frontend Integration

We'll create components to display the data:

1. Technical Indicators Chart Component
2. Forex Exchange Rates Component
3. Commodity Prices Component
4. Market News Feed Component

## Implementation Steps (Remaining)

1. **Implement the Run All Fetchers Script**
   - Create a consolidated script to run all fetchers on a schedule
   - Set up proper error handling and logging

2. **Create API Endpoints**
   - Develop RESTful API endpoints to expose the data
   - Implement authentication and rate limiting

3. **Build Frontend Components**
   - Design and implement UI components for each data type
   - Create interactive visualizations for technical indicators

4. **Set Up Scheduled Updates**
   - Configure a CRON job to call our API endpoint
   - Set up monitoring for data collection jobs
   - Implement logging for data collection processes

## Technical Considerations

### API Rate Limits

Alpha Vantage has these rate limits:
- 5 API requests per minute
- 500 requests per day (free tier)

Our implementation handles this by:
- Processing in small batches
- Adding delays between requests
- Focusing on watchlisted stocks first
- Tracking the last API call time and implementing minimum intervals

### Data Freshness

Stock data becomes stale quickly. Our approach:
- Update watchlisted stocks every 15 minutes during market hours
- Update technical indicators every 4 hours
- Update forex data every 6 hours
- Update commodity data every 12 hours
- Include last_updated timestamp in responses
- Display "data age" in the UI

### Timezone Handling

Our implementations properly handle timezones:
- All datetime objects are timezone-aware (using `datetime.now(timezone.utc)`)
- Date strings from APIs are converted to timezone-aware objects
- All comparisons are done with properly timezone-aware objects
- Database timestamps include timezone information

## Monitoring and Maintenance

1. **Data Validation**
   - Implement sanity checks on API responses
   - Log unusual price movements or data anomalies
   - Add alerts for failed data collection jobs

2. **Performance Monitoring**
   - Track API response times
   - Monitor database query performance
   - Watch for bottlenecks in the data pipeline

3. **Regular Maintenance**
   - Clean up stale data periodically
   - Review API usage and adjust collection frequency
   - Update mock data generators as fallbacks

## Conclusion

We've successfully implemented a comprehensive data pipeline for collecting and storing financial data:

1. Technical indicators (MACD, RSI) for market analysis
2. Forex exchange rates for currency tracking
3. Commodity prices for monitoring raw materials
4. Market news for sentiment analysis

These data sources provide a solid foundation for our financial dashboard, offering users diverse insights into market conditions and investment opportunities.

The next steps involve creating API endpoints to expose this data to the frontend and developing UI components to visualize the information in an intuitive and useful way. 