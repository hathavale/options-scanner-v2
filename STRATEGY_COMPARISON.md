# Strategy Comparison: PMCC vs PMCP

## Visual Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     POOR MAN'S COVERED CALL (PMCC)                          │
│                              📈 BULLISH                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Long Position:  Buy LEAP Call (Deep ITM, Δ ~0.8)                          │
│                  └─→ Expiry: 180-730 days                                   │
│                  └─→ Strike: 10-50% ITM                                     │
│                                                                             │
│  Short Position: Sell Short Call (OTM, Δ ~0.3)                             │
│                  └─→ Expiry: 30-45 days                                     │
│                  └─→ Strike: 3-20% OTM                                      │
│                                                                             │
│  Expectation:    Stock price rises moderately                               │
│  Max Profit:     Short Strike - LEAP Strike - Net Debit                     │
│  Ideal When:     Bullish but want to reduce cost vs buying 100 shares      │
│                                                                             │
│  Example:        Stock @ $100                                               │
│                  Buy  $80 LEAP Call (Jan 2026) for $25.00                   │
│                  Sell $105 Short Call (Nov 2025) for $2.50                  │
│                  Net Debit: $22.50 per share ($2,250 per contract)          │
│                  Max Profit: $105 - $80 - $22.50 = $2.50 ($250)             │
│                  ROC: 11.1%                                                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                     POOR MAN'S COVERED PUT (PMCP)                           │
│                              📉 BEARISH                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Long Position:  Buy LEAP Put (Deep ITM, Δ ~-0.8)                          │
│                  └─→ Expiry: 180-730 days                                   │
│                  └─→ Strike: 10-50% ITM                                     │
│                                                                             │
│  Short Position: Sell Short Put (OTM, Δ ~-0.3)                             │
│                  └─→ Expiry: 30-45 days                                     │
│                  └─→ Strike: 3-20% OTM                                      │
│                                                                             │
│  Expectation:    Stock price falls moderately                               │
│  Max Profit:     LEAP Strike - Short Strike - Net Debit                     │
│  Ideal When:     Bearish but want to reduce cost vs short selling stock    │
│                                                                             │
│  Example:        Stock @ $100                                               │
│                  Buy  $120 LEAP Put (Jan 2026) for $25.00                   │
│                  Sell $95 Short Put (Nov 2025) for $2.50                    │
│                  Net Debit: $22.50 per share ($2,250 per contract)          │
│                  Max Profit: $120 - $95 - $22.50 = $2.50 ($250)             │
│                  ROC: 11.1%                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Key Differences

| Aspect | PMCC | PMCP |
|--------|------|------|
| **Options Type** | Calls | Puts |
| **LEAP Delta** | +0.8 (positive) | -0.8 (negative) |
| **Short Delta** | +0.3 (positive) | -0.3 (negative) |
| **LEAP Position** | ITM Call (below spot) | ITM Put (above spot) |
| **Short Position** | OTM Call (above spot) | OTM Put (below spot) |
| **Profit If** | Stock rises | Stock falls |
| **Alternative To** | Owning 100 shares | Short selling 100 shares |
| **Badge Color** | 🟢 Green | 🔴 Red |
| **Emoji** | 📈 | 📉 |

## Filter Configuration Examples

### Conservative PMCC (Higher Probability, Lower Return)
```
Strategy: Poor Man's Covered Call
LEAPS: 365-730 days, Min Delta 0.75, ITM 10-30%
Short: 30-45 days, OTM 5-15%
Min OI: 100, Min Volume: 50
Max Net Debit: 50%
```

### Aggressive PMCC (Lower Probability, Higher Return)
```
Strategy: Poor Man's Covered Call
LEAPS: 180-365 days, Min Delta 0.70, ITM 15-50%
Short: 30-45 days, OTM 10-25%
Min OI: 10, Min Volume: 10
Max Net Debit: 60%
```

### Conservative PMCP (Higher Probability, Lower Return)
```
Strategy: Poor Man's Covered Put
LEAPS: 365-730 days, Min Delta 0.75, ITM 10-30%
Short: 30-45 days, OTM 5-15%
Min OI: 100, Min Volume: 50
Max Net Debit: 50%
```

### Aggressive PMCP (Lower Probability, Higher Return)
```
Strategy: Poor Man's Covered Put
LEAPS: 180-365 days, Min Delta 0.70, ITM 15-50%
Short: 30-45 days, OTM 10-25%
Min OI: 10, Min Volume: 10
Max Net Debit: 60%
```

## Profit/Loss Diagrams

### PMCC P/L at Short Expiration
```
Profit
  │
  │         ╱────────  (Max profit reached)
  │       ╱
  │     ╱
  │   ╱
──┼─╱─────────────────── Stock Price
  │╱              │
 ╱│               │
  │           Short    LEAP
  │           Strike   Strike
Loss
```

### PMCP P/L at Short Expiration
```
Profit
  │
──┼────────╲
  │         ╲
  │          ╲          (Max profit reached)
  │           ╲
  │            ╲─────── Stock Price
  │     │       │
  │     │       │
  │    LEAP   Short
  │   Strike  Strike
Loss
```

## Real-World Use Cases

### When to Use PMCC:
- ✅ Bullish on a stock but premium is high
- ✅ Want exposure without buying 100 shares
- ✅ Market is in uptrend
- ✅ High IV on short-term calls
- ✅ Looking for income generation in bull market

### When to Use PMCP:
- ✅ Bearish on a stock but don't want to short
- ✅ Want downside exposure without margin requirements
- ✅ Market is in downtrend
- ✅ High IV on short-term puts
- ✅ Looking for income generation in bear market
- ✅ Hedging long positions

## Risk Considerations

### PMCC Risks:
- ❌ Stock falls below LEAP strike → Full loss of net debit
- ❌ Stock rises sharply → Limited profit (capped at max profit)
- ❌ Time decay on LEAP
- ❌ Assignment risk on short call

### PMCP Risks:
- ❌ Stock rises above LEAP strike → Full loss of net debit
- ❌ Stock falls sharply → Limited profit (capped at max profit)
- ❌ Time decay on LEAP
- ❌ Assignment risk on short put

## Alpha Vantage Data Fields

Both strategies use the same Alpha Vantage API endpoints:
- `GLOBAL_QUOTE` - Current stock price
- `REALTIME_OPTIONS` - Options chain with Greeks

The scanner automatically:
1. Fetches CALL options for PMCC
2. Fetches PUT options for PMCP
3. Filters by ITM/OTM percentages appropriately
4. Calculates probability of profit using Black-Scholes
5. Computes ROC for ranking opportunities
