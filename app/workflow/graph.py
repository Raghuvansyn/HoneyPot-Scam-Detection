# app/workflow/graph.py
"""
LangGraph Workflow Implementation
Proper graph-based agent orchestration with nodes, edges, state management, logging, and context-aware persona.
"""

from datetime import datetime
from typing import Literal
from langgraph.graph import StateGraph, END
from app.models import HoneypotRequest, Message, JudgeResponse, ResponseMeta, GuviCallback, ExtractedIntelligence, AgentState
from app.database import SessionManager
from app.agents.detection import detect_scam
from app.agents.persona import generate_persona_response
from app.agents.extraction import extract_intelligence
from app.agents.hallucination_filter import validate_persona_output
from app.agents.timeline import get_conversation_summary, calculate_confidence_level

from app.utils import (
    logger, 
    get_session_logger, 
    PerformanceLogger, 
    log_intelligence,
    send_final_callback,
    should_send_callback
)


# ============================================
# NODE FUNCTIONS
# ============================================

def load_session_node(state: AgentState) -> AgentState:
    """
    Node 1: Load or create session from database.
    
    This is the entry point of the graph.
    """
    
    session_id = state["sessionId"]
    session_logger = get_session_logger(session_id)
    
    logger.info(f"\n{'-'*70}")
    logger.info(f"NODE: Load Session")
    logger.info(f"{'-'*70}")
    
    session_logger.info(f"Loading session: {session_id}")
    
    db = SessionManager()
    
    # Try to load existing session
    existing_state = db.get_session(session_id)
    
    if existing_state:
        logger.info(f"OK: Found existing session (messages: {existing_state['totalMessages']})")
        session_logger.info(f"Loaded existing session with {existing_state['totalMessages']} messages")
        # Merge existing state with new message
        state.update(existing_state)
    else:
        logger.info(f"NEW: Creating new session")
        session_logger.info("Created new session")
    
    return state


def detection_node(state: AgentState) -> AgentState:
    """
    Node 2: Run scam detection (only on first message).
    
    Sets scamDetected flag in state.
    """
    
    session_id = state["sessionId"]
    session_logger = get_session_logger(session_id)
    
    logger.info(f"\n{'-'*70}")
    logger.info(f"NODE: Detection Agent")
    logger.info(f"{'-'*70}")
    
    # Only run detection on first message
    if state["totalMessages"] == 1:
        with PerformanceLogger("Detection Agent", logger):
            last_message = state["conversationHistory"][-1]["text"]
            
            is_scam, confidence = detect_scam(last_message)
            
            state["scamDetected"] = is_scam
            state["agentNotes"] = f"Detection: {'SCAM' if is_scam else 'LEGITIMATE'} (confidence: {confidence:.2f})"
            
            logger.info(f"{'='*70}")
            logger.info(f"RESULT: {'SCAM DETECTED' if is_scam else 'NOT A SCAM'}")
            logger.info(f"   Confidence: {confidence:.2f}")
            logger.info(f"{'='*70}")
            
            session_logger.info(f"Detection: scam={is_scam}, confidence={confidence:.2f}")
    else:
        logger.info(f"SKIP: Skipping detection (not first message)")
    
    return state


def persona_node(state: AgentState) -> AgentState:
    """
    Node 3: Generate context-aware persona response using LLM.
    
    Extracts intelligence FIRST to inform persona strategy.
    Only runs if scam was detected.
    """
    
    session_id = state["sessionId"]
    session_logger = get_session_logger(session_id)
    
    logger.info(f"\n{'-'*70}")
    logger.info(f"NODE: Persona Agent (Context-Aware)")
    logger.info(f"{'-'*70}")
    
    try:
        with PerformanceLogger("Persona Agent", logger):
            
            # ============================================
            # EXTRACT INTELLIGENCE FIRST (for context)
            # ============================================
            
            logger.debug("Extracting current intelligence for persona context...")
            
            current_intelligence = extract_intelligence(
                conversation_history=state["conversationHistory"]
            )
            
            # Count evidence pieces
            evidence_count = sum([
                len(current_intelligence.get("phoneNumbers", [])),
                len(current_intelligence.get("upiIds", [])),
                len(current_intelligence.get("phishingLinks", [])),
                len(current_intelligence.get("bankAccounts", []))
            ])
            
            logger.debug(f"Current evidence count: {evidence_count} pieces")
            session_logger.info(f"Current intelligence: {current_intelligence}")
            
            # ============================================
            # GENERATE CONTEXT-AWARE RESPONSE
            # ============================================
            
            raw_persona_response = generate_persona_response(
                conversation_history=state["conversationHistory"],
                metadata=state["metadata"],
                extracted_intelligence=current_intelligence  # <- Context-aware!
            )
            
            # ============================================
            # ANTI-HALLUCINATION FILTER
            # Runs BEFORE response enters conversation.
            # Catches any sensitive data the LLM invented.
            # ============================================
            
            persona_response, was_filtered = validate_persona_output(raw_persona_response)
            
            if was_filtered:
                logger.warning(f"🛡️  Response sanitized before sending")
            
            logger.info(f"OK: Generated: '{persona_response[:80]}...'")
            session_logger.info(f"Persona response: {persona_response}")
            
            # Add to conversation history
            state["conversationHistory"].append({
                "sender": "user",
                "text": persona_response,
                "timestamp": datetime.now().isoformat() + "Z"
            })
            state["totalMessages"] += 1
            
    except Exception as e:
        logger.error(f"ERR: Persona error: {e}", exc_info=True)
        session_logger.error(f"Persona generation failed: {str(e)}")
        
        # Fallback response
        fallback = "I'm sorry, I'm getting confused. Can you explain more slowly?"
        
        logger.warning(f"Using fallback response: {fallback}")
        
        state["conversationHistory"].append({
            "sender": "user",
            "text": fallback,
            "timestamp": datetime.now().isoformat() + "Z"
        })
        state["totalMessages"] += 1
    
    return state


