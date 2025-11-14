"""Quick test script for AI categorization."""

import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.abspath('.'))

# Load environment variables
load_dotenv()

from src.ai.categorizer import categorize_transaction

# Test transactions
test_cases = [
    {
        'description': 'STARBUCKS COFFEE',
        'merchant': 'Starbucks',
        'amount': 4.50
    },
    {
        'description': 'UBER TRIP TO AIRPORT',
        'merchant': 'Uber',
        'amount': 25.00
    },
    {
        'description': 'VODAFONE BILL',
        'merchant': 'Vodafone',
        'amount': 45.99
    },
    {
        'description': 'AMAZON PURCHASE',
        'merchant': 'Amazon',
        'amount': 89.99
    },
    {
        'description': 'NETFLIX SUBSCRIPTION',
        'merchant': 'Netflix',
        'amount': 15.99
    }
]

print("Testing AI Categorization")
print("=" * 60)

for i, test in enumerate(test_cases, 1):
    print(f"\nTest {i}: {test['description']}")
    print(f"  Merchant: {test['merchant']}, Amount: ${test['amount']}")

    result = categorize_transaction(
        description=test['description'],
        merchant=test['merchant'],
        amount=test['amount']
    )

    if result:
        print(f"  ✓ Category: {result['category']}")
        print(f"  ✓ Confidence: {result['confidence']:.2%}")
    else:
        print("  ✗ Categorization failed")

print("\n" + "=" * 60)
print("Test complete!")
