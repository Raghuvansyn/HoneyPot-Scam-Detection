# app/utils/callbacks.py
"""
Callback utilities for sending final results to GUVI.
Dynamic termination logic based on extracted intelligence.
Protected by MODE environment variable.
"""

import requests
from src.config import MODE
from src.models import GuviCallback, ExtractedIntelligence
from src.utils.logger import logger

# GUVI endpoint
# GUVI endpoint
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

# ============================================
# DYNAMIC THRESHOLDS (EXTENDED FOR LONGER CONVERSATIONS)
# ============================================

HARD_MAX_MESSAGES = 20      # Absolute limit - never go beyond
EARLY_END_MESSAGES = 5      # Never end before this
GOOD_INTEL_CATEGORIES = 3   # 3+ categories = Jackpot (End immediately)
DECENT_INTEL_MESSAGES = 6   # 2 categories (e.g. Phone+Link) -> End after 6 messages (Efficiency)
WEAK_INTEL_MESSAGES = 12    # 1 category -> Keep engaging until 12 messages (Digging)
NO_INTEL_MESSAGES = 12      # 0 categories -> Give up after 12


def count_intel_categories(extracted_intelligence: dict) -> dict:
    """
    Count how many CATEGORIES have useful data.
    
    We care about categories, not total items.
    Having 5 phone numbers is same as having 1 phone number = 1 category.
    
    Returns:
        {
            "total_categories": 3,
            "filled": ["phoneNumbers", "upiIds", "phishingLinks"],
            "empty": ["bankAccounts"]
        }
    """
    
    categories = {
        "phoneNumbers": extracted_intelligence.get("phoneNumbers", []),
        "upiIds": extracted_intelligence.get("upiIds", []),
        "phishingLinks": extracted_intelligence.get("phishingLinks", []),
        "bankAccounts": extracted_intelligence.get("bankAccounts", [])
    }
    
    filled = [name for name, items in categories.items() if len(items) > 0]
    empty = [name for name, items in categories.items() if len(items) == 0]
    
    return {
        "total_categories": len(filled),
        "filled": filled,
        "empty": empty
    }


def should_send_callback(state: dict) -> bool:
    """
    DYNAMIC decision: should we end conversation and send callback?
    
    Scenarios handled:
    1. All/most categories filled → end early (strong evidence)
    2. Few categories but many messages → end (tried enough)
    3. No categories after 8 messages → end (nothing to extract)
    4. Hard max reached → end regardless
    5. Non-scam detected → end immediately
    
    Args:
        state: Complete session state
        
    Returns:
        True if we should end + send callback
    """
    
    total_messages = state["totalMessages"]
    scam_detected = state["scamDetected"]
    
    # ============================================
    # NON-SCAM: END IMMEDIATELY
    # ============================================
    
    if not scam_detected:
        logger.info("📊 Termination: Non-scam detected → ending immediately")
        return True
    
    # ============================================
    # GET INTELLIGENCE STATUS
    # ============================================
    
    intel_status = count_intel_categories(state["extractedIntelligence"])
    categories = intel_status["total_categories"]
    filled = intel_status["filled"]
    empty = intel_status["empty"]
    
    logger.info(f"📊 Intel Check - Messages: {total_messages} | Categories filled: {categories}/4 | Filled: {filled}")
    
    # ============================================
    # NEVER END BEFORE EARLY_END
    # ============================================
    
    if total_messages < EARLY_END_MESSAGES:
        logger.info(f"   → Too early (min {EARLY_END_MESSAGES} messages) - continuing")
        return False
    
    # ============================================
    # HARD MAX - ABSOLUTE LIMIT
    # ============================================
    
    if total_messages >= HARD_MAX_MESSAGES:
        logger.info(f"   → ⏰ Hard max reached ({HARD_MAX_MESSAGES}) - ending regardless")
        return True
    
    # ============================================
    # STRONG EVIDENCE: 3+ categories filled
    # ============================================
    
    if categories >= GOOD_INTEL_CATEGORIES:
        logger.info(f"   → 🏆 Strong evidence ({categories} categories) - ending!")
        return True
    
    # ============================================
    # DECENT EVIDENCE: 2 categories + enough messages
    # ============================================
    
    if categories == 2 and total_messages >= DECENT_INTEL_MESSAGES:
        logger.info(f"   → ✅ Decent evidence (2 categories, {total_messages} messages) - ending")
        return True
    
    # ============================================
    # WEAK EVIDENCE: 1 category + many messages
    # ============================================
    
    if categories == 1 and total_messages >= WEAK_INTEL_MESSAGES:
        logger.info(f"   → ⚠️ Weak evidence (1 category, {total_messages} messages) - ending")
        return True
    
    # ============================================
    # NO EVIDENCE: Nothing found after 8 messages
    # ============================================
    
    if categories == 0 and total_messages >= NO_INTEL_MESSAGES:
        logger.info(f"   → ❌ No intel after {total_messages} messages - ending")
        return True
    
    # ============================================
    # KEEP GOING
    # ============================================
    
    logger.info(f"   → 🔄 Continuing conversation (need more intel)")
    return False


