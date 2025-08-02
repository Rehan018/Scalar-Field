#!/usr/bin/env python3
"""
Quick test script to verify SEC API is working
"""

import sys
import os
sys.path.append('src')

from data_collection.sec_api_client import SECAPIClient

def test_api():
    print("Testing SEC API connection...")
    
    client = SECAPIClient()
    
    if not client.api_key:
        print("ERROR: No API key found!")
        return False
    
    print(f"API Key: {client.api_key[:10]}...")
    print(f"Search URL: {client.search_url}")
    
    # Test with a simple query for Apple 10-K
    print("\nTesting search for AAPL 10-K filings...")
    filings = client.search_filings("AAPL", "10-K", "2023-01-01", "2024-12-31")
    
    print(f"Found {len(filings)} filings")
    
    if filings:
        print("\nFirst filing details:")
        first_filing = filings[0]
        for key, value in first_filing.items():
            print(f"  {key}: {value}")
        return True
    else:
        print("No filings found - there might still be an API issue")
        return False

if __name__ == "__main__":
    success = test_api()
    if success:
        print("\n✅ API test successful!")
    else:
        print("\n❌ API test failed!")
