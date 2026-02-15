
"""
Digital Arrest Prevention Module
Specialized handling for India's #1 scam type 2024
"""

from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Digital Arrest Signature Patterns
AUTHORITY_KEYWORDS = [
    "cbi", "cbi officer", "cbi inspector", "inspector", "officer",
    "police", "police inspector", "ips officer", "cyber crime",
    "enforcement directorate", "ed officer",
    "income tax", "income tax officer", "tax",
    "customs", "customs officer",
    "trai", "telecom authority", "telecom",
    "supreme court", "high court", "court",
    "judge", "magistrate", "narcotics bureau"
]

SCAM_TRIGGER_PHRASES = [
    "parcel seized", "parcel found", "courier seized", "parcel",
    "drugs found", "narcotics", "contraband", "drugs",
    "fake passport", "forged document", "passport", "fake", "forged",
    "money laundering", "terror financing", "laundering", "terror",
    "illegal activities", "fraud case", "illegal", "criminal",
    "aadhaar linked", "aadhaar misused", "aadhaar",
    "bank accounts opened", "multiple accounts", "bank", "account", "id",
    "under investigation", "fir registered", "investigation", "fir", "case",
    "arrest warrant", "non-bailable warrant", "warrant", "arrest",
    "digital arrest", "cyber arrest",
    "custody", "jail", "jailed", "surrender", "linked",
    "disconnect", "bailable", "activity", "activities",
    "simcard", "number", "mobile", "sim", "card",
    "fedex", "dhl", "financing", "file", "report", "registered",
    "pan", "funding", "courier", "cyber",
    "immediate", "stop", "pay", "order", "digitally",
    "crime", "phone", "turning", "off", "transer", "coming", "come",
    "contempt", "call", "turn", "misused",
    "ads", "block", "blocked"
]

PRESSURE_TACTICS = [
    "do not inform", "don't tell anyone", "secret", "confidential",
    "do not disconnect", "stay on call", "disconnect", "cut",
    "video call hearing", "skype hearing", "zoom hearing", "video", "skype", "zoom",
    "security deposit", "bail amount", "deposit", "bail",
    "stay the arrest", "stop the warrant", "stop",
    "within 3 hours", "within 24 hours", "hours",
    "immediate action", "urgent payment", "immediate", "urgent", "action",
    "transfer to safe account", "verification account", "transfer", "payment",
    "verify", "face", "attend", "statement", "interrogation",
    "camera", "room", "home", "share", "details", "transaction", "link",
    "family", "tell"
]


def detect_digital_arrest(text: str) -> Dict:
    """
    Specialized detection for digital arrest scams
    Returns detailed threat assessment
    """
    text_lower = text.lower()
    
    # Score different components
    authority_score = sum(1 for kw in AUTHORITY_KEYWORDS if kw in text_lower)
    trigger_score = sum(1 for phrase in SCAM_TRIGGER_PHRASES if phrase in text_lower)
    pressure_score = sum(1 for tactic in PRESSURE_TACTICS if tactic in text_lower)
    
    total_score = authority_score + trigger_score + pressure_score
    
    # Determine threat level
    is_digital_arrest = False
    severity = "NORMAL"
    
    # Lowered threshold to >= 2 to match previous sensitivity
    if total_score >= 3:
        is_digital_arrest = True
        severity = "CRITICAL"
    elif total_score >= 2:
        is_digital_arrest = True
        severity = "HIGH"
    elif "digital arrest" in text_lower or "cyber arrest" in text_lower:
        is_digital_arrest = True
        severity = "CRITICAL"
    
    # Build detailed response
    result = {
        "is_digital_arrest": is_digital_arrest,
        "severity": severity,
        "confidence": min(total_score * 0.25, 1.0),
        "scores": {
            "authority_impersonation": authority_score,
            "scam_triggers": trigger_score,
            "pressure_tactics": pressure_score,
            "total": total_score
        },
        "detected_patterns": {
            "authorities_claimed": [kw for kw in AUTHORITY_KEYWORDS if kw in text_lower],
            "threats_used": [phrase for phrase in SCAM_TRIGGER_PHRASES if phrase in text_lower],
            "pressure_applied": [tactic for tactic in PRESSURE_TACTICS if tactic in text_lower]
        }
    }
    
    if is_digital_arrest:
        logger.critical(f"[CRITICAL] DIGITAL ARREST DETECTED - Severity: {severity} - Score: {total_score}")
    
    return result


