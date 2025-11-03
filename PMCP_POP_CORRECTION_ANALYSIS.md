# PMCP POP Calculation Error - Root Cause Analysis

**Date**: November 2, 2025  
**Issue**: PMCP strategy calculates POP incorrectly  
**Severity**: 🔴 HIGH - Misleading probability metric

---

## The Problem

### Current PMCP POP Calculation (INCORRECT)

**Code (Line 338 in app.py):**
```python
pop = calculate_pop(price, short_strike, T, risk_free_rate, short_iv, option_type)
```

**What it calculates:**
- Probability that stock stays ABOVE short strike at expiration
- This is the probability that SHORT PUT expires worthless (profit)
- **NOT** the probability of actual trade profit

### What PMCP POP SHOULD Calculate

**Correct Definition:**
- Probability stock falls BELOW breakeven at expiration
- Only then does the trade make a profit

---

## Mathematical Proof

### PMCP (Poor Man's Covered Put) Trade Mechanics

**Setup:**
- Buy LEAP Put: Strike $75, Cost $1,660 (LEAP debit)
- Sell Short Put: Strike $50, Credit $1 (short premium)
- Net Debit: $1,659
- Breakeven: $75 - ($1,659/100) = $58.41

**Profit/Loss Scenarios at Short Expiration:**

| Stock Price | SHORT PUT | LEAP PUT | Net Result | Profit? |
|------------|-----------|----------|------------|---------|
| $40 | ITM: -$1,000 | ITM: +$3,500 | +$2,500 - $1,659 = +$841 | ✅ YES |
| $58.41 (BE) | OTM: $0 | ITM: +$1,659 | $1,659 - $1,659 = $0 | ❌ BREAKEVEN |
| $58.50 | OTM: $0 | ITM: +$1,650 | $1,650 - $1,659 = -$9 | ❌ NO |
| $60 | OTM: $0 | ITM: +$1,500 | $1,500 - $1,659 = -$159 | ❌ NO |
| $50 (short strike) | OTM: $0 | ITM: +$2,500 | $2,500 - $1,659 = +$841 | ✅ YES |
| $62 (current) | OTM: $0 | ITM: +$1,300 | $1,300 - $1,659 = -$359 | ❌ NO |

### The Critical Insight

**For PMCP profit, stock must stay BELOW breakeven ($58.41), NOT above short strike ($50)**

- **Short strike ($50)**: Irrelevant to profitability once passed
- **Breakeven ($58.41)**: True profit threshold
- **Current stock ($62)**: Already above short strike but BELOW breakeven means LOSS

---

## Current vs Correct POP Calculations

### ETSY PMCP Example

**Trade Parameters:**
- Stock: $62.00
- LEAP Put: Strike $75, Delta -0.646
- Short Put: Strike $50, Delta -0.077
- Net Debit: $1,659
- Breakeven: $58.41
- Days to Expiration: 32
- Implied Volatility: (example) 28%

### Current (INCORRECT) POP Calculation

```
calculate_pop(S=62, K=50, T=32/365, r=0.045, sigma=0.28, option_type="put")

d2 = [ln(62/50) + (0.045 - 0.5×0.28²)×0.0877] / (0.28×√0.0877)
d2 = [0.2191 + 0.0030] / 0.0930
d2 = 2.38

POP = N(d2) = N(2.38) = 0.9913 = 99.13%
```

**Interpretation (WRONG):**
- "99.13% probability short put expires worthless"
- **This is misleading!** We want to know probability of PROFIT, not expiration

### Correct POP Calculation for PMCP

```
calculate_pop(S=62, K=58.41, T=32/365, r=0.045, sigma=0.28, option_type="put")

d2 = [ln(62/58.41) + (0.045 - 0.5×0.28²)×0.0877] / (0.28×√0.0877)
d2 = [0.0606 + 0.0030] / 0.0930
d2 = 0.684

POP = N(d2) = N(0.684) = 0.753 = 75.3%
```

**Interpretation (CORRECT):**
- "75.3% probability stock stays below breakeven ($58.41)"
- "Only if stock falls below $58.41 do we profit"
- **This is accurate probability of profit!**

---

## Why This Matters

