"""
DeepSeek Multi-Agent Debate System
Three specialized agents debate to reach superior trading decisions
"""
import json
import requests
from loguru import logger
from deepseek_validator import DeepSeekValidator

class DeepSeekDebate:
    """
    Multi-agent debate system for critical trading decisions.

    Agents:
    1. Bull Agent - Makes strongest case for BUY
    2. Bear Agent - Makes strongest case against BUY
    3. Risk Manager - Weighs both arguments and makes final decision
    """

    def __init__(self, api_key: str = None):
        self.validator = DeepSeekValidator(api_key=api_key)
        self.api_key = self.validator.api_key
        logger.success("✓ DeepSeek Debate System initialized (3-agent adversarial analysis)")

    async def debate_trade(self, symbol: str, current_price: float,
                          technical_indicators: dict, sentiment: dict,
                          candles: list, portfolio_context: dict,
                          volatility_metrics: dict):
        """
        Execute full multi-agent debate.

        Returns:
            dict: Final decision with both bull and bear arguments
        """
        logger.info(f"⚖️ STARTING MULTI-AGENT DEBATE for {symbol}")

        # AGENT 1: Bull Case
        bull_case = await self._get_bull_case(
            symbol, current_price, technical_indicators, sentiment, candles, volatility_metrics
        )

        if not bull_case:
            logger.error("❌ Bull agent failed to respond")
            return None

        logger.success(f"🐂 BULL AGENT: {bull_case['confidence']}% confidence - {bull_case['summary']}")

        # AGENT 2: Bear Case
        bear_case = await self._get_bear_case(
            symbol, current_price, technical_indicators, sentiment, candles, volatility_metrics
        )

        if not bear_case:
            logger.error("❌ Bear agent failed to respond")
            return None

        logger.success(f"🐻 BEAR AGENT: {bear_case['confidence']}% confidence - {bear_case['summary']}")

        # AGENT 3: Risk Manager (Final Decision)
        final_decision = await self._risk_manager_decision(
            symbol, current_price, bull_case, bear_case, portfolio_context, volatility_metrics
        )

        if not final_decision:
            logger.error("❌ Risk manager failed to decide")
            return None

        logger.success(f"⚖️ RISK MANAGER: {final_decision['action']} with {final_decision['confidence']}% confidence")
        logger.success(f"🎯 DEBATE COMPLETE: {final_decision['verdict']}")

        return final_decision

    async def _get_bull_case(self, symbol: str, price: float, indicators: dict,
                             sentiment: dict, candles: list, volatility: dict):
        """
        AGENT 1: Bull Agent - Make strongest case for BUY.

        Returns:
            dict: Bull argument with key points
        """
        logger.info("🐂 Bull Agent analyzing...")

        rsi = indicators.get('rsi', 50)
        macd = indicators.get('macd_signal', 'NEUTRAL')
        volume = indicators.get('volume_ratio', 1.0)
        sentiment_label = sentiment.get('label', 'NEUTRAL')
        vol_regime = volatility.get('regime', 'NORMAL')

        # Calculate recent price momentum
        recent_closes = [c['close'] for c in candles[-10:]]
        momentum = ((recent_closes[-1] - recent_closes[0]) / recent_closes[0]) * 100

        system_prompt = """You are an aggressive, optimistic BULL trader. Your goal is to find every possible reason to BUY.

You MUST make the strongest possible case for why this trade will be profitable. Be persuasive and highlight ALL positive signals. Your job is to convince others that this is a great buying opportunity.

Focus on:
- Bullish technical signals
- Positive sentiment
- Growth momentum
- Potential upside
- Why risks are manageable

Be enthusiastic but use data to support your argument."""

        user_prompt = f"""Analyze {symbol} at ${price:.6f} and make the **BULL CASE** for buying.

**MARKET DATA:**
- Price: ${price:.6f}
- RSI: {rsi:.1f}
- MACD: {macd}
- Volume: {volume:.2f}x average
- Sentiment: {sentiment_label}
- Volatility: {vol_regime}
- Recent Momentum: {momentum:+.2f}%

**YOUR TASK:**
Find every bullish signal and make a compelling argument for why this is a BUY opportunity.

Respond in JSON format:
{{
    "summary": "One-line bull case (max 15 words)",
    "argument": "Your full bull case (3-4 sentences)",
    "key_points": ["bullish point 1", "bullish point 2", "bullish point 3"],
    "confidence": 0-100,
    "target_upside": "Estimated % gain potential"
}}
"""

        try:
            response = await self._call_with_system_prompt(system_prompt, user_prompt)
            result = self._parse_json_response(response)

            if result:
                logger.debug(f"Bull Case: {result['argument']}")
                return result
            else:
                return None

        except Exception as e:
            logger.error(f"Error getting bull case: {e}")
            return None

    async def _get_bear_case(self, symbol: str, price: float, indicators: dict,
                             sentiment: dict, candles: list, volatility: dict):
        """
        AGENT 2: Bear Agent - Make strongest case AGAINST buying.

        Returns:
            dict: Bear argument with key risks
        """
        logger.info("🐻 Bear Agent analyzing...")

        rsi = indicators.get('rsi', 50)
        macd = indicators.get('macd_signal', 'NEUTRAL')
        volume = indicators.get('volume_ratio', 1.0)
        sentiment_label = sentiment.get('label', 'NEUTRAL')
        vol_regime = volatility.get('regime', 'NORMAL')

        # Calculate recent price momentum
        recent_closes = [c['close'] for c in candles[-10:]]
        momentum = ((recent_closes[-1] - recent_closes[0]) / recent_closes[0]) * 100

        system_prompt = """You are a cautious, pessimistic BEAR trader. Your goal is to identify every possible risk and flaw.

You MUST make the strongest possible case for why this trade will FAIL. Be critical and highlight ALL negative signals and risks. Your job is to protect capital by finding reasons NOT to trade.

Focus on:
- Bearish technical signals
- Negative sentiment
- Downside risks
- Why the trade could lose money
- Hidden dangers

Be skeptical and use data to support your concerns."""

        user_prompt = f"""Analyze {symbol} at ${price:.6f} and make the **BEAR CASE** against buying.

**MARKET DATA:**
- Price: ${price:.6f}
- RSI: {rsi:.1f}
- MACD: {macd}
- Volume: {volume:.2f}x average
- Sentiment: {sentiment_label}
- Volatility: {vol_regime}
- Recent Momentum: {momentum:+.2f}%

**YOUR TASK:**
Find every bearish signal and risk factor. Make a compelling argument for why this is NOT a good trade.

Respond in JSON format:
{{
    "summary": "One-line bear case (max 15 words)",
    "argument": "Your full bear case (3-4 sentences)",
    "key_risks": ["risk 1", "risk 2", "risk 3"],
    "confidence": 0-100,
    "downside_potential": "Estimated % loss potential"
}}
"""

        try:
            response = await self._call_with_system_prompt(system_prompt, user_prompt)
            result = self._parse_json_response(response)

            if result:
                logger.debug(f"Bear Case: {result['argument']}")
                return result
            else:
                return None

        except Exception as e:
            logger.error(f"Error getting bear case: {e}")
            return None

    async def _risk_manager_decision(self, symbol: str, price: float,
                                     bull_case: dict, bear_case: dict,
                                     portfolio: dict, volatility: dict):
        """
        AGENT 3: Risk Manager - Make final decision based on both arguments.

        Returns:
            dict: Final trade decision
        """
        logger.info("⚖️ Risk Manager deliberating...")

        positions = portfolio.get('total_positions', 0)
        max_positions = portfolio.get('max_positions', 10)
        exposure = portfolio.get('total_exposure_usd', 0)
        atr_percent = volatility.get('atr_percent', 0)
        vol_regime = volatility.get('regime', 'NORMAL')

        system_prompt = """You are the HEAD OF RISK MANAGEMENT. You have received conflicting analyses from your Bull and Bear analysts.

Your job is to:
1. Weigh both arguments objectively
2. Evaluate the risk/reward ratio
3. Make the final, rational decision
4. Prioritize CAPITAL PRESERVATION while seeking profitable opportunities

Your decision is BINDING and must be based on:
- Which argument is more convincing based on the DATA
- The quality of evidence (not just enthusiasm)
- Portfolio considerations and risk exposure
- Risk/reward balance

Be rational, balanced, and decisive."""

        user_prompt = f"""You must decide whether to BUY {symbol} at ${price:.6f}.

**BULL ANALYST'S ARGUMENT:**
Summary: {bull_case['summary']}
Argument: {bull_case['argument']}

Key Bull Points:
{chr(10).join(f"  ✅ {point}" for point in bull_case['key_points'])}

Bull Confidence: {bull_case['confidence']}%
Upside Potential: {bull_case.get('target_upside', 'Unknown')}

**BEAR ANALYST'S ARGUMENT:**
Summary: {bear_case['summary']}
Argument: {bear_case['argument']}

Key Bear Risks:
{chr(10).join(f"  ⚠️ {risk}" for risk in bear_case['key_risks'])}

Bear Confidence: {bear_case['confidence']}%
Downside Potential: {bear_case.get('downside_potential', 'Unknown')}

**PORTFOLIO CONTEXT:**
- Current Positions: {positions}/{max_positions}
- Total Exposure: ${exposure:.2f}
- Volatility: {vol_regime} (ATR: {atr_percent:.2f}%)

**YOUR DECISION FRAMEWORK:**
1. Which argument is MORE convincing based on the DATA?
2. Does the risk/reward ratio justify the trade?
3. Does the portfolio have capacity and is diversification acceptable?
4. Are the bull's points stronger than the bear's risks?
5. What's the probability of success vs. failure?

Respond in JSON format:
{{
    "action": "BUY" or "HOLD",
    "confidence": 0-100,
    "position_size_percent": 1-20,
    "stop_loss_percent": 0.5-5.0,
    "take_profit_percent": 1.0-15.0,
    "reasoning": "Your balanced analysis (3-4 sentences)",
    "verdict": "Why you sided with the bull or bear case (1-2 sentences)",
    "risk_reward_assessment": "Your evaluation of the risk/reward ratio"
}}

**GUIDELINES:**
- Only recommend BUY if confidence > 55%
- Consider BOTH arguments equally
- Make decision based on DATA, not just optimism/pessimism
- Ensure risk/reward is at least 2:1 for BUY
- If arguments are equally strong, default to HOLD (preserve capital)
"""

        try:
            response = await self._call_with_system_prompt(system_prompt, user_prompt)
            result = self._parse_json_response(response)

            if result:
                # Add debate context
                result['bull_case'] = bull_case
                result['bear_case'] = bear_case

                # Calculate risk/reward ratio
                if 'stop_loss_percent' in result and 'take_profit_percent' in result:
                    result['risk_reward_ratio'] = result['take_profit_percent'] / result['stop_loss_percent']

                logger.debug(f"Risk Manager Decision: {result['reasoning']}")
                logger.debug(f"Verdict: {result['verdict']}")

                return result
            else:
                return None

        except Exception as e:
            logger.error(f"Error in risk manager decision: {e}")
            return None

    async def _call_with_system_prompt(self, system_prompt: str, user_prompt: str):
        """Call DeepSeek API with custom system prompt."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "deepseek-reasoner",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 2000
            }

            response = requests.post(
                f"{self.validator.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
                proxies={}  # Disable proxy completely
            )

            response.raise_for_status()
            data = response.json()

            message = data['choices'][0]['message']
            reasoning_content = message.get('reasoning_content', '')
            final_answer = message.get('content', '')

            return {
                'reasoning': reasoning_content,
                'answer': final_answer
            }

        except Exception as e:
            logger.error(f"API call error: {e}")
            raise

    def _parse_json_response(self, response_data):
        """Parse JSON from DeepSeek response."""
        try:
            if isinstance(response_data, dict):
                answer_text = response_data.get('answer', '')
            else:
                answer_text = response_data

            # Try to parse JSON
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
