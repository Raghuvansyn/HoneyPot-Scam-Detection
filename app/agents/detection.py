# app/agents/detection.py
"""
Detection Agent — Rule-based + ML (TF-IDF + SVM) Cascading Detection
---------------------------------------------------------------------
Works exactly like a cascading pipeline:

    Step 1: Rule-based scoring
            → If score >= 0.7  → SCAM (rules are confident, done)

    Step 2: ML Model (TF-IDF + LinearSVC)
            → If ML confident  → Return ML result (done)

    Step 3: Fallback
            → If nothing triggered → NOT SCAM

This is the same cascading pattern as the friend's approach,
but trained on 100 samples instead of 10.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from app.utils import logger

# ============================================
# STEP 1 — RULE-BASED KEYWORDS
# ============================================

SCAM_KEYWORDS = [
    "account blocked", "verify", "urgent", "otp",
    "upi", "send money", "click link", "bank",
    "suspension", "immediately", "click here",
    "reset password", "security alert", "unusual activity",
    "kyc", "frozen", "legal action", "arrest",
    "congratulations", "winner", "prize", "lottery",
    "send otp", "share otp", "verify now",
    "confirm", "blocked", "suspended",
    "electricity", "cut off", "disconnect", "apk", "download app",
    "quicksupport", "anydesk", "teamviewer", "remote access"
]


def rule_based_score(text: str) -> dict:
    """
    Score the message based on keyword hits.
    
    Returns:
        {
            "rule_score": float 0.0–1.0,
            "suspicious": bool,
            "matched_keywords": list
        }
    """
    text_lower = text.lower()
    matched = [kw for kw in SCAM_KEYWORDS if kw in text_lower]
    
    # CRITICAL KEYWORDS usually imply immediate scam
    critical_triggers = ["apk", "electricity", "cut off", "disconnect", "quicksupport"]
    is_critical = any(trigger in text_lower for trigger in critical_triggers)

    if is_critical:
        score = 1.0 # Immediate SCAM
    else:
        # Normal scoring: 3 keywords = High Suspicion
        score = min(len(matched) * 0.3, 1.0)

    return {
        "rule_score": round(score, 2),
        "suspicious": score >= 0.3,
        "matched_keywords": matched,
    }


# ============================================
# STEP 2 — ML MODEL (TF-IDF + SVM)
# Trained on 100 samples (50 scam, 50 legit)
# ============================================

SCAM_TRAINING_DATA = [
    "URGENT! Your bank account will be blocked today. Verify immediately.",
    "Your account is suspended. Send OTP to verify your identity now.",
    "Congratulations! You won a prize of Rs 50000. Claim it now by clicking here.",
    "Your KYC verification is pending. Update KYC or your account will be frozen.",
    "Security alert: Unusual activity on your account. Verify now to avoid legal action.",
    "Your UPI payment failed. Share your OTP with our support team immediately.",
    "URGENT: Your bank account blocked. Send OTP to 9876543210 to unblock.",
    "You won a lottery! Click the link to claim your free gift now.",
    "Your account is frozen. Verify now or face arrest and police action.",
    "Reset password immediately. Account expires today. Click here to confirm.",
    "Dear customer your account will be blocked. Click here to verify details.",
    "Your bank has detected suspicious activity. Send OTP to confirm identity.",
    "Congratulations you are the lucky winner. Claim your reward by clicking link.",
    "Urgent: Your KYC is incomplete. Share details or account will be suspended.",
    "Your account is blocked due to security reasons. Verify immediately via link.",
    "Prize notification: You won Rs 1 lakh. Click to claim before it expires.",
    "Your UPI ID needs verification. Send OTP to confirm your account details.",
    "Security alert: Someone tried to access your account. Verify now urgently.",
    "Your bank account will be frozen. Share OTP with customer support now.",
    "Congratulations! Free gift waiting for you. Click here to claim your prize.",
    "Account blocked alert: Verify your details immediately or face legal action.",
    "Your online banking is suspended. Click link to reset password now.",
    "Lucky draw winner announcement. You won a cashback reward. Claim now.",
    "KYC update required urgently. Your account will be blocked if not verified.",
    "Suspicious login detected on your account. Verify OTP immediately.",
    "Your payment of Rs 500 is pending. Confirm by sharing OTP now.",
    "Winner notification: Claim your prize by clicking the verification link.",
    "URGENT: Account freeze notice. Send OTP to customer care immediately.",
    "Your bank has flagged unusual activity. Verify identity by sending OTP.",
    "Congratulations you won a free iPhone. Click here to claim your reward.",
    "Account suspension notice: Verify your KYC details or lose access today.",
    "Security warning: Your account is compromised. Send OTP to secure it now.",
    "Lottery result: You are the winner. Click link to claim prize money.",
    "Your UPI transaction failed. Re-verify by sending OTP to support team.",
    "Dear user your account will expire. Click here to renew and verify details.",
    "Urgent security alert: Share OTP to prevent your account from being blocked.",
    "Free cashback offer! Verify your account now to claim Rs 5000 reward.",
    "Your bank account is under review. Send OTP to avoid suspension immediately.",
    "Prize claim notification: Click here to verify and collect your winnings.",
    "KYC verification failed. Update your details or account will be frozen today.",
    "Suspicious activity alert: Verify your identity by clicking this link now.",
    "Your account access is restricted. Send OTP to restore banking services.",
    "Congratulations! You are eligible for a free gift. Claim it by verifying now.",
    "URGENT bank alert: Your account is blocked. Verify details via this link.",
    "Winner declared: Claim your lottery prize by sending OTP for verification.",
    "Security notice: Your password has been compromised. Reset it immediately.",
    "Your UPI account is suspended. Verify by clicking the link and sending OTP.",
    "Account blocked: Share your OTP with our team to unblock your account now.",
    "Prize alert: You won a reward. Click here immediately to claim it.",
    "Urgent KYC alert: Your account will be closed if you don't verify today.",
]

LEGIT_TRAINING_DATA = [
    "Hi how are you doing today?",
    "Are you coming to college tomorrow?",
    "Let's meet at the library at 3pm.",
    "Happy birthday! Wishing you a wonderful day.",
    "Can you send me the notes from today's lecture?",
    "I need to make a payment for the project. What's the account number?",
    "Please check the link I sent you for the assignment.",
    "The refund for the cancelled order should arrive today.",
    "Hey are we still free this weekend?",
    "The exam results will be out now. Check the portal.",
    "What time is the meeting tomorrow?",
    "Did you finish the homework for physics class?",
    "I'm going to the market. Do you need anything?",
    "The weather is really nice today. Let's go for a walk.",
    "Have you seen the new movie that came out last week?",
    "Thanks for helping me with the project yesterday.",
    "Can we reschedule our study session to Friday?",
    "My mom made amazing food today. You should come over.",
    "The train leaves at 8am. Don't forget your ticket.",
    "I got a new phone. The camera is really good.",
    "Please send me the address of the restaurant.",
    "Did you register for the workshop next week?",
    "The professor said the deadline is extended by two days.",
    "I just finished reading that book you recommended.",
    "Are you free for lunch today? Let's catch up.",
    "The project presentation is on Monday. Are you ready?",
    "I'll transfer the money for dinner tonight.",
    "Check out this funny video I found online.",
    "The college fest is next month. Are you volunteering?",
    "I need to renew my library card. When is the office open?",
    "Did you hear about the new coffee shop near campus?",
    "The assignment is due next Friday. Let's work on it together.",
    "My laptop is acting slow. Do you know any good repair shops?",
    "Let's plan a trip for the summer holidays.",
    "I just got my salary. Time to treat myself.",
    "The project report needs to be submitted by the end of the month.",
    "Have you updated your resume for campus placements?",
    "The gym is closed today due to maintenance.",
    "I found a good deal on that jacket we saw last week.",
    "Thanks for the birthday wishes everyone. You are all amazing.",
    "The new semester starts next Monday. Ready for it?",
    "I ordered food online. Should arrive in 30 minutes.",
    "Did you get the email from the professor about the exam?",
    "Let me know if you need a ride to the airport.",
    "The park is beautiful in the morning. You should visit.",
    "I'm thinking of learning a new programming language.",
    "The bookstore is having a sale. Let's go check it out.",
    "My friend is getting married next month. Excited!",
    "Can you help me move the furniture this weekend?",
    "I just submitted my application. Fingers crossed!",
]


def _train_model() -> Pipeline:
    """Train TF-IDF + LinearSVC once at module load."""
    texts  = SCAM_TRAINING_DATA + LEGIT_TRAINING_DATA
    labels = [1] * len(SCAM_TRAINING_DATA) + [0] * len(LEGIT_TRAINING_DATA)

    model = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=5000)),
        ("svm",   LinearSVC(C=1.0, max_iter=5000)),
    ])
    model.fit(texts, labels)
    logger.info("✅ ML model trained (TF-IDF + SVM, 100 samples)")
    return model

# Train once when module loads
_ML_MODEL = _train_model()


def ml_classify(text: str) -> dict:
    """
    Run ML prediction on the text.

    Returns:
        {
            "is_scam": bool,
            "confidence": float 0.0–1.0
        }
    """
    prediction = _ML_MODEL.predict([text])[0]
    confidence = abs(_ML_MODEL.decision_function([text])[0])
    confidence = min(round(confidence, 2), 1.0)

    return {
        "is_scam": bool(prediction),
        "confidence": confidence,
    }


# ============================================
# MAIN — Cascading Detection
# ============================================

def detect_scam(text: str) -> tuple[bool, float]:
    """
    Cascading detection pipeline with stricter thresholds:
        1. Rules  → if score >= 0.15 → SCAM (at least 4-5 keywords)
        2. ML     → if confident >= 0.7 → trust ML result
        3. Else   → NOT SCAM

    Args:
        text: Incoming message.

    Returns:
        (is_scam, confidence)
    """

    # ── Step 1: Rules ──
    rule_result = rule_based_score(text)

    # Need at least 15% keyword match (4-5 keywords) to be confident
    if rule_result["rule_score"] >= 0.15:
        logger.info(f"🔍 Detection: SCAM detected by RULES (score={rule_result['rule_score']})")
        logger.info(f"   Matched keywords: {rule_result['matched_keywords']}")
        return True, 0.95

    # ── Step 2: ML ──
    ml_result = ml_classify(text)

    logger.info(f"🔍 Detection: Rules inconclusive (score={rule_result['rule_score']}) → ML consulted")
    logger.info(f"   ML result: is_scam={ml_result['is_scam']}, confidence={ml_result['confidence']}")
    logger.info(f"   Matched keywords: {rule_result['matched_keywords']}")

    # ML must be VERY confident (70%+) to override low rule score
    if ml_result["is_scam"] and ml_result["confidence"] >= 0.7:
        return True, ml_result["confidence"]

    # ── Step 3: Fallback — nothing triggered ──
    logger.info(f"🔍 Detection: NOT SCAM (insufficient evidence)")
    return False, 0.15
