#!/usr/bin/env python3
"""
Print SQL to create the technical indicators table.
This can be copied and pasted into the Supabase SQL editor.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def print_sql_file(file_path):
    """Print SQL statements from a file."""
    logger.info(f"Reading SQL from file: {file_path}")
    
    # Read SQL file
    try:
        with open(file_path, 'r') as f:
            sql_content = f.read()
        
        print("\n" + "=" * 80)
        print("COPY THE FOLLOWING SQL AND EXECUTE IT IN THE SUPABASE SQL EDITOR:")
        print("=" * 80)
        print(sql_content)
        print("=" * 80 + "\n")
        
        return True
    except Exception as e:
        logger.error(f"Error reading SQL file: {str(e)}")
        return False

def main():
    """Main function."""
    try:
        # Print SQL to create technical indicators table
        file_path = "sql/create_technical_indicators_table.sql"
        success = print_sql_file(file_path)
        
        if success:
            logger.info("SQL successfully printed. Copy it to your Supabase SQL Editor.")
        else:
            logger.warning("Failed to print SQL.")
    
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 