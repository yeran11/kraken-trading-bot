"""
DeepSeek Chained Prompting System
Multi-call structured reasoning for superior decision-making
"""
import json
import requests
from loguru import logger
from deepseek_validator import DeepSeekValidator

class DeepSeekChain:
    """
    Execute a chain of DeepSeek calls for structured, step-by-step analysis.

    Chain Flow:
    1. Market Regime Analysis → Determine if TRENDING, RANGING, or VOLATILE
    2. Strategy Selection → Choose optimal strategy for the regime
    3. Trade Validation → Final decision with execution parameters
    """

    def __init__(self, api_key: str = None):
        self.validator = DeepSeekValidator(api_key=api_key)
        self.api_key = self.validator.api_key
        logger.success("✓ DeepSeek Chain initialized (3-call structured reasoning)")

    async def execute_chain(self, symbol: str, current_price: float,
                           technical_indicators: dict, sentiment: dict,
                           candles: list, portfolio_context: dict,
                           volatility_metrics: dict):
        """
        Execute full reasoning chain.

        Returns:
            dict: Final trade decision with all context from the chain
        """
        logger.info(f"🔗 STARTING DEEPSEEK REASONING CHAIN for {symbol}")

        # CALL 1: Market Regime Analysis
        regime_result = await self._analyze_market_regime(
            symbol, candles, technical_indicators, volatility_metrics
        )

        if not regime_result:
            logger.error("❌ Chain failed at Step 1: Market Regime Analysis")
            return None

        logger.success(f"✅ Step 1: Market Regime = {regime_result['regime']} ({regime_result['confidence']}% confidence)")

        # CALL 2: Strategy Selection
        strategy_result = await self._select_strategy(
            regime_result['regime'], technical_indicators, volatility_metrics
        )

        if not strategy_result:
            logger.error("❌ Chain failed at Step 2: Strategy Selection")
            return None

        logger.success(f"✅ Step 2: Recommended Strategy = {strategy_result['recommended_strategy']} ({strategy_result['confidence']}% confidence)")

        # CALL 3: Trade Validation & Parameterization
        trade_result = await self._validate_and_parameterize(
            symbol, current_price, technical_indicators, sentiment,
            candles, portfolio_context, volatility_metrics,
            regime_result, strategy_result
        )

        if not trade_result:
            logger.error("❌ Chain failed at Step 3: Trade Validation")
            return None

        logger.success(f"✅ Step 3: Final Decision = {trade_result['action']} ({trade_result['confidence']}% confidence)")
        logger.success(f"🎯 CHAIN COMPLETE: {trade_result['action']} {symbol}")

        return trade_result

    async def _analyze_market_regime(self, symbol: str, candles: list,
                                     indicators: dict, volatility: dict):
        """
        CALL 1: Determine current market regime.

        Returns:
            dict: {'regime': str, 'confidence': int, 'reasoning': str}
        """
        logger.info("🧠 Chain Step 1: Analyzing market regime...")

        # Calculate trend direction
        closes = [c['close'] for c in candles[-20:]]
        is_uptrend = closes[-1] > closes[0] and closes[-5] > closes[-10]
        is_downtrend = closes[-1] < closes[0] and closes[-5] < closes[-10]

        adx = indicators.get('adx', 0)
        rsi = indicators.get('rsi', 50)
        vol_regime = volatility.get('regime', 'NORMAL')

        prompt = f"""Analyze the market data for {symbol} and determine the current market regime.

**MARKET DATA:**
- Price Trend: {"Uptrend" if is_uptrend else "Downtrend" if is_downtrend else "Sideways"}
- ADX (Trend Strength): {adx:.1f}
- RSI: {rsi:.1f}
- Volatility: {vol_regime}
- Recent Price Action: Last close ${closes[-1]:.6f}, 20 candles ago ${closes[0]:.6f}

**REGIME DEFINITIONS:**
1. **TRENDING**: Strong directional movement
   - ADX > 25 (strong trend)
   - Clear price direction (consecutive higher highs/lower lows)
   - RSI not in extreme zones (30-70 range)

2. **RANGING**: Sideways, choppy movement
   - ADX < 20 (weak trend)
   - Price oscillating without clear direction
   - Multiple touches of support/resistance

3. **VOLATILE**: High volatility, uncertain direction
   - ATR elevated (volatility regime = VOLATILE or HIGH)
   - Large candle wicks, erratic movement
   - RSI whipsawing between extremes

Based on this data, determine the current market regime.

Respond in JSON format:
{{
    "regime": "TRENDING" or "RANGING" or "VOLATILE",
    "confidence": 0-100,
    "reasoning": "Brief explanation (2-3 sentences)"
}}
"""

        try:
            response = await self.validator._call_deepseek_api(prompt)
            result = self._parse_json_response(response)

            if result:
                logger.debug(f"Regime Analysis: {result['reasoning']}")
                return result
            else:
                return None

        except Exception as e:
            logger.error(f"Error in regime analysis: {e}")
            return None

    async def _select_strategy(self, regime: str, indicators: dict, volatility: dict):
        """
        CALL 2: Select optimal strategy based on market regime.

        Returns:
            dict: {'recommended_strategy': str, 'confidence': int, 'reasoning': str}
        """
        logger.info(f"🧠 Chain Step 2: Selecting strategy for {regime} regime...")

        rsi = indicators.get('rsi', 50)
        adx = indicators.get('adx', 0)
        macd = indicators.get('macd_signal', 'NEUTRAL')
        vol_regime = volatility.get('regime', 'NORMAL')

        prompt = f"""The market is currently in a **{regime}** regime.

**CURRENT INDICATORS:**
- RSI: {rsi:.1f}
- ADX: {adx:.1f}
- MACD Signal: {macd}
- Volatility: {vol_regime}

**AVAILABLE STRATEGIES:**

1. **scalping** - Quick 0.8-1.2% gains on micro-dips
   - Best in: RANGING markets
   - Position size: 5%
   - Holding time: Minutes to hours
   - Stop-loss: Tight (0.5-1%)

2. **momentum** - 3-5% trend-following
   - Best in: TRENDING markets
   - Position size: 10%
   - Holding time: Hours to days
   - Stop-loss: Medium (1.5-2.5%)

3. **mean_reversion** - 2-4% bounce trades from extremes
   - Best in: RANGING markets
   - Position size: 12%
   - Holding time: Hours to 2 days
   - Stop-loss: Medium (1.5-2%)

4. **macd_supertrend** - 5-10% multi-day swing trades
   - Best in: TRENDING markets (strong trend)
   - Position size: 15%
   - Holding time: Days to weeks
   - Stop-loss: Wide (2-4%)

**SELECTION CRITERIA:**
- Match strategy to regime (TRENDING → momentum/macd, RANGING → scalping/mean_reversion)
- Consider volatility (high volatility → wider stops, lower position sizes)
- Check if indicators support the strategy (e.g., momentum needs MACD bullish, mean_reversion needs RSI extreme)

Which strategy is most appropriate for the current market conditions?

Respond in JSON format:
{{
    "recommended_strategy": "scalping" or "momentum" or "mean_reversion" or "macd_supertrend",
    "confidence": 0-100,
    "reasoning": "Explanation (2-3 sentences)"
}}
"""

        try:
            response = await self.validator._call_deepseek_api(prompt)
            result = self._parse_json_response(response)

            if result:
                logger.debug(f"Strategy Selection: {result['reasoning']}")
                return result
            else:
                return None

        except Exception as e:
            logger.error(f"Error in strategy selection: {e}")
            return None

    async def _validate_and_parameterize(self, symbol: str, price: float,
                                         indicators: dict, sentiment: dict,
                                         candles: list, portfolio: dict,
                                         volatility: dict, regime_result: dict,
                                         strategy_result: dict):
        """
        CALL 3: Validate the recommended strategy signal and provide execution parameters.

        Returns:
            dict: Full trade decision with parameters
        """
        logger.info(f"🧠 Chain Step 3: Validating trade and calculating parameters...")

        regime = regime_result['regime']
        strategy = strategy_result['recommended_strategy']

        # Build comprehensive context
        rsi = indicators.get('rsi', 50)
        macd = indicators.get('macd_signal', 'NEUTRAL')
        adx = indicators.get('adx', 0)
        sentiment_label = sentiment.get('label', 'NEUTRAL')
        sentiment_score = sentiment.get('score', 0.5)

        # Portfolio context
        positions = portfolio.get('total_positions', 0)
        max_positions = portfolio.get('max_positions', 10)
        exposure = portfolio.get('total_exposure_usd', 0)

        # Volatility context
        atr_percent = volatility.get('atr_percent', 0)
        vol_regime = volatility.get('regime', 'NORMAL')

        prompt = f"""A **{strategy}** signal has been detected for {symbol} at ${price:.6f}.

**CONTEXT FROM PREVIOUS ANALYSIS:**
- Market Regime: {regime} ({regime_result['reasoning']})
- Recommended Strategy: {strategy} ({strategy_result['reasoning']})

**CURRENT MARKET STATE:**
- Price: ${price:.6f}
- RSI: {rsi:.1f}
- MACD: {macd}
- ADX: {adx:.1f}
- Sentiment: {sentiment_label} ({sentiment_score:.2f})
- Volatility: {vol_regime} (ATR: {atr_percent:.2f}% of price)

**PORTFOLIO:**
- Positions: {positions}/{max_positions}
- Exposure: ${exposure:.2f}

**YOUR TASK:**
Validate this {strategy} trade signal and provide complete execution parameters.

**DECISION FRAMEWORK:**
1. Does this {strategy} signal align with the {regime} regime? (Consistency check)
2. Are the technical indicators supporting the trade? (RSI, MACD, ADX all aligned?)
3. Does sentiment support or contradict the trade?
4. Is volatility acceptable for this strategy? (Not too high/low)
5. Does the portfolio have capacity? (Not too concentrated)
6. What's the risk/reward ratio? (Should be minimum 2:1)

Respond in JSON format:
{{
    "action": "BUY" or "HOLD",
    "confidence": 0-100,
    "position_size_percent": 1-20,
    "stop_loss_percent": 0.5-5.0,
    "take_profit_percent": 1.0-15.0,
    "reasoning": "Your final decision based on ALL the context (3-4 sentences)",
    "risks": ["risk1", "risk2", "risk3"]
}}

**GUIDELINES:**
- Only recommend BUY if confidence > 55%
- Adjust position size based on confidence and volatility
- Set stops based on ATR and volatility regime
- Ensure risk/reward ratio is at least 2:1
"""

        try:
            response = await self.validator._call_deepseek_api(prompt)
            result = self._parse_json_response(response)

            if result:
                # Add chain context to result
                result['recommended_strategy'] = strategy
                result['market_regime'] = regime
                result['chain_reasoning'] = {
                    'regime': regime_result,
                    'strategy': strategy_result
                }

                # Calculate risk/reward ratio
                if 'stop_loss_percent' in result and 'take_profit_percent' in result:
                    result['risk_reward_ratio'] = result['take_profit_percent'] / result['stop_loss_percent']

                logger.debug(f"Final Decision: {result['reasoning']}")
                return result
            else:
                return None

        except Exception as e:
            logger.error(f"Error in trade validation: {e}")
            return None

    def _parse_json_response(self, response_data):
        """Parse JSON from DeepSeek response."""
        try:
            # Handle dict response from reasoning model
            if isinstance(response_data, dict):
                answer_text = response_data.get('answer', '')
            else:
                answer_text = response_data

            # Try to parse JSON from answer
            try:
                data = json.loads(answer_text)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', answer_text, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(1))
                else:
                    # Try to find raw JSON
                    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', answer_text, re.DOTALL)
                    if json_match:
                        data = json.loads(json_match.group(0))
                    else:
                        logger.error(f"Could not parse JSON from response: {answer_text[:200]}")
                        return None

            return data

        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return None
