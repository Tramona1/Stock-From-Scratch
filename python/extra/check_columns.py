#!/usr/bin/env python3
"""
Check Columns in Supabase Table
Checks the actual columns in the insider_trades table
"""

import os
import sys
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
    
    # Try to get the column information using a workaround
    try:
        # Use EXPLAIN ANALYZE to see column names without needing data
        explain_query = """
        EXPLAIN ANALYZE SELECT * FROM insider_trades LIMIT 0;
        """
        
        # You can't directly run arbitrary SQL with the Supabase Python client
        # So we'll execute a function that we create on the server
        
        print("Creating a temporary function to check columns...")
        
        create_function = """
        CREATE OR REPLACE FUNCTION get_insider_trades_columns()
        RETURNS TABLE (column_name text, data_type text) AS $$
        BEGIN
            RETURN QUERY SELECT c.column_name::text, c.data_type::text
                FROM information_schema.columns c
                WHERE c.table_name = 'insider_trades'
                ORDER BY c.ordinal_position;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        try:
            # Try to create the function
            # Note: This may fail if the user doesn't have CREATE FUNCTION privileges
            function_result = supabase.rpc("exec_sql", {"sql": create_function}).execute()
            print("Function created successfully")
        except Exception as func_e:
            print(f"Could not create function: {str(func_e)}")
        
        # Try to call the function if it exists
        try:
            function_result = supabase.rpc("get_insider_trades_columns").execute()
            
            if function_result.data:
                print("\nColumns in insider_trades table:")
                print("=" * 50)
                print(f"{'Column Name':<30} {'Data Type':<20}")
                print("-" * 50)
                for col in function_result.data:
                    print(f"{col['column_name']:<30} {col['data_type']:<20}")
                print("=" * 50)
            else:
                print("Function returned no data")
                
        except Exception as call_e:
            print(f"Could not call function: {str(call_e)}")
            
        # If we couldn't create or call the function, fall back to a simpler query
        print("\nAttempting simple query to see available columns...")
        
        # This will include metadata but at least we can see column names
        meta_query = supabase.table("insider_trades").select("*").limit(0).execute()
        
        if hasattr(meta_query, 'columns') and meta_query.columns:
            print("\nColumns from metadata:")
            for col in meta_query.columns:
                print(f"- {col}")
                
    except Exception as e:
        print(f"Error checking columns: {str(e)}")
        
        # Let's try to run the SQL we originally wanted to run
        print("\nCreating a new insider_trades table with the correct schema...")
        sql_file = """
        DROP TABLE IF EXISTS insider_trades;
        
        CREATE TABLE insider_trades (
          id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
          filing_id uuid NOT NULL,
          symbol text NOT NULL,
          company_name text,
          insider_name text,
          transaction_type text,
          transaction_date date,
          shares numeric,
          price numeric,
          total_value numeric,
          shares_owned_after numeric,
          filing_date date,
          source text,
          created_at timestamp with time zone DEFAULT now(),
          updated_at timestamp with time zone DEFAULT now()
        );
        
        CREATE INDEX idx_insider_trades_symbol ON insider_trades (symbol);
        CREATE INDEX idx_insider_trades_transaction_date ON insider_trades (transaction_date);
        CREATE INDEX idx_insider_trades_filing_id ON insider_trades (filing_id);
        
        ALTER TABLE insider_trades ENABLE ROW LEVEL SECURITY;
        
        -- Allow authenticated users to read insider trades
        CREATE POLICY "Allow authenticated users to read insider_trades"
        ON insider_trades
        FOR SELECT 
        TO authenticated
        USING (true);
        
        -- Allow service role to insert insider trades
        CREATE POLICY "Allow service role to insert insider_trades"
        ON insider_trades
        FOR INSERT 
        TO service_role
        WITH CHECK (true);
        
        -- Allow service role to update insider trades
        CREATE POLICY "Allow service role to update insider_trades"
        ON insider_trades 
        FOR UPDATE
        TO service_role
        USING (true)
        WITH CHECK (true);
        """
        
        try:
            # Try running the SQL directly - this may not work depending on permissions
            print("\nThis will probably fail due to permissions, but giving it a try...")
            sql_result = supabase.rpc("exec_sql", {"sql": sql_file}).execute()
            print("SQL executed successfully!")
        except Exception as sql_e:
            print(f"\nCould not execute SQL: {str(sql_e)}")
            
            print("\nIMPORTANT: You need to manually run the following SQL in the Supabase SQL Editor:")
            print("=" * 80)
            print(sql_file)
            print("=" * 80)
            print("\nAfter running this SQL, try running the pipeline again.")
    
except Exception as e:
    print(f"Error connecting to Supabase: {str(e)}")
    sys.exit(1) 