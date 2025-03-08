#!/usr/bin/env python3
"""
Environment Variable Checker

This script checks if key environment variables are set and prints their values.
"""

import os
import sys
from dotenv import load_dotenv

def main():
    """Check if key environment variables are set and print their values."""
    # Load environment variables from .env file
    load_dotenv()
    
    # List of variables to check
    variables = [
        "API_KEY_UNUSUAL_WHALES",
        "UNUSUAL_WHALES_API_KEY",
        "UW_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "NEXT_PUBLIC_SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY"
    ]
    
    print("Checking environment variables...")
    
    for var in variables:
        value = os.getenv(var)
        if value:
            # Mask the value for security
            masked_value = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
            print(f"✅ {var}: {masked_value}")
        else:
            print(f"❌ {var}: Not set")
    
    # Special check for the Unusual Whales API key
    uw_key = os.getenv("API_KEY_UNUSUAL_WHALES") or os.getenv("UNUSUAL_WHALES_API_KEY") or os.getenv("UW_API_KEY")
    if uw_key:
        print("\n✅ Unusual Whales API key is set with one of the variable names")
    else:
        print("\n❌ Unusual Whales API key is not set with any of the expected variable names")

if __name__ == "__main__":
    main() 