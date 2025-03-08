#!/usr/bin/env python3
"""
Options Flow Schema Checker

This script checks the schema of the options_flow table in the database
to determine what columns are available.
"""

import os
import sys
import json
import logging
from dotenv import load_dotenv
import requests
from typing import Dict, List, Any, Optional
from supabase import create_client, Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("options_flow_schema")

# Load environment variables
load_dotenv()

def get_supabase_credentials():
    """Get Supabase credentials from environment variables."""
    supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("Supabase URL or key not found in environment variables")
        sys.exit(1)
    
    return supabase_url, supabase_key

def check_table_schema(supabase: Client, table_name: str):
    """
    Check the schema of a table by getting sample data and inferring columns.
    
    Args:
        supabase: Supabase client
        table_name: Name of the table to check
    """
    logger.info(f"Checking schema for table: {table_name}")
    
    try:
        # Get sample data from the table
        response = supabase.table(table_name).select("*").limit(10).execute()
        
        if not response.data:
            logger.warning(f"No data found in {table_name}")
            return
            
        # Log the columns found in the first record
        first_record = response.data[0]
        logger.info(f"Found {len(response.data)} records in {table_name}")
        logger.info(f"Schema for {table_name}:")
        
        for column_name in first_record.keys():
            logger.info(f"  - {column_name}")
            
        # Also print raw first record to see the data
        logger.info(f"Sample record from {table_name}:")
        logger.info(json.dumps(first_record, indent=2))
    
    except Exception as e:
        logger.error(f"Error checking schema for {table_name}: {str(e)}")

def create_test_record(supabase: Client, table_name: str):
    """
    Create a test record in the table with minimal fields.
    
    Args:
        supabase: Supabase client
        table_name: Name of the table to insert into
    """
    logger.info(f"Creating test record in {table_name}")
    
    try:
        # Create a minimal record
        test_record = {
            "id": "test-record-" + os.urandom(4).hex(),
            "ticker": "AAPL",
            "created_at": "2025-03-08T01:00:00Z",
            "updated_at": "2025-03-08T01:00:00Z"
        }
        
        # Try to insert the record
        result = supabase.table(table_name).insert(test_record).execute()
        
        if result.data:
            logger.info(f"Successfully created test record in {table_name}")
            logger.info(f"Test record ID: {test_record['id']}")
        else:
            logger.error(f"Failed to create test record: {result.error}")
    
    except Exception as e:
        logger.error(f"Error creating test record: {str(e)}")

def main():
    """Main function to check the options_flow table schema."""
    logger.info("Starting options flow schema check")
    
    # Get Supabase credentials
    supabase_url, supabase_key = get_supabase_credentials()
    
    # Create Supabase client
    try:
        supabase = create_client(supabase_url, supabase_key)
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {str(e)}")
        sys.exit(1)
    
    # Check the options_flow table schema
    check_table_schema(supabase, "options_flow")
    
    # Also check option_flow_data (without the s) in case it's a different table
    check_table_schema(supabase, "option_flow_data")
    
    logger.info("Schema check complete")

if __name__ == "__main__":
    main() 