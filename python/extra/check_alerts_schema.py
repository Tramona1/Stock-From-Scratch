#!/usr/bin/env python3
"""
Check the schema of the alerts table to understand its structure.
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
logger = logging.getLogger("check_alerts")

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def check_alerts_schema():
    """Check the schema of the alerts table."""
    try:
        # Connect to Supabase
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")
        
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Checking if alerts table exists")
        
        # First try to get some data from the table
        try:
            response = supabase.table("alerts").select("*").limit(1).execute()
            if response.data:
                logger.info("Alerts table exists with data")
                sample = response.data[0]
                logger.info(f"Sample alert: {json.dumps(sample, indent=2)}")
                
                # Get the column names from this sample
                columns = list(sample.keys())
                logger.info(f"Columns: {columns}")
                return columns
            else:
                logger.info("Alerts table exists but has no data")
                
                # Try to create a test alert with minimal fields
                test_alert = {
                    "id": "test_alert_1",
                    "title": "Test Alert",
                    "message": "This is a test alert",
                    "type": "test",
                    "created_at": "2025-03-08T00:00:00Z"
                }
                
                try:
                    result = supabase.table("alerts").insert(test_alert).execute()
                    logger.info("Created test alert successfully")
                    
                    # Clean up by deleting the test alert
                    supabase.table("alerts").delete().eq("id", "test_alert_1").execute()
                    logger.info("Deleted test alert")
                    
                    return list(test_alert.keys())
                except Exception as e:
                    logger.error(f"Error creating test alert: {str(e)}")
                    
                    # Try to figure out required columns from the error message
                    error_msg = str(e)
                    if "not-null constraint" in error_msg:
                        # Extract the column name from error like "column X violates not-null constraint"
                        import re
                        match = re.search(r"column \"([^\"]+)\"", error_msg)
                        if match:
                            missing_column = match.group(1)
                            logger.info(f"Required column missing: {missing_column}")
                    
                    return []
                
        except Exception as e:
            logger.error(f"Error querying alerts table: {str(e)}")
            
            if "relation \"alerts\" does not exist" in str(e):
                logger.warning("Alerts table does not exist")
                return []
            
            return []
            
    except Exception as e:
        logger.error(f"Error checking alerts schema: {str(e)}")
        return []

def main():
    """Check the alerts table schema."""
    columns = check_alerts_schema()
    
    if columns:
        logger.info(f"Found {len(columns)} columns in alerts table")
        logger.info(f"Columns: {', '.join(columns)}")
    else:
        logger.warning("Could not determine alerts table schema")

if __name__ == "__main__":
    main() 