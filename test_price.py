#!/usr/bin/env python3
"""Standalone test script to verify Alpha Vantage API response"""
import os
import requests
import json
from datetime import datetime

# Get API key from environment
ALPHAVANTAGE_API_KEY = os.environ.get('ALPHAVANTAGE_API_KEY')
if not ALPHAVANTAGE_API_KEY:
    print("❌ ERROR: ALPHAVANTAGE_API_KEY not set")
    exit(1)

def test_global_quote():
    """Test GLOBAL_QUOTE API directly"""
    print("=" * 60)
    print(f"Testing GLOBAL_QUOTE API for AMD at {datetime.now()}")
    print("=" * 60)
    
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AMD&apikey={ALPHAVANTAGE_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        payload = response.json()
        
        print("\n📥 Full API Response:")
        print(json.dumps(payload, indent=2))
        
        if "Global Quote" in payload:
            global_quote = payload["Global Quote"]
            current_price = global_quote.get("05. price")
            previous_close = global_quote.get("08. previous close")
            
            print("\n🔍 Key Fields:")
            print(f"  '05. price' (CURRENT): ${current_price}")
            print(f"  '08. previous close' (YESTERDAY): ${previous_close}")
            
            if current_price:
                price_float = float(current_price)
                print(f"\n✅ Code extracts: float(payload['Global Quote']['05. price']) = ${price_float:.2f}")
                
                if abs(price_float - 218.09) < 0.01:
                    print("\n⚠️  WARNING: This would return $218.09 (previous close)!")
                elif abs(price_float - 238.60) < 1.0:
                    print("\n✅ CORRECT: This returns the current price (~$238.60)")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise
    
    print("=" * 60)

if __name__ == "__main__":
    test_global_quote()
