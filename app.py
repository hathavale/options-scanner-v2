from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime, timedelta
import logging
import requests
import json
import math
from decimal import Decimal
from typing import Dict, List, Tuple
from itertools import product
from scipy.stats import norm

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database connection
DB_URL = os.environ.get('DATABASE_URL')
if not DB_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Alpha Vantage API Configuration
ALPHAVANTAGE_API_KEY = os.environ.get('ALPHAVANTAGE_API_KEY', '')
if not ALPHAVANTAGE_API_KEY:
    logger.warning("⚠️  ALPHAVANTAGE_API_KEY not set - live data fetching will fail")

ALPHAVANTAGE_BASE_URL = "https://www.alphavantage.co/query"

# Throttling for API calls - Updated for 600 calls/min capacity
last_call = 0
MIN_INTERVAL = 60 / 590  # ~590 calls/min to stay under 600 limit

def throttled_request(url, timeout=30):
    """Make throttled API request for Alpha Vantage"""
    global last_call
    import time
    elapsed = time.time() - last_call
    if elapsed < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - elapsed)
    last_call = time.time()
    return requests.get(url, timeout=timeout)

# ============ Alpha Vantage API Functions ============

def fetch_last_price(symbol: str) -> float:
    """Fetch current stock price from Alpha Vantage"""
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": ALPHAVANTAGE_API_KEY
    }
    url = f"{ALPHAVANTAGE_BASE_URL}?" + "&".join([f"{k}={v}" for k, v in params.items()])
    response = throttled_request(url, timeout=10)
    response.raise_for_status()
    payload = response.json()
    
    if "Note" in payload:
        raise RuntimeError(f"API rate limit reached: {payload['Note']}")
    
    if "Global Quote" not in payload or not payload["Global Quote"]:
        raise RuntimeError(f"No price data for {symbol}")
    
    return float(payload["Global Quote"]["05. price"])

def fetch_options_data(symbol: str) -> List[Dict]:
    """Fetch options chain data from Alpha Vantage"""
    params = {
        "function": "REALTIME_OPTIONS",
        "symbol": symbol,
        "apikey": ALPHAVANTAGE_API_KEY,
        "require_greeks": "true"
    }
    url = f"{ALPHAVANTAGE_BASE_URL}?" + "&".join([f"{k}={v}" for k, v in params.items()])
    response = throttled_request(url, timeout=30)
    response.raise_for_status()
    payload = response.json()
    
    if "Note" in payload:
        raise RuntimeError(f"API rate limit reached: {payload['Note']}")
    
    if "data" not in payload:
        raise RuntimeError(f"Unexpected response format: {payload}")
    
    return payload["data"]

def parse_expiration_date(date_str: str) -> datetime:
    """Parse expiration date string to datetime object"""
    return datetime.strptime(date_str, "%Y-%m-%d")

def find_leaps(
    data: List[Dict],
    current_price: float,
    min_days: int,
    max_days: int,
    itm_min_pct: float,
    itm_max_pct: float,
    min_oi: int,
    min_volume: int,
    option_type: str,
    target_delta: float
) -> List[Tuple]:
    """Filter and find qualifying LEAPS options"""
    today = datetime.now()
    leaps = []
    
    # Debug: Log what we're looking for
    logger.info(f"🔍 find_leaps: Looking for option_type='{option_type}'")
    
    # Debug: Count option types in data
    call_count = sum(1 for opt in data if opt.get("type") == "call")
    put_count = sum(1 for opt in data if opt.get("type") == "put")
    logger.info(f"📊 Available options: {call_count} calls, {put_count} puts")
    
    for option in data:
        if option.get("type") != option_type:
            continue
        
        exp_date = parse_expiration_date(option["expiration"])
        days_to_exp = (exp_date - today).days
        
        if not (min_days <= days_to_exp <= max_days):
            continue
        
        strike = float(option["strike"])
        
        # Calculate ITM percentage
        if option_type == "call":
            itm_pct = ((current_price - strike) / current_price)
        else:
            itm_pct = ((strike - current_price) / current_price)
        
        if not (itm_min_pct <= itm_pct <= itm_max_pct):
            continue
        
        volume = int(option.get("volume", 0))
        if volume < min_volume:
            continue
        
        oi = int(option.get("open_interest", 0))
        if oi < min_oi:
            continue
        
        delta = float(option.get("delta", 0))
        ask = float(option.get("ask", 0))
        
        leaps.append((
            option["expiration"],
            strike,
            ask,
            delta,
            oi,
            volume
        ))
    
    # Sort by delta closest to target
    return sorted(leaps, key=lambda x: abs(x[3] - target_delta))

