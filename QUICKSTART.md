# Quick Start Guide - Options Strategy Scanner v2

## Prerequisites Checklist
- [ ] Python 3.8 or higher installed
- [ ] PostgreSQL database with `strategy_filter_criteria` and `strategy_favorites` tables created
- [ ] Database connection details (host, port, username, password, database name)

## Step-by-Step Setup

### 1. Set Up Virtual Environment
```bash
# Navigate to project directory
cd /Users/herambhathavale/jupyterDir2/Oct-12-2025-Options-Scanner-v2/options-scanner-v2

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
# Copy example env file
cp .env.example .env

# Edit .env file with your database credentials
# Use your favorite text editor
nano .env  # or vim, code, etc.
```

**Example .env configuration:**
```
DATABASE_URL=postgresql://your_user:your_password@your_host:5432/your_database
ALPHA_VANTAGE_API_KEY=optional_api_key
```

### 4. Verify Database Tables
The application expects these tables to exist:
- ✅ `strategy_filter_criteria` (already created)
- ✅ `strategy_favorites` (already created)

You can optionally create the `options_data` table using `database_schema.sql`:
```bash
psql -h your_host -U your_user -d your_database -f database_schema.sql
```

### 5. Test Database Connection
```bash
# Quick test (optional)
python3 << EOF
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
db_url = os.environ.get('DATABASE_URL')

try:
    conn = psycopg2.connect(db_url)
    print("✅ Database connection successful!")
    conn.close()
except Exception as e:
    print(f"❌ Database connection failed: {e}")
EOF
```

### 6. Run the Application
```bash
python app.py
```

You should see output like:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://0.0.0.0:5000
```

### 7. Access the Application
Open your browser to: **http://localhost:5000**

## First Time Usage

### 1. Configure a Filter
1. The default filter should be loaded automatically
2. Adjust the criteria as needed:
   - **LEAPS criteria**: Days range (180-365), Min Delta (0.70), Min ITM% (10%)
   - **Short criteria**: Days range (30-45), OTM range (3%-20%)
   - **Strategy params**: Max Net Debit% (0.50), Max Trades (5)
3. Click **"💾 Save"** or **"📝 Save As"** to save your configuration

### 2. Scan for Opportunities
1. Enter stock symbols in the input field (e.g., `AAPL, TSLA, MSFT`)
2. Click **"🔍 Scan for Opportunities"**
3. Watch the Service Logs panel for real-time updates
4. Review results in the cards below

### 3. Add to Favorites
1. Browse the opportunity cards
2. Click **"⭐ Add to Favorites"** on interesting opportunities
3. Navigate to the **Favorites** tab to manage saved items

### 4. Manage Favorites
1. Click the **"⭐ Favorites"** tab
2. Use sorting controls to organize by ROC%, POP%, etc.
3. Apply filters by symbol or trade type
4. Remove items with the **"🗑️ Remove"** button

## Common Issues & Solutions

### Issue: "DATABASE_URL environment variable is not set"
**Solution:** Make sure your `.env` file exists and contains the DATABASE_URL

### Issue: "No module named 'psycopg2'"
**Solution:** Activate your virtual environment and install dependencies:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "relation 'strategy_filter_criteria' does not exist"
**Solution:** Create the table using the SQL in `database_schema.sql`

### Issue: Port 5000 already in use
**Solution:** Either:
- Stop the other application using port 5000
- Or modify `app.py` to use a different port:
  ```python
  app.run(debug=True, host='0.0.0.0', port=5001)
  ```

### Issue: No opportunities found
**Solution:** 
- The application currently uses placeholder data
- You need to integrate with an options data API
- Or populate the `options_data` table with real data

## Next Steps

### Integrate Live Data
The scanner currently uses placeholder data. To get real results:

1. **Option 1: Alpha Vantage**
   - Get free API key from https://www.alphavantage.co/
   - Add to `.env` file
   - Implement data fetching in `app.py`

2. **Option 2: Other APIs**
   - TD Ameritrade
   - Interactive Brokers
   - Tradier
   - Polygon.io

3. **Option 3: Manual Data**
   - Import historical options data
   - Populate `options_data` table

### Customize the Scanner
- Modify filter criteria ranges
- Add new strategy types
- Implement custom metrics
- Add visualizations

## Development Tips

### Enable Debug Mode
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py
```

### View Logs
Check the Service Logs panel in the UI for real-time activity

### Database Queries
```bash
# Connect to your database
psql -h your_host -U your_user -d your_database

# View filters
SELECT * FROM strategy_filter_criteria;

# View favorites
SELECT * FROM strategy_favorites ORDER BY roc_pct DESC;
```

## Support

For issues or questions:
1. Check the README.md for detailed documentation
2. Review the database_schema.sql for table structures
3. Examine the Service Logs panel for error messages
4. Check browser console for JavaScript errors

## Shutdown

To stop the application:
1. Press `Ctrl+C` in the terminal
2. Deactivate virtual environment: `deactivate`

---

**Happy Scanning! 📊⭐**
