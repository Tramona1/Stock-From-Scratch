#!/usr/bin/env python3
"""
Check the schema of the options_flow and option_flow_data tables
to understand the correct structure for storing data.
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
logger = logging.getLogger("check_schema")

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def check_table_schema(table_name):
    """Check the schema of a specific table."""
    try:
        # Connect to Supabase
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")
        
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info(f"Checking schema for table: {table_name}")
        
        # Query the information_schema.columns table to get column information
        response = supabase.table("information_schema.columns").select(
            "column_name,data_type,is_nullable,column_default"
        ).eq("table_name", table_name).execute()
        
        if response.data:
            logger.info(f"Found {len(response.data)} columns for table {table_name}:")
            columns = response.data
            for col in columns:
                logger.info(f"- {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
            
            # Write schema to a JSON file for reference
            with open(f"{table_name}_schema.json", "w") as f:
                json.dump(columns, f, indent=4)
                logger.info(f"Schema saved to {table_name}_schema.json")
            
            return columns
        else:
            logger.warning(f"No columns found for table {table_name}")
            return []
            
    except Exception as e:
        logger.error(f"Error checking schema: {str(e)}")
        return []

def check_sample_data(table_name, limit=5):
    """Check sample data from the table to understand its structure."""
    try:
        # Connect to Supabase
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")
        
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info(f"Fetching sample data from table: {table_name}")
        
        # Query the table to get sample data
        response = supabase.table(table_name).select("*").limit(limit).execute()
        
        if response.data and len(response.data) > 0:
            logger.info(f"Found {len(response.data)} rows of sample data")
            sample = response.data[0]
            logger.info(f"Sample data: {json.dumps(sample, indent=2)}")
            
            # Write sample to a JSON file for reference
            with open(f"{table_name}_sample.json", "w") as f:
                json.dump(response.data, f, indent=4)
                logger.info(f"Sample data saved to {table_name}_sample.json")
            
            return response.data
        else:
            logger.warning(f"No data found in table {table_name}")
            return []
            
    except Exception as e:
        logger.error(f"Error fetching sample data: {str(e)}")
        return []

def check_watchlist_schema():
    """Check the schema of the watchlists table to understand the column structure."""
    return check_table_schema("watchlists")

def main():
    """Check the schemas of the options-related tables."""
    # Check options_flow table schema
    options_flow_schema = check_table_schema("options_flow")
    
    # Check option_flow_data table schema
    option_flow_data_schema = check_table_schema("option_flow_data")
    
    # Check watchlists table schema
    watchlist_schema = check_watchlist_schema()
    
    # Also check samples if there's any data
    check_sample_data("options_flow")
    check_sample_data("option_flow_data")
    check_sample_data("watchlists")
    
    # Summary
    logger.info("Schema checking complete")
    
    if not options_flow_schema or not option_flow_data_schema:
        logger.warning("One or more tables had no schema information. Check for correct table names.")

if __name__ == "__main__":
    main() 