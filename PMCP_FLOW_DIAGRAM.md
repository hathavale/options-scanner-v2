# PMCP Algorithm Flow Diagram

## Complete PMCP Processing Flow

```mermaid
graph TD
    Start["🚀 START: PMCP Scan"] --> FetchAPI["📊 Fetch Options Chain<br/>from Alpha Vantage"]
    
    FetchAPI --> FilterLeaps["🔍 Filter LEAPS<br/>Criteria:<br/>• 365-730 DTE<br/>• Delta ≥ 0.70<br/>• ITM 10-50%"]
    
    FilterLeaps --> FilterShorts["🔍 Filter Shorts<br/>Criteria:<br/>• 30-60 DTE<br/>• Delta ≥ 0.30<br/>• OTM 3-20%"]
    
    FilterShorts --> LeapCount{"LEAPS<br/>Found?"}
    LeapCount -->|No| EndEmpty["⚠️ No qualifying LEAPS"]
    LeapCount -->|Yes| ShortCount{"Shorts<br/>Found?"}
    
    ShortCount -->|No| EndEmpty
    ShortCount -->|Yes| LoopLeaps["📍 For each LEAP"]
    
    LoopLeaps --> LoopShorts["📍 For each SHORT"]
    
    LoopShorts --> CheckExp{"Short expires<br/>BEFORE<br/>LEAP?"}
    CheckExp -->|No| SkipExp["❌ Skip: Expiry mismatch"]
    
    CheckExp -->|Yes| CheckStrike{"Short Strike<br/>≥<br/>LEAP Strike?"}
    CheckStrike -->|No| SkipStrike["❌ Skip: Strike mismatch"]
    
    CheckStrike -->|Yes| CalcDebit["💰 Calculate Net Debit<br/>= LEAP ASK - SHORT BID"]
    
    CalcDebit --> DebitCheck{"Net Debit ≤<br/>Max Debit?"}
    DebitCheck -->|No| SkipDebit["❌ Skip: Debit too high"]
    
    DebitCheck -->|Yes| CalcMetrics["📈 Calculate Position Metrics"]
    
    CalcMetrics --> CalcMaxProfit["Max Profit<br/>= LEAP Strike - SHORT Strike - Net Debit"]
    
    CalcMaxProfit --> CalcROC["🎯 ROC Calculation<br/>= Max Profit / Net Debit * 100"]
    
    CalcROC --> CalcPOP["🎲 POP Calculation<br/>Using Black-Scholes:<br/>- S = Stock Price<br/>- K = Short Strike<br/>- T = Days to expiry<br/>- σ = Implied Vol<br/>- r = Risk-free rate"]
    
    CalcPOP --> CalcDelta["📊 Position Delta<br/>= LEAP Delta + SHORT Delta"]
    
    CalcDelta --> CalcBreakeven["📍 Breakeven<br/>= LEAP Strike - Net Debit"]
    
    CalcBreakeven --> CreateOppty["✅ Create Opportunity Object<br/>with all metrics"]
    
    CreateOppty --> MoreShorts{"More<br/>Shorts?"}
    MoreShorts -->|Yes| LoopShorts
    MoreShorts -->|No| MoreLeaps{"More<br/>LEAPs?"}
    
    MoreLeaps -->|Yes| LoopLeaps
    MoreLeaps -->|No| SortResults["🔢 Sort by ROC Descending"]
    
    SortResults --> LimitResults["⚡ Limit to Max Trades"]
    
    LimitResults --> End["✅ END: Return Results"]
    
    SkipExp --> MoreShorts
    SkipStrike --> MoreShorts
    SkipDebit --> MoreShorts
    EndEmpty --> End
    
    style Start fill:#90EE90
    style End fill:#FFB6C6
    style CalcROC fill:#FFE4B5,stroke:#FF6347,stroke-width:2px
    style CalcPOP fill:#FFE4B5,stroke:#FF6347,stroke-width:2px
    style CalcMaxProfit fill:#87CEEB
    style CalcBreakeven fill:#87CEEB
    style DebitCheck fill:#FFFFE0
    style CheckStrike fill:#FFFFE0
    style CheckExp fill:#FFFFE0
```

---

## ROC & POP Calculation Detail

### ❌ Current (INCORRECT) Implementation

```mermaid
graph LR
    A["Short Premium<br/>$100"] --> B["÷ Net Debit<br/>$200"]
    B --> C["× 100 = 50% ROC<br/>WRONG!"]
    
    D["Short Delta<br/>-0.30"] --> E["1 - 0.30 = 0.70"]
    E --> F["× 100 = 70% POP<br/>WRONG!"]
    
    style C fill:#FFB6C6
    style F fill:#FFB6C6
```

### ✅ Correct Implementation

