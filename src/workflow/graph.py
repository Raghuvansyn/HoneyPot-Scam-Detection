"""
LangGraph Workflow — multi-agent orchestration for honeypot.
"""

import time
from datetime import datetime
from typing import Literal
from langgraph.graph import StateGraph, END
from src.models import (
    HoneypotRequest, JudgeResponse, ResponseMeta,
    ExtractedIntelligence, AgentState, EngagementMetrics,
)
from src.database import SessionManager
from src.agents.detection import detect_scam
from src.agents.persona import generate_persona_response
from src.agents.extraction import extract_intelligence
from src.agents.hallucination_filter import validate_persona_output
from src.agents.timeline import get_conversation_summary, calculate_confidence_level

from src.utils import (
    logger, get_session_logger, PerformanceLogger, log_intelligence,
    send_final_callback, should_send_callback, alert_law_enforcement_digital_arrest,
)


# --- Node Functions ---

def load_session_node(state: AgentState) -> AgentState:
    session_id = state["sessionId"]
    session_logger = get_session_logger(session_id)
    logger.info(f"[load_session] session={session_id}")

    db = SessionManager()
    existing_state = db.get_session(session_id)

    if existing_state:
        logger.info(f"[load_session] existing session, msgs={existing_state['totalMessages']}")
        new_message = state["conversationHistory"][0]
        wall_clock = state.get("wallClockStart", time.time())
        state.update(existing_state)
        # preserve wall clock from DB if available, else keep current
        if not state.get("wallClockStart"):
            state["wallClockStart"] = wall_clock
        state["conversationHistory"].append(new_message)
        state["totalMessages"] += 1
    else:
        logger.info("[load_session] new session")
        state["wallClockStart"] = time.time()

    return state


async def detection_node(state: AgentState) -> AgentState:
    session_id = state["sessionId"]
    logger.info(f"[detection] session={session_id} turn={state['totalMessages']}")

    with PerformanceLogger("Detection", logger):
        last_message = state["conversationHistory"][-1]["text"]
        is_scam, confidence, details = await detect_scam(last_message, session_id=session_id)
        state["detectionConfidence"] = confidence

        if is_scam:
            state["scamDetected"] = True
            state["agentNotes"] = f"Detection: SCAM (confidence: {confidence:.2f})"

            if details.get("is_digital_arrest"):
                state["digitalArrestInfo"] = details
                state["agentNotes"] += f" | DIGITAL ARREST ({details.get('severity', 'CRITICAL')})"
                if not details.get("lea_alert_sent", False):
                    await alert_law_enforcement_digital_arrest(
                        session_id=session_id, message=last_message,
                        intelligence=state["extractedIntelligence"], confidence=confidence,
                    )

            logger.info(f"[detection] SCAM conf={confidence:.2f}")
        else:
            if not state.get("scamDetected", False):
                state["agentNotes"] = f"Detection: SAFE (confidence: {confidence:.2f})"
                if confidence == 0.00:
                    if not state.get("metadata"):
                        state["metadata"] = {}
                    state["metadata"]["isTrusted"] = True
                    logger.info("[detection] trusted sender -> safe exit")

    return state


async def persona_node(state: AgentState) -> AgentState:
    session_id = state["sessionId"]
    logger.info(f"[persona] session={session_id}")

    try:
        with PerformanceLogger("Persona", logger):
            # Use cached intelligence from state instead of re-extracting
            current_intelligence = state.get("extractedIntelligence", {})

            # fast path for turn 1 when not yet flagged as scam
            if len(state["conversationHistory"]) <= 1 and not state.get("scamDetected", False):
                import random
                fast_replies = [
                    "Who is this?",
                    "I don't verify numbers I don't know.",
                    "Hello? Who are you?",
                    "What is this about? I am busy.",
                    "I don't understand message.",
                ]
                raw_response = random.choice(fast_replies)
                logger.info(f"[persona] fast path: '{raw_response}'")
            else:
                raw_response = await generate_persona_response(
                    conversation_history=state["conversationHistory"],
                    metadata=state["metadata"],
                    extracted_intelligence=current_intelligence,
                )

            persona_response, was_filtered = validate_persona_output(raw_response)
            if was_filtered:
                logger.warning("[persona] response sanitized")

            state["conversationHistory"].append({
                "sender": "user",
                "text": persona_response,
                "timestamp": datetime.now().isoformat() + "Z",
            })
            state["totalMessages"] += 1

    except Exception as e:
        logger.error(f"[persona] error: {e}", exc_info=True)
        fallback = "I'm sorry, I'm getting confused. Can you explain more slowly?"
        state["conversationHistory"].append({
            "sender": "user", "text": fallback,
            "timestamp": datetime.now().isoformat() + "Z",
        })
        state["totalMessages"] += 1

    return state


