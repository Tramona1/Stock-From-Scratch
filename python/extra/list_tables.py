#!/usr/bin/env python3
"""
List all tables in the Supabase database.
"""

import os
import json
import logging
from dotenv import load_dotenv
from supabase import create_client, Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("list_tables")

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def list_tables():
    """List all tables in the Supabase database."""
    try:
        # Connect to Supabase
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")
        
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Listing tables in the database")
        
        # Query pg_catalog.pg_tables to get table information
        query = """
        SELECT tablename
        FROM pg_catalog.pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename;
        """
        
        response = supabase.rpc("exec_sql", {"query": query}).execute()
        
        if not hasattr(response, 'data') or not response.data:
            logger.warning("No tables found or no access to pg_catalog")
            
            # Fallback: Try to directly query some known tables to see what exists
            known_tables = [
                "options_flow", "option_flow_data", "alerts", "watchlists",
                "institutions", "institution_holdings", "institution_activity", "hedge_fund_trades",
                "users", "profiles", "historical_data", "stock_info"
            ]
            
            tables_found = []
            for table in known_tables:
                try:
                    # Try to query the table (just check if it exists)
                    test_response = supabase.table(table).select("*").limit(1).execute()
                    tables_found.append(table)
                    logger.info(f"Table exists: {table}")
                except Exception as e:
                    if "relation" in str(e) and "does not exist" in str(e):
                        logger.info(f"Table does not exist: {table}")
                    else:
                        logger.warning(f"Error checking table {table}: {str(e)}")
            
            return tables_found
        
        # Process results
        tables = [item['tablename'] for item in response.data]
        return tables
            
    except Exception as e:
        logger.error(f"Error listing tables: {str(e)}")
        return []

def main():
    """List all tables in the database."""
    tables = list_tables()
    
    if tables:
        logger.info(f"Found {len(tables)} tables in the database")
        for table in tables:
            logger.info(f"- {table}")
    else:
        logger.warning("No tables found")

if __name__ == "__main__":
    main() 