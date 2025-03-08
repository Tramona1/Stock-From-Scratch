#!/usr/bin/env python3
"""
Set Up Missing Database Tables

This script executes SQL files to create the missing tables in Supabase
that were causing issues with the data pipeline.
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv
from supabase import create_client, Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(supabase_url, supabase_key)

async def execute_sql_file(file_path):
    """
    Execute SQL commands from a file
    
    Args:
        file_path: Path to the SQL file
    """
    try:
        logger.info(f"Executing SQL file: {file_path}")
        with open(file_path, 'r') as sql_file:
            sql_content = sql_file.read()
            
            # Split by semicolon to handle multiple statements
            statements = sql_content.split(';')
            
            for statement in statements:
                statement = statement.strip()
                if statement:  # Skip empty statements
                    try:
                        # Use Supabase's rpc function to execute raw SQL
                        result = await supabase.rpc('exec_sql', {'sql_string': statement}).execute()
                        logger.info(f"Executed statement successfully")
                    except Exception as e:
                        logger.error(f"Error executing statement: {str(e)}")
                        logger.error(f"Statement: {statement}")
                        # Continue with other statements even if one fails
                        continue
        
        logger.info(f"Finished executing SQL file: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error processing SQL file {file_path}: {str(e)}")
        return False

async def main():
    """Main function to set up missing tables"""
    logger.info("Starting setup of missing database tables")
    
    # SQL files to execute
    sql_files = [
        "sql/create_economic_tables.sql",
        "sql/create_fda_calendar_table.sql"
    ]
    
    for sql_file in sql_files:
        success = await execute_sql_file(sql_file)
        if success:
            logger.info(f"Successfully set up tables from {sql_file}")
        else:
            logger.error(f"Failed to set up tables from {sql_file}")
    
    logger.info("Database table setup complete")

if __name__ == "__main__":
    asyncio.run(main()) 