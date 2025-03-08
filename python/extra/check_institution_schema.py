#!/usr/bin/env python3
"""
Institution Tables Schema Checker

This script checks the actual schema of institution tables in the Supabase database
to determine which columns actually exist.
"""

import os
import sys
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
logger = logging.getLogger("schema_checker")

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

def check_table_schema(table_name):
    """
    Check the schema of a specific table by trying to insert a minimal record.
    
    Args:
        table_name: Name of the table to check
    """
    logger.info(f"Checking schema for table: {table_name}")
    
    # Minimal record with just an ID
    minimal_record = {"id": "00000000-0000-0000-0000-000000000000"}
    
    try:
        # Attempt to insert (this will fail but show the expected columns)
        result = supabase.table(table_name).insert(minimal_record).execute()
        logger.info("Insertion succeeded (unexpected!)")
    except Exception as e:
        error_msg = str(e)
        if "Could not find" in error_msg and "column" in error_msg:
            # This is what we're looking for - schema errors
            logger.info(f"Schema error for {table_name}: {error_msg}")
        else:
            # Some other error
            logger.error(f"Error checking schema for {table_name}: {error_msg}")
    
    # Try to get the existing data to infer schema
    try:
        result = supabase.table(table_name).select("*").limit(1).execute()
        if result.data:
            columns = list(result.data[0].keys())
            logger.info(f"Columns in {table_name} based on data: {columns}")
        else:
            logger.info(f"No data found in {table_name}")
    except Exception as e:
        logger.error(f"Error retrieving data from {table_name}: {str(e)}")

def check_institution_tables():
    """Check schemas for all institution-related tables."""
    tables = [
        "institutions",
        "institution_holdings",
        "institution_activity",
        "hedge_fund_trades"
    ]
    
    for table in tables:
        check_table_schema(table)
        print()  # Blank line for readability

def main():
    """Main function to run the schema checker."""
    logger.info("Starting institution tables schema checker...")
    check_institution_tables()
    logger.info("Schema check complete.")

if __name__ == "__main__":
    main() 