| Metric | Current (WRONG) | Correct | Impact |
|--------|-----------------|---------|---------|
| POP | 99.13% | 75.3% | ❌ Overstates probability by 24% |
| Meaning | Misleading | Actual profit odds | 💡 Critical for traders |
| Decision Impact | Appears "too good" | Realistic expectations | ⚠️ Risk assessment affected |

**Current calculation suggests trade is nearly guaranteed to profit (99%), but actual probability is only 75%!**

---

## The Fix Required

### Option 1: Modify Function Signature (BEST)

```python
def calculate_pop(S: float, K: float, T: float, r: float, sigma: float, 
                  option_type: str, breakeven: float = None) -> float:
    """
    Calculate Probability of Profit using Black-Scholes
    
    For calls: Probability stock stays below strike (max profit zone)
    For puts: Probability stock stays below breakeven (profit zone)
    """
    if sigma == 0 or T == 0:
        return 1.0 if (S < K if option_type == "call" else S > K) else 0.0
    
    # For puts, use breakeven if provided (PMCP strategy)
    strike_to_use = breakeven if (option_type == "put" and breakeven is not None) else K
    
    d2 = (math.log(S / strike_to_use) + (r - 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    
    if option_type == "call":
        return norm.cdf(-d2)  # Probability stock stays below strike
    else:
        return norm.cdf(d2)   # Probability stock stays below breakeven
```

### Option 2: Calculate Before Calling Function

```python
# Calculate POP
T = days_to_exp / 365.0

if option_type == "call":
    # For PMCC: Probability stock stays below short strike
    pop = calculate_pop(price, short_strike, T, risk_free_rate, short_iv, "call")
else:
    # For PMCP: Probability stock stays below breakeven
    # Calculate breakeven first
    breakeven = leaps_strike - (net_debit / 100)
    # Then calculate POP with breakeven as strike
    pop = calculate_pop(price, breakeven, T, risk_free_rate, short_iv, "put")

pop_pct = pop * 100
```

---

## Recommended Solution

**Implement Option 1** - Modify function to accept optional breakeven parameter

**Benefits:**
- ✅ Clean function design
- ✅ Works for both PMCC and PMCP
- ✅ Backward compatible
- ✅ Clear intent

**Implementation:**

1. Update `calculate_pop()` function signature (line 236)
2. Update POP calculation call (line 338)
3. Pass breakeven for puts strategy

**Code Change Summary:**

```python
# BEFORE (Line 236-245):
def calculate_pop(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    if sigma == 0 or T == 0:
        return 1.0 if (S < K if option_type == "call" else S > K) else 0.0
    d2 = (math.log(S / K) + (r - 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    if option_type == "call":
        return norm.cdf(-d2)
    else:
        return norm.cdf(d2)

# AFTER (Line 236-250):
def calculate_pop(S: float, K: float, T: float, r: float, sigma: float, option_type: str, breakeven: float = None) -> float:
    """Calculate Probability of Profit using Black-Scholes
    
    For calls: Probability stock stays below strike
    For puts: Probability stock stays below breakeven (PMCP) or short strike (PMCC if no breakeven)
    """
    if sigma == 0 or T == 0:
        return 1.0 if (S < K if option_type == "call" else S > K) else 0.0
    
    # Use breakeven for puts if provided (PMCP strategy for accurate POP)
    strike_to_use = breakeven if (option_type == "put" and breakeven is not None) else K
    
    d2 = (math.log(S / strike_to_use) + (r - 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    
    if option_type == "call":
        return norm.cdf(-d2)
    else:
        return norm.cdf(d2)

# BEFORE (Line 335-339):
    T = days_to_exp / 365.0
    pop = calculate_pop(price, short_strike, T, risk_free_rate, short_iv, option_type)
    pop_pct = pop * 100

# AFTER (Line 335-350):
    T = days_to_exp / 365.0
    
    # For PMCP (puts): Use breakeven for accurate profit probability
    if option_type == "put":
        pop = calculate_pop(price, short_strike, T, risk_free_rate, short_iv, option_type, breakeven)
    else:
        pop = calculate_pop(price, short_strike, T, risk_free_rate, short_iv, option_type)
    
    pop_pct = pop * 100
```

---

## Impact Assessment

**Current Users:** Heroku Release v11 with incorrect PMCP POP
**Affected Metric:** Probability of Profit for PMCP trades only
**User Impact:** Misleading probability (too optimistic by ~24%)

**Fix Status:** 🔴 CRITICAL - Ready to implement