def find_shorts(
    data: List[Dict],
    current_price: float,
    min_days: int,
    max_days: int,
    otm_min_pct: float,
    otm_max_pct: float,
    min_oi: int,
    min_volume: int,
    option_type: str,
    target_delta: float
) -> List[Tuple]:
    """Filter and find qualifying short options"""
    today = datetime.now()
    shorts = []
    
    # Debug: Log what we're looking for
    logger.info(f"🔍 find_shorts: Looking for option_type='{option_type}'")
    
    for option in data:
        if option.get("type") != option_type:
            continue
        
        exp_date = parse_expiration_date(option["expiration"])
        days_to_exp = (exp_date - today).days
        
        if not (min_days <= days_to_exp <= max_days):
            continue
        
        strike = float(option["strike"])
        
        # Calculate OTM percentage
        if option_type == "call":
            otm_pct = ((strike - current_price) / current_price)
        else:
            otm_pct = ((current_price - strike) / current_price)
        
        if not (otm_min_pct <= otm_pct <= otm_max_pct):
            continue
        
        volume = int(option.get("volume", 0))
        if volume < min_volume:
            continue
        
        oi = int(option.get("open_interest", 0))
        if oi < min_oi:
            continue
        
        delta = float(option.get("delta", 0))
        iv = float(option.get("implied_volatility", 0))
        bid = float(option.get("bid", 0))
        
        shorts.append((
            option["expiration"],
            strike,
            bid,
            delta,
            iv,
            days_to_exp,
            oi,
            volume
        ))
    
    # Sort by delta closest to target
    return sorted(shorts, key=lambda x: abs(x[3] - target_delta))

