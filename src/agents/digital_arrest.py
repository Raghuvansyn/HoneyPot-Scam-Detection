"""
Digital Arrest Prevention Module
Specialized handling for authority-impersonation scams.
"""

from datetime import datetime
from typing import Dict
import logging

logger = logging.getLogger(__name__)

# Multi-word phrases only — avoids false positives from single common words
AUTHORITY_KEYWORDS = [
    "cbi officer", "cbi inspector", "police inspector", "ips officer",
    "enforcement directorate", "ed officer", "income tax officer",
    "customs officer", "cyber crime", "narcotics bureau",
    "trai officer", "telecom authority",
    "supreme court", "high court", "magistrate",
]

SCAM_TRIGGER_PHRASES = [
    "parcel seized", "drugs found", "fake passport", "forged document",
    "money laundering", "terror financing", "illegal activities",
    "aadhaar linked", "aadhaar misused",
    "under investigation", "fir registered",
    "arrest warrant", "non-bailable warrant",
    "digital arrest", "cyber arrest",
]

PRESSURE_TACTICS = [
    "do not inform", "don't tell anyone", "stay on call",
    "do not disconnect", "video call hearing", "skype hearing", "zoom hearing",
    "security deposit", "bail amount", "stay the arrest", "stop the warrant",
    "transfer to safe account", "verification account",
    "within 3 hours", "within 24 hours",
    "immediate arrest", "contempt of court",
]


def detect_digital_arrest(text: str) -> Dict:
    text_lower = text.lower()

    authority_hits = [kw for kw in AUTHORITY_KEYWORDS if kw in text_lower]
    trigger_hits = [p for p in SCAM_TRIGGER_PHRASES if p in text_lower]
    pressure_hits = [t for t in PRESSURE_TACTICS if t in text_lower]

    authority_score = len(authority_hits)
    trigger_score = len(trigger_hits)
    pressure_score = len(pressure_hits)
    total_score = authority_score + trigger_score + pressure_score

    is_digital_arrest = False
    severity = "NORMAL"

    # need at least 1 authority claim + 1 trigger/pressure, or explicit phrase
    if authority_score >= 1 and (trigger_score + pressure_score) >= 1 and total_score >= 3:
        is_digital_arrest = True
        severity = "CRITICAL"
    elif authority_score >= 1 and total_score >= 2:
        is_digital_arrest = True
        severity = "HIGH"
    elif "digital arrest" in text_lower or "cyber arrest" in text_lower:
        is_digital_arrest = True
        severity = "CRITICAL"

    result = {
        "is_digital_arrest": is_digital_arrest,
        "severity": severity,
        "confidence": min(total_score * 0.25, 1.0),
        "scores": {
            "authority_impersonation": authority_score,
            "scam_triggers": trigger_score,
            "pressure_tactics": pressure_score,
            "total": total_score,
        },
        "detected_patterns": {
            "authorities_claimed": authority_hits,
            "threats_used": trigger_hits,
            "pressure_applied": pressure_hits,
        },
    }

    if is_digital_arrest:
        logger.critical(f"DIGITAL ARREST DETECTED | severity={severity} | score={total_score}")

    return result


def generate_emergency_guidance(threat_assessment: Dict) -> Dict:
    patterns = threat_assessment["detected_patterns"]
    guidance = {
        "primary_action": "HANG_UP_IMMEDIATELY",
        "urgency_level": threat_assessment["severity"],
        "victim_instructions": [
            "HANG UP the call right now",
            "This is a SCAM - you are NOT under arrest",
            "Real police/CBI/courts NEVER call and demand money",
            "Call 1930 (National Cyber Crime Helpline)",
            "Report at cybercrime.gov.in",
            "Do NOT transfer any money",
            "Do NOT share Aadhaar/PAN/OTP",
        ],
        "helpline": {"number": "1930", "name": "National Cyber Crime Helpline", "portal": "cybercrime.gov.in"},
    }
    if patterns["authorities_claimed"]:
        claimed = patterns["authorities_claimed"][0].upper()
        guidance["specific_warning"] = f"Caller claims to be from {claimed}. This is FAKE."
    return guidance


def alert_law_enforcement(session_id: str, message: str, threat_assessment: Dict, intelligence: Dict) -> Dict:
    alert_payload = {
        "alert_type": "DIGITAL_ARREST_IN_PROGRESS",
        "severity": threat_assessment["severity"],
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "scam_message": message[:200],
        "threat_assessment": threat_assessment,
        "extracted_intelligence": intelligence,
        "recommended_action": "IMMEDIATE_INTERVENTION",
        "priority": "CRITICAL",
    }

    logger.critical(f"LAW ENFORCEMENT ALERT | session={session_id} | severity={threat_assessment['severity']}")

    try:
        import json, os
        os.makedirs("logs", exist_ok=True)
        with open(os.path.join("logs", "emergency.log"), "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": datetime.now().isoformat(),
                "level": "CRITICAL",
                "type": "DIGITAL_ARREST",
                "session_id": session_id,
                "payload": alert_payload,
            }) + "\n")
    except Exception as e:
        logger.error(f"Failed to write emergency log: {e}")

    return alert_payload


DIGITAL_ARREST_STATS = {
    "total_detected": 0,
    "claimed_authorities": {},
    "peak_times": [],
}


def track_digital_arrest_attempt(threat_assessment: Dict):
    DIGITAL_ARREST_STATS["total_detected"] += 1
    for authority in threat_assessment["detected_patterns"]["authorities_claimed"]:
        DIGITAL_ARREST_STATS["claimed_authorities"][authority] = (
            DIGITAL_ARREST_STATS["claimed_authorities"].get(authority, 0) + 1
        )
    DIGITAL_ARREST_STATS["peak_times"].append({
        "timestamp": datetime.now().isoformat(),
        "severity": threat_assessment["severity"],
    })