def extraction_node(state: AgentState) -> AgentState:
    """
    Node 4: Extract intelligence from conversation.
    
    Runs after persona generates response.
    Final extraction for storage and reporting.
    """
    
    session_id = state["sessionId"]
    session_logger = get_session_logger(session_id)
    
    logger.info(f"\n{'-'*70}")
    logger.info(f"NODE: Extraction Agent (Final)")
    logger.info(f"{'-'*70}")
    
    try:
        with PerformanceLogger("Extraction Agent", logger):
            # Extract intelligence
            intelligence = extract_intelligence(
                conversation_history=state["conversationHistory"]
            )
            
            state["extractedIntelligence"] = intelligence
            
            # Log intelligence
            log_intelligence(session_id, intelligence)
            session_logger.info(f"Final extracted intelligence: {intelligence}")
            
            # Count extracted items (for logging ONLY - don't add to agentNotes)
            extracted_count = sum(
                len(v) for v in intelligence.values()
                if isinstance(v, list)
            )
            
            if extracted_count > 0:
                logger.info(f"[STATS] Total intelligence items: {extracted_count}")
            else:
                logger.info(f"[STATS] No intelligence extracted yet")
            
    except Exception as e:
        logger.error(f"ERR: Extraction error: {e}", exc_info=True)
        session_logger.error(f"Extraction failed: {str(e)}")
    
    return state


def not_scam_node(state: AgentState) -> AgentState:
    """
    Node 5: Handle non-scam messages.
    
    Adds polite response and ends conversation.
    """
    
    session_id = state["sessionId"]
    session_logger = get_session_logger(session_id)
    
    logger.info(f"\n{'-'*70}")
    logger.info(f"OK: NODE: Not A Scam Handler")
    logger.info(f"{'-'*70}")
    
    response_text = "Thank you for your message. Have a great day!"
    
    state["conversationHistory"].append({
        "sender": "user",
        "text": response_text,
        "timestamp": datetime.now().isoformat() + "Z"
    })
    state["totalMessages"] += 1
    
    logger.info(f"SEND: Response: {response_text}")
    session_logger.info(f"Not a scam - sent polite response")
    
    return state


