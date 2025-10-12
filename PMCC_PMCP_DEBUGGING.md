# PMCC vs PMCP - Troubleshooting Identical Results

## Issue
PMCC (Poor Man's Covered Call) and PMCP (Poor Man's Covered Put) are showing identical results when they should show different options (calls vs puts).

## Root Cause Analysis

The issue is likely one of the following:

### 1. **Option Type Filtering Not Working**
**Most Likely Cause:** The Alpha Vantage API might be returning options with a different field name than "type".

**Check:**
```python
# In app.py lines 111 and 171
if option.get("type") != option_type:  # This might not be finding the field
```

**Possible API field names:**
- `"type"` → "call" or "put"
- `"contract_type"` → "call" or "put"  
- `"option_type"` → "call" or "put"
- `"contractType"` → "call" or "put"

### 2. **Debugging Steps Added**

I've added debug logging to help diagnose the issue:

**In `scan_opportunities_alphavantage()` (line ~260):**
```python
logger.info(f"🎯 Strategy: {type_of_trade} → option_type='{option_type}'")
logger.info(f"🎯 Target deltas: LEAPS={leaps_target_delta}, SHORT={short_target_delta}")
```

**In `find_leaps()` (line ~105):**
```python
logger.info(f"🔍 find_leaps: Looking for option_type='{option_type}'")
call_count = sum(1 for opt in data if opt.get("type") == "call")
put_count = sum(1 for opt in data if opt.get("type") == "put")
logger.info(f"📊 Available options: {call_count} calls, {put_count} puts")
```

**In `find_shorts()` (line ~175):**
```python
logger.info(f"🔍 find_shorts: Looking for option_type='{option_type}'")
```

### 3. **How to Diagnose**

Run the app and check the terminal output when scanning:

```bash
cd /path/to/options-scanner-v2
source .env
export FLASK_RUN_PORT=5001
python app.py
```

Then scan with PMCC strategy, look for:
```
🎯 Strategy: Poor Mans Covered Call → option_type='call'
🎯 Target deltas: LEAPS=0.8, SHORT=0.3
🔍 find_leaps: Looking for option_type='call'
📊 Available options: 150 calls, 142 puts
```

Then scan with PMCP strategy, look for:
```
🎯 Strategy: Poor Mans Covered Put → option_type='put'
🎯 Target deltas: LEAPS=-0.8, SHORT=-0.3
🔍 find_leaps: Looking for option_type='put'
📊 Available options: 150 calls, 142 puts
```

**If you see `Available options: 0 calls, 0 puts`**, the field name is wrong!

### 4. **Fixing the Field Name**

If the API uses a different field name, update these lines in `app.py`:

**Line 111 (in `find_leaps`):**
```python
# OLD:
if option.get("type") != option_type:
    continue

# NEW (try one of these):
if option.get("contract_type") != option_type:  # or
if option.get("option_type") != option_type:   # or
if option.get("contractType") != option_type:   # etc.
```

**Line 171 (in `find_shorts`):**
```python
# Same fix as above
```

### 5. **Testing the Fix**

1. Update the field name in both `find_leaps` and `find_shorts`
2. Restart the app
3. Scan with PMCC → Should see call options
4. Scan with PMCP → Should see put options
5. Verify results are different

### 6. **Alternative: API Response Inspection**

Add temporary debug code to see the actual API response:

```python
# In fetch_options_data() function (around line 85):
def fetch_options_data(symbol: str) -> List[Dict]:
    """Fetch options chain data from Alpha Vantage"""
    params = {
        "function": "REALTIME_OPTIONS",
        "symbol": symbol,
        "apikey": ALPHAVANTAGE_API_KEY,
        "require_greeks": "true"
    }
    url = f"{ALPHAVANTAGE_BASE_URL}?" + "&".join([f"{k}={v}" for k, v in params.items()])
    response = throttled_request(url, timeout=30)
    response.raise_for_status()
    payload = response.json()
    
    if "Note" in payload:
        raise RuntimeError(f"API rate limit reached: {payload['Note']}")
    
    if "data" not in payload:
        raise RuntimeError(f"Unexpected response format: {payload}")
    
    # DEBUG: Print first option to see field names
    if payload["data"]:
        logger.info(f"🔍 DEBUG: First option fields: {list(payload['data'][0].keys())}")
        logger.info(f"🔍 DEBUG: First option sample: {payload['data'][0]}")
    
    return payload["data"]
```

This will show you the exact field names used by the API.

## Expected Behavior

### PMCC (Bullish - Calls)
- **LEAPS:** Deep ITM call (strike < current price)
- **Short:** OTM call (strike > current price)
- **Delta:** Positive (LEAPS ~+0.8, Short ~+0.3)
- **Profit:** Stock rises to short strike

### PMCP (Bearish - Puts)
- **LEAPS:** Deep ITM put (strike > current price)
- **Short:** OTM put (strike < current price)
- **Delta:** Negative (LEAPS ~-0.8, Short ~-0.3)
- **Profit:** Stock falls to short strike

## Quick Test

Use this simple test:
1. Scan symbol "AAPL" with PMCC
2. Note the strike prices (should have LEAPS strike < current price)
3. Scan symbol "AAPL" with PMCP
4. Note the strike prices (should have LEAPS strike > current price)

If both show the same strikes, the filtering is not working.

## Status

✅ Debug logging added  
⏳ Waiting for test results to identify exact field name  
⏳ Fix to be applied once field name confirmed

## Next Steps

1. Run the app with debug logging
2. Check terminal output for the diagnostic messages
3. Identify if the field name needs to be changed
4. Apply fix if needed
5. Test both strategies
6. Commit fix to GitHub