def calculate_pop(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    """Calculate Probability of Profit using Black-Scholes"""
    if sigma == 0 or T == 0:
        return 1.0 if (S < K if option_type == "call" else S > K) else 0.0
    
    d2 = (math.log(S / K) + (r - 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    
    if option_type == "call":
        return norm.cdf(-d2)
    else:
        return norm.cdf(d2)

def scan_opportunities_alphavantage(
    symbols: List[str],
    type_of_trade: str = 'Poor Mans Covered Call',
    leaps_min_days: int = 365,
    leaps_max_days: int = 730,
    leaps_itm_min_pct: float = 0.10,
    leaps_itm_max_pct: float = 0.50,
    leaps_min_oi: int = 10,
    leaps_min_volume: int = 10,
    short_min_days: int = 30,
    short_max_days: int = 60,
    short_otm_min_pct: float = 0.05,
    short_otm_max_pct: float = 0.15,
    short_min_oi: int = 10,
    short_min_volume: int = 10,
    max_net_debit_pct: float = 0.5,
    max_trades: int = 500,
    risk_free_rate: float = 0.05
) -> List[Dict]:
    """
    Scan for PMCC/PMCP opportunities using Alpha Vantage API
    
    Returns list of opportunities with all metrics calculated
    """
    option_type = "call" if type_of_trade == 'Poor Mans Covered Call' else "put"
    leaps_target_delta = 0.8 if option_type == "call" else -0.8
    short_target_delta = 0.3 if option_type == "call" else -0.3
    
    # Debug: Log the strategy type
    logger.info(f"🎯 Strategy: {type_of_trade} → option_type='{option_type}'")
    logger.info(f"🎯 Target deltas: LEAPS={leaps_target_delta}, SHORT={short_target_delta}")
    
    opportunities = []
    errors = []
    
    for symbol in symbols:
        try:
            logger.info(f"🔍 Fetching data for {symbol}...")
            
            # Fetch current price
            price = fetch_last_price(symbol)
            logger.info(f"💰 {symbol} price: ${price:.2f}")
            
            # Fetch options chain
            options = fetch_options_data(symbol)
            logger.info(f"📊 Fetched {len(options)} options for {symbol}")
            
            # Find qualifying LEAPS
            leaps = find_leaps(
                options, price, leaps_min_days, leaps_max_days,
                leaps_itm_min_pct, leaps_itm_max_pct,
                leaps_min_oi, leaps_min_volume,
                option_type, leaps_target_delta
            )
            logger.info(f"✅ Found {len(leaps)} qualifying LEAPS")
            
            # Find qualifying shorts
            shorts = find_shorts(
                options, price, short_min_days, short_max_days,
                short_otm_min_pct, short_otm_max_pct,
                short_min_oi, short_min_volume,
                option_type, short_target_delta
            )
            logger.info(f"✅ Found {len(shorts)} qualifying shorts")
            
            # Match LEAPS with shorts
            for leap, short in product(leaps[:50], shorts[:50]):
                leaps_exp, leaps_strike, leaps_ask, leaps_delta, leaps_oi, leaps_volume = leap
                short_exp, short_strike, short_bid, short_delta, short_iv, days_to_exp, short_oi, short_volume = short
                
                # Calculate costs
                leaps_cost = leaps_ask * 100
                short_premium = short_bid * 100
                net_debit = leaps_cost - short_premium
                net_debit_pct = net_debit / (price * 100)
                
                # Check net debit threshold
                if net_debit > 0 and net_debit_pct < max_net_debit_pct:
                    # Calculate ROC
                    roc_pct = (short_premium / net_debit) * 100 if net_debit > 0 else 0
                    
                    # Calculate POP
                    T = days_to_exp / 365.0
                    pop = calculate_pop(price, short_strike, T, risk_free_rate, short_iv, option_type)
                    pop_pct = pop * 100
                    
                    # Calculate position delta
                    if option_type == "call":
                        position_delta = leaps_delta - short_delta
                    else:
                        position_delta = leaps_delta + short_delta
                    
                    # Calculate breakeven
                    if option_type == "call":
                        breakeven = leaps_strike + (net_debit / 100)
                    else:
                        breakeven = leaps_strike - (net_debit / 100)
                    
                    opportunities.append({
                        "symbol": symbol,
                        "price": price,
                        "leaps_exp": leaps_exp,
                        "leaps_strike": leaps_strike,
                        "leaps_cost": leaps_cost,
                        "leaps_delta": leaps_delta,
                        "leaps_oi": leaps_oi,
                        "leaps_volume": leaps_volume,
                        "short_exp": short_exp,
                        "short_strike": short_strike,
                        "short_premium": short_premium,
                        "short_delta": short_delta,
                        "short_iv": short_iv,
                        "short_oi": short_oi,
                        "short_volume": short_volume,
                        "net_debit": net_debit,
                        "net_debit_pct": net_debit_pct * 100,
                        "roc_pct": roc_pct,
                        "pop_pct": pop_pct,
                        "position_delta": position_delta,
                        "breakeven": breakeven,
                        "type_of_trade": type_of_trade
                    })
        
        except Exception as e:
            error_msg = f"Error processing {symbol}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            errors.append({"symbol": symbol, "error": str(e)})
    
    # Sort by ROC
    opportunities.sort(key=lambda x: x["roc_pct"], reverse=True)
    
    # Limit results
    opportunities = opportunities[:max_trades]
    
    logger.info(f"🎯 Total opportunities found: {len(opportunities)}")
    
    return opportunities, errors

def initialize_default_filter():
    """Create default filter if none exists"""
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    # Check if any non-deprecated filters exist
    cur.execute("SELECT COUNT(*) FROM strategy_filter_criteria WHERE is_deprecated = FALSE")
    count = cur.fetchone()[0]
    
    if count == 0:
        logger.info("📝 Creating default strategy filter...")
        cur.execute("""
            INSERT INTO strategy_filter_criteria (
                filter_criteria_name, leaps_min_days, leaps_max_days,
                leaps_min_delta, leaps_min_itm_percent, leaps_max_itm_percent,
                short_min_days, short_max_days,
                short_min_otm_percent, short_max_otm_percent,
                leaps_open_interest_min, short_open_interest_min,
                leaps_volume_min, short_volume_min,
                max_net_debit_pct, max_trades, risk_free_rate,
                type_of_trade, is_active, is_deprecated, 
                last_accessed_timestamp, date_created, date_modified
            ) VALUES (
                'Default PMCC Filter', 180, 730,
                0.70, 10.0, 50.0,
                30, 45,
                3.0, 20.0,
                10, 10,
                10, 10,
                0.5000, 5, 0.045,
                'Poor Mans Covered Call', TRUE, FALSE,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        logger.info("✅ Default filter created")
    
    cur.close()
    conn.close()

def get_active_filter():
    """Get the currently active filter criteria"""
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT * FROM strategy_filter_criteria 
            WHERE is_active = TRUE AND is_deprecated = FALSE
            ORDER BY last_accessed_timestamp DESC
            LIMIT 1
        """)
        
        filter_criteria = cur.fetchone()
        cur.close()
        conn.close()
        
        if not filter_criteria:
            logger.warning("⚠️  No active filter found, initializing default...")
            initialize_default_filter()
            return get_active_filter()
        
        return dict(filter_criteria)
    except Exception as e:
        logger.error(f"❌ Error getting active filter: {str(e)}")
        return None

def screener(symbol, underlying_price, filter_criteria, options_data=None):
    """
    Screen options for strategy opportunities (PMCC/PMCP)
    
    Args:
        symbol: Stock symbol
        underlying_price: Current stock price
        filter_criteria: Filter criteria dict
        options_data: Optional list of options data dicts
    
    Returns:
        tuple: (list of opportunities, filtering_stats dict)
    """
    logger.info(f"🔍 Starting screening for {symbol}")
    
    opportunities = []
    rejection_stats = {
        'total_calls': 0,
        'leaps_rejections': {'days': 0, 'delta': 0, 'itm': 0, 'oi': 0, 'volume': 0},
        'short_rejections': {'days': 0, 'otm': 0, 'oi': 0, 'volume': 0},
        'match_rejections': {'net_debit': 0, 'delta_comparison': 0}
    }
    
    # Use in-memory data if provided
    if options_data is not None:
        all_calls = [opt for opt in options_data 
                     if opt.get('option_type') == 'CALL' 
                     and opt.get('expiration_date') >= datetime.now().date()]
        logger.info(f"📊 Found {len(all_calls)} total CALL options")
    else:
        # Query from database
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT * FROM options_data 
            WHERE symbol = %s 
            AND option_type = 'CALL'
            AND expiration_date >= CURRENT_DATE
            ORDER BY expiration_date, strike_price
        """, (symbol,))
        all_calls = cur.fetchall()
        cur.close()
        conn.close()
        logger.info(f"📊 Queried {len(all_calls)} CALL options from database")
    
    rejection_stats['total_calls'] = len(all_calls)
    
    # Filter LEAPS (Long calls)
    leaps = []
    for opt in all_calls:
        days_to_exp = (opt['expiration_date'] - datetime.now().date()).days
        
        # Check DTE criteria
        if not (filter_criteria['leaps_min_days'] <= days_to_exp <= filter_criteria['leaps_max_days']):
            rejection_stats['leaps_rejections']['days'] += 1
            continue
        
        # Check delta criteria
        if opt.get('delta') and opt['delta'] < filter_criteria['leaps_min_delta']:
            rejection_stats['leaps_rejections']['delta'] += 1
            continue
        
        # Check ITM percentage
        if underlying_price > 0:
            strike_price = float(opt['strike_price'])
            itm_percent = ((underlying_price - strike_price) / underlying_price) * 100
            
            if itm_percent < filter_criteria['leaps_min_itm_percent']:
                rejection_stats['leaps_rejections']['itm'] += 1
                continue
        
        # Check OI and Volume
        if opt.get('open_interest', 0) < filter_criteria['leaps_open_interest_min']:
            rejection_stats['leaps_rejections']['oi'] += 1
            continue
        
        if opt.get('volume', 0) < filter_criteria['leaps_volume_min']:
            rejection_stats['leaps_rejections']['volume'] += 1
            continue
        
        leaps.append(opt)
    
    logger.info(f"✅ Found {len(leaps)} qualifying LEAPS out of {len(all_calls)} total")
    
    # Filter SHORT calls
    short_calls = []
    for opt in all_calls:
        days_to_exp = (opt['expiration_date'] - datetime.now().date()).days
        
        # Check DTE criteria
        if not (filter_criteria['short_min_days'] <= days_to_exp <= filter_criteria['short_max_days']):
            rejection_stats['short_rejections']['days'] += 1
            continue
        
        # Check OTM percentage
        if underlying_price > 0:
            strike_price = float(opt['strike_price'])
            otm_percent = ((strike_price - underlying_price) / underlying_price) * 100
            
            if not (filter_criteria['short_min_otm_percent'] <= otm_percent <= filter_criteria['short_max_otm_percent']):
                rejection_stats['short_rejections']['otm'] += 1
                continue
        
        # Check OI and Volume
        if opt.get('open_interest', 0) < filter_criteria['short_open_interest_min']:
            rejection_stats['short_rejections']['oi'] += 1
            continue
        
        if opt.get('volume', 0) < filter_criteria['short_volume_min']:
            rejection_stats['short_rejections']['volume'] += 1
            continue
        
        short_calls.append(opt)
    
    logger.info(f"✅ Found {len(short_calls)} qualifying SHORT calls out of {len(all_calls)} total")
    
    # Match LEAPS with SHORT calls
    for leap in leaps:
        best_matches = []
        
        for short in short_calls:
            # Ensure short expires before LEAP
            if short['expiration_date'] >= leap['expiration_date']:
                continue
            
            # Ensure short strike > leap strike
            if float(short['strike_price']) <= float(leap['strike_price']):
                continue
            
            # Calculate net debit
            leap_cost = float(leap.get('mark_price', 0))
            short_credit = float(short.get('mark_price', 0))
            net_debit = leap_cost - short_credit
            
            # Check max net debit percentage
            if underlying_price > 0:
                net_debit_pct = (net_debit / underlying_price)
                if net_debit_pct > filter_criteria['max_net_debit_pct']:
                    rejection_stats['match_rejections']['net_debit'] += 1
                    continue
            else:
                net_debit_pct = 0
            
            # Calculate metrics
            max_profit = float(short['strike_price']) - float(leap['strike_price']) - net_debit
            breakeven = float(leap['strike_price']) + net_debit
            
            if net_debit > 0:
                roc_pct = (max_profit / net_debit) * 100
            else:
                roc_pct = 0
            
            # Calculate position delta
            leap_delta = float(leap.get('delta', 0))
            short_delta = float(short.get('delta', 0))
            position_delta = leap_delta - short_delta
            
            # Calculate POP (simplified - assumes short delta as rough POP)
            pop_pct = (1 - abs(short_delta)) * 100
            
            opportunity = {
                'symbol': symbol,
                'underlying_price': underlying_price,
                'leaps_strike': float(leap['strike_price']),
                'leaps_price': leap_cost,
                'leaps_expiration': leap['expiration_date'].strftime('%Y-%m-%d'),
                'leaps_days_to_expiration': (leap['expiration_date'] - datetime.now().date()).days,
                'leaps_delta': leap_delta,
                'leaps_open_interest': leap.get('open_interest', 0),
                'leaps_volume': leap.get('volume', 0),
                'short_strike': float(short['strike_price']),
                'short_price': short_credit,
                'short_expiration': short['expiration_date'].strftime('%Y-%m-%d'),
                'short_days_to_expiration': (short['expiration_date'] - datetime.now().date()).days,
                'short_delta': short_delta,
                'short_iv': float(short.get('implied_volatility', 0)),
                'short_open_interest': short.get('open_interest', 0),
                'short_volume': short.get('volume', 0),
                'net_debit': net_debit,
                'net_debit_pct': net_debit_pct * 100,
                'max_profit': max_profit,
                'roc_pct': roc_pct,
                'pop_pct': pop_pct,
                'position_delta': position_delta,
                'breakeven': breakeven,
                'type_of_trade': filter_criteria['type_of_trade']
            }
            
            best_matches.append(opportunity)
        
        # Sort by ROC and take top 5 per LEAP
        best_matches.sort(key=lambda x: x['roc_pct'], reverse=True)
        opportunities.extend(best_matches[:5])
    
    # Sort all opportunities by ROC
    opportunities.sort(key=lambda x: x['roc_pct'], reverse=True)
    
    # Limit to max_trades
    if filter_criteria.get('max_trades'):
        opportunities = opportunities[:filter_criteria['max_trades']]
    
    logger.info(f"🎯 Found {len(opportunities)} total opportunities")
    
    filtering_stats = {
        'total_calls': rejection_stats['total_calls'],
        'leaps_rejections': rejection_stats['leaps_rejections'],
        'short_rejections': rejection_stats['short_rejections'],
        'match_rejections': rejection_stats['match_rejections']
    }
    
    return opportunities, filtering_stats

# ============ API Routes for Filter Management ============

@app.route('/api/filters', methods=['GET'])
def get_filters():
    """Get all non-deprecated filters"""
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT * FROM strategy_filter_criteria 
            WHERE is_deprecated = FALSE
            ORDER BY last_accessed_timestamp DESC
        """)
        filters = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify([dict(f) for f in filters])
    except Exception as e:
        logger.error(f"Error getting filters: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/filters/<int:filter_id>', methods=['GET'])
def get_filter(filter_id):
    """Get specific filter by ID"""
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT * FROM strategy_filter_criteria 
            WHERE id = %s AND is_deprecated = FALSE
        """, (filter_id,))
        filter_data = cur.fetchone()
        cur.close()
        conn.close()
        
        if filter_data:
            return jsonify(dict(filter_data))
        else:
            return jsonify({'error': 'Filter not found'}), 404
    except Exception as e:
        logger.error(f"Error getting filter: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/filters', methods=['POST'])
def create_or_update_filter():
    """Create new filter or update existing one"""
    try:
        data = request.json
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        if data.get('id'):
            # Update existing filter
            cur.execute("""
                UPDATE strategy_filter_criteria SET
                    filter_criteria_name = %s,
                    leaps_min_days = %s, leaps_max_days = %s,
                    leaps_min_delta = %s, leaps_min_itm_percent = %s, leaps_max_itm_percent = %s,
                    short_min_days = %s, short_max_days = %s,
                    short_min_otm_percent = %s, short_max_otm_percent = %s,
                    leaps_open_interest_min = %s, short_open_interest_min = %s,
                    leaps_volume_min = %s, short_volume_min = %s,
                    max_net_debit_pct = %s, max_trades = %s, risk_free_rate = %s,
                    type_of_trade = %s, date_modified = CURRENT_TIMESTAMP,
                    last_accessed_timestamp = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id
            """, (
                data['filter_criteria_name'],
                data['leaps_min_days'], data['leaps_max_days'],
                data['leaps_min_delta'], data['leaps_min_itm_percent'], 
                data.get('leaps_max_itm_percent', 50.0),
                data['short_min_days'], data['short_max_days'],
                data['short_min_otm_percent'], data['short_max_otm_percent'],
                data['leaps_open_interest_min'], data['short_open_interest_min'],
                data['leaps_volume_min'], data['short_volume_min'],
                data['max_net_debit_pct'], data['max_trades'], data['risk_free_rate'],
                data['type_of_trade'], data['id']
            ))
            result = cur.fetchone()
        else:
            # Create new filter
            cur.execute("""
                INSERT INTO strategy_filter_criteria (
                    filter_criteria_name, leaps_min_days, leaps_max_days,
                    leaps_min_delta, leaps_min_itm_percent, leaps_max_itm_percent,
                    short_min_days, short_max_days,
                    short_min_otm_percent, short_max_otm_percent,
                    leaps_open_interest_min, short_open_interest_min,
                    leaps_volume_min, short_volume_min,
                    max_net_debit_pct, max_trades, risk_free_rate,
                    type_of_trade, is_active, is_deprecated,
                    date_created, date_modified, last_accessed_timestamp
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, FALSE, FALSE,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                RETURNING id
            """, (
                data['filter_criteria_name'],
                data['leaps_min_days'], data['leaps_max_days'],
                data['leaps_min_delta'], data['leaps_min_itm_percent'],
                data.get('leaps_max_itm_percent', 50.0),
                data['short_min_days'], data['short_max_days'],
                data['short_min_otm_percent'], data['short_max_otm_percent'],
                data['leaps_open_interest_min'], data['short_open_interest_min'],
                data['leaps_volume_min'], data['short_volume_min'],
                data['max_net_debit_pct'], data['max_trades'], data['risk_free_rate'],
                data['type_of_trade']
            ))
            result = cur.fetchone()
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'id': result['id'], 'success': True})
    except Exception as e:
        logger.error(f"Error creating/updating filter: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/filters/<int:filter_id>', methods=['DELETE'])
def delete_filter(filter_id):
    """Soft delete a filter by marking as deprecated"""
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("""
            UPDATE strategy_filter_criteria 
            SET is_deprecated = TRUE, date_modified = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (filter_id,))
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error deleting filter: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/filters/<int:filter_id>/activate', methods=['POST'])
def activate_filter(filter_id):
    """Set a filter as active (deactivate others)"""
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # Deactivate all filters
        cur.execute("UPDATE strategy_filter_criteria SET is_active = FALSE")
        
        # Activate selected filter
        cur.execute("""
            UPDATE strategy_filter_criteria 
            SET is_active = TRUE, last_accessed_timestamp = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (filter_id,))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error activating filter: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============ API Route for Scanning ============

@app.route('/api/scan', methods=['POST'])
def scan_opportunities():
    """Trigger scan for symbols using Alpha Vantage API"""
    try:
        data = request.json
        symbols = [s.strip().upper() for s in data.get('symbols', '').split(',') if s.strip()]
        
        if not symbols:
            return jsonify({'error': 'No symbols provided'}), 400
        
        if not ALPHAVANTAGE_API_KEY:
            return jsonify({'error': 'ALPHAVANTAGE_API_KEY not configured. Please set it in your .env file.'}), 500
        
        # Use filter criteria from request if provided, otherwise use active filter from database
        filter_criteria = data.get('filter_criteria')
        if not filter_criteria:
            filter_criteria = get_active_filter()
            if not filter_criteria:
                return jsonify({'error': 'No active filter found'}), 400
        
        logger.info(f"🚀 Starting scan for symbols: {', '.join(symbols)}")
        logger.info(f"📋 Using strategy: {filter_criteria.get('type_of_trade', 'Not specified')}")
        
        # Map filter criteria to Alpha Vantage function parameters
        opportunities, errors = scan_opportunities_alphavantage(
            symbols=symbols,
            type_of_trade=filter_criteria['type_of_trade'],
            leaps_min_days=filter_criteria['leaps_min_days'],
            leaps_max_days=filter_criteria.get('leaps_max_days', 730),
            leaps_itm_min_pct=filter_criteria['leaps_min_itm_percent'] / 100,
            leaps_itm_max_pct=filter_criteria.get('leaps_max_itm_percent', 50.0) / 100,
            leaps_min_oi=filter_criteria['leaps_open_interest_min'],
            leaps_min_volume=filter_criteria['leaps_volume_min'],
            short_min_days=filter_criteria['short_min_days'],
            short_max_days=filter_criteria['short_max_days'],
            short_otm_min_pct=filter_criteria['short_min_otm_percent'] / 100,
            short_otm_max_pct=filter_criteria['short_max_otm_percent'] / 100,
            short_min_oi=filter_criteria['short_open_interest_min'],
            short_min_volume=filter_criteria['short_volume_min'],
            max_net_debit_pct=filter_criteria['max_net_debit_pct'],
            max_trades=filter_criteria['max_trades'],
            risk_free_rate=float(filter_criteria['risk_free_rate'])
        )
        
        # Format results for UI
        all_results = []
        symbols_with_data = set()
        
        for opp in opportunities:
            symbol = opp['symbol']
            symbols_with_data.add(symbol)
            
            # Find or create result entry for this symbol
            result = next((r for r in all_results if r['symbol'] == symbol), None)
            if not result:
                result = {
                    'symbol': symbol,
                    'underlying_price': opp['price'],
                    'opportunities_found': 0,
                    'opportunities': []
                }
                all_results.append(result)
            
            # Add opportunity in the format expected by UI
            # Calculate max profit if not already calculated
            max_profit = opp['short_strike'] - opp['leaps_strike'] - (opp['net_debit'] / 100)
            
            result['opportunities'].append({
                'symbol': symbol,
                'underlying_price': opp['price'],
                'leaps_strike': opp['leaps_strike'],
                'leaps_price': opp['leaps_cost'] / 100,  # Convert back to per-share
                'leaps_expiration': opp['leaps_exp'],
                'leaps_days_to_expiration': (parse_expiration_date(opp['leaps_exp']) - datetime.now()).days,
                'leaps_delta': opp['leaps_delta'],
                'leaps_open_interest': opp['leaps_oi'],
                'leaps_volume': opp['leaps_volume'],
                'short_strike': opp['short_strike'],
                'short_price': opp['short_premium'] / 100,  # Convert back to per-share
                'short_expiration': opp['short_exp'],
                'short_days_to_expiration': (parse_expiration_date(opp['short_exp']) - datetime.now()).days,
                'short_delta': opp['short_delta'],
                'short_iv': opp['short_iv'],
                'short_open_interest': opp['short_oi'],
                'short_volume': opp['short_volume'],
                'net_debit': opp['net_debit'],
                'net_debit_pct': opp['net_debit_pct'],
                'max_profit': max_profit * 100,  # Convert to total contract value
                'roc_pct': opp['roc_pct'],
                'pop_pct': opp['pop_pct'],
                'position_delta': opp['position_delta'],
                'breakeven': opp['breakeven'],
                'type_of_trade': opp['type_of_trade']
            })
            result['opportunities_found'] = len(result['opportunities'])
        
        # Add symbols that had errors
        for error in errors:
            if error['symbol'] not in symbols_with_data:
                all_results.append({
                    'symbol': error['symbol'],
                    'underlying_price': 0,
                    'opportunities_found': 0,
                    'opportunities': [],
                    'error': error['error']
                })
        
        response = {
            'success': True,
            'symbols_processed': len(symbols),
            'total_opportunities': len(opportunities),
            'results': all_results
        }
        
        if errors:
            response['errors'] = errors
        
        logger.info(f"✅ Scan complete: {len(opportunities)} opportunities found")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Error scanning: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ============ Favorites API Routes ============

@app.route('/api/favorites', methods=['GET'])
def get_favorites():
    """Get all favorites with optional sorting and filtering"""
    try:
        # Get query parameters
        sort_field_1 = request.args.get('sort_field_1', 'roc_pct')
        sort_order_1 = request.args.get('sort_order_1', 'DESC')
        sort_field_2 = request.args.get('sort_field_2', '')
        sort_order_2 = request.args.get('sort_order_2', 'DESC')
        filter_field = request.args.get('filter_field', '')
        filter_value = request.args.get('filter_value', '')
        
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Build query
        query = "SELECT * FROM strategy_favorites WHERE 1=1"
        params = []
        
        if filter_field and filter_value:
            query += f" AND {filter_field} = %s"
            params.append(filter_value)
        
        # Add sorting
        order_by = []
        if sort_field_1:
            order_by.append(f"{sort_field_1} {sort_order_1}")
        if sort_field_2:
            order_by.append(f"{sort_field_2} {sort_order_2}")
        
        if order_by:
            query += " ORDER BY " + ", ".join(order_by)
        
        cur.execute(query, params)
        favorites = cur.fetchall()
        cur.close()
        conn.close()
        
        # Convert Decimal to float for JSON serialization
        result = []
        for fav in favorites:
            fav_dict = dict(fav)
            for key, value in fav_dict.items():
                if isinstance(value, Decimal):
                    fav_dict[key] = float(value)
            result.append(fav_dict)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting favorites: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/favorites', methods=['POST'])
def add_favorite():
    """Add opportunity to favorites"""
    try:
        data = request.json
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            INSERT INTO strategy_favorites (
                symbol, price, leaps_exp, leaps_strike, leaps_cost,
                leaps_delta, leaps_oi, leaps_volume,
                short_exp, short_strike, short_cost, short_delta,
                short_iv, short_oi, short_volume,
                net_debit, net_debit_pct, roc_pct, pop_pct,
                position_delta, break_even, type_of_trade
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s
            )
            RETURNING id
        """, (
            data['symbol'], data['underlying_price'],
            data['leaps_expiration'], data['leaps_strike'], data['leaps_price'],
            data['leaps_delta'], data['leaps_open_interest'], data['leaps_volume'],
            data['short_expiration'], data['short_strike'], -data['short_price'],
            data['short_delta'], data['short_iv'],
            data['short_open_interest'], data['short_volume'],
            data['net_debit'], data['net_debit_pct'], data['roc_pct'],
            data['pop_pct'], data['position_delta'], data['breakeven'],
            data['type_of_trade']
        ))
        
        result = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'id': result['id'], 'success': True})
    except Exception as e:
        logger.error(f"Error adding favorite: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/favorites/<int:favorite_id>', methods=['DELETE'])
def delete_favorite(favorite_id):
    """Delete a favorite"""
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("DELETE FROM strategy_favorites WHERE id = %s", (favorite_id,))
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error deleting favorite: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/favorites/field-values/<field>', methods=['GET'])
def get_favorite_field_values(field):
    """Get distinct values for a field in favorites"""
    try:
        allowed_fields = ['symbol', 'leaps_strike', 'short_strike', 'type_of_trade']
        if field not in allowed_fields:
            return jsonify({'error': 'Invalid field'}), 400
        
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(f"SELECT DISTINCT {field} FROM strategy_favorites ORDER BY {field}")
        values = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        
        return jsonify({'values': values})
    except Exception as e:
        logger.error(f"Error getting field values: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============ Main Routes ============

@app.route('/', methods=['GET'])
def index():
    """Main page"""
    logger.info("="*80)
    logger.info(f"📥 Received GET request to /")
    logger.info("📄 Rendering initial page")
    
    # Get active filter
    filter_criteria = get_active_filter()
    
    logger.info(f"🎨 Rendering template")
    logger.info("="*80 + "\n")
    
    return render_template('index.html', filter_criteria=filter_criteria)

@app.route('/favorites', methods=['GET'])
def favorites_page():
    """Favorites page"""
    return render_template('favorites.html')

# Initialize default filter on startup
with app.app_context():
    try:
        initialize_default_filter()
        logger.info("✅ Application initialized successfully")
    except Exception as e:
        logger.error(f"❌ Error initializing application: {str(e)}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)
