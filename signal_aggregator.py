"""
Signal Aggregator - Collects and evaluates trading signals across multiple strategies and timeframes
"""

from loguru import logger
import time
from datetime import datetime
from trading_config import STRATEGY_CONFIGS, get_strategy_config, should_check_strategy

class SignalAggregator:
    """
    Aggregates signals from multiple strategies across different timeframes
    Prepares comprehensive analysis for AI decision-making
    """

    def __init__(self, exchange):
        self.exchange = exchange
        self.last_check_times = {}  # Track when each strategy was last checked
        self.recent_signals = {}    # Cache recent signals

    def collect_all_signals(self, symbol, pair_config, strategy_evaluator):
        """
        Collect signals from ALL enabled strategies on their respective timeframes
        Returns list of signal objects with full context
        """
        current_time = time.time()
        enabled_strategies = pair_config.get('strategies', [])
        all_signals = []

        logger.debug(f"Collecting signals for {symbol} from {len(enabled_strategies)} strategies")

        for strategy_name in enabled_strategies:
            # Check if this strategy should run now (based on its interval)
            if not should_check_strategy(strategy_name, self.last_check_times, current_time):
                logger.debug(f"Skipping {strategy_name} - not time to check yet")
                continue

            # Get strategy configuration
            config = get_strategy_config(strategy_name)
            if not config or not config.get('enabled', True):
                continue

            try:
                # Fetch data for this strategy's timeframe
                timeframe = config['timeframe']
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=100)

                if len(ohlcv) < 20:
                    logger.warning(f"{strategy_name}: Not enough {timeframe} data for {symbol}")
                    continue

                # Get current price
                current_price = ohlcv[-1][4]  # Last close

                # Evaluate strategy on its timeframe
                buy_signal = strategy_evaluator(symbol, current_price, [strategy_name], 'BUY', ohlcv)
                sell_signal = strategy_evaluator(symbol, current_price, [strategy_name], 'SELL', ohlcv)

                # If signal detected, package it with full context
                if buy_signal:
                    signal = self._create_signal_package(
                        symbol=symbol,
                        strategy=strategy_name,
                        action='BUY',
                        price=current_price,
                        timeframe=timeframe,
                        config=config,
                        ohlcv=ohlcv
                    )
                    all_signals.append(signal)
                    logger.info(f"📊 {strategy_name} BUY signal on {timeframe}: {symbol} @ ${current_price:.6f}")

                elif sell_signal:
                    signal = self._create_signal_package(
                        symbol=symbol,
                        strategy=strategy_name,
                        action='SELL',
                        price=current_price,
                        timeframe=timeframe,
                        config=config,
                        ohlcv=ohlcv
                    )
                    all_signals.append(signal)
                    logger.info(f"📊 {strategy_name} SELL signal on {timeframe}: {symbol} @ ${current_price:.6f}")

                # Update last check time for this strategy
                self.last_check_times[strategy_name] = current_time

            except Exception as e:
                logger.error(f"Error collecting signal from {strategy_name}: {e}")

        if all_signals:
            logger.success(f"✅ Collected {len(all_signals)} signal(s) for {symbol}")
        else:
            logger.debug(f"No signals for {symbol} at this time")

        return all_signals

    def _create_signal_package(self, symbol, strategy, action, price, timeframe, config, ohlcv):
        """
        Create a comprehensive signal package with all context
        """
        # Calculate some basic technical indicators for context
        closes = [c[4] for c in ohlcv]
        highs = [c[2] for c in ohlcv]
        lows = [c[3] for c in ohlcv]

        sma_20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else price
        sma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else sma_20

        # Recent price action
        price_change_5 = ((closes[-1] - closes[-5]) / closes[-5] * 100) if len(closes) >= 5 else 0
        price_change_20 = ((closes[-1] - closes[-20]) / closes[-20] * 100) if len(closes) >= 20 else 0

        # Volatility
        recent_high = max(highs[-20:]) if len(highs) >= 20 else price
        recent_low = min(lows[-20:]) if len(lows) >= 20 else price
        volatility = ((recent_high - recent_low) / recent_low * 100) if recent_low > 0 else 0

        signal = {
            'symbol': symbol,
            'strategy': strategy,
            'strategy_name': config['name'],
            'action': action,
            'price': price,
            'timeframe': timeframe,
            'timestamp': datetime.now().isoformat(),

            # Risk parameters for this strategy
            'risk_params': {
                'stop_loss_percent': config['stop_loss_percent'],
                'take_profit_percent': config['take_profit_percent'],
                'min_hold_minutes': config['min_hold_minutes'],
                'max_hold_minutes': config.get('max_hold_minutes'),
                'trailing_stop': config.get('trailing_stop', False),
                'trailing_activation': config.get('trailing_activation'),
                'trailing_distance': config.get('trailing_distance')
            },

            # Technical context
            'technical_context': {
                'current_price': price,
                'sma_20': sma_20,
                'sma_50': sma_50,
                'price_vs_sma20': ((price - sma_20) / sma_20 * 100),
                'price_vs_sma50': ((price - sma_50) / sma_50 * 100),
                'price_change_5_candles': price_change_5,
                'price_change_20_candles': price_change_20,
                'volatility_percent': volatility
            },

            # Recent candles (last 10 for AI pattern recognition)
            'recent_candles': [
                {
                    'timestamp': c[0],
                    'open': c[1],
                    'high': c[2],
                    'low': c[3],
                    'close': c[4],
                    'volume': c[5]
                }
                for c in ohlcv[-10:]
            ],

            # Strategy description
            'strategy_description': config['description']
        }

        return signal

    def prioritize_signals(self, signals):
        """
        If multiple signals, prioritize by strategy quality and confidence
        Returns sorted list (best first)
        """
        if not signals:
            return []

        # Priority ranking (higher = more important)
        strategy_priority = {
            'macd_supertrend': 4,   # Swing trades highest priority (best risk/reward)
            'momentum': 3,           # Day trades good priority
            'mean_reversion': 2,     # Mean reversion moderate
            'scalping': 1            # Scalping lowest (noisiest)
        }

        def signal_score(signal):
            """Calculate priority score for a signal"""
            score = 0

            # Strategy base priority
            score += strategy_priority.get(signal['strategy'], 0) * 10

            # Stronger moves get bonus
            technical = signal['technical_context']
            price_change = abs(technical['price_change_20_candles'])
            score += min(price_change, 10)  # Up to +10 for strong moves

            # Trend alignment bonus
            if abs(technical['price_vs_sma20']) > 2:
                score += 5  # Price strongly above/below SMA

            # Lower volatility bonus (more predictable)
            if technical['volatility_percent'] < 5:
                score += 3

            return score

        # Sort by score (highest first)
        sorted_signals = sorted(signals, key=signal_score, reverse=True)

        return sorted_signals

    def get_signal_summary(self, signals):
        """
        Create human-readable summary of all signals
        """
        if not signals:
            return "No trading signals detected"

        summary_lines = [f"Found {len(signals)} trading signal(s):"]

        for i, sig in enumerate(signals, 1):
            action_emoji = "🟢" if sig['action'] == 'BUY' else "🔴"
            summary_lines.append(
                f"{i}. {action_emoji} {sig['strategy_name']} on {sig['timeframe']} - "
                f"{sig['action']} {sig['symbol']} @ ${sig['price']:.6f}"
            )

        return "\n".join(summary_lines)