def save_session_node(state: AgentState) -> AgentState:
    """
    Node 6: Save session to database.
    
    Generates timeline summary, saves to DB,
    then dynamically decides whether to end conversation
    based on extracted intelligence categories.
    Sets sessionStatus to "closed" or "active".
    """
    
    session_id = state["sessionId"]
    session_logger = get_session_logger(session_id)
    
    logger.info(f"\n{'─'*70}")
    logger.info(f"💾 NODE: Save Session")
    logger.info(f"{'─'*70}")
    
    state["lastUpdated"] = datetime.now().isoformat() + "Z"
    
    # ============================================
    # GENERATE SUMMARY
    # ============================================
    
    # ============================================
    # GENERATE SUMMARY (FOR CALLBACK ONLY)
    # ============================================
    
    # Store complete summary with intelligence for CALLBACK
    # This will be sent to GUVI endpoint ONLY, not to user
    if state["scamDetected"] and state["totalMessages"] >= 3:
        logger.info("📊 Generating conversation summary for callback...")
        
        # Extract detection confidence from agentNotes
        detection_confidence = 0.5  # default
        if "confidence:" in state.get("agentNotes", ""):
            try:
                conf_str = state["agentNotes"].split("confidence:")[1].split(")")[0].strip()
                detection_confidence = float(conf_str)
            except:
                pass
        
        try:
            complete_summary = get_conversation_summary(
                conversation_history=state["conversationHistory"],
                extracted_intelligence=state["extractedIntelligence"],
                detection_confidence=detection_confidence,
                scam_detected=state["scamDetected"]
            )
            
            # Store in a SEPARATE field for callback only
            state["fullSummaryForCallback"] = complete_summary
            
            logger.info(f"✅ Summary generated for callback")
            session_logger.info(f"Callback summary: {complete_summary}")
            
        except Exception as e:
            logger.warning(f"⚠️ Summary generation failed: {e}")
            session_logger.warning(f"Summary generation failed: {e}")
            state["fullSummaryForCallback"] = state["agentNotes"]  # Fallback to basic detection
    
    # ============================================
    # DYNAMIC CALLBACK CHECK
    # ============================================
    
    if should_send_callback(state):
        # IDEMPOTENCY CHECK
        if state.get("callbackSent", False):
            logger.info(f"⏭️  Callback ALREADY SENT previously. Skipping to prevent duplicates.")
            session_logger.info("Callback skipped (idempotency check passed)")
            state["sessionStatus"] = "closed"
            # Proceed to save state (so sessionStatus is persisted)
        else:
            logger.info(f"\n🏁 TERMINATION DECIDED - Sending final callback...")
            session_logger.info("Conversation ending - sending callback to GUVI")
            
            callback_success = send_final_callback(state["sessionId"], state)
            
            if callback_success:
                logger.info(f"✅ Final callback sent successfully")
                session_logger.info("Final callback sent successfully")
                state["callbackSent"] = True  # MARK AS SENT
            else:
                logger.warning(f"⚠️ Final callback failed")
                session_logger.warning("Final callback failed")
            
            # Mark conversation as closed
            state["sessionStatus"] = "closed"
    else:
        logger.info(f"🔄 Conversation continuing...")
        state["sessionStatus"] = "active"
        
    # ============================================
    # SAVE TO DATABASE (FINAL STATE)
    # ============================================
    
    db = SessionManager()
    db.save_session(state["sessionId"], state)
    
    logger.info(f"✅ Session saved")
    session_logger.info(f"Session saved - Total messages: {state['totalMessages']}")
    
    return state


# ============================================
# ROUTING FUNCTIONS (Conditional Edges)
# ============================================

def should_detect(state: AgentState) -> Literal["detection", "persona"]:
    """
    Route decision: Should we run detection?
    
    Only detect on first message.
    """
    if state["totalMessages"] == 1:
        logger.debug("Routing: First message → Detection Agent")
        return "detection"
    else:
        logger.debug("Routing: Not first message → Persona Agent")
        return "persona"


def route_after_detection(state: AgentState) -> Literal["persona", "not_scam"]:
    """
    Route decision: Is it a scam?
    
    If scam → persona agent
    If not scam → polite exit
    """
    if state["scamDetected"]:
        logger.debug("Routing: Scam detected → Persona Agent")
        return "persona"
    else:
        logger.debug("Routing: Not a scam → Polite Exit")
        return "not_scam"


# ============================================
# BUILD THE GRAPH
# ============================================

