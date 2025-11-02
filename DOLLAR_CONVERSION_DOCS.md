# Max Net Debit Parameter: Percentage to Dollar Conversion

## Overview
Converted the Max Net Debit parameter from a **percentage-based** filter to an **absolute dollar amount** filter for more intuitive and consistent trade filtering.

## What Changed

### Before (Percentage-Based)
- **Parameter**: `max_net_debit_pct` (decimal 0-1 range)
- **User Input**: Percentage (0-100%)
- **Filter Logic**: `net_debit_pct = net_debit / (price * 100)` then compare to threshold
- **Example**: Set to 50% meant max debit = 50% of stock price
  - For $200 stock: max $100 debit
  - For $100 stock: max $50 debit
  - **Problem**: Inconsistent dollar amounts across different stock prices

### After (Dollar-Based)
- **Parameter**: `max_net_debit` (dollar amount)
- **User Input**: Dollar amount (e.g., $5,000)
- **Filter Logic**: Compare `net_debit` directly to dollar threshold
- **Example**: Set to $5,000 means max debit = $5,000 for ALL stocks
  - For $200 stock: max $5,000 debit
  - For $100 stock: max $5,000 debit
  - **Benefit**: Consistent risk limit regardless of stock price

## Changes Made

### 1. Backend (app.py)

#### Function Signature
```python
# BEFORE
def scan_opportunities_alphavantage(
    ...
    max_net_debit_pct: float = 0.5,  # 50% of stock price
    ...
)

# AFTER
def scan_opportunities_alphavantage(
    ...
    max_net_debit: float = 5000.0,  # $5,000 absolute
    ...
)
```

#### Filtering Logic
```python
# BEFORE (Line 323)
net_debit_pct = net_debit / (price * 100)
if net_debit > 0 and net_debit_pct < max_net_debit_pct:
    # Accept trade

# AFTER
if net_debit > 0 and net_debit <= max_net_debit:
    # Accept trade (direct dollar comparison)
```

#### Screener Function (Line 586-593)
```python
# BEFORE
net_debit = leap_cost - short_credit
if underlying_price > 0:
    net_debit_pct = (net_debit / underlying_price)
    if net_debit_pct > filter_criteria['max_net_debit_pct']:
        reject()

# AFTER
net_debit = leap_cost - short_credit
if net_debit > filter_criteria['max_net_debit_pct']:  # Direct comparison
    reject()
# Still calculate net_debit_pct for display purposes
```

#### Database Default (Line 416)
```python
# BEFORE
0.5000,  # 50% of stock price

# AFTER
5000.0,  # $5,000 absolute
```

#### Scan Endpoint (Line 878)
```python
# BEFORE
max_net_debit_pct=filter_criteria['max_net_debit_pct'],

# AFTER
max_net_debit=filter_criteria['max_net_debit_pct'],  # Column name unchanged
```

### 2. Frontend (templates/index.html)

#### HTML Input Field
```html
<!-- BEFORE -->
<label>Max Net Debit % of Stock Price:</label>
<input type="number" id="maxNetDebitPct" 
       value="{{ (filter_criteria['max_net_debit_pct'] * 100) if filter_criteria else 50 }}" 
       step="1" min="0" max="100"
       title="Maximum debit as percentage of underlying stock price">
<span>%</span>

<!-- AFTER -->
<label>Max Net Debit ($):</label>
<input type="number" id="maxNetDebitPct" 
       value="{{ filter_criteria['max_net_debit_pct'] if filter_criteria else 5000 }}" 
       step="100" min="0" max="50000"
       title="Maximum net debit in dollars">
<span>USD</span>
```

#### JavaScript - Loading Filter (Line 293)
```javascript
// BEFORE
document.getElementById('maxNetDebitPct').value = filter.max_net_debit_pct * 100;

// AFTER
document.getElementById('maxNetDebitPct').value = filter.max_net_debit_pct;
```

#### JavaScript - Submitting Scan (Line 422)
```javascript
// BEFORE
max_net_debit_pct: parseFloat(document.getElementById('maxNetDebitPct').value) / 100,

// AFTER
max_net_debit_pct: parseFloat(document.getElementById('maxNetDebitPct').value),
```

