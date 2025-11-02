"""
Telegram Alert System for Trading Bot
Sends real-time notifications for critical events
"""
import requests
import os
from loguru import logger
from datetime import datetime

class TelegramAlerter:
    """Send alerts to Telegram for critical trading events."""

    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.token and self.chat_id)

        if self.enabled:
            logger.success("✅ Telegram alerts enabled")
        else:
            logger.warning("⚠️ Telegram alerts disabled (no credentials)")

    def send(self, message: str, silent: bool = False):
        """
        Send alert to Telegram.

        Args:
            message: Message to send (supports Markdown)
            silent: If True, sends without notification sound
        """
        if not self.enabled:
            logger.debug(f"Alert (not sent): {message}")
            return

        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_notification": silent
            }

            response = requests.post(url, json=payload, timeout=5)

            if response.status_code == 200:
                logger.debug(f"✅ Telegram alert sent")
            else:
                logger.error(f"❌ Telegram alert failed: {response.text}")

        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")

    def bot_started(self):
        """Alert that bot has started."""
        message = f"""🚀 **BOT STARTED** 🚀

📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC

✅ Trading engine is now live
🔍 Monitoring markets for opportunities
🤖 AI Ensemble: OPERATIONAL

⚡ All systems ready for trading!
"""
        self.send(message)

    def bot_stopped(self, reason: str = "Manual shutdown"):
        """Alert that bot has stopped."""
        message = f"""🛑 **BOT STOPPED** 🛑

📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
📝 Reason: {reason}

⚠️ Trading has been paused
"""
        self.send(message)

    def buy_executed(self, symbol: str, price: float, quantity: float,
                     usd_amount: float, ai_confidence: float, strategy: str):
        """Alert for BUY order execution."""
        message = f"""✅ **BUY ORDER EXECUTED** ✅

📊 Symbol: `{symbol}`
💵 Price: ${price:.6f}
📦 Quantity: {quantity:.4f}
💰 Amount: ${usd_amount:.2f}

🤖 AI Confidence: {ai_confidence:.1%}
📈 Strategy: {strategy.replace('_', ' ').title()}

⏰ {datetime.now().strftime('%H:%M:%S')} UTC
"""
        self.send(message)

    def sell_executed(self, symbol: str, price: float, quantity: float,
                      pnl_usd: float, pnl_percent: float, reason: str):
        """Alert for SELL order execution."""

        emoji = "🎉🟢" if pnl_usd > 0 else "🔴"
        outcome = "PROFIT" if pnl_usd > 0 else "LOSS"

        message = f"""{emoji} **SELL ORDER EXECUTED** {emoji}

📊 Symbol: `{symbol}`
💵 Exit Price: ${price:.6f}
📦 Quantity: {quantity:.4f}

{outcome}: ${pnl_usd:+.2f} ({pnl_percent:+.2f}%)
📝 Reason: {reason}

⏰ {datetime.now().strftime('%H:%M:%S')} UTC
"""
        self.send(message)

    def stop_loss_hit(self, symbol: str, entry_price: float, exit_price: float, loss_percent: float):
        """Alert for stop-loss trigger."""
        message = f"""🛑 **STOP-LOSS TRIGGERED** 🛑

📊 Symbol: `{symbol}`
🔽 Entry: ${entry_price:.6f}
🔽 Exit: ${exit_price:.6f}
📉 Loss: {loss_percent:.2f}%

⚠️ Position closed to protect capital

⏰ {datetime.now().strftime('%H:%M:%S')} UTC
"""
        self.send(message)

    def take_profit_hit(self, symbol: str, entry_price: float, exit_price: float, profit_percent: float):
        """Alert for take-profit trigger."""
        message = f"""🎯 **TAKE-PROFIT TRIGGERED** 🎯

📊 Symbol: `{symbol}`
🔼 Entry: ${entry_price:.6f}
🔼 Exit: ${exit_price:.6f}
📈 Profit: +{profit_percent:.2f}%

✅ Target achieved successfully!

⏰ {datetime.now().strftime('%H:%M:%S')} UTC
"""
        self.send(message)

    def critical_error(self, error_message: str):
        """Alert for critical errors."""
        message = f"""🚨 **CRITICAL ERROR** 🚨

⚠️ The bot encountered a critical issue:

`{error_message}`

🔧 Please check logs immediately
⏸️ Trading may have been paused

⏰ {datetime.now().strftime('%H:%M:%S')} UTC
"""
        self.send(message, silent=False)

    def daily_summary(self, total_trades: int, wins: int, losses: int,
                     total_pnl: float, win_rate: float):
        """Send daily performance summary."""
        message = f"""📊 **DAILY SUMMARY** 📊

📅 {datetime.now().strftime('%Y-%m-%d')}

🔢 Total Trades: {total_trades}
✅ Wins: {wins}
❌ Losses: {losses}
📈 Win Rate: {win_rate:.1f}%

💰 Total P&L: ${total_pnl:+.2f}

⏰ {datetime.now().strftime('%H:%M:%S')} UTC
"""
        self.send(message)

    def ai_validation_failed(self, symbol: str, reason: str):
        """Alert when AI blocks a trade."""
        message = f"""🛡️ **AI BLOCKED TRADE** 🛡️

📊 Symbol: `{symbol}`
🤖 AI Decision: HOLD

💭 Reason: {reason}

✅ Capital protected by AI validation

⏰ {datetime.now().strftime('%H:%M:%S')} UTC
"""
        self.send(message, silent=True)


# Global instance
alerter = TelegramAlerter()
