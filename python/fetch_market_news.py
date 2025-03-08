#!/usr/bin/env python3
"""
Market News Fetcher
Fetches news and sentiment data for stocks from Alpha Vantage API
"""

import os
import sys
import json
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from supabase import create_client, Client
import requests
import traceback

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/market_news_fetcher.log")
    ]
)
logger = logging.getLogger("market_news_fetcher")

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
MARKET_NEWS_TABLE = "market_news"
NEWS_SENTIMENT_TABLE = "news_sentiment"
MAX_NEWS_PER_REQUEST = 50
MAX_CACHE_AGE_HOURS = 6  # Refresh news every 6 hours
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"


class MarketNewsFetcher:
    def __init__(self):
        """Initialize the market news fetcher."""
        self.last_api_call = 0
        self.min_api_interval = 1.0  # seconds between API calls to avoid rate limits
        
        # Verify Alpha Vantage API key exists
        if not ALPHA_VANTAGE_API_KEY:
            logger.error("ALPHA_VANTAGE_API_KEY environment variable not set")
            raise ValueError("ALPHA_VANTAGE_API_KEY must be set in environment")
    
    def fetch_user_tickers(self) -> List[str]:
        """
        Fetch tickers from user watchlists.
        
        Returns:
            List of unique ticker symbols
        """
        try:
            logger.info("Fetching user watchlist tickers")
            
            # Get tickers from watchlists table
            response = supabase.table("watchlists").select("ticker").execute()
            
            all_tickers = set()
            for watchlist in response.data:
                ticker = watchlist.get("ticker")
                if ticker:
                    all_tickers.add(ticker)
            
            # Get any additional tickers from portfolios table if it exists
            try:
                response = supabase.table("portfolios").select("ticker").execute()
                for portfolio in response.data:
                    ticker = portfolio.get("ticker")
                    if ticker:
                        all_tickers.add(ticker)
            except Exception as e:
                logger.warning(f"Error fetching portfolio tickers: {str(e)}")
            
            # If no tickers found, use some default popular tickers
            if not all_tickers:
                logger.warning("No tickers found in database, using default tickers")
                default_tickers = ["AAPL", "MSFT", "GOOG", "AMZN", "META", "TSLA", "NVDA", "AMD", "SPY", "QQQ"]
                all_tickers.update(default_tickers)
            
            logger.info(f"Found {len(all_tickers)} unique tickers to process")
            return list(all_tickers)
        except Exception as e:
            logger.error(f"Error fetching user tickers: {str(e)}")
            # Return default tickers in case of error
            return ["AAPL", "MSFT", "GOOG", "AMZN", "META"]
    
    def should_update_news(self, tickers: List[str]) -> bool:
        """
        Check if news for the given tickers should be updated.
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            True if news should be updated, False otherwise
        """
        try:
            # Join tickers into a comma-separated string for the query
            ticker_str = ','.join(tickers)
            
            # Check if we have recent news data for these tickers
            response = supabase.table(MARKET_NEWS_TABLE) \
                .select("fetched_at") \
                .eq("ticker_query", ticker_str) \
                .order("fetched_at", desc=True) \
                .limit(1) \
                .execute()
                
            # If no data exists, we should definitely update
            if not response.data or len(response.data) == 0:
                return True
            
            # Check if data is older than our cache age
            fetched_at = response.data[0].get("fetched_at")
            if fetched_at:
                fetched_date = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
                update_threshold = datetime.now() - timedelta(hours=MAX_CACHE_AGE_HOURS)
                
                # If data is older than the threshold, update it
                if fetched_date < update_threshold:
                    logger.info(f"News for {ticker_str} is outdated, last update: {fetched_date}")
                    return True
                else:
                    logger.info(f"News for {ticker_str} is recent, skipping update")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error checking update status for news: {str(e)}")
            return True  # Default to updating if we hit an error
    
    def fetch_news_sentiment(self, tickers: List[str], topics: Optional[List[str]] = None, 
                            time_from: Optional[str] = None, limit: int = MAX_NEWS_PER_REQUEST) -> Dict:
        """
        Fetch news and sentiment data from Alpha Vantage API.
        
        Args:
            tickers: List of ticker symbols
            topics: Optional list of news topics to filter by
            time_from: Optional start time in YYYYMMDDTHHMM format
            limit: Maximum number of news articles to fetch
            
        Returns:
            Dictionary containing news and sentiment data
        """
        # Apply rate limiting
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call
        if time_since_last_call < self.min_api_interval:
            time.sleep(self.min_api_interval - time_since_last_call)
        
        # Prepare API parameters
        params = {
            "function": "NEWS_SENTIMENT",
            "apikey": ALPHA_VANTAGE_API_KEY,
            "limit": limit
        }
        
        # Add optional parameters if provided
        if tickers:
            params["tickers"] = ','.join(tickers)
        
        if topics:
            params["topics"] = ','.join(topics)
            
        if time_from:
            params["time_from"] = time_from
        
        # Make API request
        try:
            logger.info(f"Fetching news sentiment for tickers: {tickers}")
            url = f"{ALPHA_VANTAGE_BASE_URL}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
            logger.info(f"API URL: {url}")
            
            response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params)
            response.raise_for_status()
            self.last_api_call = time.time()
            
            data = response.json()
            
            # Debug output
            logger.info(f"API Response Status: {response.status_code}")
            logger.info(f"API Response Headers: {response.headers}")
            logger.info(f"API Response Keys: {data.keys() if isinstance(data, dict) else 'Not a dictionary'}")
            logger.info(f"API Response Content: {json.dumps(data, indent=2)}")
            
            if "Information" in data:
                logger.error(f"Alpha Vantage API information message: {data['Information']}")
                return {}
            
            if "Error Message" in data:
                logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                return {}
                
            return data
        except Exception as e:
            logger.error(f"Error fetching news sentiment: {str(e)}")
            logger.error(traceback.format_exc())
            return {}
    
    def process_news_data(self, news_data: Dict, ticker_query: str) -> bool:
        """
        Process and store news sentiment data in the database.
        
        Args:
            news_data: News data from Alpha Vantage API
            ticker_query: The original ticker query string
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not news_data or "feed" not in news_data:
                logger.warning("No news data to process")
                return False
                
            # Extract feed items and metadata
            feed_items = news_data.get("feed", [])
            if not feed_items:
                logger.warning("No news feed items found")
                return False
                
            # Store overall query info in market_news table
            news_meta = {
                "ticker_query": ticker_query,
                "fetched_at": datetime.now().isoformat(),
                "items_count": len(feed_items),
                "query_metadata": json.dumps({
                    "items_count": len(feed_items),
                    "sentiment_score_definition": news_data.get("sentiment_score_definition", ""),
                    "relevance_score_definition": news_data.get("relevance_score_definition", "")
                })
            }
            
            # Insert into market_news table
            news_meta_result = supabase.table(MARKET_NEWS_TABLE) \
                .insert(news_meta) \
                .execute()
                
            if not news_meta_result.data:
                logger.error("Failed to insert news metadata")
                return False
                
            news_id = news_meta_result.data[0].get("id")
            
            # Process individual news items
            for item in feed_items:
                # Format sentiment data
                ticker_sentiment = []
                if "ticker_sentiment" in item:
                    ticker_sentiment = item.get("ticker_sentiment", [])
                
                # Create entry for news_sentiment table
                news_item = {
                    "news_id": news_id,
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "time_published": item.get("time_published", ""),
                    "authors": json.dumps(item.get("authors", [])),
                    "summary": item.get("summary", ""),
                    "source": item.get("source", ""),
                    "category_within_source": item.get("category_within_source", ""),
                    "source_domain": item.get("source_domain", ""),
                    "overall_sentiment_score": item.get("overall_sentiment_score", 0),
                    "overall_sentiment_label": item.get("overall_sentiment_label", ""),
                    "ticker_sentiment": json.dumps(ticker_sentiment)
                }
                
                # Insert into news_sentiment table
                sentiment_result = supabase.table(NEWS_SENTIMENT_TABLE) \
                    .insert(news_item) \
                    .execute()
                    
                if not sentiment_result.data:
                    logger.warning(f"Failed to insert news item: {item.get('title')}")
            
            logger.info(f"Successfully processed {len(feed_items)} news items for {ticker_query}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing news data: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def run(self, tickers: Optional[List[str]] = None, topics: Optional[List[str]] = None, 
            time_from: Optional[str] = None, limit: int = MAX_NEWS_PER_REQUEST) -> Dict:
        """
        Run the market news fetcher.
        
        Args:
            tickers: Optional list of tickers. If None, fetch from user watchlists.
            topics: Optional list of topics to filter by
            time_from: Optional start time in YYYYMMDDTHHMM format
            limit: Maximum number of news articles to fetch
            
        Returns:
            Dictionary with results summary
        """
        logger.info("Starting market news fetcher")
        
        try:
            # Get tickers to process if not provided
            if tickers is None:
                tickers = self.fetch_user_tickers()
                
            if not tickers:
                logger.warning("No tickers found to process")
                return {"status": "success", "message": "No tickers found"}
            
            # Join tickers for query string
            ticker_query = ','.join(tickers)
            
            # Check if we should update the news data
            if not self.should_update_news(tickers):
                return {
                    "status": "success", 
                    "message": "Recent news data exists, skipping update"
                }
            
            # Fetch news and sentiment data
            news_data = self.fetch_news_sentiment(tickers, topics, time_from, limit)
            
            if not news_data:
                return {
                    "status": "error",
                    "message": "Failed to fetch news data"
                }
            
            # Process and store news data
            success = self.process_news_data(news_data, ticker_query)
            
            if success:
                return {
                    "status": "success",
                    "tickers": tickers,
                    "articles_processed": len(news_data.get("feed", [])),
                    "message": "Successfully fetched and stored news data"
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to process news data"
                }
            
        except Exception as e:
            logger.error(f"Error running market news fetcher: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "error": str(e)
            }


def main():
    """Run the market news fetcher as a standalone script."""
    try:
        fetcher = MarketNewsFetcher()
        
        # Parse command line arguments for optional parameters
        import argparse
        parser = argparse.ArgumentParser(description='Fetch market news and sentiment data')
        parser.add_argument('--tickers', help='Comma-separated list of tickers')
        parser.add_argument('--topics', help='Comma-separated list of topics')
        parser.add_argument('--time_from', help='Start time in YYYYMMDDTHHMM format')
        parser.add_argument('--limit', type=int, default=MAX_NEWS_PER_REQUEST, 
                            help=f'Maximum number of articles (default: {MAX_NEWS_PER_REQUEST})')
        args = parser.parse_args()
        
        # Process arguments
        tickers = args.tickers.split(',') if args.tickers else None
        topics = args.topics.split(',') if args.topics else None
        
        # Run the fetcher
        result = fetcher.run(tickers, topics, args.time_from, args.limit)
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 