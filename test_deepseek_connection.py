#!/usr/bin/env python3
"""
Test DeepSeek API Connection
Diagnoses network issues preventing DeepSeek from working
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

def test_deepseek_connection():
    """Test if we can reach DeepSeek API"""

    print("=" * 70)
    print("🧪 DEEPSEEK CONNECTION DIAGNOSTIC TEST")
    print("=" * 70)
    print()

    # Load API key
    load_dotenv()
    api_key = os.getenv('DEEPSEEK_API_KEY')

    if not api_key:
        print("❌ DEEPSEEK_API_KEY not found in .env file")
        print("   Please add your API key to .env")
        return False

    print(f"✅ API Key found: {api_key[:20]}...{api_key[-10:]}")
    print()

    # Test 1: Basic connectivity
    print("📡 Test 1: Can we reach api.deepseek.com?")
    print("-" * 70)

    try:
        response = requests.get("https://api.deepseek.com", timeout=10)
        print(f"✅ Connection successful! Status: {response.status_code}")
    except requests.exceptions.ProxyError as e:
        print(f"❌ PROXY ERROR: {e}")
        print("   Your network has a proxy blocking the connection")
        print("   Solution: Disable proxy or configure Python to bypass it")
        return False
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT: Cannot reach api.deepseek.com")
        print("   Your network might be blocking this domain")
        print("   Solution: Check firewall/VPN settings")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

    print()

    # Test 2: API Authentication
    print("🔑 Test 2: Is the API key valid?")
    print("-" * 70)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Simple test request
    payload = {
        "model": "deepseek-chat",  # Use chat model for testing (faster)
        "messages": [
            {"role": "user", "content": "Say 'API working' if you can read this"}
        ],
        "max_tokens": 10
    }

    try:
        print("Sending test request to DeepSeek API...")
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            print("✅ API KEY IS VALID!")
            data = response.json()
            answer = data['choices'][0]['message']['content']
            print(f"✅ DeepSeek responded: '{answer}'")
            print()
            print("🎉 ALL TESTS PASSED!")
            print("DeepSeek API is working perfectly!")
            return True

        elif response.status_code == 401:
            print("❌ API KEY INVALID (401 Unauthorized)")
            print("   Your API key is wrong or expired")
            print("   Get a new key from: https://platform.deepseek.com")
            return False

        elif response.status_code == 429:
            print("⚠️ RATE LIMIT (429 Too Many Requests)")
            print("   You've used up your API quota")
            print("   Wait or upgrade your plan")
            return False

        else:
            print(f"❌ UNEXPECTED STATUS: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.ProxyError as e:
        print(f"❌ PROXY ERROR: {e}")
        print()
        print("🔧 FIX: Your network proxy is blocking DeepSeek")
        print()
        print("   Windows Solution:")
        print("   1. Open Command Prompt as Administrator")
        print("   2. Run: set HTTP_PROXY=")
        print("   3. Run: set HTTPS_PROXY=")
        print("   4. Restart your bot")
        print()
        print("   OR disable your VPN/Proxy temporarily")
        return False

    except requests.exceptions.Timeout:
        print("❌ TIMEOUT (30 seconds)")
        print("   DeepSeek API is too slow or blocked")
        print()
        print("🔧 Possible causes:")
        print("   • Corporate firewall blocking api.deepseek.com")
        print("   • VPN routing through restricted region")
        print("   • ISP blocking Chinese domains")
        print()
        print("🔧 Solutions:")
        print("   • Disable VPN")
        print("   • Check firewall settings")
        print("   • Try different network (mobile hotspot)")
        return False

    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

def test_network_proxy():
    """Check for proxy settings"""
    print()
    print("🌐 Checking for proxy settings...")
    print("-" * 70)

    http_proxy = os.getenv('HTTP_PROXY') or os.getenv('http_proxy')
    https_proxy = os.getenv('HTTPS_PROXY') or os.getenv('https_proxy')

    if http_proxy or https_proxy:
        print(f"⚠️ PROXY DETECTED:")
        if http_proxy:
            print(f"   HTTP_PROXY: {http_proxy}")
        if https_proxy:
            print(f"   HTTPS_PROXY: {https_proxy}")
        print()
        print("   This proxy might be blocking DeepSeek API")
        print("   Try running without proxy:")
        print("   • Windows: set HTTP_PROXY= && set HTTPS_PROXY=")
        print("   • Linux: unset HTTP_PROXY && unset HTTPS_PROXY")
    else:
        print("✅ No proxy environment variables detected")

    print()

if __name__ == '__main__':
    print()
    test_network_proxy()
    print()

    success = test_deepseek_connection()

    print()
    print("=" * 70)

    if success:
        print("✅ DeepSeek is ready to trade!")
        print("   Run your bot with: python run.py")
        sys.exit(0)
    else:
        print("❌ DeepSeek connection FAILED")
        print("   Fix the issues above before running the bot")
        sys.exit(1)
