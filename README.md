# Options Strategy Scanner v2

A sophisticated web application for scanning and analyzing options strategies, specifically Poor Man's Covered Call (PMCC) and Poor Man's Covered Put (PMCP) strategies.

## Features

- 🔍 **Strategy Scanner**: Scan multiple symbols for PMCC/PMCP opportunities
- 🎯 **Advanced Filtering**: Customizable filter criteria for LEAPS and short options
- ⭐ **Favorites Management**: Save and organize promising opportunities
- 📊 **Real-time Analysis**: Calculate ROC, POP, breakeven, and position delta
- 📝 **Service Logs**: Track all scanning activity in real-time
- 🎨 **Modern UI**: Dark-themed, responsive design with card-based layouts

## Database Schema

### strategy_filter_criteria
Stores filter configurations for scanning:
- Filter identification and naming
- LEAPS criteria (days range, delta, ITM%, OI, volume)
- Short option criteria (days range, OTM%, OI, volume)
- Strategy parameters (max net debit %, max trades, risk-free rate)
- Trade type (PMCC/PMCP)

### strategy_favorites
Stores saved opportunities:
- Symbol and underlying price
- LEAPS details (expiration, strike, cost, delta, OI, volume)
- Short option details (expiration, strike, cost, delta, IV, OI, volume)
- Strategy metrics (net debit, ROC%, POP%, position delta, breakeven)
- Trade type

## Installation

1. **Clone the repository:**
   ```bash
   cd /path/to/options-scanner-v2
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```
   DATABASE_URL=postgresql://user:password@host:port/database
   ALPHA_VANTAGE_API_KEY=your_api_key_here  # Optional
   ```

5. **Database Setup:**
   
   The `strategy_filter_criteria` table should already be created. Here's the schema for reference:
   ```sql
   CREATE TABLE strategy_filter_criteria (
       id SERIAL PRIMARY KEY,
       filter_criteria_name VARCHAR(255) NOT NULL,
       leaps_min_days INTEGER NOT NULL,
       leaps_max_days INTEGER NOT NULL,
       leaps_min_delta DECIMAL(5,4) NOT NULL,
       leaps_min_itm_percent DECIMAL(10,4) NOT NULL,
       short_min_days INTEGER NOT NULL,
       short_max_days INTEGER NOT NULL,
       short_min_otm_percent DECIMAL(10,4) NOT NULL,
       short_max_otm_percent DECIMAL(10,4) NOT NULL,
       leaps_open_interest_min INTEGER NOT NULL,
       short_open_interest_min INTEGER NOT NULL,
       leaps_volume_min INTEGER NOT NULL,
       short_volume_min INTEGER NOT NULL,
       max_net_debit_pct DECIMAL(10,4) NOT NULL,
       max_trades INTEGER NOT NULL,
       risk_free_rate DECIMAL(10,6) NOT NULL,
       type_of_trade VARCHAR(50) NOT NULL DEFAULT 'Poor Mans Covered Call',
       is_active BOOLEAN DEFAULT FALSE,
       is_deprecated BOOLEAN DEFAULT FALSE,
       last_accessed_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       date_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

   The `strategy_favorites` table is already created as per your schema.

## Usage

1. **Start the application:**
   ```bash
   python app.py
   ```

2. **Access the web interface:**
   Open your browser to `http://localhost:5000`

3. **Configure filters:**
   - Set LEAPS criteria (days range, delta, ITM%)
   - Set short option criteria (days range, OTM%)
   - Configure strategy parameters
   - Save filter configurations for reuse

4. **Scan for opportunities:**
   - Enter stock symbols (comma-separated)
   - Click "Scan for Opportunities"
   - Review results in card format

5. **Manage favorites:**
   - Click "Add to Favorites" on promising opportunities
   - Navigate to Favorites page
   - Sort and filter saved opportunities
   - Remove opportunities as needed

## Project Structure

```
options-scanner-v2/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── templates/
│   ├── index.html             # Main scanner page
│   └── favorites.html         # Favorites management page
└── static/
    └── css/
        ├── styles.css         # Main stylesheet
        └── favorites.css      # Favorites page stylesheet
```

## Key Components

### Backend (app.py)
- **Filter Management**: CRUD operations for filter configurations
- **Screening Logic**: Analyzes options chains to find strategy opportunities
- **Favorites API**: Save and retrieve favorite opportunities
- **Database Integration**: PostgreSQL with psycopg2

### Frontend
- **Service Logs Panel**: Real-time activity monitoring
- **Filter Configuration**: Dynamic form with save/load functionality
- **Results Display**: Card-based layout for opportunities
- **Favorites Management**: Advanced sorting and filtering

## Filter Criteria Explained

### LEAPS (Long Call) Criteria
- **Days Range**: Minimum and maximum days to expiration (e.g., 180-365 days)
- **Min Delta**: Minimum delta value (e.g., 0.70 for deep ITM)
- **Min ITM %**: Minimum in-the-money percentage
- **Min Open Interest**: Minimum open interest for liquidity
- **Min Volume**: Minimum daily volume

### Short Call Criteria
- **Days Range**: Minimum and maximum days to expiration (e.g., 30-45 days)
- **OTM Range**: Out-of-the-money percentage range (e.g., 3%-20%)
- **Min Open Interest**: Minimum open interest
- **Min Volume**: Minimum daily volume

### Strategy Parameters
- **Max Net Debit %**: Maximum net debit as percentage of underlying price
- **Max Trades**: Maximum number of opportunities to return
- **Risk Free Rate**: Current risk-free rate for calculations
- **Trade Type**: PMCC or PMCP

## Metrics Calculated

- **ROC (Return on Capital)**: (Max Profit / Net Debit) × 100
- **POP (Probability of Profit)**: Estimated using short delta
- **Net Debit**: LEAPS cost - Short credit
- **Net Debit %**: (Net Debit / Underlying Price) × 100
- **Position Delta**: LEAPS delta - Short delta
- **Breakeven**: LEAPS strike + Net debit
- **Max Profit**: (Short strike - LEAPS strike) - Net debit

## TODO

- [ ] Integrate live options data API
- [ ] Add historical performance tracking
- [ ] Implement Greeks visualization
- [ ] Add email alerts for new opportunities
- [ ] Support for spreads and other strategies
- [ ] Export opportunities to CSV/Excel
- [ ] Add backtesting functionality

## Notes

- The application currently uses placeholder data for underlying prices and options chains
- You'll need to integrate with an options data provider (e.g., Alpha Vantage, TD Ameritrade, etc.)
- The screener logic is adapted from the PMCC scanner reference but uses your database schema
- All monetary values use appropriate decimal precision for financial calculations

## License

MIT License - feel free to use and modify as needed.
