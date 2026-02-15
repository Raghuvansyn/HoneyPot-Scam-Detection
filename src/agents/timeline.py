"""
Timeline Analysis Agent
Analyzes conversation retrospectively to identify scam phases and generate summary.
"""

from typing import List, Dict
from src.utils import logger


def analyze_scam_timeline(conversation_history: list) -> str:
    phases = detect_scam_phases(conversation_history)
    if not phases:
        return "No clear scam pattern detected in conversation."
    return build_timeline_summary(phases)


def detect_scam_phases(conversation_history: list) -> List[Dict]:
    phase_patterns = {
        "urgency": {"keywords": ["urgent", "immediately", "today", "now", "expire", "deadline", "soon", "quickly"], "description": "Creates time pressure"},
        "authority": {"keywords": ["bank", "government", "police", "official", "department", "manager", "officer"], "description": "Impersonates authority"},
        "fear": {"keywords": ["blocked", "suspended", "legal action", "arrest", "fine", "penalty", "closed"], "description": "Threatens consequences"},
        "credential_request": {"keywords": ["otp", "password", "pin", "cvv", "verify", "confirm", "code"], "description": "Requests credentials"},
        "payment_redirection": {"keywords": ["send money", "transfer", "pay", "payment", "amount", "rupees", "deposit", "upi"], "description": "Demands payment"},
        "impersonation": {"keywords": ["i am from", "calling from", "representative", "agent", "this is", "my name is"], "description": "Identity fraud"},
    }

    detected_phases = []
    for i, msg in enumerate(conversation_history):
        if msg.get("sender") != "scammer":
            continue
        text = msg.get("text", "").lower()
        for phase_name, phase_data in phase_patterns.items():
            matches = [kw for kw in phase_data["keywords"] if kw in text]
            if matches and not any(p["phase"] == phase_name for p in detected_phases):
                detected_phases.append({"phase": phase_name, "description": phase_data["description"], "first_seen": i + 1})

    detected_phases.sort(key=lambda x: x["first_seen"])
    return detected_phases


PHASE_DISPLAY = {
    "urgency": "Urgency Tactics", "authority": "Authority Impersonation",
    "fear": "Fear & Threats", "credential_request": "Credential Theft",
    "payment_redirection": "Payment Fraud", "impersonation": "Identity Fraud",
}


def build_timeline_summary(phases: List[Dict]) -> str:
    if not phases:
        return "No clear scam tactics identified"

    phase_list = [f"({i}) {PHASE_DISPLAY.get(p['phase'], p['phase'])} - {p['description']}" for i, p in enumerate(phases, 1)]
    summary = f"Scam executed in {len(phases)}-phase attack: " + " | ".join(phase_list)

    pattern = classify_scam_pattern(phases)
    if pattern:
        summary += f" | Pattern: {pattern}"
    return summary


def classify_scam_pattern(phases: List[Dict]) -> str:
    names = [p["phase"] for p in phases]

    if "urgency" in names and "authority" in names and "credential_request" in names:
        return "Classic Bank Fraud"
    if "urgency" in names and "payment_redirection" in names:
        return "Payment Fraud"
    if "fear" in names and "credential_request" in names:
        return "Intimidation Fraud"
    if "authority" in names and "payment_redirection" in names:
        return "Impersonation Fraud"
    if len(names) >= 4:
        return "Multi-Stage Scam"
    return "Standard Scam"


def get_conversation_summary(
    conversation_history: list, extracted_intelligence: dict,
    detection_confidence: float, scam_detected: bool,
) -> str:
    detection_status = "SCAM" if scam_detected else "LEGITIMATE"
    parts = [f"Detection: {detection_status} (confidence: {detection_confidence:.2f})"]

    if scam_detected and len(conversation_history) >= 3:
        parts.append(analyze_scam_timeline(conversation_history))

    intel_details = []
    for key, label in [("phoneNumbers", "phone(s)"), ("upiIds", "UPI(s)"), ("phishingLinks", "link(s)"), ("bankAccounts", "account(s)"), ("emailAddresses", "email(s)")]:
        items = extracted_intelligence.get(key, [])
        if items:
            intel_details.append(f"{len(items)} {label}")

    if intel_details:
        parts.append(f"Intelligence: {', '.join(intel_details)}")
    elif scam_detected:
        parts.append("Intelligence: none extracted")

    return " | ".join(parts)


def calculate_confidence_level(detection_confidence: float, intelligence_count: int, message_count: int) -> float:
    score = detection_confidence
    if intelligence_count >= 3:
        score += 0.1
    elif intelligence_count >= 1:
        score += 0.05

    if message_count >= 10:
        score += 0.05

    return min(score, 1.0)
