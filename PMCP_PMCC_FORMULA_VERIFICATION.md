# PMCP/PMCC Max Profit Formula Verification

**Date**: November 2, 2025  
**Issue Fixed**: Max profit displaying incorrectly for PMCP (-$4159 instead of $841)

## Problem Identified

The `scan_opportunities_alphavantage()` function correctly calculated max_profit for both PMCC and PMCP strategies, but the `/api/scan` endpoint was **recalculating** it incorrectly, destroying the correct values.

## Location of Bug

**File**: `app.py`  
**Endpoint**: `/api/scan` (POST)  
**Old Code (Line 934)**:
```python
max_profit = opp['short_strike'] - opp['leaps_strike'] - (opp['net_debit'] / 100)
```

This line was:
1. Using ONLY the PMCC formula (call spreads)
2. Using per-share values instead of contract values
3. Overwriting the correct max_profit already calculated

## Solution Applied

**New Code (Line 955)**:
```python
'max_profit': opp['max_profit'],  # Already calculated correctly in scan_opportunities_alphavantage
```

Now uses the pre-calculated max_profit from the scanning function, which is correct for both strategies.

---

## Formula Verification - Core Calculations

All calculations happen in `scan_opportunities_alphavantage()` (lines 314-370), which is **NOT affected** by this fix:

### PMCC (Poor Man's Covered Call) - Calls

**Line 328**:
```python
if option_type == "call":
    max_profit = (short_strike - leaps_strike) * 100 - net_debit
```

**Example - CALL Spread:**
- LEAP Call: Strike $100, Price $3.00 (ASK)
- Short Call: Strike $105, Price $0.80 (BID)
- LEAP Cost: $3.00 × 100 = $300
- Short Credit: $0.80 × 100 = $80
- Net Debit: $300 - $80 = $220

**Max Profit Calculation:**
```
max_profit = ($105 - $100) × 100 - $220
max_profit = $500 - $220 = $280
```

**Interpretation:**
- Maximum profit occurs if stock stays below $105 at short expiration
- All $500 width is captured minus the $220 debit paid
- Result: $280 profit

✅ **CORRECT FOR CALLS**

---

### PMCP (Poor Man's Covered Put) - Puts

**Line 330**:
```python
else:
    max_profit = (leaps_strike - short_strike) * 100 - net_debit
```

**Example - PUT Spread (From Screenshot):**
- LEAP Put: Strike $75, Price $16.60 (ASK)
- Short Put: Strike $50, Price $0.01 (BID)
- LEAP Cost: $16.60 × 100 = $1,660
- Short Credit: $0.01 × 100 = $1
- Net Debit: $1,660 - $1 = $1,659

**Max Profit Calculation:**
```
max_profit = ($75 - $50) × 100 - $1,659
max_profit = $2,500 - $1,659 = $841
```

**Interpretation:**
- Maximum profit occurs if stock stays above $50 at short expiration
- All $2,500 width is captured minus the $1,659 debit paid
- Result: $841 profit ✅ (Matches expected value from user report)

✅ **CORRECT FOR PUTS**

---

## Verification Results

| Strategy | Formula | Status | Verified |
|----------|---------|--------|----------|
| **PMCC (Calls)** | (short_strike - leap_strike) × 100 - net_debit | ✅ CORRECT | Line 328 |
| **PMCP (Puts)** | (leap_strike - short_strike) × 100 - net_debit | ✅ CORRECT | Line 330 |
| **API Response** | Uses pre-calculated max_profit | ✅ FIXED | Line 955 |

## Test Case Validation

**ETSY PMCP Trade:**
```
Underlying: $62.00
Strategy: Poor Man's Covered Put (PMCP)
ROC: 50.7%

LEAP PUT:
  Strike: $75.00
  Price: $16.60
  Delta: -0.646
  DTE: 137 days

SHORT PUT:
  Strike: $50.00
  Credit: $0.01
  Delta: -0.077
  DTE: 32 days

METRICS:
  Net Debit: $1,659.00
  Max Profit: $841.00 ✅ (Previously showed -$4,159.00)
  Breakeven: $58.41
  POP: 90.8%
```

**Calculation Verification:**
- Max Profit = ($75 - $50) × 100 - $1,659 = $2,500 - $1,659 = **$841.00** ✅
- ROC = ($841 / $1,659) × 100 = **50.66%** ✅
- Breakeven = $75 - ($1,659 / 100) = $75 - $16.59 = **$58.41** ✅

---

## Changes Summary

**Files Modified:**
1. `app.py` (1 line)
   - Line 934: Removed incorrect max_profit recalculation
   - Line 955: Now uses correct pre-calculated value

**Frontend Changes:**
1. `templates/index.html` (2 additions)
   - Added Volume display under Price for LEAP leg
   - Added Volume display under Credit for SHORT leg

**No Breaking Changes:**
- Core algorithm logic (lines 314-370) unchanged
- PMCC calculations verified and correct
- PMCP calculations verified and correct
- All metrics now display accurately for both strategies

---

## Deployment Status

✅ Changes committed and ready for production  
✅ Both PMCC and PMCP formulas verified  
✅ API endpoint now uses correct pre-calculated values  
✅ Frontend displays volume for each leg  
✅ Test case (ETSY) validates to expected values  

**Ready for Heroku deployment (Release v11)**
