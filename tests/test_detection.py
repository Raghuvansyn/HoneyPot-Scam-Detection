# tests/test_detection.py
"""
Detection Agent — Accuracy Test Suite
--------------------------------------
Shows exactly how the cascading detection works:
  Rules → ML → Result

Usage:
    cd <your project root>
    python tests/test_detection.py
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.detection import detect_scam, rule_based_score, ml_classify

# ============================================
# TEST CASES
# ============================================

TEST_CASES = [

    # ── SCAM MESSAGES ──
    ("URGENT! Your bank account will be blocked today. Verify immediately by clicking this link: http://fake-bank.com/verify",   True,  "Classic banking scam with link"),
    ("Your account is suspended. Send OTP 4521 to verify your identity immediately.",                                            True,  "OTP phishing scam"),
    ("Congratulations! You have won a prize of Rs 50,000. Claim your reward now by clicking here.",                              True,  "Prize/lottery scam"),
    ("Dear customer, your KYC verification is pending. Click here to update KYC or your account will be frozen.",                True,  "KYC scam with freeze threat"),
    ("Security alert: Unusual activity detected on your account. Verify now to avoid legal action.",                             True,  "Security alert + legal threat"),
    ("Your UPI payment has failed. Verify immediately by sharing your OTP with our support team.",                               True,  "UPI + OTP scam"),
    ("URGENT: Your bank account will be blocked. Send your OTP to 9876543210 to unblock.",                                      True,  "Urgent bank block + OTP demand"),
    ("You have won a lottery prize! Click the link to claim your free gift: http://scam.com/claim",                              True,  "Lottery + free gift + link"),
    ("Your account is frozen due to suspicious activity. Verify now or face arrest and police action.",                          True,  "Freeze + threat scam"),
    ("Reset password immediately. Your account will expire today. Click here to confirm your details.",                          True,  "Password reset phishing"),

    # ── LEGITIMATE MESSAGES ──
    ("Hi, how are you doing today?",                                                                                            False, "Simple greeting"),
    ("Are you coming to college tomorrow?",                                                                                     False, "College plan"),
    ("Let's meet at the library at 3pm.",                                                                                       False, "Meeting plan"),
    ("Happy birthday! Wishing you a wonderful day.",                                                                           False, "Birthday wish"),
    ("Can you send me the notes from today's lecture?",                                                                        False, "Notes request"),
    ("I need to make a payment for the project. What's the account number?",                                                    False, "Legit payment discussion"),
    ("Please check the link I sent you for the assignment.",                                                                    False, "Sharing a link normally"),
    ("The refund for the cancelled order should arrive today.",                                                                  False, "Legit refund mention"),
    ("Hey, are we still free this weekend?",                                                                                    False, "'free' in casual context"),
    ("The exam results will be out now. Check the portal.",                                                                     False, "'now' in casual context"),
]


def run_tests():
    print("=" * 80)
    print("  DETECTION AGENT — CASCADING ACCURACY TEST (Rules → ML)")
    print("=" * 80 + "\n")

    passed = 0
    failed = 0
    false_positives  = []
    false_negatives  = []

    rules_caught  = 0   # how many scams rules caught alone
    ml_caught     = 0   # how many scams ML caught (rules missed)

    for i, (text, expected, description) in enumerate(TEST_CASES, 1):

        # Run each layer individually so we can show the breakdown
        rule  = rule_based_score(text)
        ml    = ml_classify(text)
        # Run the actual cascading detect
        is_scam, confidence = detect_scam(text)

        correct = (is_scam == expected)
        status  = "✅ PASS" if correct else "❌ FAIL"

        # Figure out which layer made the call
        if is_scam and rule["rule_score"] >= 0.7:
            source = "RULES"
            rules_caught += 1
        elif is_scam:
            source = "ML"
            ml_caught += 1
        else:
            source = "—"

        exp_label = "SCAM"  if expected else "LEGIT"
        got_label = "SCAM"  if is_scam  else "LEGIT"

        print(f"  [{status}]  Test {i:>2} | Expected: {exp_label:>5} | Got: {got_label:>5} | conf={confidence:.2f} | caught by: {source}")
        print(f"          Rules: {rule['rule_score']:.2f} | ML: {'SCAM' if ml['is_scam'] else 'LEGIT'} ({ml['confidence']:.2f}) | {description}")
        print()

        if correct:
            passed += 1
        else:
            failed += 1
            if not expected and is_scam:
                false_positives.append((i, description))
            else:
                false_negatives.append((i, description))

    # ── SUMMARY ──
    total    = passed + failed
    accuracy = (passed / total) * 100

    print("=" * 80)
    print("  SUMMARY")
    print("=" * 80)
    print(f"  Total tests       : {total}")
    print(f"  Passed            : {passed}")
    print(f"  Failed            : {failed}")
    print(f"  Accuracy          : {accuracy:.1f}%")
    print(f"  False Positives   : {len(false_positives)}  (legit flagged as scam)")
    print(f"  False Negatives   : {len(false_negatives)}  (scam missed)")
    print(f"  ---")
    print(f"  Scams caught by RULES : {rules_caught}")
    print(f"  Scams caught by ML    : {ml_caught}")

    if false_positives:
        print(f"\n  ⚠️  False Positives:")
        for num, desc in false_positives:
            print(f"     Test {num}: {desc}")
    if false_negatives:
        print(f"\n  ⚠️  False Negatives:")
        for num, desc in false_negatives:
            print(f"     Test {num}: {desc}")

    print("=" * 80 + "\n")
    return accuracy


if __name__ == "__main__":
    accuracy = run_tests()
    sys.exit(0 if accuracy >= 85 else 1)
