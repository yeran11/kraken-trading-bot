"""
Multi-Timeframe Trading Configuration
Defines strategy-specific timeframes and parameters
"""

# ============================================
# STRATEGY TIMEFRAME CONFIGURATIONS
# ============================================
# Each strategy has its optimal timeframe and risk parameters

STRATEGY_CONFIGS = {
    'scalping': {
        'name': 'Scalping (Fast Day Trades)',
        'timeframe': '5m',           # 5-minute candles
        'check_interval': 60,         # Check every 1 minute
        'ai_validation_tf': '15m',    # AI validates on 15-minute context
        'stop_loss_percent': 1.0,     # Tight stop: 1%
        'take_profit_percent': 1.5,   # Quick target: 1.5%
        'min_hold_minutes': 5,        # Hold at least 5 minutes
        'max_hold_minutes': 120,      # Exit after 2 hours if not hit targets
        'description': 'Quick scalps on 5-minute momentum - high frequency, small gains',
        'enabled': True
    },

    'momentum': {
        'name': 'Momentum Day Trading',
        'timeframe': '1h',            # 1-hour candles
        'check_interval': 300,        # Check every 5 minutes
        'ai_validation_tf': '4h',     # AI validates on 4-hour context
        'stop_loss_percent': 2.0,     # Standard stop: 2%
        'take_profit_percent': 3.5,   # Day trade target: 3.5%
        'min_hold_minutes': 60,       # Hold at least 1 hour
        'max_hold_minutes': 720,      # Exit after 12 hours if not hit targets
        'description': 'Ride hourly momentum - medium frequency, medium gains',
        'enabled': True
    },

    'mean_reversion': {
        'name': 'Mean Reversion Intraday',
        'timeframe': '1h',            # 1-hour candles
        'check_interval': 300,        # Check every 5 minutes
        'ai_validation_tf': '4h',     # AI validates on 4-hour context
        'stop_loss_percent': 2.0,     # Standard stop: 2%
        'take_profit_percent': 3.0,   # Reversion target: 3%
        'min_hold_minutes': 30,       # Hold at least 30 minutes
        'max_hold_minutes': 480,      # Exit after 8 hours if not hit targets
        'description': 'Buy dips, sell peaks - medium frequency, quick reversions',
        'enabled': True
    },

    'macd_supertrend': {
        'name': 'MACD+Supertrend Swing Trading',
        'timeframe': '4h',            # 4-hour candles
        'check_interval': 900,        # Check every 15 minutes
        'ai_validation_tf': '1d',     # AI validates on daily context
        'stop_loss_percent': 3.0,     # Wider stop: 3%
        'take_profit_percent': 8.0,   # Bigger target: 8%
        'trailing_stop': True,        # Use trailing stop
        'trailing_activation': 5.0,   # Activate at 5% profit
        'trailing_distance': 3.0,     # Trail 3% below high
        'min_hold_minutes': 240,      # Hold at least 4 hours
        'max_hold_minutes': 10080,    # Exit after 7 days if not hit targets
        'description': 'Multi-day swing trades - low frequency, large gains',
        'enabled': True
    }
}

# ============================================
# AI MULTI-TIMEFRAME ANALYSIS SETTINGS
# ============================================

AI_TIMEFRAME_ANALYSIS = {
    # AI analyzes ALL these timeframes to get full market context
    'macro_trend': '1d',        # Daily: Overall market direction
    'swing_trend': '4h',        # 4-hour: Current swing direction
    'day_trend': '1h',          # Hourly: Intraday trend
    'entry_timing': '15m',      # 15-min: Precise entry timing
    'micro_timing': '5m',       # 5-min: Micro-level price action

    # Number of candles to fetch for each timeframe
    'candles_per_tf': {
        '1d': 30,   # 30 days of context
        '4h': 60,   # 10 days of 4h candles
        '1h': 100,  # ~4 days of hourly data
        '15m': 100, # ~1 day of 15m data
        '5m': 100   # ~8 hours of 5m data
    }
}

# ============================================
# TRADING LOOP CONFIGURATION
# ============================================

TRADING_LOOP_CONFIG = {
    # Main loop checks at the FASTEST strategy interval
    'base_check_interval': 60,  # 1 minute (for scalping)

    # Track last check time for each strategy
    # Strategies checked at their specific intervals
    'strategy_check_intervals': {
        strategy: config['check_interval']
        for strategy, config in STRATEGY_CONFIGS.items()
        if config.get('enabled', True)
    }
}

# ============================================
# POSITION MANAGEMENT RULES
# ============================================

POSITION_RULES = {
    # Can we have multiple positions on the same pair?
    'allow_multiple_strategies_per_pair': False,  # Safer: Only one strategy per pair at a time

    # If False above, which strategy takes priority?
    'strategy_priority': [
        'macd_supertrend',  # Swing trades have priority
        'momentum',         # Then day trades
        'mean_reversion',   # Then mean reversion
        'scalping'          # Scalping lowest priority
    ],

    # Maximum positions per strategy type
    'max_positions_per_strategy': {
        'scalping': 2,          # Max 2 scalp positions
        'momentum': 3,          # Max 3 momentum positions
        'mean_reversion': 2,    # Max 2 mean reversion positions
        'macd_supertrend': 3    # Max 3 swing positions
    },

    # Total maximum positions across all strategies
    'max_total_positions': 6,

    # Position sizing by strategy (% of available capital per trade)
    'position_size_percent': {
        'scalping': 8,          # 8% per scalp (smaller, more frequent)
        'momentum': 12,         # 12% per momentum trade
        'mean_reversion': 10,   # 10% per mean reversion
        'macd_supertrend': 15   # 15% per swing trade (fewer, larger)
    }
}

# ============================================
# HELPER FUNCTIONS
# ============================================

def get_enabled_strategies():
    """Get list of enabled strategies"""
    return [
        strategy for strategy, config in STRATEGY_CONFIGS.items()
        if config.get('enabled', True)
    ]

def get_strategy_config(strategy_name):
    """Get configuration for a specific strategy"""
    return STRATEGY_CONFIGS.get(strategy_name, None)

def get_all_unique_timeframes():
    """Get all unique timeframes used across strategies"""
    timeframes = set()

    # Strategy timeframes
    for config in STRATEGY_CONFIGS.values():
        if config.get('enabled', True):
            timeframes.add(config['timeframe'])
            timeframes.add(config['ai_validation_tf'])

    # AI analysis timeframes
    for tf in AI_TIMEFRAME_ANALYSIS.values():
        if isinstance(tf, str):
            timeframes.add(tf)

    return sorted(list(timeframes))

def should_check_strategy(strategy_name, last_check_times, current_time):
    """Determine if a strategy should be checked based on its interval"""
    config = STRATEGY_CONFIGS.get(strategy_name)
    if not config or not config.get('enabled', True):
        return False

    interval = config['check_interval']
    last_check = last_check_times.get(strategy_name, 0)

    return (current_time - last_check) >= interval