## Migration Notes

### Database Column
- Column name `max_net_debit_pct` **remains unchanged** in database
- Only the **meaning** and **values** stored have changed
- Old percentage values (0-1) should be updated to dollar amounts (e.g., 5000)

### Existing Data
If you have existing filters in the database with percentage values:
```sql
-- Update old percentage values to reasonable dollar amounts
-- Example: 0.5 (50%) → 5000 ($5,000)
UPDATE strategy_filter_criteria 
SET max_net_debit_pct = 5000.0 
WHERE max_net_debit_pct < 10;  -- Assume values < 10 are old percentages
```

### Default Value
- **Old**: 0.5 (50% of stock price)
- **New**: 5000.0 ($5,000 absolute)
- Reasonable for stocks ranging from $50 to $500

## Benefits

### 1. **Consistent Risk Management**
- Set one dollar limit that applies to all stocks
- Example: $5,000 max debit = $5,000 for TSLA, AMD, NVDA, etc.

### 2. **Easier Budgeting**
- "I want to risk max $5,000 per trade" is clearer than "max 50% of stock price"
- Aligns with typical trading account size thinking

### 3. **Simplified Mental Model**
- No need to calculate percentages
- Direct dollar amounts are more intuitive

### 4. **Better for Mixed Portfolios**
- When scanning multiple symbols with different prices
- Consistent capital allocation across all trades

## Examples

### Scenario 1: High-Priced Stock (TSLA @ $435)
```
BEFORE (50% limit):
- Max debit = $435 × 50% = $217.50 per share = $21,750 per contract
- Allows expensive spreads

AFTER ($5,000 limit):
- Max debit = $5,000 per contract (absolute)
- Filters out expensive spreads
- More conservative for high-priced stocks
```

### Scenario 2: Low-Priced Stock (SOFI @ $28)
```
BEFORE (50% limit):
- Max debit = $28 × 50% = $14 per share = $1,400 per contract
- Restricts opportunities

AFTER ($5,000 limit):
- Max debit = $5,000 per contract (absolute)
- Allows more opportunities
- More flexibility for low-priced stocks
```

### Scenario 3: Multi-Symbol Scan
```
BEFORE (50% limit):
- TSLA ($435): max $21,750 per contract
- AMD ($238): max $11,900 per contract  
- SOFI ($28): max $1,400 per contract
- Inconsistent risk across symbols

AFTER ($5,000 limit):
- TSLA ($435): max $5,000 per contract
- AMD ($238): max $5,000 per contract
- SOFI ($28): max $5,000 per contract
- Consistent risk across all symbols
```

## Testing

### Test Case 1: Verify Dollar Filter
```
1. Set Max Net Debit to $5,000
2. Scan for TSLA (high-priced)
3. Verify all results have net_debit ≤ $5,000
```

### Test Case 2: Verify Display
```
1. Load a saved filter
2. Verify dollar amount displays correctly (not percentage)
3. Edit and save filter
4. Verify dollar amount persists
```

### Test Case 3: Verify Calculation
```
1. Check terminal logs during scan
2. Verify: "Check net debit threshold (dollar amount)"
3. Confirm filter logic uses direct dollar comparison
```

## Deployment

- **GitHub**: Commit 51aec78
- **Heroku**: Release v9
- **Live URL**: https://options-scanner-v2-78b74c58ddef.herokuapp.com/

## Backward Compatibility

⚠️ **Breaking Change**: This is a breaking change for existing filters
- Old percentage-based filters will now be interpreted as dollar amounts
- Example: If filter had 0.5 (meant 50%), it's now $0.50 (invalid)
- **Recommendation**: Update existing filters to dollar amounts (e.g., 5000)

## Future Enhancements

Potential improvements for consideration:
1. Add percentage view as optional display mode
2. Add presets (Conservative: $3,000, Moderate: $5,000, Aggressive: $10,000)
3. Add per-symbol override capability
4. Add warning if dollar amount seems unusually high/low

---

**Date**: October 17, 2025  
**Version**: Release v9  
**Impact**: All scans now use absolute dollar filtering for consistent risk management
