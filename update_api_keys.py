#!/usr/bin/env python3
"""
Quick script to update Kraken API keys in .env file
"""

import os
import sys

print("=" * 70)
print("🔑 KRAKEN API KEY UPDATER")
print("=" * 70)
print()
print("Get your new API keys from: https://www.kraken.com/u/security/api")
print()
print("REQUIRED PERMISSIONS:")
print("  ✅ Query Funds")
print("  ✅ Query Open Orders & Trades")
print("  ✅ Query Closed Orders & Trades")
print("  ✅ Create & Modify Orders")
print("  ✅ Cancel/Close Orders")
print()
print("=" * 70)
print()

# Get new API keys from user
api_key = input("Enter your NEW Kraken API Key: ").strip()
if not api_key:
    print("❌ API key cannot be empty!")
    sys.exit(1)

api_secret = input("Enter your NEW Kraken Private Key (Secret): ").strip()
if not api_secret:
    print("❌ API secret cannot be empty!")
    sys.exit(1)

print()
print("Testing API connection...")

# Test the connection
try:
    import ccxt

    exchange = ccxt.kraken({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True
    })

    balance = exchange.fetch_balance()
    usd_balance = balance.get('USD', {}).get('free', 0)

    print("✅ API Connection successful!")
    print(f"📊 Your USD Balance: ${usd_balance:.2f}")
    print()

except Exception as e:
    print(f"❌ API Connection FAILED: {e}")
    print()
    print("Please check:")
    print("1. API key is correct (no extra spaces)")
    print("2. Private key is correct (no extra spaces)")
    print("3. API key has required permissions")
    print("4. API key is not expired")
    sys.exit(1)

# Update .env file
print("Updating .env file...")

env_file = '.env'
if not os.path.exists(env_file):
    print(f"❌ .env file not found!")
    sys.exit(1)

# Read current .env
with open(env_file, 'r') as f:
    lines = f.readlines()

# Update API key lines
updated = False
for i, line in enumerate(lines):
    if line.startswith('KRAKEN_API_KEY='):
        lines[i] = f'KRAKEN_API_KEY={api_key}\n'
        updated = True
    elif line.startswith('KRAKEN_API_SECRET='):
        lines[i] = f'KRAKEN_API_SECRET={api_secret}\n'
        updated = True

if not updated:
    print("⚠️  Could not find KRAKEN_API_KEY lines in .env")
    print("Adding them manually...")
    lines.append(f'\nKRAKEN_API_KEY={api_key}\n')
    lines.append(f'KRAKEN_API_SECRET={api_secret}\n')

# Write updated .env
with open(env_file, 'w') as f:
    f.writelines(lines)

print("✅ .env file updated successfully!")
print()
print("=" * 70)
print("🎉 API KEYS UPDATED AND VERIFIED!")
print("=" * 70)
print()
print("You can now start the bot:")
print("  python run.py")
print()
print("Or test again with:")
print("  python3 start_trading.py")
print()
