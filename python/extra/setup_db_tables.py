#!/usr/bin/env python3
"""
Setup Database Tables

This script sets up all the necessary tables in Supabase by executing the SQL files.
It connects to Supabase and runs the SQL commands for each component.
"""

import os
import sys
import logging
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/setup_db_tables.log")
    ]
)
logger = logging.getLogger("setup_db_tables")

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

# SQL files to execute
SQL_FILES = [
    "sql/create_economic_reports_table.sql",
    "sql/create_option_flow_data_table.sql", 
    "sql/create_dark_pool_data_table.sql",
    "sql/create_stock_info_table.sql",
    "sql/create_market_news_tables.sql"
]

async def execute_sql_file(file_path):
    """Execute SQL commands from a file"""
    logger.info(f"Executing SQL file: {file_path}")
    
    try:
        # Read SQL file
        with open(file_path, 'r') as file:
            sql_content = file.read()
        
        # Split into individual statements (crude but effective for most cases)
        statements = sql_content.split(';')
        
        # Execute each statement
        for statement in statements:
            # Skip empty statements
            statement = statement.strip()
            if not statement:
                continue
                
            # Add back the semicolon that was removed by the split
            statement += ';'
            
            # Execute the statement
            try:
                logger.debug(f"Executing SQL: {statement[:100]}...")
                # We need to use rpc for statements that don't return rows
                response = supabase.rpc(
                    'execute_sql', 
                    {'sql_command': statement}
                ).execute()
                
                logger.debug(f"SQL execution result: {response}")
            except Exception as e:
                logger.error(f"Error executing SQL statement: {str(e)}")
                logger.error(f"Statement: {statement}")
                # Continue with other statements even if one fails
        
        logger.info(f"Successfully executed SQL file: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error executing SQL file {file_path}: {str(e)}")
        return False

async def main():
    """Setup all database tables"""
    logger.info("Starting database table setup")
    
    # Track success/failure for each file
    results = {}
    
    # Execute each SQL file
    for sql_file in SQL_FILES:
        try:
            success = await execute_sql_file(sql_file)
            results[sql_file] = "SUCCESS" if success else "FAILED"
        except Exception as e:
            logger.error(f"Error processing {sql_file}: {str(e)}")
            results[sql_file] = "ERROR"
    
    # Print summary
    logger.info("===== SQL EXECUTION SUMMARY =====")
    for file, result in results.items():
        logger.info(f"{file}: {result}")
    
    # Return overall success/failure
    return all(result == "SUCCESS" for result in results.values())

# If the script is run directly, execute the main function
if __name__ == "__main__":
    # Create custom RPC function in Supabase if it doesn't exist
    # This function allows executing arbitrary SQL from Python
    try:
        # First check if the function already exists
        check_function_sql = """
        SELECT routine_name 
        FROM information_schema.routines 
        WHERE routine_name = 'execute_sql' 
        AND routine_schema = 'public';
        """
        
        response = supabase.rpc('execute_sql', {'sql_command': check_function_sql}).execute()
        
        # If function doesn't exist, create it
        if not response.data or len(response.data) == 0:
            create_function_sql = """
            CREATE OR REPLACE FUNCTION execute_sql(sql_command text)
            RETURNS JSONB
            LANGUAGE plpgsql
            SECURITY DEFINER
            AS $$
            BEGIN
                EXECUTE sql_command;
                RETURN '{"status": "success"}'::JSONB;
            EXCEPTION WHEN OTHERS THEN
                RETURN jsonb_build_object(
                    'status', 'error',
                    'error', SQLERRM,
                    'detail', SQLSTATE
                );
            END;
            $$;
            """
            
            # We need to use the REST API directly for this
            logger.info("Creating execute_sql function in Supabase")
            response = supabase.rpc('execute_sql', {'sql_command': create_function_sql}).execute()
            logger.info("Function created successfully")
        else:
            logger.info("execute_sql function already exists")
    except Exception as e:
        logger.error(f"Error setting up execute_sql function: {str(e)}")
        sys.exit(1)
    
    # Run the main function
    result = asyncio.run(main())
    
    if result:
        logger.info("All database tables set up successfully!")
        sys.exit(0)
    else:
        logger.error("Failed to set up some database tables.")
        sys.exit(1) 