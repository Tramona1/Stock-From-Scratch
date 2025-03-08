#!/usr/bin/env python3
"""
Options API Response Inspector

This script makes API calls to the Unusual Whales API and prints the structure
of the responses to identify the correct field names.
"""

import os
import sys
import json
import logging
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("options_api_inspector")

def get_api_key():
    """Get the API key from environment variables."""
    api_key = os.getenv("API_KEY_UNUSUAL_WHALES")
    if not api_key:
        logger.error("API key not found in environment variables")
        sys.exit(1)
    return api_key

def make_api_request(endpoint, params=None):
    """Make a request to the Unusual Whales API."""
    base_url = "https://api.unusualwhales.com/api"
    url = f"{base_url}/{endpoint}"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {get_api_key()}"
    }
    
    if params is None:
        params = {}
        
    logger.info(f"Making request to {url}")
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error making request: {e}")
        return None

def inspect_option_contracts_response(ticker="AAPL"):
    """Inspect the response structure for option contracts."""
    logger.info(f"Inspecting option contracts response for {ticker}")
    
    data = make_api_request(f"stock/{ticker}/option-contracts")
    
    if not data:
        logger.error("No data returned from API")
        return
    
    # Print the top-level structure
    logger.info("Top-level response structure:")
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            logger.info(f"  {key}: {type(value).__name__} with {len(value)} items")
        else:
            logger.info(f"  {key}: {value}")
    
    # Check the structure of the data field
    if "data" in data:
        if isinstance(data["data"], list):
            # Print structure of the first item
            if len(data["data"]) > 0:
                logger.info("Structure of first item in data array:")
                first_item = data["data"][0]
                for key, value in first_item.items():
                    logger.info(f"  {key}: {value}")
                
                # Save key names that might be contract IDs
                potential_ids = [k for k in first_item.keys() if any(id_name in k.lower() for id_name in ["id", "symbol", "contract"])]
                logger.info(f"Potential ID fields: {potential_ids}")
        elif isinstance(data["data"], dict):
            logger.info("Structure of data dictionary:")
            for key, value in data["data"].items():
                if isinstance(value, (dict, list)):
                    logger.info(f"  {key}: {type(value).__name__} with {len(value)} items")
                else:
                    logger.info(f"  {key}: {value}")
    
    # Save the response to a file for further inspection
    with open("options_contracts_response.json", "w") as f:
        json.dump(data, f, indent=2)
    logger.info("Saved response to options_contracts_response.json")

def inspect_option_flow_response(option_id=None):
    """Inspect the response structure for option flow."""
    if option_id is None:
        logger.warning("No option ID provided, attempting to get one first")
        data = make_api_request("stock/AAPL/option-contracts")
        
        if not data or "data" not in data:
            logger.error("Failed to get option contracts data")
            return
        
        # Try to find an option ID in the response
        if isinstance(data["data"], list) and len(data["data"]) > 0:
            first_item = data["data"][0]
            option_id = first_item.get("option_id") or first_item.get("id") or first_item.get("option_symbol")
            
            if not option_id:
                # Try to find any field that could be an ID
                for key, value in first_item.items():
                    if "id" in key.lower() or "symbol" in key.lower():
                        option_id = value
                        logger.info(f"Using {key} as option ID: {option_id}")
                        break
            
            if not option_id:
                logger.error("Could not find option ID in response")
                return
        else:
            logger.error("No option contracts found")
            return
    
    logger.info(f"Inspecting option flow response for option ID: {option_id}")
    data = make_api_request(f"option-contract/{option_id}/flow")
    
    if not data:
        logger.error("No data returned from API")
        return
    
    # Print the top-level structure
    logger.info("Top-level response structure:")
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            logger.info(f"  {key}: {type(value).__name__} with {len(value)} items")
        else:
            logger.info(f"  {key}: {value}")
    
    # Save the response to a file for further inspection
    with open("option_flow_response.json", "w") as f:
        json.dump(data, f, indent=2)
    logger.info("Saved response to option_flow_response.json")

def main():
    """Run the inspector script."""
    logger.info("Starting options API inspector")
    
    # Inspect option contracts response
    inspect_option_contracts_response()
    
    # Inspect option flow response
    inspect_option_flow_response()
    
    logger.info("Inspection complete")

if __name__ == "__main__":
    main() 