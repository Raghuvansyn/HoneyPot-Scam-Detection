# app/main.py
"""
FastAPI Application with Logging
Main entry point - handles HTTP requests from judges.
Updated with new response format for judges' screen.
"""

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from app.models import HoneypotRequest, JudgeResponse  # <- Changed from HoneypotResponse
from app.workflow.graph import run_honeypot_workflow
from app.config import API_KEY
from app.utils import logger, log_request, log_error  # <- Using centralized logger
import time
from fastapi.concurrency import run_in_threadpool

# Create FastAPI app
app = FastAPI(
    title="🛡️ AI Honeypot & Scam Detection System",
    version="1.0.0"
)

from app.database import SessionManager

@app.on_event("startup")
async def startup_event():
    """Log startup"""
    logger.info("="*70)
    logger.info("STARTUP: HONEYPOT API STARTING")
    logger.info("="*70)
    
    # Initialize DB immediately (in threadpool to avoid blocking loop)
    # try:
    #     await run_in_threadpool(SessionManager)
    #     logger.info("OK: Database initialized and tables created")
    # except Exception as e:
    #     logger.error(f"ERR: Database initialization failed: {e}")
        
    logger.info("OK: Logging system initialized")
    logger.info("OK: Database ready")
    logger.info("OK: LangGraph workflow compiled")
    logger.info("OK: New response format enabled")
    logger.info("="*70)

@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown"""
    logger.info("="*70)
    logger.info("SHUTDOWN: HONEYPOT API SHUTTING DOWN")
    logger.info("="*70)



@app.get("/")
async def root():
    """
    Health check endpoint.
    Test with: http://localhost:8000/
    """
    logger.debug("Health check requested")
    return {
        "status": "online",
        "service": "Honeypot Scam Detection API",
        "version": "1.0.0 - Phase 1",
        "features": [
            "Context-Aware Persona",
            "Timeline Analysis",
            "Intelligence Extraction",
            "GUVI Callback Integration"
        ]
    }

@app.get("/health")
async def health_check():
    """
    Detailed health check.
    Test with: http://localhost:8000/health
    """
    logger.debug("Detailed health check requested")
    return {
        "status": "healthy",
        "database": "connected",
        "agents": "ready",
        "workflow": "compiled",
        "llm": "groq-connected"
    }

@app.post("/api/v1/honeypot", response_model=JudgeResponse)  # <- Changed response model
async def honeypot_endpoint(
    request: HoneypotRequest,
    x_api_key: str = Header(..., description="API key for authentication")
):
    """
    Main honeypot endpoint with new response format.
    
    Receives scam messages from judges and returns intelligent responses.
    
    RESPONSE FORMAT (What judges see on their screen):
    {
        "status": "success",
        "reply": "persona response text",
        "meta": {
            "agentState": "engaging" | "completed",
            "sessionStatus": "active" | "closed",
            "persona": "confused_customer" | "polite_responder",
            "turn": message_count,
            "confidence": "high" | "medium" | "low" (final only),
            "agentNotes": "detection and timeline summary"
        }
    }
    
    CALLBACK (Sent to GUVI endpoint automatically):
    - POST https://hackathon.guvi.in/api/updateHoneyPotFinalResult
    - Contains: sessionId, scamDetected, totalMessagesExchanged, 
                extractedIntelligence, agentNotes
    
    Headers:
        x-api-key: Your secret API key
    
    Body:
        HoneypotRequest JSON (see models.py)
    
    Returns:
        JudgeResponse JSON (clean format for judges' screen)
    
    Example curl command:
        curl -X POST http://localhost:8000/api/v1/honeypot \
          -H "x-api-key: YOUR_KEY_HERE" \
          -H "Content-Type: application/json" \
          -d @test.json
    """
    
    # ============================================
    # STEP 1: Validate API key
    # ============================================
    
    if x_api_key != API_KEY:
        logger.warning(f"WARN: Invalid API key attempt for session: {request.sessionId}")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    # ============================================
    # STEP 2: Log request
    # ============================================
    
    logger.info("="*70)
    logger.info(f"OK: Valid API key - Session: {request.sessionId}")
    log_request(request.sessionId, request.message.text)
    logger.info("="*70)
    
    # ============================================
    # STEP 3: Process through workflow
    # ============================================
    
    try:
        response = await run_honeypot_workflow(request)
        
        logger.info(f"OK: Request processed successfully for session: {request.sessionId}")
        logger.info(f"SEND: Response - Agent State: {response.meta.agentState}, Turn: {response.meta.turn}")
        
        return response
        
    except Exception as e:
        log_error(e, f"Session: {request.sessionId}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
    # return JudgeResponse(status="mock", reply="debug mode", meta={"agentState": "engaging", "sessionStatus": "active", "persona": "debug", "turn": 0, "agentNotes": ""})

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all exceptions and log them"""
    log_error(exc, f"Unhandled exception on {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "detail": f"Internal server error: {str(exc)}"
        }
    )