def create_workflow_graph():
    """
    Create and compile the LangGraph workflow.
    
    Graph Structure:
    
        START
          ↓
      load_session
          ↓
      [First message?]
          ↓
       detection ←─── (only if first message)
          ↓
      [Is scam?]
       ↙      ↘
    persona  not_scam
       ↓         ↓
    extraction   ↓
       ↓         ↓
    save_session
       ↓
       END
    """
    
    logger.info("[BUILD] Building LangGraph workflow...")
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # ============================================
    # ADD NODES
    # ============================================
    
    workflow.add_node("load_session", load_session_node)
    workflow.add_node("detection", detection_node)
    workflow.add_node("persona", persona_node)
    workflow.add_node("extraction", extraction_node)
    workflow.add_node("not_scam", not_scam_node)
    workflow.add_node("save_session", save_session_node)
    
    logger.debug("OK: Added 6 nodes to graph")
    
    # ============================================
    # SET ENTRY POINT
    # ============================================
    
    workflow.set_entry_point("load_session")
    logger.debug("OK: Set entry point: load_session")
    
    # ============================================
    # ADD EDGES
    # ============================================
    
    # From load_session → conditional: detect or skip to persona
    workflow.add_conditional_edges(
        "load_session",
        should_detect,
        {
            "detection": "detection",
            "persona": "persona"
        }
    )
    
    # From detection → conditional: scam or not_scam
    workflow.add_conditional_edges(
        "detection",
        route_after_detection,
        {
            "persona": "persona",
            "not_scam": "not_scam"
        }
    )
    
    # From persona → extraction (always)
    workflow.add_edge("persona", "extraction")
    
    # From extraction → save_session
    workflow.add_edge("extraction", "save_session")
    
    # From not_scam → save_session
    workflow.add_edge("not_scam", "save_session")
    
    # From save_session → END
    workflow.add_edge("save_session", END)
    
    logger.debug("OK: Added all edges (2 conditional, 4 direct)")
    
    # ============================================
    # COMPILE THE GRAPH
    # ============================================
    
    compiled_graph = workflow.compile()
    
    logger.info("OK: LangGraph workflow compiled successfully")
    logger.info("   Nodes: 6 (load_session, detection, persona, extraction, not_scam, save_session)")
    logger.info("   Edges: 6 (2 conditional routing points)")
    logger.info("   Features: Context-aware persona, dynamic termination, logging, final callback")
    
    return compiled_graph


# ============================================
# GLOBAL COMPILED GRAPH
# ============================================

# Compile once at module load
logger.info("="*70)
logger.info("[INIT] Initializing LangGraph Workflow")
logger.info("="*70)

WORKFLOW_GRAPH = create_workflow_graph()

logger.info("="*70)
logger.info("OK: LangGraph Workflow Ready")
logger.info("="*70)


# ============================================
# MAIN ENTRY POINT
# ============================================

async def run_honeypot_workflow(request: HoneypotRequest) -> JudgeResponse:
    """
    Execute the LangGraph workflow.
    
    This is called by FastAPI main.py.
    
    Args:
        request: HoneypotRequest from judges
    
    Returns:
        JudgeResponse (new format for judges' screen)
    """
    
    logger.info(f"\n{'='*70}")
    logger.info(f"START: LANGGRAPH WORKFLOW STARTING")
    logger.info(f"{'='*70}")
    
    # ============================================
    # Prepare initial state
    # ============================================
    
    session_id = request.sessionId
    scammer_message = request.message
    metadata = request.metadata.dict() if request.metadata else {}
    
    logger.info(f"📋 Session ID: {session_id}")
    logger.info(f"📨 Scammer Message: {scammer_message.text[:100]}...")
    logger.info(f"📍 Channel: {metadata.get('channel', 'unknown')}")
    
    # Create initial state
    initial_state = AgentState(
        sessionId=session_id,
        conversationHistory=[{
            "sender": scammer_message.sender,
            "text": scammer_message.text,
            "timestamp": scammer_message.timestamp
        }],
        metadata=metadata,
        scamDetected=False,
        extractedIntelligence={
            "bankAccounts": [],
            "upiIds": [],
            "phishingLinks": [],
            "phoneNumbers": [],
            "suspiciousKeywords": []
        },
        totalMessages=1,
        startTime=scammer_message.timestamp,
        lastUpdated=scammer_message.timestamp,
        agentNotes="",
        sessionStatus="active",
        callbackSent=False  # Init new field
    )
    
    # ============================================
    # Run the graph
    # ============================================
    
    try:
        logger.info("[EXEC] Executing workflow graph...")
        
        from fastapi.concurrency import run_in_threadpool
        with PerformanceLogger("Full Workflow", logger):
            final_state = await run_in_threadpool(WORKFLOW_GRAPH.invoke, initial_state)
        
        logger.info(f"\n{'='*70}")
        logger.info(f"OK: LANGGRAPH WORKFLOW COMPLETED")
        logger.info(f"{'='*70}")
        logger.info(f"[STATS] Final Stats:")
        logger.info(f"   Total Messages: {final_state['totalMessages']}")
        logger.info(f"   Scam Detected: {final_state['scamDetected']}")
        logger.info(f"   Session Status: {final_state.get('sessionStatus', 'unknown')}")
        logger.info(f"   Intelligence Items: {sum(len(v) for v in final_state['extractedIntelligence'].values() if isinstance(v, list))}")
        logger.info(f"{'='*70}\n")
        
        # ============================================
        # Build response for judges
        # ============================================
        
        last_message = final_state["conversationHistory"][-1]
        reply_text = last_message["text"]
        
        # Check if conversation ended (set by save_session_node via should_send_callback)
        is_complete = final_state.get("sessionStatus") == "closed"
        
        # Calculate confidence (only show on final response)
        confidence = None
        if is_complete:
            detection_conf = 0.5
            if "confidence:" in final_state.get("agentNotes", ""):
                try:
                    conf_str = final_state["agentNotes"].split("confidence:")[1].split(")")[0].strip()
                    detection_conf = float(conf_str)
                except:
                    pass
            
            intel_count = sum(
                len(v) for v in final_state['extractedIntelligence'].values()
                if isinstance(v, list)
            )
            
            confidence = calculate_confidence_level(
                detection_conf,
                intel_count,
                final_state["totalMessages"]
            )
        
        # Persona type
        persona = "confused_customer" if final_state["scamDetected"] else "polite_responder"
        
        # ============================================
        # SANITIZE agentNotes - NO INTELLIGENCE LEAK
        # ============================================
        # Only show detection result, NOT intelligence details
        # Full intelligence goes ONLY to GUVI callback
        
        if final_state["scamDetected"]:
            # Extract ONLY detection confidence
            detection_line = "Detection: SCAM"
            if "confidence:" in final_state.get("agentNotes", ""):
                try:
                    conf_str = final_state["agentNotes"].split("confidence:")[1].split(")")[0].strip()
                    detection_line = f"Detection: SCAM (confidence: {conf_str})"
                except:
                    pass
            sanitized_notes = detection_line
        else:
            sanitized_notes = "Detection: LEGITIMATE"
        
        # Build response metadata (with sanitized notes)
        response_meta = ResponseMeta(
            agentState="completed" if is_complete else "engaging",
            sessionStatus="closed" if is_complete else "active",
            persona=persona,
            turn=final_state["totalMessages"],
            confidence=confidence,
            agentNotes=sanitized_notes  # <-- SANITIZED
        )
        
        # Build judge response
        response = JudgeResponse(
            status="success",
            reply=reply_text,
            meta=response_meta
        )
        
        logger.info(f"📤 Response - State: {response_meta.agentState} | Status: {response_meta.sessionStatus} | Turn: {response_meta.turn}")
        if confidence:
            logger.info(f"   Confidence: {confidence}")
        
        return response
        
    except Exception as e:
        logger.error(f"\n{'='*70}")
        logger.error(f"WORKFLOW ERROR")
        logger.error(f"{'='*70}")
        logger.error(f"Error: {str(e)}", exc_info=True)
        logger.error(f"{'='*70}\n")
        raise


