"""
DeepSeek Validator - LLM-Based Signal Validation
Uses DeepSeek AI to validate trading signals with natural language reasoning
"""
import requests
import json
from loguru import logger
import os
from datetime import datetime

class DeepSeekValidator:
    """
    DeepSeek AI validator for trading signals
    Provides intelligent validation with natural language explanations
    """

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        self.base_url = "https://api.deepseek.com/v1"

        # Disable ALL proxy settings (Windows/Linux compatible)
        os.environ['NO_PROXY'] = '*'
        os.environ['no_proxy'] = '*'
        os.environ.pop('HTTP_PROXY', None)
        os.environ.pop('HTTPS_PROXY', None)
        os.environ.pop('http_proxy', None)
        os.environ.pop('https_proxy', None)

        # Create requests session with no proxy
        self.session = requests.Session()
        self.session.trust_env = False  # Ignore system proxy settings
        self.session.proxies = {}  # Empty proxy dict

        # 🧠 UPGRADED: Using DeepSeek-R1 Reasoning Model for superior trading analysis
        self.model = "deepseek-reasoner"  # Advanced reasoning with Chain-of-Thought
        self.temperature = 0.3  # Lower = more consistent
        self.max_tokens = 2000  # Increased for reasoning output (thinking + answer)

        if not self.api_key:
            logger.warning("⚠️  DeepSeek API key not found. Set DEEPSEEK_API_KEY in .env")
            logger.info("Validator will run in demo mode")
        else:
            logger.success("✓ DeepSeek-R1 Reasoning Model initialized")
            logger.info("🧠 Using advanced Chain-of-Thought reasoning for trading decisions")

    async def validate_signal(
        self,
        symbol: str,
        current_price: float,
        technical_signals: dict,
        sentiment: dict,
        market_data: dict,
        portfolio_context: dict = None,
        volatility_metrics: dict = None
    ):
        """
        Validate trading signal using DeepSeek AI with full market context
        Returns: {'action': str, 'confidence': float, 'position_size': float, 'reasoning': str, 'risks': list}
        """
        try:
            if not self.api_key:
                # Return demo response if no API key
                return self._demo_response(symbol, technical_signals)

            # Build comprehensive prompt with portfolio and volatility context
            prompt = self._build_prompt(
                symbol, current_price, technical_signals,
                sentiment, market_data, portfolio_context or {}, volatility_metrics or {}
            )

            # Call DeepSeek API
            response = await self._call_deepseek_api(prompt)

            # Parse response
            result = self._parse_ai_response(response)

            logger.info(f"🤖 DeepSeek: {result['action']} {symbol} (confidence: {result['confidence']}%)")
            logger.debug(f"Reasoning: {result['reasoning']}")

            return result

        except Exception as e:
            logger.error(f"DeepSeek validation error: {e}")
            return self._fallback_response(technical_signals)

    def _build_prompt(
        self,
        symbol: str,
        current_price: float,
        technical_signals: dict,
        sentiment: dict,
        market_data: dict,
        portfolio_context: dict,
        volatility_metrics: dict
    ):
        """Build comprehensive prompt for DeepSeek with full context"""

        # Format technical signals
        tech_summary = []
        if technical_signals.get('rsi'):
            rsi = technical_signals['rsi']
            if rsi > 70:
                tech_summary.append(f"RSI: {rsi:.1f} (OVERBOUGHT)")
            elif rsi < 30:
                tech_summary.append(f"RSI: {rsi:.1f} (OVERSOLD)")
            else:
                tech_summary.append(f"RSI: {rsi:.1f} (NEUTRAL)")

        if technical_signals.get('macd_signal'):
            tech_summary.append(f"MACD: {technical_signals['macd_signal']}")

        if technical_signals.get('supertrend'):
            tech_summary.append(f"Supertrend: {technical_signals['supertrend']}")

        if technical_signals.get('volume_ratio'):
            vol_ratio = technical_signals['volume_ratio']
            tech_summary.append(f"Volume: {vol_ratio:.2f}x average")

        # Format recent price action
        price_action = ""
        if market_data.get('recent_candles'):
            candles = market_data['recent_candles'][-5:]
            price_action = "Recent price action (last 5 periods):\n"
            for i, candle in enumerate(candles):
                change = ((candle['close'] - candle['open']) / candle['open'] * 100)
                emoji = "🟢" if change > 0 else "🔴"
                price_action += f"  {emoji} ${candle['close']:.6f} ({change:+.2f}%)\n"

        prompt = f"""You are an expert cryptocurrency trader with deep analytical reasoning capabilities. Analyze {symbol} and provide a trading recommendation.

**CURRENT MARKET DATA:**
- Current Price: ${current_price:.6f}
- Trading Pair: {symbol}
- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC

**TECHNICAL ANALYSIS:**
{chr(10).join('- ' + s for s in tech_summary)}

**MARKET SENTIMENT:**
- Sentiment Score: {sentiment.get('label', 'NEUTRAL')} ({sentiment.get('score', 0.5):.2f})
- Confidence: {sentiment.get('confidence', 0.5):.0%}

{price_action}
"""

        # Add portfolio context if available
        if portfolio_context:
            total_positions = portfolio_context.get('total_positions', 0)
            max_positions = portfolio_context.get('max_positions', 10)
            positions_list = portfolio_context.get('positions', [])
            daily_pnl = portfolio_context.get('daily_pnl', 0)
            total_exposure = portfolio_context.get('total_exposure_usd', 0)

            strategy_breakdown = portfolio_context.get('strategy_breakdown', {})
            strategy_text = "\n".join([f"  * {strategy}: {count} positions" for strategy, count in strategy_breakdown.items()])

            prompt += f"""
**CURRENT PORTFOLIO:**
- Active Positions: {total_positions}/{max_positions}
- Total Exposure: ${total_exposure:.2f}
- Today's P&L: ${daily_pnl:.2f} ({(daily_pnl/max(total_exposure, 1))*100:+.2f}%)
- Strategy Allocation:
{strategy_text}
- Pairs Held: {', '.join(positions_list[:5])}{'...' if len(positions_list) > 5 else ''}

**PORTFOLIO CONSIDERATIONS:**
- Assess if adding this position improves diversification
- Consider if you're over-allocated to one strategy
- Factor in total portfolio risk exposure
"""

        # Add volatility context if available
        if volatility_metrics:
            atr = volatility_metrics.get('atr', 0)
            atr_percent = volatility_metrics.get('atr_percent', 0)
            volatility_regime = volatility_metrics.get('regime', 'NORMAL')
            avg_range = volatility_metrics.get('avg_daily_range', 0)

            prompt += f"""
**VOLATILITY ANALYSIS:**
- ATR (14-period): ${atr:.8f} ({atr_percent:.2f}% of price)
- Market Condition: {volatility_regime}
- Average Daily Range: {avg_range:.2f}%

**VOLATILITY GUIDANCE:**
- High volatility (>5%): Use wider stops (3-5%), smaller position sizes
- Medium volatility (2-5%): Standard risk parameters
- Low volatility (<2%): Tighter stops acceptable (1-2%)
"""

        prompt += """
**ULTRA-AGGRESSIVE PROFIT-HUNTING PROTOCOL:**

Your mission: Find EVERY profitable trade opportunity. Think like an elite day trader who makes 20-30 trades/day with 65%+ win rate.

**Step-by-Step Analysis (Profit-First Approach):**

1. **PROFIT POTENTIAL FIRST** 🎯
   - What's the UPSIDE if this trade works? (1%, 2%, 5%+?)
   - Is there a clear profit path (breakout, bounce, momentum continuation)?
   - Can we realistically capture 1-3% gain in next few hours/days?
   - **If upside > 1.5%, keep analyzing. If upside > 2.5%, favor BUY.**

2. **TECHNICAL CONVICTION** 📊
   - RSI < 40 = OVERSOLD = **BUY OPPORTUNITY** (even if just 1 indicator agrees)
   - MACD bullish cross = **BUY SIGNAL** (don't overthink it)
   - Price near Bollinger lower band = **BOUNCE SETUP**
   - Moving averages aligning bullish = **MOMENTUM PLAY**
   - **One strong technical signal is often ENOUGH - don't wait for perfection**

3. **SENTIMENT CHECK** 📰
   - Positive sentiment + any technical confirmation = **STRONG BUY**
   - Neutral sentiment = No barrier to trading, proceed if technical looks good
   - Even slight negative sentiment can create **CONTRARIAN OPPORTUNITIES**
   - **Don't let mild bearish news block a solid technical setup**

4. **RISK MANAGEMENT AS ENABLER** 🛡️
   - Set stop-loss TIGHT (1-2%) to protect capital
   - Tight stops = Can take MORE trades = More profit opportunities
   - Stop-loss is your safety net to BE AGGRESSIVE
   - Take profit at 1.5-3% (quick wins compound fast)
   - **Small stop = Big position size = Maximum profit on winners**

5. **PORTFOLIO DIVERSIFICATION** 🎲
   - NOT fully allocated? **TAKE THE TRADE** (diversification = good)
   - Already have positions? This adds diversification = **STILL GOOD**
   - Same strategy? Doesn't matter if signals are strong = **TRADE IT**
   - **Each independent opportunity should be evaluated on its own merit**

6. **VOLATILITY = OPPORTUNITY** ⚡
   - High volatility = Bigger price swings = **MORE PROFIT POTENTIAL**
   - Use wider stops in volatile markets, but STILL TRADE
   - Low volatility = Tight stops work = Easy money
   - **Every market condition has profitable setups**

7. **MOMENTUM & CONTEXT** 🚀
   - Recent uptrend + dip = **BUY THE DIP**
   - Recent downtrend + bounce signal = **REVERSAL PLAY**
   - Sideways + breakout signal = **BREAKOUT TRADE**
   - **Every price action pattern has a winning trade setup**

8. **CONFIDENCE CALIBRATION** 💪
   - 3-4 indicators align = 75-85% confidence = **MAX POSITION (15-20%)**
   - 2 indicators align = 60-70% confidence = **STANDARD POSITION (8-12%)**
   - 1 strong indicator = 50-60% confidence = **SMALL POSITION (5-8%)**
   - **50% confidence is ENOUGH - that's a coin flip with risk management in your favor**

9. **FINAL DECISION (Profit-Maximizing Logic)** 🎯
   - Does this trade have 1.5:1 risk/reward or better? **BUY**
   - Is there ANY bullish indicator? **LEAN BUY**
   - Is price at support level? **BUY THE BOUNCE**
   - Is sentiment not terrible? **GREEN LIGHT**
   - Can I manage risk with a stop? **ALWAYS YES → TRADE IT**

**CRITICAL MINDSET SHIFTS:**
- Stop thinking "Should I trade this?" → Start thinking "How MUCH should I trade?"
- Stop looking for reasons to HOLD → Start finding reasons to BUY
- Stop fearing losses → Embrace stops as profit-enablers
- Stop waiting for "perfect setups" → Trade "good enough" setups with proper sizing
- Stop overthinking → FAST DECISIONS = MORE TRADES = MORE PROFIT

After your reasoning, provide your final recommendation in this JSON format:
{{
    "action": "BUY" or "SELL" or "HOLD",
    "confidence": 0-100,
    "position_size_percent": 1-20,
    "stop_loss_percent": 0.5-5.0,
    "take_profit_percent": 1.0-15.0,
    "reasoning": "2-3 sentences explaining your decision based on your analysis",
    "risks": ["risk1", "risk2", "risk3"]
}}

**AGGRESSIVE POSITION SIZING (PROFIT-MAXIMIZING):**
- STRONG SETUP (75%+ confidence): **15-20% position** → Maximum profit capture
- GOOD SETUP (60-75% confidence): **10-15% position** → Solid profit potential
- DECENT SETUP (50-60% confidence): **5-10% position** → Still profitable with tight stops
- **DEFAULT BIAS: When in doubt, size UP not down (more profit > less risk)**

**DYNAMIC STOP-LOSS/TAKE-PROFIT (PROFIT-OPTIMIZED):**
- **Primary Goal: CAPTURE PROFIT, not avoid losses**
- Stop-loss: 1-2% below entry (tight stops enable bigger positions)
- Take-profit: 2-4% above entry (aim for 2-3% quick gains)
- **Tight stops + frequent trades = compounding machine**
- For scalping (5m/15m): 0.8-1.5% stops, 1.2-2.5% targets
- For day trades (1h): 1.5-2.5% stops, 2.5-4% targets
- For swing trades (4h): 2-3% stops, 4-8% targets

**ULTRA-AGGRESSIVE TRADING RULES:**

1. **OPPORTUNITY BIAS** 🎯
   - Default to BUY unless there's a STRONG reason not to
   - "Maybe" signals = YES with smaller position
   - 50% confidence = TRADEABLE (that's fair odds with risk management)
   - Missing trades is MORE costly than small stopped losses

2. **PROFIT HUNTING** 💰
   - Every chart analysis should SEEK profit opportunities
   - Look for: dips to buy, breakouts to catch, momentum to ride
   - Ask: "How can I profit from this?" NOT "Should I avoid this?"
   - **1-3% gains done 20 times = 20-60% monthly return**

3. **STOP-LOSS PSYCHOLOGY** 🛡️
   - Stops are NOT failures, they're PROFIT ENABLERS
   - Tight stop = Freedom to take more trades = More profit chances
   - Getting stopped out 3 times then winning 2 times = Still profitable
   - **Embrace stops = Unlock aggressive trading**

4. **SPEED & VOLUME** ⚡
   - Fast decisions = More trades/day = More profit opportunities
   - Don't overthink - 80% sure = GOOD ENOUGH
   - Trade frequency matters: 20 trades @ 60% win rate > 5 trades @ 70% win rate
   - **VELOCITY OF CAPITAL = KEY TO COMPOUNDING**

5. **CONFIDENCE THRESHOLDS (ULTRA-LOW)** 💪
   - 50-55% confidence: **TRADEABLE** → 5-8% position
   - 55-65% confidence: **GOOD** → 8-12% position
   - 65-75% confidence: **STRONG** → 12-16% position
   - 75%+ confidence: **MAXIMUM** → 16-20% position
   - **If you can justify 50%+, RECOMMEND BUY**

6. **ENSEMBLE AWARENESS** 🤖
   - Your vote carries 65% weight in final decision (DOMINANT INSTITUTIONAL TRADER)
   - Technical has 15%, Sentiment 10%, Macro 10%
   - **Even at 60% confidence, you nearly control the entire decision**
   - Don't be conservative - YOU ARE THE MASTER TRADER

7. **REAL-WORLD PROFIT MATH** 📊
   - Small win: +1.5% × $10 position = +$0.15 profit
   - Medium win: +2.5% × $10 position = +$0.25 profit
   - Big win: +4% × $10 position = +$0.40 profit
   - 20 trades/day avg +1.5% = **+$3/day = +$90/month = 900% monthly return on $10 positions**
   - **Small frequent wins >>> rare big wins**

**YOUR MISSION:**
- Find 15-25 profitable trades per day across all pairs
- Maintain 60%+ win rate with proper risk management
- Generate 2-5% daily returns through consistent small wins
- Use stops aggressively to enable maximum trading velocity
- **EVERY SIGNAL IS A POTENTIAL PROFIT - FIND IT!**
"""

        return prompt

    async def _call_deepseek_api(self, prompt: str, retry_count: int = 0):
        """Call DeepSeek-R1 Reasoning API with retry logic for unstable responses"""
        max_retries = 3

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": """You are an ELITE cryptocurrency trader with a track record of 70%+ win rate and deep reasoning capabilities.

