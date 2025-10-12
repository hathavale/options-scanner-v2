# Quick Reference: PMCC vs PMCP

## At a Glance

| | PMCC | PMCP |
|---|---|---|
| **Full Name** | Poor Man's Covered Call | Poor Man's Covered Put |
| **Direction** | 📈 Bullish | 📉 Bearish |
| **Badge Color** | 🟢 Green | 🔴 Red |
| **Options Type** | Calls | Puts |
| **Long LEAP** | Deep ITM Call | Deep ITM Put |
| **LEAP Strike** | Below current price | Above current price |
| **LEAP Delta** | ~+0.80 | ~-0.80 |
| **Short Option** | OTM Call | OTM Put |
| **Short Strike** | Above current price | Below current price |
| **Short Delta** | ~+0.30 | ~-0.30 |
| **Profit When** | Stock rises to short strike | Stock falls to short strike |
| **Max Profit** | (Short - LEAP) - Net Debit | (LEAP - Short) - Net Debit |
| **Break Even** | LEAP Strike + Net Debit | LEAP Strike - Net Debit |
| **Best For** | Bullish outlook, reduce capital vs shares | Bearish outlook, reduce capital vs shorting |

## Filter Settings Cheat Sheet

### Conservative (Higher POP, Lower ROC)
```yaml
LEAPS Days: 365-730
LEAPS ITM%: 10-30%
Short Days: 30-45
Short OTM%: 5-15%
Min OI: 100
Min Volume: 50
```

### Moderate (Balanced)
```yaml
LEAPS Days: 270-540
LEAPS ITM%: 15-40%
Short Days: 30-45
Short OTM%: 8-18%
Min OI: 50
Min Volume: 25
```

### Aggressive (Lower POP, Higher ROC)
```yaml
LEAPS Days: 180-365
LEAPS ITM%: 20-50%
Short Days: 30-45
Short OTM%: 10-25%
Min OI: 10
Min Volume: 10
```

## Example Trades

### PMCC Example (Stock @ $100)
```
Long:  Buy  $80 Call Jan 2026 @ $25.00
Short: Sell $105 Call Nov 2025 @ $2.50
Net Debit: $22.50 ($2,250 per contract)
Max Profit: $2.50 ($250) = 11.1% ROC
```

### PMCP Example (Stock @ $100)
```
Long:  Buy  $120 Put Jan 2026 @ $25.00
Short: Sell $95 Put Nov 2025 @ $2.50
Net Debit: $22.50 ($2,250 per contract)
Max Profit: $2.50 ($250) = 11.1% ROC
```

## UI Elements

### Strategy Selector
- **Location:** Top of filter section (purple banner)
- **Updates:** Labels change automatically when switched
- **Description:** Shows strategy objective in real-time

### Dynamic Labels
- PMCC: "Long Call (LEAPS)" + "Short Call"
- PMCP: "Long Put (LEAPS)" + "Short Put"

### Result Cards
- Badge shows PMCC/PMCP
- Color-coded (green=bullish, red=bearish)
- All metrics auto-calculated

## Quick Testing

```bash
# Start app
cd /path/to/options-scanner-v2
source .env
export FLASK_RUN_PORT=5001
.venv/bin/python app.py

# Test PMCC
1. Select "Poor Man's Covered Call"
2. Enter: NVDA, AMD, TSLA
3. Click "Scan Opportunities"

# Test PMCP
1. Select "Poor Man's Covered Put"
2. Enter: SPY (or bearish picks)
3. Click "Scan Opportunities"
```

## Risk Summary

### PMCC Risks
- Stock falls below LEAP strike = Full loss
- Stock rises above short strike = Limited profit
- Time decay + volatility changes

### PMCP Risks
- Stock rises above LEAP strike = Full loss
- Stock falls below short strike = Limited profit
- Time decay + volatility changes

## When to Use

**Use PMCC When:**
- ✅ Bullish on stock
- ✅ Don't want to buy 100 shares
- ✅ High IV on short-term calls
- ✅ Uptrend expected

**Use PMCP When:**
- ✅ Bearish on stock
- ✅ Don't want to short stock
- ✅ High IV on short-term puts
- ✅ Downtrend expected
