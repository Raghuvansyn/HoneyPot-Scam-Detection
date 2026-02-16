import time
import aiohttp
from src.config import MODE
from src.models import GuviCallback, ExtractedIntelligence, EngagementMetrics
from src.utils.logger import logger

GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

HARD_MAX_MESSAGES = 20
EARLY_END_MESSAGES = 8  # Increased from 5 to allow more engagement
GOOD_INTEL_CATEGORIES = 4  # Increased from 3 to require more intel before closing
DECENT_INTEL_MESSAGES = 10  # Increased from 6 to keep conversation going
WEAK_INTEL_MESSAGES = 15  # Increased from 12 to extract more data
NO_INTEL_MESSAGES = 12


def count_intel_categories(extracted_intelligence: dict) -> dict:
    categories = {
        "phoneNumbers": extracted_intelligence.get("phoneNumbers", []),
        "upiIds": extracted_intelligence.get("upiIds", []),
        "phishingLinks": extracted_intelligence.get("phishingLinks", []),
        "bankAccounts": extracted_intelligence.get("bankAccounts", []),
        "emailAddresses": extracted_intelligence.get("emailAddresses", []),
    }
    filled = [name for name, items in categories.items() if len(items) > 0]
    empty = [name for name, items in categories.items() if len(items) == 0]
    return {"total_categories": len(filled), "filled": filled, "empty": empty}


def should_send_callback(state: dict) -> bool:
    """
    Determine if conversation should end and callback should be sent.
    
    HACKATHON OPTIMIZATION: Align with maxTurns=10 from evaluator.
    Keep conversations going for 8-10 turns to maximize engagement and intelligence scores.
    """
    total_messages = state["totalMessages"]
    scam_detected = state["scamDetected"]

    # Hard maximum at 20 turns (safety limit)
    if total_messages >= HARD_MAX_MESSAGES:
        logger.info(f"Hard max reached ({HARD_MAX_MESSAGES})")
        return True

    # For scams, check intelligence extraction
    intel_status = count_intel_categories(state["extractedIntelligence"])
    categories = intel_status["total_categories"]
    filled = intel_status["filled"]

    logger.info(f"Intel check - msgs: {total_messages} | categories: {categories}/5 | filled: {filled}")

    # Minimum engagement threshold: 8 turns (ensures we get engagement points)
    # Engagement scoring: 5 pts for >0 msgs, 5 pts for >=5 msgs
    MIN_ENGAGEMENT_TURNS = 8

    if total_messages < MIN_ENGAGEMENT_TURNS:
        logger.info(f"Continue: only {total_messages} turns, need minimum {MIN_ENGAGEMENT_TURNS} for engagement")
        return False

    # If not a scam and we've had 10+ turns, we can close
    if not scam_detected and total_messages >= 10:
        logger.info("Termination: non-scam after 10 turns")
        return True

    # INTELLIGENCE-BASED TERMINATION (for scams)
    # If we have excellent intel (4+ categories), close after 10 turns
    if categories >= 4 and total_messages >= 10:
        logger.info(f"Excellent intel ({categories} categories) after 10 turns")
        return True

    # If we have good intel (3 categories), close after 12 turns
    if categories >= 3 and total_messages >= 12:
        logger.info(f"Good intel ({categories} categories) after 12 turns")
        return True

    # If we have decent intel (2 categories), close after 15 turns
    if categories >= 2 and total_messages >= 15:
        logger.info(f"Decent intel ({categories} categories) after 15 turns")
        return True

    # If we have minimal intel (1 category), close after 18 turns
    if categories >= 1 and total_messages >= 18:
        logger.info(f"Minimal intel ({categories} categories) after 18 turns")
        return True

    # Otherwise, keep going until hard max
    return False


async def send_final_callback(session_id: str, state: dict) -> bool:
    """Send final intelligence to GUVI. Async to avoid blocking the event loop."""

    wall_start = state.get("wallClockStart", 0)
    duration = time.time() - wall_start if wall_start else 0

    intelligence = ExtractedIntelligence(**state["extractedIntelligence"])
    callback_notes = state.get("fullSummaryForCallback", state["agentNotes"])

    if state.get("digitalArrestInfo"):
        severity = "CRITICAL"
    elif state["scamDetected"]:
        severity = "HIGH"
    else:
        severity = "NORMAL"

    payload = GuviCallback(
        sessionId=session_id,
        status="completed",
        scamDetected=state["scamDetected"],
        totalMessagesExchanged=state["totalMessages"],
        extractedIntelligence=intelligence,
        engagementMetrics=EngagementMetrics(
            totalMessagesExchanged=state["totalMessages"],
            engagementDurationSeconds=round(duration, 2),
        ),
        agentNotes=callback_notes,
        digitalArrestInfo=state.get("digitalArrestInfo"),
        severity=severity,
    )

    if MODE != "prod":
        logger.info(f"[DEV] Callback skipped | session={session_id} | scam={state['scamDetected']} | msgs={state['totalMessages']}")
        intel_status = count_intel_categories(state["extractedIntelligence"])
        logger.info(f"[DEV] Would send: categories={intel_status['total_categories']}/5 | filled={intel_status['filled']}")
        return True

    try:
        logger.info(f"Sending callback | session={session_id} | severity={severity} | msgs={state['totalMessages']}")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                GUVI_CALLBACK_URL,
                json=payload.dict(),
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                body = await response.text()
                if response.status == 200:
                    logger.info(f"Callback OK | response={body}")
                    return True
                else:
                    logger.warning(f"Callback returned {response.status} | response={body}")
                    return False
    except aiohttp.ClientError as e:
        logger.error(f"Callback network error: {e}")
        return False
    except Exception as e:
        logger.error(f"Callback failed: {e}", exc_info=True)
        return False


LEA_API_KEY = "mock_lea_key_12345"


async def alert_law_enforcement_digital_arrest(
    session_id: str, message: str, intelligence: dict, confidence: float
):
    """Emergency alert for digital arrest scams (mocked for hackathon)."""
    from datetime import datetime
    import json, os

    payload = {
        "alert_type": "DIGITAL_ARREST_IN_PROGRESS",
        "severity": "CRITICAL",
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "scam_message": message[:200],
        "extracted_intelligence": intelligence,
        "confidence": confidence,
        "recommended_action": "IMMEDIATE_INTERVENTION",
    }

    logger.critical(f"[DIGITAL ARREST ALERT] session={session_id} | conf={confidence}")

    try:
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, "emergency.log"), "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": datetime.now().isoformat(),
                "level": "CRITICAL",
                "type": "DIGITAL_ARREST",
                "session_id": session_id,
                "payload": payload,
            }) + "\n")
    except Exception as e:
        logger.error(f"Failed to write emergency log: {e}")
