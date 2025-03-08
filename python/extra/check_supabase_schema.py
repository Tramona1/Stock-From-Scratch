#!/usr/bin/env python3
"""
Check Supabase Schema
Connects to Supabase and checks the insider_trades table
"""

import os
import sys
import json
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Get Supabase credentials
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Supabase credentials not found in environment variables")
    sys.exit(1)

try:
    # Initialize Supabase client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Connected to Supabase successfully")
    
    # Attempt to query the insider_trades table
    try:
        result = supabase.table("insider_trades").select("*").limit(1).execute()
        print("\nSuccessfully queried the insider_trades table")
        
        if result.data:
            print("\nSample row from insider_trades table:")
            print(json.dumps(result.data[0], indent=2))
            
            # Print column names from the first row
            print("\nColumns in insider_trades table:")
            columns = list(result.data[0].keys())
            for col in columns:
                print(f"- {col}")
        else:
            print("\nThe insider_trades table exists but contains no data")
            
        # Try to query specifically for filing_id to see the error
        try:
            filing_query = supabase.table("insider_trades").select("filing_id").limit(1).execute()
            print("\nCould query filing_id column - it exists in the table")
        except Exception as filing_e:
            print(f"\nError when querying filing_id column: {str(filing_e)}")
            
    except Exception as table_e:
        print(f"\nError accessing insider_trades table: {str(table_e)}")
        
        # Try to list all tables
        try:
            print("\nAttempting to list all tables in the database...")
            tables = supabase.table("pg_catalog.pg_tables").select("tablename").eq("schemaname", "public").execute()
            
            if tables.data:
                print("\nTables in the database:")
                for table in tables.data:
                    print(f"- {table['tablename']}")
            else:
                print("No tables found or insufficient permissions")
        except Exception as list_e:
            print(f"Error listing tables: {str(list_e)}")
        
except Exception as e:
    print(f"Error connecting to Supabase: {str(e)}")
    sys.exit(1) 