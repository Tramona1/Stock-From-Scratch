#!/usr/bin/env python3
"""
Schema Checker

This script directly queries Supabase to get the actual column names
for each table, bypassing the schema cache that seems to be causing issues.
"""

import os
import sys
import json
import logging
from dotenv import load_dotenv
import requests
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("schema_checker")

# Load environment variables
load_dotenv()

def get_supabase_credentials():
    """Get Supabase credentials from environment variables."""
    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        logger.error("Missing Supabase credentials in environment variables")
        sys.exit(1)
    
    return url, key

def get_table_schema(url: str, key: str, table_name: str) -> List[str]:
    """
    Get the actual schema for a table directly from PostgreSQL information_schema.
    
    Args:
        url: Supabase URL
        key: Supabase service role key
        table_name: Name of the table to check
        
    Returns:
        List of column names in the table
    """
    # Construct REST API URL for RPC call
    api_url = f"{url}/rest/v1/rpc/get_table_definition"
    
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    
    # Use custom PostgreSQL function (we'll add this if it doesn't exist)
    # Fallback to a direct query to information_schema
    
    try:
        # First try with direct query to information_schema
        sql_api_url = f"{url}/rest/v1"
        
        direct_headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        # Using a query parameter to safely include the table_name 
        query = f"?select=column_name&table_name=eq.{table_name}"
        information_schema_url = f"{sql_api_url}/information_schema/columns{query}"
        
        logger.info(f"Querying information_schema for table {table_name}")
        response = requests.get(information_schema_url, headers=direct_headers)
        
        if response.status_code == 200:
            columns = [col["column_name"] for col in response.json()]
            return columns
        else:
            logger.warning(f"Failed to query information_schema: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Error querying information_schema: {str(e)}")
    
    # If direct approach failed, try using a SQL query via RPC
    try:
        # Create a function to get column names if it doesn't exist
        create_function_body = {
            "name": "get_table_columns",
            "sql": """
            CREATE OR REPLACE FUNCTION get_table_columns(table_name text)
            RETURNS TABLE(column_name text) 
            LANGUAGE SQL
            AS $$
              SELECT column_name::text
              FROM information_schema.columns
              WHERE table_name = table_name;
            $$;
            """
        }
        
        # Try to create the function
        function_url = f"{url}/rest/v1/rpc/get_table_columns"
        function_response = requests.post(
            f"{url}/rest/v1/rpc/create_function", 
            headers=headers,
            json=create_function_body
        )
        
        # Now call the function
        response = requests.post(
            function_url,
            headers=headers,
            json={"table_name": table_name}
        )
        
        if response.status_code == 200:
            return [col["column_name"] for col in response.json()]
        else:
            logger.error(f"Error getting schema for {table_name}: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error creating/calling function: {str(e)}")
        return []

def get_sample_data(url: str, key: str, table_name: str, limit: int = 1) -> List[Dict]:
    """
    Get sample data from a table to infer schema.
    
    Args:
        url: Supabase URL
        key: Supabase service role key
        table_name: Name of the table
        limit: Maximum number of rows to return
        
    Returns:
        List of dictionaries representing rows from the table
    """
    api_url = f"{url}/rest/v1/{table_name}"
    
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}"
    }
    
    params = {
        "limit": limit
    }
    
    try:
        logger.info(f"Getting sample data from {table_name}")
        response = requests.get(api_url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                logger.info(f"Found {len(data)} sample records in {table_name}")
                return data
            else:
                logger.info(f"No data found in {table_name}")
                return []
        else:
            logger.error(f"Error getting sample data for {table_name}: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logger.error(f"Exception getting sample data: {str(e)}")
        return []

def check_table_schema(url: str, key: str, table_name: str):
    """
    Check the schema for a table and print column names.
    
    Args:
        url: Supabase URL
        key: Supabase service role key
        table_name: Name of the table to check
    """
    logger.info(f"Checking schema for table: {table_name}")
    
    # Try to get schema through information_schema
    columns = get_table_schema(url, key, table_name)
    
    if columns:
        logger.info(f"Table {table_name} has the following columns:")
        for col in columns:
            logger.info(f"  - {col}")
    else:
        # If schema query failed, try to infer from sample data
        sample_data = get_sample_data(url, key, table_name)
        
        if sample_data:
            inferred_columns = list(sample_data[0].keys())
            logger.info(f"Inferred schema for {table_name} from sample data:")
            for col in inferred_columns:
                logger.info(f"  - {col}")
        else:
            # Try to insert a minimal record to see error message
            logger.info(f"Attempting to insert minimal record into {table_name} to observe error")
            minimal_record = {
                "id": "00000000-0000-0000-0000-000000000000"
            }
            
            headers = {
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            
            try:
                response = requests.post(
                    f"{url}/rest/v1/{table_name}",
                    headers=headers,
                    json=minimal_record
                )
                
                if response.status_code == 400:
                    # Extract error message which often contains schema information
                    error = response.json()
                    logger.error(f"Error inserting minimal record: {json.dumps(error, indent=2)}")
                    
                    # Look for column name in error message
                    if "message" in error and "column" in error["message"]:
                        logger.info("Error message contains schema information")
            except Exception as e:
                logger.error(f"Error inserting minimal record: {str(e)}")

def main():
    """Main function."""
    logger.info("Starting schema checker")
    
    url, key = get_supabase_credentials()
    
    # List of tables to check
    tables = [
        "institutions",
        "institution_holdings",
        "institution_activity",
        "hedge_fund_trades"
    ]
    
    for table in tables:
        check_table_schema(url, key, table)
        print("\n")  # Add some spacing between tables
    
    logger.info("Schema check complete")

if __name__ == "__main__":
    main() 