def generate_emergency_guidance(threat_assessment: Dict) -> Dict:
    """Generate victim guidance based on threat level"""
    
    severity = threat_assessment["severity"]
    patterns = threat_assessment["detected_patterns"]
    
    guidance = {
        "primary_action": "HANG_UP_IMMEDIATELY",
        "urgency_level": severity,
        "victim_instructions": [
            "HANG UP the call right now",
            "This is a SCAM - you are NOT under arrest",
            "Real police/CBI/courts NEVER call and demand money",
            "Call 1930 (National Cyber Crime Helpline)",
            "Report at cybercrime.gov.in",
            "Do NOT transfer any money",
            "Do NOT share Aadhaar/PAN/OTP"
        ],
        "helpline": {
            "number": "1930",
            "name": "National Cyber Crime Helpline",
            "portal": "cybercrime.gov.in"
        },
        "what_real_police_never_do": [
            "Call and threaten immediate arrest",
            "Demand money to 'stay arrest' or 'post bail'",
            "Conduct hearings over Skype/Zoom/Video call",
            "Ask you to transfer money to 'safe account'",
            "Tell you to isolate yourself or not inform family",
            "Request OTP, Aadhaar, or bank details over call"
        ]
    }
    
    # Add specific warnings based on detected patterns
    if patterns["authorities_claimed"]:
        claimed_auth = patterns["authorities_claimed"][0].upper()
        guidance["specific_warning"] = (
            f"The caller claims to be from {claimed_auth}. "
            f"This is FAKE. Real {claimed_auth} never operates this way."
        )
    
    return guidance


def alert_law_enforcement(
    session_id: str,
    message: str,
    threat_assessment: Dict,
    intelligence: Dict
) -> Dict:
    """
    Send emergency alert to law enforcement
    For digital arrest, this gets highest priority
    """
    
    alert_payload = {
        "alert_type": "DIGITAL_ARREST_IN_PROGRESS",
        "severity": threat_assessment["severity"],
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "scam_message": message,
        "threat_assessment": threat_assessment,
        "extracted_intelligence": intelligence,
        "recommended_action": "IMMEDIATE_INTERVENTION",
        "escalation_required": True,
        "priority": "CRITICAL",
        
        # Scammer profile
        "scammer_profile": {
            "claimed_authority": threat_assessment["detected_patterns"]["authorities_claimed"],
            "contact_method": intelligence.get("phoneNumbers", []),
            "payment_demands": intelligence.get("upiIds", []) + intelligence.get("bankAccounts", [])
        },
        
        # Victim protection
        "victim_guidance_shown": True,
        "helpline_displayed": "1930",
        "family_alert_recommended": True
    }
    
    # Log for audit trail
    logger.critical(f"\n{'='*70}")
    logger.critical(
        f"[CRITICAL] LAW ENFORCEMENT ALERT | "
        f"Session: {session_id} | "
        f"Severity: {threat_assessment['severity']} | "
        f"Type: DIGITAL_ARREST"
    )
    logger.critical(f"{'='*70}")
    
    # Log to Critical Emergency File
    try:
        import json
        import os
        
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        with open(os.path.join(log_dir, "emergency.log"), "a", encoding="utf-8") as f:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": "CRITICAL",
                "type": "DIGITAL_ARREST",
                "session_id": session_id,
                "payload": alert_payload
            }
            f.write(json.dumps(log_entry) + "\n")
            
        logger.info(f"[SAVED] Emergency Log Saved: logs/emergency.log")
        
    except Exception as e:
        logger.error(f"Failed to write emergency log: {e}")

    return alert_payload


# Statistics tracking
DIGITAL_ARREST_STATS = {
    "total_detected": 0,
    "prevented_attempts": 0,
    "law_enforcement_alerts": 0,
    "claimed_authorities": {},
    "peak_times": []
}


def track_digital_arrest_attempt(threat_assessment: Dict):
    """Track patterns for intelligence gathering"""
    
    DIGITAL_ARREST_STATS["total_detected"] += 1
    
    for authority in threat_assessment["detected_patterns"]["authorities_claimed"]:
        DIGITAL_ARREST_STATS["claimed_authorities"][authority] = \
            DIGITAL_ARREST_STATS["claimed_authorities"].get(authority, 0) + 1
    
    DIGITAL_ARREST_STATS["peak_times"].append({
        "timestamp": datetime.now().isoformat(),
        "severity": threat_assessment["severity"]
    })


def get_digital_arrest_statistics() -> Dict:
    """Return aggregated statistics for dashboard"""
    return DIGITAL_ARREST_STATS