def extraction_node(state: AgentState) -> AgentState:
    session_id = state["sessionId"]
    logger.info(f"[extraction] session={session_id}")

    try:
        with PerformanceLogger("Extraction", logger):
            intelligence = extract_intelligence(state["conversationHistory"])
            state["extractedIntelligence"] = intelligence
            log_intelligence(session_id, intelligence)
    except Exception as e:
        logger.error(f"[extraction] error: {e}", exc_info=True)

    return state


def not_scam_node(state: AgentState) -> AgentState:
    logger.info(f"[not_scam] session={state['sessionId']}")
    state["conversationHistory"].append({
        "sender": "user",
        "text": "Thank you for your message. Have a great day!",
        "timestamp": datetime.now().isoformat() + "Z",
    })
    state["totalMessages"] += 1
    return state


async def save_session_node(state: AgentState) -> AgentState:
    session_id = state["sessionId"]
    logger.info(f"[save_session] session={session_id}")
    state["lastUpdated"] = datetime.now().isoformat() + "Z"

    if should_send_callback(state):
        if state.get("callbackSent", False):
            logger.info("[save_session] callback already sent, skipping")
            state["sessionStatus"] = "closed"
        else:
            logger.info("[save_session] finalizing conversation...")

            if state["scamDetected"] and state["totalMessages"] >= 3:
                try:
                    detection_confidence = _parse_confidence(state.get("agentNotes", ""))
                    state["fullSummaryForCallback"] = get_conversation_summary(
                        conversation_history=state["conversationHistory"],
                        extracted_intelligence=state["extractedIntelligence"],
                        detection_confidence=detection_confidence,
                        scam_detected=state["scamDetected"],
                    )
                except Exception as e:
                    logger.warning(f"[save_session] summary failed: {e}")
                    state["fullSummaryForCallback"] = state["agentNotes"]

            callback_success = await send_final_callback(session_id, state)
            if callback_success:
                state["callbackSent"] = True
            state["sessionStatus"] = "closed"
    else:
        state["sessionStatus"] = "active"

    db = SessionManager()
    db.save_session(session_id, state)
    logger.info(f"[save_session] saved | msgs={state['totalMessages']} | status={state['sessionStatus']}")
    return state


def _parse_confidence(agent_notes: str) -> float:
    if "confidence:" in agent_notes:
        try:
            return float(agent_notes.split("confidence:")[1].split(")")[0].strip())
        except (ValueError, IndexError):
            pass
    return 0.5


# --- Routing ---

def should_detect(state: AgentState) -> Literal["detection", "persona"]:
    if state.get("scamDetected", False):
        return "persona"
    return "detection"


def route_after_detection(state: AgentState) -> Literal["persona", "not_scam"]:
    if state["scamDetected"]:
        return "persona"
    if state.get("metadata", {}).get("isTrusted", False):
        return "not_scam"
    if state["totalMessages"] <= 3:
        return "persona"
    return "not_scam"


# --- Build Graph ---

def create_workflow_graph():
    logger.info("Building LangGraph workflow...")
    workflow = StateGraph(AgentState)

    workflow.add_node("load_session", load_session_node)
    workflow.add_node("detection", detection_node)
    workflow.add_node("persona", persona_node)
    workflow.add_node("extraction", extraction_node)
    workflow.add_node("not_scam", not_scam_node)
    workflow.add_node("save_session", save_session_node)

    workflow.set_entry_point("load_session")

    workflow.add_conditional_edges("load_session", should_detect, {
        "detection": "detection", "persona": "persona",
    })
    workflow.add_conditional_edges("detection", route_after_detection, {
        "persona": "persona", "not_scam": "not_scam",
    })
    workflow.add_edge("persona", "extraction")
    workflow.add_edge("extraction", "save_session")
    workflow.add_edge("not_scam", "save_session")
    workflow.add_edge("save_session", END)

    compiled = workflow.compile()
    logger.info("LangGraph workflow compiled (6 nodes, 2 conditional edges)")
    return compiled


