# app/agents/timeline.py
"""
Timeline Analysis Agent
Analyzes conversation retrospectively to identify scam phases and tactics.
Generates summary at END of conversation.
"""

from typing import List, Dict
from app.utils import logger

def analyze_scam_timeline(conversation_history: list) -> str:
    """
    Analyze complete conversation and generate timeline summary.
    
    This runs ONCE at the end to summarize how the scam unfolded.
    
    Args:
        conversation_history: Complete conversation
        
    Returns:
        Human-readable timeline summary string
    """
    
    phases = detect_scam_phases(conversation_history)
    
    if not phases:
        return "No clear scam pattern detected in conversation."
    
    # Build summary
    summary = build_timeline_summary(phases)
    
    logger.debug(f"Timeline analysis: {len(phases)} phases detected")
    
    return summary


def detect_scam_phases(conversation_history: list) -> List[Dict]:
    """
    Detect which scam phases appeared in the conversation.
    
    Returns list of phases with their details.
    """
    
    # Phase definitions
    phase_patterns = {
        "urgency": {
            "keywords": ["urgent", "immediately", "today", "now", "expire", "deadline", "soon", "quickly"],
            "description": "Creates time pressure"
        },
        "authority": {
            "keywords": ["bank", "government", "police", "official", "department", "manager", "headquarters", "officer"],
            "description": "Impersonates authority"
        },
        "fear": {
            "keywords": ["blocked", "suspended", "legal action", "arrest", "fine", "penalty", "closed", "terminate"],
            "description": "Threatens consequences"
        },
        "credential_request": {
            "keywords": ["otp", "password", "pin", "cvv", "verify", "confirm", "code", "authentication"],
            "description": "Requests credentials"
        },
        "payment_redirection": {
            "keywords": ["send money", "transfer", "pay", "payment", "amount", "rupees", "deposit", "upi"],
            "description": "Demands payment"
        },
        "impersonation": {
            "keywords": ["i am from", "calling from", "representative", "agent", "this is", "my name is"],
            "description": "Identity fraud"
        }
    }
    
    detected_phases = []
    
    # Analyze each scammer message
    for i, msg in enumerate(conversation_history):
        if msg.get("sender") != "scammer":
            continue
        
        text = msg.get("text", "").lower()
        message_number = i + 1
        
        # Check each phase
        for phase_name, phase_data in phase_patterns.items():
            matches = [kw for kw in phase_data["keywords"] if kw in text]
            
            if matches:
                # Check if we already detected this phase
                existing = next((p for p in detected_phases if p["phase"] == phase_name), None)
                
                if not existing:
                    detected_phases.append({
                        "phase": phase_name,
                        "description": phase_data["description"],
                        "first_seen": message_number
                    })
    
    # Sort by first appearance
    detected_phases.sort(key=lambda x: x["first_seen"])
    
    return detected_phases


def build_timeline_summary(phases: List[Dict]) -> str:
    """
    Build human-readable summary from detected phases.
    """
    
    if not phases:
        return "No clear scam tactics identified"
    
    # Phase names for better readability
    phase_display = {
        "urgency": "Urgency Tactics",
        "authority": "Authority Impersonation",
        "fear": "Fear & Threats",
        "credential_request": "Credential Theft",
        "payment_redirection": "Payment Fraud",
        "impersonation": "Identity Fraud"
    }
    
    # Build compact summary
    phase_list = []
    for i, phase_info in enumerate(phases, 1):
        phase_name = phase_display.get(phase_info["phase"], phase_info["phase"])
        description = phase_info["description"]
        phase_list.append(f"({i}) {phase_name} - {description}")
    
    summary = f"Scam executed in {len(phases)}-phase attack: " + " | ".join(phase_list)
    
    # Pattern classification
    pattern = classify_scam_pattern(phases)
    if pattern:
        summary += f" | Pattern: {pattern}"
    
    return summary


def classify_scam_pattern(phases: List[Dict]) -> str:
    """
    Classify the overall scam pattern based on phases detected.
    """
    
    phase_names = [p["phase"] for p in phases]
    
    # Common patterns
    if "urgency" in phase_names and "authority" in phase_names and "credential_request" in phase_names:
        return "Classic Bank Fraud"
    
    if "urgency" in phase_names and "payment_redirection" in phase_names:
        return "Payment Fraud"
    
    if "fear" in phase_names and "credential_request" in phase_names:
        return "Intimidation Fraud"
    
    if "authority" in phase_names and "payment_redirection" in phase_names:
        return "Impersonation Fraud"
    
    if len(phase_names) >= 4:
        return "Multi-Stage Scam"
    
    return "Standard Scam"


def get_conversation_summary(
    conversation_history: list,
    extracted_intelligence: dict,
    detection_confidence: float,
    scam_detected: bool
) -> str:
    """
    Generate complete conversation summary including timeline.
    
    This is the MAIN function to call at the end.
    
    Args:
        conversation_history: Complete conversation
        extracted_intelligence: All extracted data
        detection_confidence: Detection confidence score
        scam_detected: Whether scam was detected
        
    Returns:
        Complete summary string for agentNotes
    """
    
    # Detection part
    detection_status = "SCAM" if scam_detected else "LEGITIMATE"
    summary_parts = [f"Detection: {detection_status} (confidence: {detection_confidence:.2f})"]
    
    # Timeline analysis (only for scams)
    if scam_detected and len(conversation_history) >= 3:
        timeline = analyze_scam_timeline(conversation_history)
        summary_parts.append(timeline)
    
    # Intelligence summary
    intel_details = []
    if extracted_intelligence.get("phoneNumbers"):
        intel_details.append(f"{len(extracted_intelligence['phoneNumbers'])} phone(s)")
    if extracted_intelligence.get("upiIds"):
        intel_details.append(f"{len(extracted_intelligence['upiIds'])} UPI(s)")
    if extracted_intelligence.get("phishingLinks"):
        intel_details.append(f"{len(extracted_intelligence['phishingLinks'])} link(s)")
    if extracted_intelligence.get("bankAccounts"):
        intel_details.append(f"{len(extracted_intelligence['bankAccounts'])} account(s)")
    if extracted_intelligence.get("suspiciousKeywords"):
        intel_details.append(f"{len(extracted_intelligence['suspiciousKeywords'])} keywords")
    
    if intel_details:
        summary_parts.append(f"Intelligence: {', '.join(intel_details)}")
    else:
        if scam_detected:
            summary_parts.append("Intelligence: none extracted")
    
    return " | ".join(summary_parts)


def calculate_confidence_level(
    detection_confidence: float,
    intelligence_count: int,
    message_count: int
) -> str:
    """
    Calculate overall confidence level.
    
    Returns: "high", "medium", or "low"
    """
    
    # Base on detection confidence
    score = detection_confidence
    
    # Boost if we extracted intelligence
    if intelligence_count >= 3:
        score += 0.1
    elif intelligence_count >= 1:
        score += 0.05
    
    # Boost if conversation was long (more data points)
    if message_count >= 10:
        score += 0.05
    
    # Classify
    if score >= 0.85:
        return "high"
    elif score >= 0.65:
        return "medium"
    else:
        return "low"