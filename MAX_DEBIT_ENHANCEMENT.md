# Max Net Debit Parameter Enhancement

## Summary
Enhanced the **Max Net Debit** parameter in the Options Scanner v2 to make it more user-friendly and intuitive.

## What Changed

### ✅ Already Existed (Working)
The Max Net Debit parameter was **already fully functional** in the system:
- **Database**: Column `max_net_debit_pct` in `strategy_filter_criteria` table
- **Backend**: Used in `scan_opportunities_alphavantage()` and `screener()` functions
- **Frontend**: Input field in Strategy Parameters section
- **Logic**: Filters out opportunities where net debit exceeds this percentage of stock price

### 🎨 UI Improvements Made

#### Before:
```html
<label>Max Net Debit %:</label>
<input type="number" id="maxNetDebitPct" value="0.5000" step="0.0001" min="0" max="1">
```
- Displayed as decimal (0-1 range)
- No description or help text
- Confusing: User had to enter 0.5 for 50%

#### After:
```html
<label>Max Net Debit % of Stock Price:</label>
<input type="number" id="maxNetDebitPct" value="50" step="1" min="0" max="100" 
       title="Maximum debit as percentage of underlying stock price (e.g., 50 = 50%)">
<span style="margin-left: 5px; color: #888;">%</span>
```
- Displays as percentage (0-100 range)
- Added descriptive label
- Added tooltip with explanation
- Visual "%" indicator
- User-friendly: Enter 50 for 50%

### 📝 JavaScript Updates

1. **Loading Filter** (line 293):
   ```javascript
   // Convert from decimal to percentage for display
   document.getElementById('maxNetDebitPct').value = filter.max_net_debit_pct * 100;
   ```

2. **Submitting Scan** (line 422):
   ```javascript
   // Convert from percentage back to decimal for backend
   max_net_debit_pct: parseFloat(document.getElementById('maxNetDebitPct').value) / 100,
   ```

## How It Works

### Example
If you want to limit net debit to **50% of stock price**:
- **For a $200 stock**: Max debit = $100 (50% × $200)
- **For a $100 stock**: Max debit = $50 (50% × $100)

### User Experience
1. User enters: `50` in the input field (meaning 50%)
2. JavaScript converts: `50 / 100 = 0.5` before sending to backend
3. Backend calculates: `net_debit / stock_price` and compares to `0.5`
4. Only opportunities with debit ≤ 50% of stock price are shown

### Backend Logic
From `app.py` line 591:
```python
net_debit_pct = (net_debit / underlying_price)
if net_debit_pct > filter_criteria['max_net_debit_pct']:
    rejection_stats['match_rejections']['net_debit'] += 1
    continue  # Skip this opportunity
```

## Benefits
✅ **More Intuitive**: Users think in percentages (50%) not decimals (0.5)  
✅ **Clearer Labels**: "Max Net Debit % of Stock Price" explains what it means  
✅ **Tooltips**: Hover help text provides guidance  
✅ **Visual Feedback**: "%" symbol makes it obvious it's a percentage  
✅ **Better UX**: Standard 0-100 range instead of 0-1 decimal  

## Deployment
- **GitHub**: Pushed to `main` branch (commit 27caa99)
- **Heroku**: Deployed as Release v8
- **Live URL**: https://options-scanner-v2-78b74c58ddef.herokuapp.com/

## Testing
To test the improved parameter:
1. Open the app
2. Look for "Max Net Debit % of Stock Price" in Strategy Parameters section
3. Set it to `50` (meaning 50%)
4. Run a scan
5. All results will have net debit ≤ 50% of stock price

## Technical Notes
- Database stores as decimal (0-1 range): `0.5` = 50%
- Frontend displays as percentage (0-100 range): `50` = 50%
- Conversion happens in JavaScript before submission
- Backward compatible with existing database values
- Default value: `50` (50% of stock price)
