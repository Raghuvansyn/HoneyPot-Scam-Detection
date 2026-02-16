"""
Quick test to verify callback logic locally
"""
from src.utils.callbacks import should_send_callback

# Test scenarios
test_cases = [
    {"totalMessages": 3, "scamDetected": True, "extractedIntelligence": {}, "expected": False, "reason": "Turn 3 - too early"},
    {"totalMessages": 6, "scamDetected": True, "extractedIntelligence": {}, "expected": False, "reason": "Turn 6 - too early"},
    {"totalMessages": 9, "scamDetected": True, "extractedIntelligence": {}, "expected": False, "reason": "Turn 9 - still too early"},
    {"totalMessages": 10, "scamDetected": True, "extractedIntelligence": {}, "expected": False, "reason": "Turn 10 - minimum reached but no intel"},
    {"totalMessages": 12, "scamDetected": True, "extractedIntelligence": {"phoneNumbers": ["+91-123"], "upiIds": ["test@upi"], "bankAccounts": ["123"], "phishingLinks": ["http://test.com"]}, "expected": True, "reason": "Turn 12 with 4 categories"},
    {"totalMessages": 12, "scamDetected": True, "extractedIntelligence": {"phoneNumbers": ["+91-123"]}, "expected": False, "reason": "Turn 12 with only 1 category - keep going"},
    {"totalMessages": 15, "scamDetected": True, "extractedIntelligence": {"phoneNumbers": ["+91-123"], "upiIds": ["test@upi"], "bankAccounts": ["123"]}, "expected": True, "reason": "Turn 15 with 3 categories"},
    {"totalMessages": 20, "scamDetected": True, "extractedIntelligence": {}, "expected": True, "reason": "Turn 20 - hard max"},
]

print("Testing callback logic...")
print("=" * 80)

passed = 0
failed = 0

for i, test in enumerate(test_cases, 1):
    state = {
        "totalMessages": test["totalMessages"],
        "scamDetected": test["scamDetected"],
        "extractedIntelligence": test["extractedIntelligence"]
    }
    
    result = should_send_callback(state)
    expected = test["expected"]
    
    status = "✅ PASS" if result == expected else "❌ FAIL"
    if result == expected:
        passed += 1
    else:
        failed += 1
    
    print(f"{status} Test {i}: {test['reason']}")
    print(f"   Expected: {expected}, Got: {result}")
    print()

print("=" * 80)
print(f"Results: {passed} passed, {failed} failed")

if failed == 0:
    print("✅ All tests passed! Sessions will now run 10+ turns.")
else:
    print("❌ Some tests failed. Check the logic.")
