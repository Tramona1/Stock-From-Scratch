#!/usr/bin/env python3
"""
Check Economic Tables Schema
Checks the actual schema of economic tables in Supabase
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
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("check_economic_tables")

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
    Check the actual schema of a table by trying to insert minimal data
    and seeing what column errors we get.
    """
    try:
        logger.info(f"Checking schema for table: {table_name}")
        
        # Create a minimal record with UUID as id
        minimal_record = {
            "id": "00000000-0000-0000-0000-000000000000"
        }
        
        # Try to insert and get the error
        try:
            supabase.table(table_name).insert(minimal_record).execute()
            logger.info(f"Insert succeeded with just ID - table may be empty or have only an ID column")
        except Exception as e:
            error_text = str(e)
            logger.info(f"Insert failed with error: {error_text}")
            
            # Check if we got column information from the error
            if "Could not find the" in error_text and "column" in error_text:
                missing_col = error_text.split("Could not find the '")[1].split("' column")[0]
                logger.info(f"Table requires column: {missing_col}")
                
                # Add the missing column and try again
                minimal_record[missing_col] = "test"
                try:
                    supabase.table(table_name).insert(minimal_record).execute()
                    logger.info(f"Insert succeeded with ID and {missing_col}")
                except Exception as e2:
                    error_text2 = str(e2)
                    logger.info(f"Still failed with error: {error_text2}")
                    
                    # Continue adding columns
                    if "Could not find the" in error_text2 and "column" in error_text2:
                        missing_col2 = error_text2.split("Could not find the '")[1].split("' column")[0]
                        logger.info(f"Table also requires column: {missing_col2}")
                        
                        # We could continue this process but for simplicity, we'll stop at 2 columns
        
        # Alternatively, try to query the table and look at column names
        try:
            result = supabase.table(table_name).select("*").limit(1).execute()
            if result.data:
                logger.info(f"Table has data with columns: {list(result.data[0].keys())}")
            else:
                logger.info(f"Table exists but has no data")
        except Exception as e:
            logger.error(f"Error querying table: {str(e)}")
            
    except Exception as e:
        logger.error(f"Error checking schema for {table_name}: {str(e)}")

def main():
    """Run the schema check"""
    tables_to_check = [
        "economic_events",
        "economic_reports"
    ]
    
    for table in tables_to_check:
        check_table_schema(table)

if __name__ == "__main__":
    main() 