WORKFLOW_GRAPH = create_workflow_graph()


# --- Entry Point ---

async def run_honeypot_workflow(request: HoneypotRequest) -> JudgeResponse:
    session_id = request.sessionId
    scammer_message = request.message
    metadata = request.metadata.dict() if request.metadata else {}

    logger.info(f"[workflow] start | session={session_id} | msg='{scammer_message.text[:80]}'")

    initial_state = AgentState(
        sessionId=session_id,
        conversationHistory=[{
            "sender": scammer_message.sender,
            "text": scammer_message.text,
            "timestamp": scammer_message.timestamp,
        }],
        metadata=metadata,
        scamDetected=False,
        extractedIntelligence={
            "bankAccounts": [], "upiIds": [], "phishingLinks": [],
            "phoneNumbers": [], "emailAddresses": [], "suspiciousKeywords": [],
        },
        totalMessages=1,
        startTime=scammer_message.timestamp,
        lastUpdated=scammer_message.timestamp,
        wallClockStart=time.time(),
        agentNotes="",
        sessionStatus="active",
        callbackSent=False,
        digitalArrestInfo=None,
        detectionConfidence=None,
    )

    try:
        with PerformanceLogger("Full Workflow", logger):
            final_state = await WORKFLOW_GRAPH.ainvoke(initial_state)

        logger.info(
            f"[workflow] done | session={session_id} | scam={final_state['scamDetected']} "
            f"| msgs={final_state['totalMessages']} | status={final_state.get('sessionStatus')}"
        )

        last_message = final_state["conversationHistory"][-1]
        reply_text = last_message["text"]
        is_complete = final_state.get("sessionStatus") == "closed"

        confidence = None
        if is_complete:
            detection_conf = _parse_confidence(final_state.get("agentNotes", ""))
            intel_count = sum(
                len(v) for v in final_state["extractedIntelligence"].values()
                if isinstance(v, list)
            )
            confidence = calculate_confidence_level(detection_conf, intel_count, final_state["totalMessages"])
        
        # If confidence is still None (active session), use the latest detection confidence
        if confidence is None:
            confidence = final_state.get("detectionConfidence")

        persona = "confused_customer" if final_state["scamDetected"] else "polite_responder"

        if final_state["scamDetected"]:
            sanitized_notes = "Detection: SCAM"
            conf = _parse_confidence(final_state.get("agentNotes", ""))
            if conf != 0.5:
                sanitized_notes = f"Detection: SCAM (confidence: {conf:.2f})"
            
            # Append extraction count for remote validation
            intel_count = sum(
                len(v) for v in final_state["extractedIntelligence"].values()
                if isinstance(v, list)
            )
            if intel_count > 0:
                sanitized_notes += f" | Extracted: {intel_count} entities"
        else:
            sanitized_notes = "Detection: LEGITIMATE"

        # Calculate engagement metrics for response
        wall_start = final_state.get("wallClockStart", time.time())
        duration = time.time() - wall_start

        return JudgeResponse(
            status="success",
            reply=reply_text,
            scamDetected=final_state["scamDetected"],  # Required (5 points)
            extractedIntelligence=ExtractedIntelligence(**final_state["extractedIntelligence"]),  # Required (5 points)
            engagementMetrics=EngagementMetrics(  # Optional (2.5 points)
                totalMessagesExchanged=final_state["totalMessages"],
                engagementDurationSeconds=round(duration, 2)
            ),
            agentNotes=sanitized_notes,  # Optional (2.5 points)
            meta=ResponseMeta(
                agentState="completed" if is_complete else "engaging",
                sessionStatus="closed" if is_complete else "active",
                persona=persona,
                turn=final_state["totalMessages"],
                confidence=confidence,
                agentNotes=sanitized_notes,
            ),
        )

    except Exception as e:
        logger.error(f"[workflow] error: {e}", exc_info=True)
        raise