```mermaid
graph LR
    A["Max Profit<br/>$800"] --> B["÷ Net Debit<br/>$200"]
    B --> C["× 100 = 400% ROC<br/>CORRECT!"]
    
    D["Black-Scholes<br/>Calculation"] --> E["N-d2 Probability<br/>Stock above Strike"]
    E --> F["× 100 = 65% POP<br/>CORRECT!"]
    
    style C fill:#90EE90
    style F fill:#90EE90
```

---

## Issue Visualization

### ROC Calculation Comparison

```
Given:
┌─────────────────────────────────────┐
│ Stock Price: $100                   │
│ LEAP Strike: $95 (ITM)              │
│ LEAP Cost (ASK): $3.00              │
│ SHORT Strike: $105 (OTM)            │
│ SHORT Credit (BID): $1.00           │
│ Net Debit: $2.00/share = $200/cont  │
│ Max Profit: $8.00/share = $800/cont │
└─────────────────────────────────────┘

CURRENT (WRONG):
┌──────────────────────────────────────┐
│ ROC = (Short Credit / Net Debit)×100 │
│ ROC = ($1.00 / $2.00) × 100          │
│ ROC = 50% ← UNDERESTIMATES by 8x!   │
└──────────────────────────────────────┘

CORRECT:
┌──────────────────────────────────────┐
│ ROC = (Max Profit / Net Debit)×100   │
│ ROC = ($8.00 / $2.00) × 100          │
│ ROC = 400% ← ACTUAL RETURN!         │
└──────────────────────────────────────┘
```

### POP Calculation Comparison

```
Given:
┌──────────────────────────────────────┐
│ Stock Price: $100                    │
│ SHORT Strike: $105                   │
│ Days to Expiry: 30                   │
│ Implied Vol: 0.30 (30%)              │
│ Risk-free Rate: 0.045 (4.5%)         │
│ Breakeven: $93 (after net debit)     │
└──────────────────────────────────────┘

CURRENT (WRONG):
┌──────────────────────────────────────┐
│ POP = (1 - |Delta|) × 100            │
│ POP = (1 - 0.30) × 100               │
│ POP = 70% ← TOO SIMPLISTIC!          │
│                                       │
│ Problems:                            │
│ • Ignores implied volatility         │
│ • Doesn't account for stock price    │
│ • Doesn't consider breakeven         │
└──────────────────────────────────────┘

CORRECT (Black-Scholes):
┌──────────────────────────────────────┐
│ Calculate d2:                        │
│ d2 = [ln(S/K) + (r-σ²/2)T] / (σ√T)  │
│                                       │
│ POP = N(d2) × 100                    │
│ POP ≈ 65% ← ACCURATE!                │
│                                       │
│ Accounts for:                        │
│ • Current stock price vs strike      │
│ • Volatility environment             │
│ • Time decay                         │
│ • Risk-free rate                     │
└──────────────────────────────────────┘
```

---

## Impact on Results

```
Example Portfolio:
┌────────────┬──────────┬──────────┬──────────┬──────────┐
│ Stock      │ Strategy │ ROC      │ POP      │ Status   │
│            │          │ Current  │ Current  │          │
├────────────┼──────────┼──────────┼──────────┼──────────┤
│ AAPL       │ PMCP     │ 30%      │ 72%      │ ✓ Sorted │
│ MSFT       │ PMCP     │ 25%      │ 68%      │ ✓ Top    │
│ NVDA       │ PMCP     │ 40%      │ 75%      │ ✓ Rank   │
└────────────┴──────────┴──────────┴──────────┴──────────┘

After Fixes:
┌────────────┬──────────┬──────────┬──────────┬──────────┐
│ Stock      │ Strategy │ ROC      │ POP      │ Status   │
│            │          │ Correct  │ Correct  │          │
├────────────┼──────────┼──────────┼──────────┼──────────┤
│ AAPL       │ PMCP     │ 240%     │ 65%      │ ✓ Sorted │
│ MSFT       │ PMCP     │ 200%     │ 58%      │ ✓ RE-    │
│ NVDA       │ PMCP     │ 320%     │ 70%      │ ✓ RANKED │
└────────────┴──────────┴──────────┴──────────┴──────────┘

New Ranking Order: NVDA → AAPL → MSFT (previously NVDA → AAPL → MSFT)
Result Reordering: YES - More accurate POP changes top picks
ROC Scaling: 8x underestimation corrected
```

---

## Key Takeaways

| Metric | Current Issue | Why It Matters | Fix |
|--------|---------------|----------------|-----|
| **ROC** | Uses credit instead of profit | Users see 8x lower returns | Use max_profit numerator |
| **POP** | Delta approximation | Misleads on success probability | Use Black-Scholes |
| **Pricing** | Mark price for all | Ignores bid-ask spreads | Use ASK for buys, BID for sells |
| **Breakeven** | Not synced with POP | Inconsistent metrics | Use LEAP Strike - Net Debit |

