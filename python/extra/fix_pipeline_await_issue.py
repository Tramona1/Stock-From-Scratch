#!/usr/bin/env python3
"""
Pipeline Await Issue Fixer

This script identifies and fixes the issue where a boolean value is being awaited
in the run_pipeline.py script, causing the "object bool can't be used in 'await' expression" error.
"""

import os
import sys
import importlib
import re
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_fetcher_result_handling(fetcher_module_name, fetcher_class_name):
    """Test how the fetcher's run() method is handled in run_pipeline.py"""
    print(f"Testing fetcher: {fetcher_module_name}.{fetcher_class_name}")
    
    try:
        # Import the module dynamically
        module = importlib.import_module(f"python.{fetcher_module_name}")
        print(f"✅ Successfully imported {fetcher_module_name}")
        
        # Get the class from the module
        fetcher_class = getattr(module, fetcher_class_name)
        print(f"✅ Found class {fetcher_class_name} in module")
        
        # Create an instance of the class
        fetcher_instance = fetcher_class()
        print(f"✅ Created instance of {fetcher_class_name}")
        
        # Check if run() method is async
        run_method = getattr(fetcher_instance, "run")
        is_async = asyncio.iscoroutinefunction(run_method)
        print(f"Is run() method async? {'Yes' if is_async else 'No'}")
        
        # Determine if run() method returns a boolean or coroutine
        print(f"Return annotation: {run_method.__annotations__.get('return', 'Not specified')}")
        
        # Problem detection
        print("\nAnalysis:")
        if is_async:
            print("✅ The run() method is correctly defined as async")
            print("✳️ In run_pipeline.py, ensure you're using 'await fetcher_instance.run()' to call this method")
        else:
            print("❌ The run() method is NOT async, but it might be awaited in run_pipeline.py")
            print("✳️ Make sure you're NOT using 'await' when calling a non-async method")
        
        return is_async
        
    except ImportError:
        print(f"❌ Failed to import {fetcher_module_name}. Make sure the file exists and the path is correct.")
        return None
    except AttributeError as e:
        print(f"❌ Error: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return None

async def check_run_pipeline_code():
    """Check run_pipeline.py for improper await statements"""
    filepath = "python/run_pipeline.py"
    
    try:
        with open(filepath, "r") as f:
            code = f.read()
            
        # Find the run_fetcher function
        run_fetcher_match = re.search(r"async def run_fetcher\([^)]*\):[^~]*?(?=async def|$)", code, re.DOTALL)
        if not run_fetcher_match:
            print("❌ Could not find run_fetcher function in run_pipeline.py")
            return
            
        run_fetcher_code = run_fetcher_match.group(0)
        print("\n--- run_fetcher function code ---")
        print(run_fetcher_code)
        
        # Look for potential issues with awaiting boolean values
        await_pattern = re.search(r"result\s*=\s*await\s*fetcher_instance\.run\(\)", run_fetcher_code)
        if await_pattern:
            print("\n⚠️ Potential issue detected: Boolean result is being awaited.")
            print("The error occurs because some fetcher classes have non-async run() methods that return boolean values.")
            print("These cannot be awaited. The fix is to check if the method is a coroutine before awaiting it.")
        
        # Offer a solution
        print("\n--- Suggested fix ---")
        print("""
        # Replace this line:
        result = await fetcher_instance.run()
        
        # With this code:
        if asyncio.iscoroutinefunction(fetcher_instance.run):
            result = await fetcher_instance.run()
        else:
            result = fetcher_instance.run()
        """)
            
    except Exception as e:
        print(f"❌ Error analyzing run_pipeline.py: {str(e)}")

async def main():
    print("=" * 80)
    print("PIPELINE AWAIT ISSUE DIAGNOSTICS")
    print("=" * 80)
    
    # Test the analyst ratings fetcher
    await test_fetcher_result_handling("fetch_analyst_ratings", "AnalystRatingsFetcher")
    
    # Test another fetcher for comparison
    print("\n" + "-" * 80)
    await test_fetcher_result_handling("insider_trades_fetcher", "InsiderTradesFetcher")
    
    # Check run_pipeline.py code
    print("\n" + "-" * 80)
    await check_run_pipeline_code()
    
    print("\n" + "=" * 80)
    print("DIAGNOSTICS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main()) 