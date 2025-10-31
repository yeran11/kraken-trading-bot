"""
Multi-Timeframe Market Analyzer
Fetches and analyzes data across multiple timeframes
Generates comprehensive market context for AI decision-making
"""

from loguru import logger
from datetime import datetime
import time

class MultiTimeframeAnalyzer:
    """
    Analyzes markets across multiple timeframes simultaneously
    Provides rich context to AI for intelligent trading decisions
    """

    def __init__(self, exchange):
        self.exchange = exchange
        self.cache = {}  # Cache recent data to reduce API calls
        self.cache_ttl = 60  # Cache for 60 seconds

    def get_multi_timeframe_data(self, symbol, timeframes):
        """
        Fetch OHLCV data for multiple timeframes
        Returns: dict with timeframe as key, candles as value
        """
        data = {}

        for tf in timeframes:
            try:
                # Check cache first
                cache_key = f"{symbol}_{tf}"
                if cache_key in self.cache:
                    cached_time, cached_data = self.cache[cache_key]
                    if time.time() - cached_time < self.cache_ttl:
                        data[tf] = cached_data
                        logger.debug(f"Using cached {tf} data for {symbol}")
                        continue

                # Fetch from exchange
                limit = self._get_candle_limit(tf)
                candles = self.exchange.fetch_ohlcv(symbol, tf, limit=limit)

                # Cache it
                self.cache[cache_key] = (time.time(), candles)
                data[tf] = candles

                logger.debug(f"Fetched {len(candles)} {tf} candles for {symbol}")

            except Exception as e:
                logger.error(f"Error fetching {tf} data for {symbol}: {e}")
                data[tf] = []

        return data

    def _get_candle_limit(self, timeframe):
        """Get appropriate number of candles for each timeframe"""
        limits = {
            '1m': 120,   # 2 hours
            '5m': 100,   # ~8 hours
            '15m': 100,  # ~1 day
            '1h': 100,   # ~4 days
            '4h': 60,    # 10 days
            '1d': 30     # 1 month
        }
        return limits.get(timeframe, 100)

    def analyze_market_context(self, symbol, multi_tf_data):
        """
        Analyze market across all timeframes to determine overall context
        Returns rich context dict for AI
        """
        context = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'timeframes': {}
        }

        for tf, candles in multi_tf_data.items():
            if not candles or len(candles) < 2:
                continue

            try:
                # Extract basic price action
                closes = [c[4] for c in candles]
                current_price = closes[-1]
                prev_price = closes[-2]

                # Calculate price change
                price_change = ((current_price - prev_price) / prev_price) * 100

                # Simple trend determination
                sma_20 = sum(closes[-20:]) / min(20, len(closes))
                sma_50 = sum(closes[-50:]) / min(50, len(closes)) if len(closes) >= 50 else sma_20

                if sma_20 > sma_50 * 1.02:
                    trend = 'STRONG_UPTREND'
                elif sma_20 > sma_50:
                    trend = 'UPTREND'
                elif sma_20 < sma_50 * 0.98:
                    trend = 'STRONG_DOWNTREND'
                elif sma_20 < sma_50:
                    trend = 'DOWNTREND'
                else:
                    trend = 'SIDEWAYS'

                # Volatility (simple range-based)
                recent_highs = [c[2] for c in candles[-20:]]
                recent_lows = [c[3] for c in candles[-20:]]
                volatility = (max(recent_highs) - min(recent_lows)) / min(recent_lows) * 100

                context['timeframes'][tf] = {
                    'current_price': current_price,
                    'price_change_percent': price_change,
                    'trend': trend,
                    'volatility_percent': volatility,
                    'sma_20': sma_20,
                    'sma_50': sma_50,
                    'num_candles': len(candles)
                }

            except Exception as e:
                logger.error(f"Error analyzing {tf} for {symbol}: {e}")

        # Determine overall market regime
        context['market_regime'] = self._determine_market_regime(context['timeframes'])

        return context

    def _determine_market_regime(self, timeframe_data):
        """
        Determine overall market regime by analyzing multiple timeframes
        """
        if not timeframe_data:
            return 'UNKNOWN'

        # Check if we have key timeframes
        has_daily = '1d' in timeframe_data
        has_4h = '4h' in timeframe_data
        has_1h = '1h' in timeframe_data

        # Daily trend (most important)
        if has_daily:
            daily_trend = timeframe_data['1d']['trend']
            if 'UPTREND' in daily_trend:
                # In uptrend, look for:
                if has_4h and 'UPTREND' in timeframe_data['4h']['trend']:
                    return 'STRONG_BULLISH'  # Daily + 4h aligned
                return 'BULLISH'  # Just daily

            elif 'DOWNTREND' in daily_trend:
                if has_4h and 'DOWNTREND' in timeframe_data['4h']['trend']:
                    return 'STRONG_BEARISH'  # Daily + 4h aligned
                return 'BEARISH'  # Just daily

        # If no daily, check 4h
        elif has_4h:
            trend_4h = timeframe_data['4h']['trend']
            if 'UPTREND' in trend_4h:
                return 'BULLISH_INTRADAY'
            elif 'DOWNTREND' in trend_4h:
                return 'BEARISH_INTRADAY'

        # If no 4h, check 1h
        elif has_1h:
            trend_1h = timeframe_data['1h']['trend']
            if 'UPTREND' in trend_1h:
                return 'BULLISH_SHORT_TERM'
            elif 'DOWNTREND' in trend_1h:
                return 'BEARISH_SHORT_TERM'

        return 'NEUTRAL'

    def get_optimal_strategy_for_conditions(self, market_context):
        """
        Based on market conditions, suggest which strategy is best suited
        This helps AI understand what kind of trade to look for
        """
        regime = market_context.get('market_regime', 'NEUTRAL')
        tf_data = market_context.get('timeframes', {})

        suggestions = []

        # Check for swing trade conditions (multi-day)
        if regime in ['STRONG_BULLISH', 'STRONG_BEARISH']:
            suggestions.append({
                'strategy': 'macd_supertrend',
                'reasoning': f'Strong aligned trend across timeframes ({regime}) - ideal for swing trading',
                'confidence': 0.9
            })

        # Check for day trading conditions
        if '4h' in tf_data:
            volatility_4h = tf_data['4h'].get('volatility_percent', 0)
            if volatility_4h > 3 and volatility_4h < 15:  # Good volatility range
                suggestions.append({
                    'strategy': 'momentum',
                    'reasoning': f'Healthy volatility ({volatility_4h:.1f}%) - good for momentum day trading',
                    'confidence': 0.8
                })

        # Check for mean reversion conditions
        if '1h' in tf_data:
            trend_1h = tf_data['1h'].get('trend', 'SIDEWAYS')
            volatility_1h = tf_data['1h'].get('volatility_percent', 0)
            if trend_1h == 'SIDEWAYS' and volatility_1h < 5:
                suggestions.append({
                    'strategy': 'mean_reversion',
                    'reasoning': 'Sideways market with low volatility - ideal for mean reversion',
                    'confidence': 0.8
                })

        # Check for scalping conditions
        if '5m' in tf_data and '15m' in tf_data:
            volatility_5m = tf_data['5m'].get('volatility_percent', 0)
            trend_15m = tf_data['15m'].get('trend', 'SIDEWAYS')
            if volatility_5m > 2 and 'TREND' in trend_15m:
                suggestions.append({
                    'strategy': 'scalping',
                    'reasoning': f'Good 5m volatility ({volatility_5m:.1f}%) with 15m trend - scalping opportunities',
                    'confidence': 0.7
                })

        return suggestions

    def format_for_ai_analysis(self, symbol, multi_tf_data, market_context, strategy_signals):
        """
        Format all collected data into a comprehensive package for AI
        """
        ai_package = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),

            # Market context across all timeframes
            'market_context': market_context,

            # Raw candle data for each timeframe (AI can see the actual price action)
            'candle_data': {},

            # Strategy signals that triggered
            'strategy_signals': strategy_signals,

            # Suggested optimal strategies based on conditions
            'strategy_suggestions': self.get_optimal_strategy_for_conditions(market_context)
        }

        # Add last N candles for each timeframe (for AI pattern recognition)
        for tf, candles in multi_tf_data.items():
            if candles:
                # Convert last 10 candles to dict format
                ai_package['candle_data'][tf] = [
                    {
                        'timestamp': c[0],
                        'open': c[1],
                        'high': c[2],
                        'low': c[3],
                        'close': c[4],
                        'volume': c[5]
                    }
                    for c in candles[-10:]  # Last 10 candles
                ]

        return ai_package

    def clear_cache(self):
        """Clear all cached data"""
        self.cache = {}
        logger.debug("Multi-timeframe cache cleared")
