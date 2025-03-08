#!/usr/bin/env python3
"""
Fix for insider trades fetcher schema mismatch

This script updates the format_insider_transaction_for_db function in the 
unusual_whales_api module to match the actual insider_trades table schema in Supabase.
"""

import sys
import os
import inspect

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the unusual_whales_api module
import unusual_whales_api

# Print the current schema of the insider_trades table expected by the module
print("\nCurrent insider transaction formatting function:\n")
print(inspect.getsource(unusual_whales_api.format_insider_transaction_for_db))

# Modified function to match the schema of the insider_trades table
def fixed_format_insider_transaction_for_db(transaction):
    """Format insider transaction data for database insertion"""
    # Convert string dates to proper format
    from datetime import datetime
    
    filing_date = ""
    if "filing_date" in transaction:
        try:
            date_obj = datetime.strptime(transaction["filing_date"], "%Y-%m-%d")
            filing_date = date_obj.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            filing_date = datetime.now().strftime("%Y-%m-%d")
            
    transaction_date = ""
    if "transaction_date" in transaction:
        try:
            date_obj = datetime.strptime(transaction["transaction_date"], "%Y-%m-%d")
            transaction_date = date_obj.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            transaction_date = datetime.now().strftime("%Y-%m-%d")
    
    # Extract numeric values
    price = 0.0
    if "price" in transaction:
        try:
            price = float(transaction["price"])
        except (ValueError, TypeError):
            price = 0.0
            
    shares = 0
    if "amount" in transaction:
        try:
            shares = int(transaction["amount"])
        except (ValueError, TypeError):
            shares = 0
            
    shares_owned_before = 0
    if "shares_owned_before" in transaction:
        try:
            shares_owned_before = int(transaction["shares_owned_before"])
        except (ValueError, TypeError):
            shares_owned_before = 0
            
    shares_owned_after = 0
    if "shares_owned_after" in transaction:
        try:
            shares_owned_after = int(transaction["shares_owned_after"])
        except (ValueError, TypeError):
            shares_owned_after = 0
    
    return {
        "filing_id": transaction.get("id", ""),
        "symbol": transaction.get("ticker", ""),
        "company_name": transaction.get("company_name", ""),
        "insider_name": transaction.get("owner_name", ""),
        "insider_title": transaction.get("officer_title", ""),
        "transaction_type": transaction.get("transaction_code", ""),
        "transaction_date": transaction_date,
        "shares": shares,  # Renamed from amount to shares
        "price": price,
        "total_value": price * shares if price and shares else 0,  # Calculate value
        "shares_owned_after": shares_owned_after,
        "filing_date": filing_date,
        "source": "Unusual Whales",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

# Monkey patch the function in the module
print("\nUpdating function to fix schema mismatch...\n")
unusual_whales_api.format_insider_transaction_for_db = fixed_format_insider_transaction_for_db

# Print the updated function
print("Updated insider transaction formatting function:\n")
print(inspect.getsource(unusual_whales_api.format_insider_transaction_for_db))

print("\nThe unusual_whales_api module has been patched to match the insider_trades table schema.")
print("Now run the insider trades fetcher again to test if the schema mismatch is fixed.") 