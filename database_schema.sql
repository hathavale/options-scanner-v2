-- ============================================
-- Options Strategy Scanner v2 - Database Schema
-- ============================================

-- Strategy Filter Criteria Table
-- Stores filter configurations for scanning opportunities
CREATE TABLE IF NOT EXISTS strategy_filter_criteria (
    id SERIAL PRIMARY KEY,
    filter_criteria_name VARCHAR(255) NOT NULL,
    
    -- LEAPS (Long Call) Criteria
    leaps_min_days INTEGER NOT NULL DEFAULT 180,
    leaps_max_days INTEGER NOT NULL DEFAULT 730,
    leaps_min_delta DECIMAL(5,4) NOT NULL DEFAULT 0.7000,
    leaps_min_itm_percent DECIMAL(10,4) NOT NULL DEFAULT 10.0000,
    leaps_max_itm_percent DECIMAL(10,4) NOT NULL DEFAULT 50.0000,
    leaps_open_interest_min INTEGER NOT NULL DEFAULT 10,
    leaps_volume_min INTEGER NOT NULL DEFAULT 10,
    
    -- Short Option Criteria
    short_min_days INTEGER NOT NULL DEFAULT 30,
    short_max_days INTEGER NOT NULL DEFAULT 45,
    short_min_otm_percent DECIMAL(10,4) NOT NULL DEFAULT 3.0000,
    short_max_otm_percent DECIMAL(10,4) NOT NULL DEFAULT 20.0000,
    short_open_interest_min INTEGER NOT NULL DEFAULT 10,
    short_volume_min INTEGER NOT NULL DEFAULT 10,
    
    -- Strategy Parameters
    max_net_debit_pct DECIMAL(10,4) NOT NULL DEFAULT 0.5000,
    max_trades INTEGER NOT NULL DEFAULT 5,
    risk_free_rate DECIMAL(10,6) NOT NULL DEFAULT 0.045000,
    type_of_trade VARCHAR(50) NOT NULL DEFAULT 'Poor Mans Covered Call',
    
    -- Management Fields
    is_active BOOLEAN DEFAULT FALSE,
    is_deprecated BOOLEAN DEFAULT FALSE,
    last_accessed_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_leaps_days CHECK (leaps_min_days <= leaps_max_days),
    CONSTRAINT chk_short_days CHECK (short_min_days <= short_max_days),
    CONSTRAINT chk_otm_percent CHECK (short_min_otm_percent <= short_max_otm_percent),
    CONSTRAINT chk_itm_percent CHECK (leaps_min_itm_percent <= leaps_max_itm_percent),
    CONSTRAINT chk_trade_type CHECK (type_of_trade IN ('Poor Mans Covered Call', 'Poor Mans Covered Put'))
);

-- Strategy Favorites Table (Already created in your system)
-- This is just for reference
CREATE TABLE IF NOT EXISTS strategy_favorites (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    price DECIMAL(10,4) NOT NULL,
    
    -- LEAPS Details
    leaps_exp VARCHAR(10) NOT NULL,
    leaps_strike DECIMAL(10,4) NOT NULL,
    leaps_cost DECIMAL(10,2) NOT NULL,
    leaps_delta DECIMAL(5,4) NOT NULL,
    leaps_oi INTEGER NOT NULL,
    leaps_volume INTEGER NOT NULL,
    
    -- Short Option Details
    short_exp VARCHAR(10) NOT NULL,
    short_strike DECIMAL(10,4) NOT NULL,
    short_cost DECIMAL(10,2) NOT NULL,  -- Negative for credit
    short_delta DECIMAL(5,4) NOT NULL,
    short_iv DECIMAL(5,4) NOT NULL,
    short_oi INTEGER NOT NULL,
    short_volume INTEGER NOT NULL,
    
    -- Strategy Metrics
    net_debit DECIMAL(10,2) NOT NULL,
    net_debit_pct DECIMAL(10,4) NOT NULL,
    roc_pct DECIMAL(10,4) NOT NULL,
    pop_pct DECIMAL(10,4) NOT NULL,
    position_delta DECIMAL(5,4) NOT NULL,
    break_even DECIMAL(10,4) NOT NULL,
    type_of_trade VARCHAR(50) NOT NULL,
    
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Options Data Table (Optional - for storing options chain data)
-- You may already have this or use a different structure
CREATE TABLE IF NOT EXISTS options_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    option_type VARCHAR(4) NOT NULL,  -- CALL or PUT
    strike_price DECIMAL(10,4) NOT NULL,
    expiration_date DATE NOT NULL,
    
    -- Pricing
    mark_price DECIMAL(10,4),
    bid_price DECIMAL(10,4),
    ask_price DECIMAL(10,4),
    last_price DECIMAL(10,4),
    
    -- Greeks
    delta DECIMAL(6,5),
    gamma DECIMAL(6,5),
    theta DECIMAL(6,5),
    vega DECIMAL(6,5),
    rho DECIMAL(6,5),
    implied_volatility DECIMAL(6,5),
    
    -- Volume & Interest
    volume INTEGER DEFAULT 0,
    open_interest INTEGER DEFAULT 0,
    
    -- Metadata
    underlying_price DECIMAL(10,4),
    data_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_option_type CHECK (option_type IN ('CALL', 'PUT'))
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_strategy_filter_active ON strategy_filter_criteria(is_active, is_deprecated);
CREATE INDEX IF NOT EXISTS idx_strategy_favorites_symbol ON strategy_favorites(symbol);
CREATE INDEX IF NOT EXISTS idx_strategy_favorites_roc ON strategy_favorites(roc_pct DESC);
CREATE INDEX IF NOT EXISTS idx_strategy_favorites_type ON strategy_favorites(type_of_trade);
CREATE INDEX IF NOT EXISTS idx_options_symbol_exp ON options_data(symbol, expiration_date);
CREATE INDEX IF NOT EXISTS idx_options_type_exp ON options_data(option_type, expiration_date);

-- Insert Default Filter (if not exists)
INSERT INTO strategy_filter_criteria (
    filter_criteria_name, 
    leaps_min_days, leaps_max_days, leaps_min_delta, leaps_min_itm_percent, leaps_max_itm_percent,
    leaps_open_interest_min, leaps_volume_min,
    short_min_days, short_max_days, short_min_otm_percent, short_max_otm_percent,
    short_open_interest_min, short_volume_min,
    max_net_debit_pct, max_trades, risk_free_rate, type_of_trade,
    is_active, is_deprecated
) VALUES (
    'Default PMCC Filter',
    180, 730, 0.7000, 10.0000, 50.0000,
    10, 10,
    30, 45, 3.0000, 20.0000,
    10, 10,
    0.5000, 5, 0.045000, 'Poor Mans Covered Call',
    TRUE, FALSE
)
ON CONFLICT DO NOTHING;

-- Sample Query: Get Active Filter
-- SELECT * FROM strategy_filter_criteria 
-- WHERE is_active = TRUE AND is_deprecated = FALSE 
-- ORDER BY last_accessed_timestamp DESC 
-- LIMIT 1;

-- Sample Query: Get All Favorites Sorted by ROC
-- SELECT * FROM strategy_favorites 
-- ORDER BY roc_pct DESC;

-- Sample Query: Get Options for a Symbol
-- SELECT * FROM options_data 
-- WHERE symbol = 'AAPL' 
-- AND option_type = 'CALL'
-- AND expiration_date >= CURRENT_DATE
-- ORDER BY expiration_date, strike_price;
