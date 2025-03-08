#!/usr/bin/env python3
"""
Execute SQL scripts to create the technical indicators table in Supabase.
"""

import os
import sys
import logging
from dotenv import load_dotenv
import supabase

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/execute_sql.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

def execute_sql_file(file_path):
    """Execute SQL statements from a file."""
    logger.info(f"Executing SQL from file: {file_path}")
    
    # Initialize Supabase client
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Supabase URL or key not found in environment variables")
        raise ValueError("Supabase URL or key not found")
    
    supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Read SQL file
    try:
        with open(file_path, 'r') as f:
            sql_content = f.read()
    except Exception as e:
        logger.error(f"Error reading SQL file: {str(e)}")
        return False
    
    # Split into individual statements and execute
    sql_statements = sql_content.split(';')
    
    for stmt in sql_statements:
        stmt = stmt.strip()
        if not stmt:
            continue
        
        try:
            logger.info(f"Executing SQL statement: {stmt[:100]}...")  # Log first 100 chars
            # Execute the statement using Supabase's rpc() function
            response = supabase_client.rpc('exec_sql', {'query': stmt}).execute()
            logger.info(f"SQL execution result: {response}")
        except Exception as e:
            logger.error(f"Error executing SQL statement: {str(e)}")
            # Continue with the next statement
    
    logger.info(f"SQL execution from file {file_path} completed")
    return True

def main():
    """Main function."""
    try:
        # Create directories if they don't exist
        os.makedirs("logs", exist_ok=True)
        
        # Execute SQL to create technical indicators table
        file_path = "sql/create_technical_indicators_table.sql"
        success = execute_sql_file(file_path)
        
        if success:
            logger.info("SQL execution completed successfully")
        else:
            logger.warning("SQL execution completed with errors")
    
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 