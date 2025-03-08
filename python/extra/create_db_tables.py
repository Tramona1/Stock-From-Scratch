#!/usr/bin/env python3
"""
Create Database Tables
Script to create necessary tables in Supabase for storing stock information and news data
"""

import os
import sys
import logging
from dotenv import load_dotenv
from supabase import create_client, Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("create_db_tables")

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Check if we have the necessary environment variables
if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Missing required environment variables (SUPABASE_URL, SUPABASE_KEY)")
    sys.exit(1)

# Initialize Supabase client
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Successfully connected to Supabase")
except Exception as e:
    logger.error(f"Failed to connect to Supabase: {str(e)}")
    sys.exit(1)

def create_stock_info_table():
    """Create the stock_info table if it doesn't exist"""
    try:
        # SQL to create the stock_info table
        sql = """
        CREATE TABLE IF NOT EXISTS stock_info (
            id SERIAL PRIMARY KEY,
            ticker TEXT NOT NULL UNIQUE,
            company_name TEXT,
            sector TEXT,
            market_cap FLOAT,
            avg_volume FLOAT,
            description TEXT,
            logo_url TEXT,
            current_price FLOAT,
            price_updated_at TIMESTAMP WITH TIME ZONE,
            fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # Execute the SQL
        supabase.table("stock_info").execute(sql, count="exact")
        logger.info("Created stock_info table (if it didn't exist)")
        return True
    except Exception as e:
        logger.error(f"Error creating stock_info table: {str(e)}")
        return False

def create_market_news_table():
    """Create the market_news table if it doesn't exist"""
    try:
        # SQL to create the market_news table
        sql = """
        CREATE TABLE IF NOT EXISTS market_news (
            id SERIAL PRIMARY KEY,
            ticker_query TEXT NOT NULL,
            fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            items_count INTEGER,
            query_metadata JSONB
        );
        
        -- Create index on ticker_query for faster lookups
        CREATE INDEX IF NOT EXISTS market_news_ticker_query_idx ON market_news (ticker_query);
        """
        
        # Execute the SQL
        supabase.table("market_news").execute(sql, count="exact")
        logger.info("Created market_news table (if it didn't exist)")
        return True
    except Exception as e:
        logger.error(f"Error creating market_news table: {str(e)}")
        return False

def create_news_sentiment_table():
    """Create the news_sentiment table if it doesn't exist"""
    try:
        # SQL to create the news_sentiment table
        sql = """
        CREATE TABLE IF NOT EXISTS news_sentiment (
            id SERIAL PRIMARY KEY,
            news_id INTEGER REFERENCES market_news(id) ON DELETE CASCADE,
            title TEXT,
            url TEXT,
            time_published TEXT,
            authors JSONB,
            summary TEXT,
            source TEXT,
            category_within_source TEXT,
            source_domain TEXT,
            overall_sentiment_score FLOAT,
            overall_sentiment_label TEXT,
            ticker_sentiment JSONB
        );
        
        -- Create index on news_id for faster lookups
        CREATE INDEX IF NOT EXISTS news_sentiment_news_id_idx ON news_sentiment (news_id);
        """
        
        # Execute the SQL
        supabase.table("news_sentiment").execute(sql, count="exact")
        logger.info("Created news_sentiment table (if it didn't exist)")
        return True
    except Exception as e:
        logger.error(f"Error creating news_sentiment table: {str(e)}")
        return False

def create_watchlists_table():
    """Create the watchlists table if it doesn't exist"""
    try:
        # SQL to create the watchlists table
        sql = """
        CREATE TABLE IF NOT EXISTS watchlists (
            id SERIAL PRIMARY KEY,
            user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
            ticker TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(user_id, ticker)
        );
        
        -- Create index on user_id and ticker
        CREATE INDEX IF NOT EXISTS watchlists_user_id_idx ON watchlists (user_id);
        CREATE INDEX IF NOT EXISTS watchlists_ticker_idx ON watchlists (ticker);
        """
        
        # Execute the SQL
        supabase.table("watchlists").execute(sql, count="exact")
        logger.info("Created watchlists table (if it didn't exist)")
        return True
    except Exception as e:
        logger.error(f"Error creating watchlists table: {str(e)}")
        return False

def create_portfolios_table():
    """Create the portfolios table if it doesn't exist"""
    try:
        # SQL to create the portfolios table
        sql = """
        CREATE TABLE IF NOT EXISTS portfolios (
            id SERIAL PRIMARY KEY,
            user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
            ticker TEXT NOT NULL,
            shares FLOAT NOT NULL,
            avg_price FLOAT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(user_id, ticker)
        );
        
        -- Create index on user_id and ticker
        CREATE INDEX IF NOT EXISTS portfolios_user_id_idx ON portfolios (user_id);
        CREATE INDEX IF NOT EXISTS portfolios_ticker_idx ON portfolios (ticker);
        """
        
        # Execute the SQL
        supabase.table("portfolios").execute(sql, count="exact")
        logger.info("Created portfolios table (if it didn't exist)")
        return True
    except Exception as e:
        logger.error(f"Error creating portfolios table: {str(e)}")
        return False

def main():
    """Create all the necessary tables"""
    logger.info("Starting table creation process")
    
    # Create tables
    create_stock_info_table()
    create_watchlists_table()
    create_portfolios_table()
    create_market_news_table()
    create_news_sentiment_table()
    
    logger.info("Table creation process completed")

if __name__ == "__main__":
    main() 