def send_final_callback(session_id: str, state: dict) -> bool:
    """
    Send final intelligence to GUVI endpoint.
    
    BLOCKED in dev mode.
    Only fires in prod mode.
    
    Sends WHATEVER we have - even if partial.
    
    Args:
        session_id: Session identifier
        state: Complete session state
        
    Returns:
        True if successful or skipped, False on failure
    """
    
    # ============================================
    # MODE CHECK - BLOCK IN DEV
    # ============================================
    
    if MODE != "prod":
        logger.info(f"\n{'='*70}")
        logger.info(f"🔧 DEV MODE - Callback SKIPPED")
        logger.info(f"{'='*70}")
        logger.info(f"   Session: {session_id}")
        logger.info(f"   Scam Detected: {state['scamDetected']}")
        logger.info(f"   Total Messages: {state['totalMessages']}")
        
        # Still log what WOULD have been sent
        intel_status = count_intel_categories(state["extractedIntelligence"])
        logger.info(f"   Categories Found: {intel_status['total_categories']}/4")
        logger.info(f"   Filled: {intel_status['filled']}")
        logger.info(f"   Would send: {state['extractedIntelligence']}")
        logger.info(f"   Nothing sent to GUVI ✅")
        logger.info(f"{'='*70}\n")
        return True
    
    # ============================================
    # PROD MODE - SEND CALLBACK
    # ============================================
    
    try:
        intelligence = ExtractedIntelligence(**state["extractedIntelligence"])
        
        # Use full summary if available, otherwise use basic agentNotes
        callback_notes = state.get("fullSummaryForCallback", state["agentNotes"])
        
        # Determine Severity
        if state.get("digitalArrestInfo"):
            severity = "CRITICAL"
        elif state["scamDetected"]:
            severity = "HIGH"
        else:
            severity = "NORMAL"

        payload = GuviCallback(
            sessionId=session_id,
            scamDetected=state["scamDetected"],
            totalMessagesExchanged=state["totalMessages"],
            extractedIntelligence=intelligence,
            agentNotes=callback_notes,
            digitalArrestInfo=state.get("digitalArrestInfo"),
            severity=severity
        )
        
        logger.info(f"\n{'='*70}")
        logger.info(f"📤 SENDING FINAL CALLBACK TO GUVI")
        logger.info(f"{'='*70}")
        logger.info(f"   Session: {session_id}")
        logger.info(f"   Scam Detected: {state['scamDetected']}")
        logger.info(f"   Severity: {severity}")
        logger.info(f"   Total Messages: {state['totalMessages']}")
        logger.info(f"   Intelligence: {state['extractedIntelligence']}")
        
        response = requests.post(
            GUVI_CALLBACK_URL,
            json=payload.dict(),
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Callback successful!")
            logger.info(f"   Response: {response.text}")
            logger.info(f"{'='*70}\n")
            return True
        else:
            logger.warning(f"⚠️ Callback returned status: {response.status_code}")
            logger.warning(f"   Response: {response.text}")
            logger.info(f"{'='*70}\n")
            return False
            
    except requests.exceptions.Timeout:
        logger.error(f"❌ Callback timeout")
        logger.info(f"{'='*70}\n")
        return False
        
    except Exception as e:
        logger.error(f"❌ Callback failed: {e}", exc_info=True)
        logger.info(f"{'='*70}\n")
        return False

# ============================================
# EMERGENCY RESPONSE SYSTEM (DIGITAL ARREST)
# ============================================

LEA_API_KEY = "mock_lea_key_12345"  # Mock key for hackathon

def send_emergency_sms(to: str, message: str):
    """Mock SMS sender"""
    logger.info(f"📱 [MOCK SMS] To: {to} | Message: {message}")

async def alert_law_enforcement_digital_arrest(
    session_id: str,
    message: str,
    intelligence: dict,
    confidence: float
):
    """Emergency alert for digital arrest scams"""
    import httpx
    from datetime import datetime
    
    logger.critical(f"\n{'='*70}")
    logger.critical(f"[CRITICAL] INITIATING EMERGENCY PROTOCOL: DIGITAL ARREST")
    logger.critical(f"{'='*70}")
    
    payload = {
        "alert_type": "DIGITAL_ARREST_IN_PROGRESS",
        "severity": "CRITICAL",
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "scam_message": message,
        "extracted_intelligence": intelligence,
        "confidence": confidence,
        "victim_status": "ENGAGED_WITH_SCAMMER",
        "recommended_action": "IMMEDIATE_INTERVENTION",
        "escalation_required": True,
        
        # Call pattern analysis
        "call_duration_estimate": "Unknown - likely ongoing",
        "scammer_location_hints": intelligence.get("phoneNumbers", []),
        
        # Victim protection
        "victim_guidance_shown": True,
        "helpline_displayed": "1930",
        "bank_freeze_recommended": True if "transfer" in message.lower() else False
    }
    
    # Send to cyber crime portal (Mocked for Hackathon)
    # response = await http_client.post(
    #     "https://cybercrime.gov.in/api/emergency-alert",
    #     json=payload,
    #     headers={"Authorization": f"Bearer {LEA_API_KEY}"}
    # )
    
    # MOCK RESPONSE
    logger.info(f"[MOCK LEA ALERT] Sending payload to cybercrime.gov.in...")
    logger.info(f"   Payload: {payload}")
    logger.info(f"[SUCCESS] Alert Acknowledged by Cyber Crime Portal (ID: LEA-{session_id[:8]})")

    # Also send SMS to victim if phone number available
    # In a real honeypot, 'victim_phone' might be known if they called us, 
    # but here we might not have it. We check if we extracted a victim phone 
    # (unlikely) or if we simulates sending to the "current user".
    
    # For demo, we assume we might have it in metadata or intelligence
    if victim_phone := intelligence.get("victim_phone"):
        send_emergency_sms(
            to=victim_phone,
            message="DIGITAL ARREST SCAM ALERT: You are NOT under arrest. "
                   "This is a scam. Hang up immediately. Call 1930 for help."
        )
    else:
        logger.info("[INFO] No victim phone number available for SMS alert.")
    
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
                "payload": payload
            }
            f.write(json.dumps(log_entry) + "\n")
            
        logger.info(f"[SAVED] Emergency Log Saved: logs/emergency.log")
        
    except Exception as e:
        logger.error(f"Failed to write emergency log: {e}")
    
    logger.critical(f"{'='*70}\n")