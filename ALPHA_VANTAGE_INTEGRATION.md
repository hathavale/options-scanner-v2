# Alpha Vantage Integration Guide

## Overview

The Options Scanner v2 now integrates with Alpha Vantage's real-time options data API to fetch live options chains and underlying prices for scanning PMCC/PMCP opportunities.

## Setup

### 1. Get Your API Key

1. Sign up at [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Free tier provides: **600 requests per minute** and **25,000 requests per day**
3. Premium plans available for higher limits

### 2. Configure Environment Variable

Update your `.env` file:

```bash
ALPHAVANTAGE_API_KEY="your_actual_api_key_here"
```

**Important:** The app will not function without this API key set.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This includes:
- `scipy==1.11.4` - For probability of profit (POP) calculations using Black-Scholes model
- Other existing dependencies

### 4. Database Migration (If Upgrading)

If you have an existing database, run the migration to add the new `leaps_max_itm_percent` field:

```bash
psql $DATABASE_URL -f migration_add_leaps_max_itm.sql
```

Or manually run the SQL in `migration_add_leaps_max_itm.sql`.

## Features

### Real-Time Data Fetching

The integration automatically fetches:

1. **Current Stock Prices** - Real-time quotes for underlying symbols
2. **Options Chains** - Complete options data including:
   - All strikes and expirations
   - Bid/Ask prices
   - Greeks (Delta, Gamma, Theta, Vega, Rho)
   - Implied Volatility
   - Volume and Open Interest

### Intelligent Throttling

- **Rate Limit:** 590 requests/min (safely under 600 limit)
- **Auto-throttling:** Built-in delay between requests
- **Per-symbol calls:** 2 API calls per symbol (1 for price, 1 for options chain)
- **Capacity:** Can scan ~295 symbols per minute

### Enhanced Filter Criteria

New filter field added:

- **LEAPS Max ITM %** - Maximum in-the-money percentage for LEAPS selection
  - Default: 50%
  - Helps narrow down LEAPS candidates to optimal delta range
  - Works with Min ITM % to create a precise ITM range

### Advanced Calculations

1. **Return on Capital (ROC)**
   ```
   ROC = (Short Premium / Net Debit) × 100
   ```

2. **Probability of Profit (POP)**
   - Uses Black-Scholes model with implied volatility
   - Calculates probability that short option expires OTM
   - Based on log-normal distribution of stock prices

3. **Position Delta**
   - For PMCC: `LEAPS Delta - Short Delta`
   - For PMCP: `LEAPS Delta + Short Delta`
   - Indicates directional exposure

4. **Break-Even Price**
   - For PMCC: `LEAPS Strike + (Net Debit / 100)`
   - For PMCP: `LEAPS Strike - (Net Debit / 100)`

## Usage

### Scanning for Opportunities

1. **Configure Filter:**
   - Set your criteria in the Filter Configuration section
   - New "Max ITM %" field available for LEAPS
   - Save filter for future use

2. **Enter Symbols:**
   - Enter comma-separated symbols: `AAPL, MSFT, GOOGL`
   - Click "Scan Opportunities"

3. **View Results:**
   - Opportunities displayed as cards sorted by ROC
   - Each card shows both LEAPS and short option details
   - Key metrics: Net Debit, ROC, POP, Position Delta, Break-Even

4. **Save Favorites:**
   - Click "Add to Favorites" on any opportunity
   - Access saved opportunities from the Favorites page

### Error Handling

The app handles various error scenarios:

1. **API Rate Limits**
   - Error message: "API rate limit reached"
   - Solution: Wait a minute and retry
   - Consider upgrading API plan for higher volume

2. **Invalid Symbols**
   - Error message: "No price data for SYMBOL"
   - Solution: Check symbol spelling and validity

3. **Missing API Key**
   - Error message: "ALPHAVANTAGE_API_KEY not configured"
   - Solution: Add API key to `.env` file

4. **Network Issues**
   - Error message: Connection timeout or HTTP errors
   - Solution: Check internet connection, retry

## API Limits & Best Practices

### Free Tier Limits

- **600 requests/minute**
- **25,000 requests/day**
- Each symbol scan = 2 requests (price + options)
- Max symbols per scan: ~295 per minute, 12,500 per day

### Optimization Tips

1. **Batch Processing:**
   - Scan 10-20 symbols at a time for optimal performance
   - Avoid scanning hundreds of symbols simultaneously

2. **Filter Optimization:**
   - Set tight filter criteria to reduce processing time
   - Higher OI/Volume minimums = faster results

3. **Peak Usage:**
   - Market hours (9:30 AM - 4:00 PM ET) = freshest data
   - After-hours data may be stale

4. **Caching Strategy:**
   - Consider scanning once per hour for swing trades
   - For day trading: scan every 15-30 minutes
   - Save results to favorites instead of re-scanning

## Data Flow

```
User Input (Symbols) 
    ↓
Filter Criteria (Active Filter)
    ↓
Alpha Vantage API
    ├── fetch_last_price() → Current stock price
    └── fetch_options_data() → Options chain with Greeks
        ↓
Filter Functions
    ├── find_leaps() → Qualifying LEAPS options
    └── find_shorts() → Qualifying short options
        ↓
Match & Calculate
    ├── ROC calculation
    ├── POP calculation (Black-Scholes)
    ├── Position Delta
    └── Break-Even
        ↓
Sort by ROC (descending)
    ↓
Return Top N Opportunities (max_trades)
    ↓
Display in UI
```

## Troubleshooting

### Issue: "Import scipy.stats could not be resolved"

**Solution:**
```bash
pip install scipy==1.11.4
```

### Issue: Slow Scanning

**Possible Causes:**
1. Too many symbols at once
2. Network latency
3. Approaching rate limit

**Solutions:**
- Reduce symbols per scan
- Check internet speed
- Space out multiple scans

### Issue: No Opportunities Found

**Possible Causes:**
1. Filter criteria too restrictive
2. Low market volatility
3. Symbols don't have suitable options

**Solutions:**
- Widen filter ranges (ITM %, OTM %, days)
- Lower OI/Volume requirements
- Try different symbols (high-liquidity stocks)

### Issue: Database Error

**Error:** "column 'leaps_max_itm_percent' does not exist"

**Solution:**
```bash
psql $DATABASE_URL -f migration_add_leaps_max_itm.sql
```

## Performance Metrics

### Expected Response Times

- **Single Symbol:** 2-5 seconds
- **5 Symbols:** 10-20 seconds
- **10 Symbols:** 20-40 seconds
- **20 Symbols:** 40-80 seconds

*Times vary based on:*
- Network speed
- Options chain size (strikes × expirations)
- Filter complexity
- Number of matches found

### Memory Usage

- **Base App:** ~50-100 MB
- **Per Symbol Scan:** ~5-10 MB additional
- **Peak Usage (20 symbols):** ~200-300 MB

## API Response Format

### Stock Price Response

```json
{
  "Global Quote": {
    "01. symbol": "AAPL",
    "05. price": "189.95",
    ...
  }
}
```

### Options Chain Response

```json
{
  "data": [
    {
      "contractID": "AAPL250117C00150000",
      "symbol": "AAPL",
      "expiration": "2025-01-17",
      "strike": "150.0",
      "type": "call",
      "bid": "41.15",
      "ask": "41.45",
      "last": "41.30",
      "volume": "125",
      "open_interest": "1542",
      "delta": "0.8523",
      "gamma": "0.0052",
      "theta": "-0.0234",
      "vega": "0.1256",
      "implied_volatility": "0.2453"
    },
    ...
  ]
}
```

## Upgrading from Placeholder Data

If you were using the previous version with placeholder data:

1. **No code changes needed** - Integration is automatic
2. **Set API key** in `.env` file
3. **Run migration** if needed
4. **Test with 1-2 symbols** first
5. **Verify results** match expectations

The old `screener()` function is preserved but no longer used. The new `scan_opportunities_alphavantage()` function handles all scanning with real data.

## Support

For issues or questions:

1. **Alpha Vantage Support:** https://www.alphavantage.co/support/
2. **Application Issues:** Check console logs in browser dev tools and terminal
3. **Database Issues:** Review PostgreSQL logs

## Future Enhancements

Potential improvements:

1. **Caching Layer** - Store options data for 5-15 minutes to reduce API calls
2. **Batch Symbol Processing** - Queue system for large symbol lists
3. **Alternative Data Sources** - TD Ameritrade, Polygon.io integration
4. **Historical Analysis** - Track opportunity performance over time
5. **Auto-Refresh** - Scheduled scans with email notifications

---

**Last Updated:** October 12, 2025
**Version:** 2.0.0 with Alpha Vantage Integration
