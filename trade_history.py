"""
Trade History Database - Performance Tracking and Learning
Stores all trades for performance analysis and AI feedback loops
"""
import sqlite3
import json
from datetime import datetime, timedelta
from loguru import logger
import os

class TradeHistory:
    """Persistent trade history with performance analytics."""

    def __init__(self, db_path='trade_history.db'):
        self.db_path = db_path
        self._init_database()
        logger.success(f"✓ Trade history database initialized: {db_path}")

    def _init_database(self):
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                strategy TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                quantity REAL NOT NULL,
                entry_time TIMESTAMP NOT NULL,
                exit_time TIMESTAMP,
                pnl_usd REAL,
                pnl_percent REAL,
                outcome TEXT,
                ai_confidence REAL,
                ai_reasoning TEXT,
                ai_position_size REAL,
                ai_stop_loss REAL,
                ai_take_profit REAL,
                exit_reason TEXT,
                market_regime TEXT,
                volatility_regime TEXT
            )
        ''')

        # Index for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_exit_time ON trades(exit_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_strategy ON trades(strategy)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_outcome ON trades(outcome)')

        conn.commit()
        conn.close()

    def record_entry(self, symbol: str, strategy: str, entry_price: float,
                     quantity: float, ai_result: dict):
        """
        Record a new trade entry.

        Args:
            symbol: Trading pair
            strategy: Strategy name
            entry_price: Entry price
            quantity: Quantity purchased
            ai_result: AI decision with confidence, reasoning, parameters

        Returns:
            trade_id: Database ID for this trade
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO trades (
                symbol, strategy, entry_price, quantity, entry_time,
                ai_confidence, ai_reasoning, ai_position_size,
                ai_stop_loss, ai_take_profit, market_regime, volatility_regime
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            symbol,
            strategy,
            entry_price,
            quantity,
            datetime.now(),
            ai_result.get('confidence', 0.0),
            ai_result.get('reasoning', ''),
            ai_result.get('position_size_percent', 0.0),
            ai_result.get('stop_loss_percent', 0.0),
            ai_result.get('take_profit_percent', 0.0),
            ai_result.get('market_regime', 'UNKNOWN'),
            ai_result.get('volatility_regime', 'UNKNOWN')
        ))

        trade_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"📝 Trade entry recorded: ID={trade_id}, {symbol}")
        return trade_id

    def record_exit(self, trade_id: int, exit_price: float, exit_reason: str):
        """
        Record trade exit and calculate P&L.

        Args:
            trade_id: Database ID of the trade
            exit_price: Exit price
            exit_reason: Reason for exit (STOP_LOSS, TAKE_PROFIT, STRATEGY, etc.)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get entry data
        cursor.execute('''
            SELECT entry_price, quantity, symbol
            FROM trades
            WHERE id = ?
        ''', (trade_id,))

        row = cursor.fetchone()
        if not row:
            logger.error(f"Trade ID {trade_id} not found!")
            conn.close()
            return

        entry_price, quantity, symbol = row

        # Calculate P&L
        pnl_usd = (exit_price - entry_price) * quantity
        pnl_percent = ((exit_price - entry_price) / entry_price) * 100
        outcome = 'WIN' if pnl_usd > 0 else 'LOSS'

        # Update record
        cursor.execute('''
            UPDATE trades
            SET exit_price = ?, exit_time = ?, pnl_usd = ?,
                pnl_percent = ?, outcome = ?, exit_reason = ?
            WHERE id = ?
        ''', (exit_price, datetime.now(), pnl_usd, pnl_percent, outcome, exit_reason, trade_id))

        conn.commit()
        conn.close()

        logger.info(f"📝 Trade exit recorded: ID={trade_id}, {symbol}, P&L: ${pnl_usd:+.2f} ({pnl_percent:+.2f}%)")

    def get_recent_performance(self, limit: int = 50):
        """
        Get performance summary of recent closed trades.

        Args:
            limit: Number of recent trades to analyze

        Returns:
            dict: Comprehensive performance metrics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM trades
            WHERE exit_time IS NOT NULL
            ORDER BY exit_time DESC
            LIMIT ?
        ''', (limit,))

        trades = cursor.fetchall()
        conn.close()

        if not trades:
            logger.warning("No closed trades found for performance analysis")
            return None

        # Parse trades
        total_trades = len(trades)
        wins = sum(1 for t in trades if t[10] == 'WIN')  # outcome column
        win_rate = (wins / total_trades) * 100

        # Calculate average win/loss
        winning_trades = [t for t in trades if t[10] == 'WIN']
        losing_trades = [t for t in trades if t[10] == 'LOSS']

        avg_win = sum(t[9] for t in winning_trades) / len(winning_trades) if winning_trades else 0  # pnl_percent
        avg_loss = sum(t[9] for t in losing_trades) / len(losing_trades) if losing_trades else 0

        # Profit factor
        total_wins = sum(t[8] for t in winning_trades)  # pnl_usd
        total_losses = abs(sum(t[8] for t in losing_trades))
        profit_factor = total_wins / total_losses if total_losses > 0 else 0

        # Strategy performance
        strategy_stats = {}
        for trade in trades:
            strategy = trade[2]
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {'wins': 0, 'total': 0}

            strategy_stats[strategy]['total'] += 1
            if trade[10] == 'WIN':
                strategy_stats[strategy]['wins'] += 1

        for strategy in strategy_stats:
            stats = strategy_stats[strategy]
            stats['win_rate'] = (stats['wins'] / stats['total']) * 100 if stats['total'] > 0 else 0

        # Confidence calibration
        confidence_buckets = {
            '55-65': {'correct': 0, 'total': 0, 'wins': 0},
            '66-75': {'correct': 0, 'total': 0, 'wins': 0},
            '76-100': {'correct': 0, 'total': 0, 'wins': 0}
        }

        for trade in trades:
            confidence = trade[11] * 100 if trade[11] else 0  # ai_confidence
            outcome = trade[10]

            if 55 <= confidence < 66:
                bucket = '55-65'
            elif 66 <= confidence < 76:
                bucket = '66-75'
            else:
                bucket = '76-100'

            confidence_buckets[bucket]['total'] += 1
            if outcome == 'WIN':
                confidence_buckets[bucket]['wins'] += 1

        for bucket in confidence_buckets:
            stats = confidence_buckets[bucket]
            if stats['total'] > 0:
                stats['win_rate'] = (stats['wins'] / stats['total']) * 100
            else:
                stats['win_rate'] = 0

        # Best and worst trades
        best_trade = max(trades, key=lambda t: t[9] if t[9] else -999)  # pnl_percent
        worst_trade = min(trades, key=lambda t: t[9] if t[9] else 999)

        return {
            'total_trades': total_trades,
            'wins': wins,
            'losses': total_trades - wins,
            'win_rate': win_rate,
            'avg_win_percent': avg_win,
            'avg_loss_percent': avg_loss,
            'profit_factor': profit_factor,
            'total_pnl_usd': sum(t[8] for t in trades if t[8]),
            'strategy_performance': strategy_stats,
            'confidence_calibration': confidence_buckets,
            'best_trade': {
                'symbol': best_trade[1],
                'pnl_percent': best_trade[9],
                'strategy': best_trade[2]
            },
            'worst_trade': {
                'symbol': worst_trade[1],
                'pnl_percent': worst_trade[9],
                'strategy': worst_trade[2]
            }
        }

    def get_performance_for_prompt(self, limit: int = 50):
        """
        Format recent performance for inclusion in DeepSeek prompt.

        Returns:
            str: Formatted performance summary for AI context
        """
        perf = self.get_recent_performance(limit)

        if not perf:
            return "\n**NO HISTORICAL PERFORMANCE DATA AVAILABLE**\n"

        # Find best and worst strategies
        if perf['strategy_performance']:
            best_strategy = max(perf['strategy_performance'].items(),
                              key=lambda x: x[1]['win_rate'])
            worst_strategy = min(perf['strategy_performance'].items(),
                                key=lambda x: x[1]['win_rate'])
        else:
            best_strategy = ('Unknown', {'win_rate': 0})
            worst_strategy = ('Unknown', {'win_rate': 0})

        strategy_breakdown = "\n".join([
            f"  - {strategy.replace('_', ' ').title()}: {stats['win_rate']:.1f}% ({stats['wins']}/{stats['total']} trades)"
            for strategy, stats in perf['strategy_performance'].items()
        ])

        confidence_breakdown = "\n".join([
            f"  - {bucket}% confidence: {stats['win_rate']:.1f}% accurate ({stats['wins']}/{stats['total']} trades)"
            for bucket, stats in perf['confidence_calibration'].items()
            if stats['total'] > 0
        ])

        prompt_section = f"""
**YOUR RECENT PERFORMANCE (LAST {perf['total_trades']} TRADES):**
- Overall Win Rate: {perf['win_rate']:.1f}%
- Wins: {perf['wins']} | Losses: {perf['losses']}
- Average Win: +{perf['avg_win_percent']:.2f}%
- Average Loss: {perf['avg_loss_percent']:.2f}%
- Profit Factor: {perf['profit_factor']:.2f}
- Total P&L: ${perf['total_pnl_usd']:+.2f}

**PERFORMANCE BY STRATEGY:**
{strategy_breakdown}

**CONFIDENCE CALIBRATION:**
{confidence_breakdown}

**BEST TRADE:** {perf['best_trade']['symbol']} +{perf['best_trade']['pnl_percent']:.2f}% ({perf['best_trade']['strategy']})
**WORST TRADE:** {perf['worst_trade']['symbol']} {perf['worst_trade']['pnl_percent']:.2f}% ({perf['worst_trade']['strategy']})

**LESSONS LEARNED:**
- Your best strategy is {best_strategy[0].replace('_', ' ').title()} with {best_strategy[1]['win_rate']:.1f}% win rate
- Your weakest strategy is {worst_strategy[0].replace('_', ' ').title()} with {worst_strategy[1]['win_rate']:.1f}% win rate
- Trust your high-confidence signals (they have proven more accurate)
- Be more selective with lower-confidence setups
"""

        return prompt_section

    def get_open_trades_count(self):
        """Get count of currently open trades."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM trades WHERE exit_time IS NULL')
        count = cursor.fetchone()[0]

        conn.close()
        return count

    def get_todays_performance(self):
        """Get today's trading performance."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        today = datetime.now().date()

        cursor.execute('''
            SELECT COUNT(*), SUM(pnl_usd), outcome
            FROM trades
            WHERE DATE(exit_time) = ?
            GROUP BY outcome
        ''', (today,))

        results = cursor.fetchall()
        conn.close()

        wins = 0
        losses = 0
        total_pnl = 0

        for row in results:
            count, pnl, outcome = row
            if outcome == 'WIN':
                wins = count
            elif outcome == 'LOSS':
                losses = count
            total_pnl += pnl if pnl else 0

        total_trades = wins + losses
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

        return {
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'total_pnl': total_pnl
        }
