# Database Migration Guide

## Quick Migration (5 Minutes)

### Step 1: Connect to Database

Using the connection string from your `.env` file:

```bash
psql "postgresql://neondb_owner:npg_frKG6w0xePSB@ep-super-king-ad9z2xxi-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
```

Or if you have `DATABASE_URL` set:

```bash
psql $DATABASE_URL
```

### Step 2: Run Migration

Once connected to the database, run:

```sql
\i migration_add_leaps_max_itm.sql
```

Or from command line:

```bash
psql "postgresql://neondb_owner:npg_frKG6w0xePSB@ep-super-king-ad9z2xxi-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require" -f migration_add_leaps_max_itm.sql
```

### Step 3: Verify Migration

Check the new column exists:

```sql
SELECT leaps_max_itm_percent 
FROM strategy_filter_criteria 
LIMIT 1;
```

Expected output:
```
 leaps_max_itm_percent 
-----------------------
                50.0000
(1 row)
```

### Step 4: Verify All Columns

```sql
\d strategy_filter_criteria
```

Should show the new column:
```
leaps_max_itm_percent | numeric(10,4) | not null | default 50.0000
```

## Alternative: Manual Migration

If the script doesn't work, run these commands manually:

```sql
-- Add the column
ALTER TABLE strategy_filter_criteria 
ADD COLUMN leaps_max_itm_percent DECIMAL(10,4) NOT NULL DEFAULT 50.0000;

-- Add constraint
ALTER TABLE strategy_filter_criteria 
DROP CONSTRAINT IF EXISTS chk_itm_percent;

ALTER TABLE strategy_filter_criteria 
ADD CONSTRAINT chk_itm_percent 
CHECK (leaps_min_itm_percent <= leaps_max_itm_percent);

-- Verify
SELECT COUNT(*) FROM strategy_filter_criteria;
```

## Rollback (If Needed)

To undo the migration:

```sql
-- Remove constraint
ALTER TABLE strategy_filter_criteria 
DROP CONSTRAINT IF EXISTS chk_itm_percent;

-- Remove column
ALTER TABLE strategy_filter_criteria 
DROP COLUMN IF EXISTS leaps_max_itm_percent;
```

## Troubleshooting

### Error: "column already exists"

This means the migration already ran. You're good to go!

```sql
-- Check if column exists
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'strategy_filter_criteria' 
AND column_name = 'leaps_max_itm_percent';
```

### Error: "permission denied"

Make sure you're using the correct database user with ALTER TABLE privileges.

### Error: "relation does not exist"

The `strategy_filter_criteria` table doesn't exist. Run the full schema:

```bash
psql $DATABASE_URL -f database_schema.sql
```

## Post-Migration Validation

### Test 1: Check Default Filter

```sql
SELECT 
    filter_criteria_name,
    leaps_min_itm_percent,
    leaps_max_itm_percent
FROM strategy_filter_criteria
WHERE filter_criteria_name = 'Default PMCC Filter';
```

Expected:
```
 filter_criteria_name  | leaps_min_itm_percent | leaps_max_itm_percent 
-----------------------+-----------------------+-----------------------
 Default PMCC Filter   |               10.0000 |               50.0000
```

### Test 2: Check Constraint

Try inserting invalid data (should fail):

```sql
-- This should fail with constraint violation
INSERT INTO strategy_filter_criteria (
    filter_criteria_name,
    leaps_min_itm_percent,
    leaps_max_itm_percent
) VALUES (
    'Test Filter',
    60.0,  -- Min is higher than max
    50.0
);
```

Expected error:
```
ERROR:  new row for relation "strategy_filter_criteria" violates check constraint "chk_itm_percent"
```

This confirms the constraint is working!

### Test 3: Insert Valid Data

```sql
-- This should succeed
INSERT INTO strategy_filter_criteria (
    filter_criteria_name,
    leaps_min_itm_percent,
    leaps_max_itm_percent,
    leaps_min_days,
    leaps_max_days,
    leaps_min_delta,
    short_min_days,
    short_max_days,
    short_min_otm_percent,
    short_max_otm_percent,
    leaps_open_interest_min,
    short_open_interest_min,
    leaps_volume_min,
    short_volume_min,
    max_net_debit_pct,
    max_trades,
    risk_free_rate,
    type_of_trade
) VALUES (
    'Test Migration Filter',
    15.0,  -- Min ITM
    45.0,  -- Max ITM (valid: min < max)
    180, 730, 0.70,
    30, 45, 3.0, 20.0,
    10, 10, 10, 10,
    0.5, 5, 0.045,
    'Poor Mans Covered Call'
);

-- Clean up test
DELETE FROM strategy_filter_criteria 
WHERE filter_criteria_name = 'Test Migration Filter';
```

## After Migration: Start Application

```bash
# Make sure you're in the project directory
cd /Users/herambhathavale/jupyterDir2/Oct-12-2025-Options-Scanner-v2/options-scanner-v2

# Activate virtual environment
source .venv/bin/activate

# Set environment variables
export DATABASE_URL="postgresql://neondb_owner:npg_frKG6w0xePSB@ep-super-king-ad9z2xxi-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
export ALPHAVANTAGE_API_KEY="ZSDQA0G3YL73HLCC"

# Run the app
python app.py
```

You should see:
```
INFO:app:📝 Creating default strategy filter...  (or already exists)
INFO:app:✅ Default filter created
INFO:app:✅ Application initialized successfully
 * Running on http://0.0.0.0:5000
```

## Common Migration Issues

### Issue 1: Connection Timeout

**Symptom:** Can't connect to database

**Solution:**
1. Check internet connection
2. Verify database URL is correct
3. Check if Neon database is running (login to Neon dashboard)

### Issue 2: SSL Error

**Symptom:** "SSL connection has been closed unexpectedly"

**Solution:**
Add `sslmode=require` to connection string:
```bash
psql "postgresql://...?sslmode=require"
```

### Issue 3: Permission Denied

**Symptom:** "permission denied for relation strategy_filter_criteria"

**Solution:**
Make sure you're using the owner account (`neondb_owner`) from your connection string.

## Migration Checklist

Use this checklist to track your migration:

- [ ] Connected to database successfully
- [ ] Ran migration script
- [ ] Verified new column exists
- [ ] Verified constraint works
- [ ] Tested app starts without errors
- [ ] Tested scanning with 1-2 symbols
- [ ] Verified new "Max ITM %" field appears in UI
- [ ] Saved a filter with new field
- [ ] Loaded saved filter and verified field populates

## Need Help?

If you encounter issues:

1. **Check the terminal output** for detailed error messages
2. **Review database logs** in Neon dashboard
3. **Verify all environment variables** are set in `.env`
4. **Check documentation:**
   - `ALPHA_VANTAGE_INTEGRATION.md` - Full guide
   - `INTEGRATION_SUMMARY.md` - Technical details
   - `ALPHA_VANTAGE_QUICK_REFERENCE.txt` - Quick commands

---

**Migration Time:** ~5 minutes
**Difficulty:** Easy
**Risk:** Low (column addition with default value)
**Rollback:** Simple (drop column if needed)