# ============================================
# OPTIONAL: Visualize Graph
# ============================================

def visualize_graph():
    """
    Print the graph structure (for debugging).
    
    Run with: python -c "from app.workflow.graph import visualize_graph; visualize_graph()"
    """
    print("\n" + "="*70)
    print("LANGGRAPH WORKFLOW STRUCTURE")
    print("="*70 + "\n")
    
    print("NODES:")
    print("  1. load_session    - Load or create session from DB")
    print("  2. detection       - Run scam detection (first message only)")
    print("  3. persona         - Generate context-aware LLM response (if scam)")
    print("  4. extraction      - Extract intelligence (final)")
    print("  5. not_scam        - Handle non-scam messages")
    print("  6. save_session    - Save to DB + dynamic termination + callback if done")
    
    print("\nEDGES:")
    print("  START → load_session")
    print("  load_session → [conditional]")
    print("     ├─ (first message) → detection")
    print("     └─ (not first) → persona")
    print("  detection → [conditional]")
    print("     ├─ (scam) → persona")
    print("     └─ (not scam) → not_scam")
    print("  persona → extraction")
    print("  extraction → save_session")
    print("  not_scam → save_session")
    print("  save_session → END")
    
    print("\nFEATURES:")
    print("  ✅ Context-Aware Persona (adapts based on extracted intelligence)")
    print("  ✅ Dynamic Termination (category-based, not fixed message count)")
    print("  ✅ Comprehensive Logging (console + file + session-specific)")
    print("  ✅ Performance Tracking (timing for each node)")
    print("  ✅ Final Callback to GUVI (automatic when conversation completes)")
    print("  ✅ Error Recovery (graceful fallbacks)")
    print("  ✅ Smart Routing (conditional logic based on state)")
    
    print("\nTERMINATION THRESHOLDS:")
    print("  3+ categories  → End immediately (strong evidence)")
    print("  2 categories   → End at 8+ messages (decent evidence)")
    print("  1 category     → End at 12+ messages (weak evidence)")
    print("  0 categories   → End at 8 messages (nothing found)")
    print("  Hard max       → 18 messages absolute limit")
    
    print("\n" + "="*70 + "\n")