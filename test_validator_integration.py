#!/usr/bin/env python3
"""
Integration test for DeepSeekValidator with proxy fix
Tests actual API calls using the validator class
"""

import asyncio
import os
from dotenv import load_dotenv
from deepseek_validator import DeepSeekValidator
from loguru import logger

# Load environment variables
load_dotenv()

async def test_validator():
    """Test DeepSeekValidator with actual API call"""
    print("=" * 70)
    print("🧪 TESTING DEEPSEEK VALIDATOR INTEGRATION")
    print("=" * 70)
    print()

    # Initialize validator
    validator = DeepSeekValidator()

    # Mock trading signal data
    test_data = {
        'symbol': 'BTC/USD',
        'current_price': 50000.0,
        'technical_signals': {
            'rsi': 45.0,
            'macd_signal': 'BULLISH',
            'volume_ratio': 1.5
        },
        'sentiment': {
            'label': 'POSITIVE',
            'score': 0.7,
            'confidence': 0.85
        },
        'market_data': {
            'recent_candles': [
                {'open': 49000, 'close': 49500},
                {'open': 49500, 'close': 49800},
                {'open': 49800, 'close': 50000},
            ]
        }
    }

    print("📊 Testing with sample BTC/USD signal...")
    print()

    try:
        # Call validator
        result = await validator.validate_signal(
            symbol=test_data['symbol'],
            current_price=test_data['current_price'],
            technical_signals=test_data['technical_signals'],
            sentiment=test_data['sentiment'],
            market_data=test_data['market_data']
        )

        print("✅ VALIDATOR INTEGRATION TEST PASSED!")
        print()
        print(f"Action: {result['action']}")
        print(f"Confidence: {result['confidence']}%")
        print(f"Position Size: {result['position_size_percent']}%")
        print(f"Stop Loss: {result['stop_loss_percent']}%")
        print(f"Take Profit: {result['take_profit_percent']}%")
        print(f"Reasoning: {result['reasoning'][:200]}...")
        print()
        print("🎉 DeepSeek validator is working correctly in bot context!")
        return True

    except Exception as e:
        print(f"❌ VALIDATOR TEST FAILED: {e}")
        print()
        print("The proxy fix may not be working correctly.")
        return False

if __name__ == '__main__':
    success = asyncio.run(test_validator())
    exit(0 if success else 1)