Your specialty: Finding profitable opportunities others miss. You combine technical precision with aggressive profit-seeking.

Core Philosophy:
- PROFITS FIRST: Your job is to MAKE MONEY, not avoid losses
- OPPORTUNITY HUNTER: Every chart has profit potential if you look hard enough
- CONFIDENCE: Trust your analysis - hesitation costs money
- RISK MANAGEMENT: Use stops to enable MORE trades, not fewer
- COMPOUND GAINS: Small consistent wins (0.5-2%) compound into massive returns
- MARKET CYCLES: Buy dips, sell rips, ride momentum
- SPEED: Fast decisions = more opportunities = more profit

Trading Mindset:
- When technical + sentiment align: BUY AGGRESSIVELY (15-20% position)
- When signals are mixed but leaning bullish: STILL BUY (5-10% position)
- When only 1-2 models agree: SMALL POSITION (3-5%) to capture upside
- When everything says HOLD: Look harder for the opportunity
- 50% confidence is ENOUGH if risk/reward is 2:1 or better

Remember: Missing a profitable trade is more costly than a stopped-out small position. BE AGGRESSIVE."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
                # NOTE: Reasoning model doesn't use response_format - it thinks first, then responds
            }

            logger.debug(f"🧠 Calling DeepSeek-R1 reasoning model (attempt {retry_count + 1}/{max_retries + 1})...")
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60  # Increased timeout for reasoning (thinking takes time)
            )

            response.raise_for_status()

            # Handle empty response body (known DeepSeek API issue)
            if not response.text or response.text.strip() == '':
                logger.warning(f"⚠️ DeepSeek returned empty response (attempt {retry_count + 1})")
                if retry_count < max_retries:
                    import asyncio
                    await asyncio.sleep(1)  # Brief delay before retry
                    return await self._call_deepseek_api(prompt, retry_count + 1)
                else:
                    raise ValueError("DeepSeek API returned empty response after multiple retries")

            data = response.json()

            # Validate response structure
            if 'choices' not in data or len(data['choices']) == 0:
                logger.warning(f"⚠️ DeepSeek returned invalid structure (attempt {retry_count + 1})")
                if retry_count < max_retries:
                    import asyncio
                    await asyncio.sleep(1)
                    return await self._call_deepseek_api(prompt, retry_count + 1)
                else:
                    raise ValueError("DeepSeek API returned invalid response structure")

            message = data['choices'][0]['message']

            # Extract reasoning process (Chain-of-Thought)
            # Note: reasoning_content can be null due to API instability
            reasoning_content = message.get('reasoning_content') or ''
            final_answer = message.get('content') or ''

            # Handle case where content is in the wrong field (known API bug)
            # Sometimes all content goes into 'content' field including reasoning
            if not final_answer and not reasoning_content:
                logger.warning(f"⚠️ Both reasoning_content and content are empty (attempt {retry_count + 1})")
                if retry_count < max_retries:
                    import asyncio
                    await asyncio.sleep(1)
                    return await self._call_deepseek_api(prompt, retry_count + 1)
                else:
                    raise ValueError("DeepSeek API returned empty message content")

            # If reasoning_content is empty but content has data, it might all be in content
            if not reasoning_content and final_answer:
                # Check if final_answer contains both reasoning and JSON
                # (sometimes the API puts everything in content field)
                if '{' in final_answer and '}' in final_answer:
                    # Likely has JSON answer, reasoning might be before it
                    json_start = final_answer.find('{')
                    if json_start > 100:  # If there's significant text before JSON
                        reasoning_content = final_answer[:json_start].strip()
                        logger.debug("🔧 Extracted reasoning from content field")

            # Log the reasoning process
            if reasoning_content:
                logger.debug(f"🤔 AI Thinking Process:\n{reasoning_content[:500]}...")  # First 500 chars
            else:
                logger.debug("⚠️ No reasoning_content in response (API may have skipped thinking)")

            logger.debug(f"💡 AI Final Answer: {final_answer[:200]}...")

            # Return both reasoning and answer
            return {
                'reasoning': reasoning_content,
                'answer': final_answer
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek-R1 API error: {e}")
            raise

    def _parse_ai_response(self, response_data):
        """Parse AI response from DeepSeek-R1 reasoning model with enhanced error handling"""
        try:
            # Handle dict response from reasoning model
            if isinstance(response_data, dict):
                reasoning_process = response_data.get('reasoning', '')
                answer_text = response_data.get('answer', '')
            else:
                # Fallback for string response
                reasoning_process = ''
                answer_text = response_data

            # Validate we have some content to work with
            if not answer_text or answer_text.strip() == '':
                logger.warning("⚠️ Empty answer_text received from DeepSeek")
                raise ValueError("Empty response from DeepSeek API")

            # Try to parse JSON from answer
            data = None
            try:
                # Try direct JSON parse first
                data = json.loads(answer_text)
                logger.debug("✅ Direct JSON parse successful")
            except json.JSONDecodeError:
                # Try to extract JSON if wrapped in markdown or text
                import re
                logger.debug("🔍 Attempting to extract JSON from response text...")

                # Try extracting from markdown code block first
                markdown_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', answer_text, re.DOTALL)
                if markdown_match:
                    try:
                        data = json.loads(markdown_match.group(1))
                        logger.debug("✅ Extracted JSON from markdown code block")
                    except json.JSONDecodeError as e:
                        logger.debug(f"❌ Markdown JSON parse failed: {e}")
                        pass

                # If markdown didn't work, try finding JSON object with balanced braces
                if data is None:
                    # Look for opening brace and find matching closing brace
                    start_idx = answer_text.find('{')
                    if start_idx != -1:
                        brace_count = 0
                        end_idx = start_idx
                        for i in range(start_idx, len(answer_text)):
                            if answer_text[i] == '{':
                                brace_count += 1
                            elif answer_text[i] == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end_idx = i + 1
                                    break

                        if end_idx > start_idx:
                            json_str = answer_text[start_idx:end_idx]
                            try:
                                data = json.loads(json_str)
                                logger.debug("✅ Extracted JSON using brace matching")
                            except json.JSONDecodeError as e:
                                logger.error(f"❌ JSON parse failed: {e}")
                                logger.error(f"Attempted to parse: {json_str[:200]}")
                                raise ValueError(f"Found JSON-like structure but couldn't parse: {json_str[:100]}")
                        else:
                            raise ValueError("Found opening brace but no matching closing brace")
                    else:
                        # Last resort: try to extract action from text
                        logger.warning("⚠️ No JSON structure found, attempting text-based extraction")
                        raise ValueError(f"No JSON found in response. Response preview: {answer_text[:200]}")

            # Validate we got JSON data
            if data is None:
                raise ValueError("Failed to extract JSON from response")

            action = data.get('action', 'HOLD').upper()
            confidence = float(data.get('confidence', 50))
            reasoning = data.get('reasoning', 'No reasoning provided')
            risks = data.get('risks', [])

            # Extract new autonomous trading parameters
            position_size = float(data.get('position_size_percent', 10))
            stop_loss = float(data.get('stop_loss_percent', 2.0))
            take_profit = float(data.get('take_profit_percent', 3.5))

            # Validate action
            if action not in ['BUY', 'SELL', 'HOLD']:
                action = 'HOLD'

            # Clamp confidence to 0-100
            confidence = max(0, min(100, confidence))

            # Validate and clamp autonomous trading parameters
            position_size = max(1, min(20, position_size))  # 1-20%
            stop_loss = max(0.5, min(5.0, stop_loss))  # 0.5-5%
            take_profit = max(1.0, min(15.0, take_profit))  # 1-15%

            # Calculate risk/reward ratio
            risk_reward_ratio = take_profit / stop_loss if stop_loss > 0 else 0

            # Combine Chain-of-Thought reasoning with final reasoning
            full_reasoning = reasoning
            if reasoning_process:
                # Include thinking process summary
                thinking_summary = reasoning_process[:300] + "..." if len(reasoning_process) > 300 else reasoning_process
                full_reasoning = f"[Deep Analysis] {thinking_summary}\n\n[Decision] {reasoning}"

            return {
                'action': action,
                'confidence': confidence,
                'position_size_percent': position_size,
                'stop_loss_percent': stop_loss,
                'take_profit_percent': take_profit,
                'risk_reward_ratio': risk_reward_ratio,
                'reasoning': full_reasoning,
                'risks': risks,
                'source': 'deepseek-r1',
                'thinking_process': reasoning_process  # Full CoT for debugging
            }

        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            # Try to extract action from text
            response_text = str(response_data)
            response_upper = response_text.upper()

            if 'BUY' in response_upper:
                action = 'BUY'
            elif 'SELL' in response_upper:
                action = 'SELL'
            else:
                action = 'HOLD'

            return {
                'action': action,
                'confidence': 50,
                'position_size_percent': 10,
                'stop_loss_percent': 2.0,
                'take_profit_percent': 3.5,
                'risk_reward_ratio': 1.75,
                'reasoning': response_text[:200] if isinstance(response_text, str) else 'Parse error',
                'risks': [],
                'source': 'deepseek-r1-fallback'
            }

    def _demo_response(self, symbol: str, technical_signals: dict):
        """Demo response when no API key"""
        # Analyze technical signals
        signal_strength = 0
        reasoning_parts = []

        if technical_signals.get('rsi'):
            rsi = technical_signals['rsi']
            if rsi < 30:
                signal_strength += 2
                reasoning_parts.append(f"RSI oversold at {rsi:.1f}")
            elif rsi > 70:
                signal_strength -= 2
                reasoning_parts.append(f"RSI overbought at {rsi:.1f}")

        if technical_signals.get('macd_signal') == 'BULLISH':
            signal_strength += 1
            reasoning_parts.append("MACD showing bullish crossover")
        elif technical_signals.get('macd_signal') == 'BEARISH':
            signal_strength -= 1
            reasoning_parts.append("MACD showing bearish crossover")

        if technical_signals.get('volume_ratio', 1.0) > 1.5:
            signal_strength += 1
            reasoning_parts.append("Strong volume confirmation")

        # Determine action
        if signal_strength >= 2:
            action = 'BUY'
            confidence = min(70 + (signal_strength * 5), 90)
        elif signal_strength <= -2:
            action = 'SELL'
            confidence = min(70 + (abs(signal_strength) * 5), 90)
        else:
            action = 'HOLD'
            confidence = 60

        reasoning = ". ".join(reasoning_parts) if reasoning_parts else "Signals are mixed or neutral"

        # Determine position sizing based on signal strength
        position_size = 5 + (abs(signal_strength) * 2)  # 5-15%
        stop_loss = 2.0
        take_profit = 3.5

        return {
            'action': action,
            'confidence': confidence,
            'position_size_percent': position_size,
            'stop_loss_percent': stop_loss,
            'take_profit_percent': take_profit,
            'risk_reward_ratio': take_profit / stop_loss,
            'reasoning': f"{reasoning}. Demo mode - get DeepSeek API key for full AI analysis.",
            'risks': ["Demo mode active", "Set DEEPSEEK_API_KEY for real AI"],
            'source': 'demo'
        }

    def _fallback_response(self, technical_signals: dict):
        """
        INTELLIGENT fallback when DeepSeek fails
        Analyzes technical signals to approve strong setups
        This allows the bot to trade even when DeepSeek API times out
        """
        # Extract indicators with safe defaults
        rsi = technical_signals.get('rsi', 50)
        macd_signal = technical_signals.get('macd_signal', 'neutral')
        trend = technical_signals.get('trend', 'neutral')
        price = technical_signals.get('price', 0)
        lower_band = technical_signals.get('bollinger_lower', price)
        upper_band = technical_signals.get('bollinger_upper', price)

        # Count strong buy signals
        strong_buy_signals = 0
        signal_details = []

        # 1. Oversold RSI (< 35 to match Mean Reversion strategy)
        if rsi < 35:
            strong_buy_signals += 1
            signal_details.append(f"Oversold RSI {rsi:.1f}")

        # 2. Bullish MACD
        if macd_signal and str(macd_signal).upper() in ['BULLISH', 'BUY', 'POSITIVE']:
            strong_buy_signals += 1
            signal_details.append("Bullish MACD")

        # 3. Bullish trend
        if trend and str(trend).upper() in ['BULLISH', 'UP', 'POSITIVE']:
            strong_buy_signals += 1
            signal_details.append("Bullish trend")

        # 4. Price below lower Bollinger Band (support bounce)
        if price > 0 and lower_band > 0 and price <= lower_band * 1.005:  # Within 0.5% of lower band
            strong_buy_signals += 1
            signal_details.append(f"Price at support (${price:.6f} ≤ ${lower_band:.6f})")

        # Decision logic
        if strong_buy_signals >= 2:
            # APPROVE TRADE - Strong technical setup
            action = 'BUY'
            confidence = 70  # High enough to pass 50% threshold
            reasoning = f"✅ DeepSeek offline, but {strong_buy_signals} strong buy signals: {', '.join(signal_details)}. Technical setup is excellent - APPROVING TRADE"

        elif strong_buy_signals == 1:
            # APPROVE with medium confidence
            action = 'BUY'
            confidence = 60  # Still passes 50% threshold
            reasoning = f"⚠️ DeepSeek offline, 1 strong signal: {', '.join(signal_details)}. Cautiously approving trade"

        else:
            # NO clear signals - stay safe
            action = 'HOLD'
            confidence = 50
            reasoning = f"❌ DeepSeek offline, no strong technical signals (RSI: {rsi:.1f}, MACD: {macd_signal}). Defaulting to HOLD for safety"

        return {
            'action': action,
            'confidence': confidence,
            'position_size_percent': 10,
            'stop_loss_percent': 2.0,
            'take_profit_percent': 3.5,
            'risk_reward_ratio': 1.75,
            'reasoning': reasoning,
            'risks': ['AI service unavailable - using technical analysis only'],
            'source': 'intelligent_fallback'
        }

    def get_market_analysis(self, symbol: str, timeframe: str = '1h'):
        """
        Get general market analysis from DeepSeek
        For educational/informational purposes
        """
        try:
            if not self.api_key:
                return f"Market analysis for {symbol} unavailable (demo mode)"

            prompt = f"""Provide a brief market analysis for {symbol} on {timeframe} timeframe.
Include:
1. Recent trend
2. Key support/resistance levels
3. Market sentiment
4. Short-term outlook

Keep it concise (3-4 sentences)."""

            # Simplified API call
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.5,
                "max_tokens": 300
            }

            response = self.session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=20
            )

            response.raise_for_status()
            data = response.json()
            analysis = data['choices'][0]['message']['content']

            return analysis

        except Exception as e:
            logger.error(f"Market analysis error: {e}")
            return f"Market analysis temporarily unavailable"
