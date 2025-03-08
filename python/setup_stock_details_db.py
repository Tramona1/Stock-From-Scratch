#!/usr/bin/env python3
"""
Script to initialize the stock_details table in Supabase.
This script reads the SQL schema from stock_details_schema.sql and executes it.
"""

import os
import sys
import logging
import httpx
from dotenv import load_dotenv

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/setup_stock_details_db.log")
    ]
)
logger = logging.getLogger("setup_stock_details_db")

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def read_sql_file(filepath):
    """Read SQL schema from a file."""
    try:
        with open(filepath, "r") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading SQL file {filepath}: {str(e)}")
        return None

def execute_sql(sql):
    """Execute SQL against Supabase using the REST API."""
    if not sql:
        logger.error("No SQL to execute")
        return False
    
    try:
        # Configure Supabase REST client
        url = f"{SUPABASE_URL}/rest/v1/rpc/execute_sql"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        
        # Execute SQL via RPC call
        payload = {"sql": sql}
        logger.info("Executing SQL statement...")
        
        response = httpx.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        logger.info("SQL executed successfully")
        return True
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"Error executing SQL: {str(e)}")
        return False

def main():
    """Main function to initialize the database."""
    logger.info("Starting database initialization")
    
    # Ensure we have required environment variables
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Missing required environment variables: NEXT_PUBLIC_SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)
    
    # Read SQL schema
    sql_path = os.path.join(os.path.dirname(__file__), "extra", "stock_details_schema.sql")
    sql = read_sql_file(sql_path)
    if not sql:
        logger.error(f"Failed to read SQL schema from {sql_path}")
        sys.exit(1)
    
    # Execute SQL
    success = execute_sql(sql)
    
    if success:
        logger.info("Database initialization completed successfully")
        return 0
    else:
        logger.error("Database initialization failed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 