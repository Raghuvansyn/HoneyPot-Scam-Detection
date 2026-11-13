"""
FastAPI Application — Honeypot API with concurrency controls.
"""

import asyncio
import time
import secrets
from contextlib import asynccontextmanager
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from src.models import HoneypotRequest, JudgeResponse
from src.workflow.graph import run_honeypot_workflow
from src.config import API_KEY, MODE
from src.utils import logger, log_request, log_error

MAX_CONCURRENT = 30
_semaphore = asyncio.Semaphore(MAX_CONCURRENT)
_session_locks: dict = {}
_session_users: dict = {}
_session_locks_lock = asyncio.Lock()


@asynccontextmanager
async def session_guard(session_id: str):
    # Count waiters before acquiring the lock so a finishing request cannot
    # remove a lock while another request is queued on it.
    async with _session_locks_lock:
        if session_id not in _session_locks:
            _session_locks[session_id] = asyncio.Lock()
            _session_users[session_id] = 0
        lock = _session_locks[session_id]
        _session_users[session_id] += 1
    try:
        async with lock:
            yield
    finally:
        async with _session_locks_lock:
            _session_users[session_id] -= 1
            if _session_users[session_id] == 0:
                del _session_locks[session_id]
                del _session_users[session_id]


app = FastAPI(
    title="ScamBait AI - Honeypot Scam Detection",
    version="2.0.0",
    description="Active defense system that engages scammers and extracts forensic intelligence",
)


@app.on_event("startup")
async def startup_event():
    from src.config import CEREBRAS_API_KEY, GROQ_API_KEY, MODE
    logger.info(f"ScamBait AI starting | max_concurrent={MAX_CONCURRENT} | mode={MODE}")
    logger.info(f"LLM keys: cerebras={'SET' if CEREBRAS_API_KEY else 'MISSING'} | groq={'SET' if GROQ_API_KEY and GROQ_API_KEY != 'temp-key' else 'MISSING'}")


@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "ScamBait AI",
        "version": "2.0.0",
        "concurrent_capacity": MAX_CONCURRENT,
        "active_sessions": len(_session_locks),
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "active_sessions": len(_session_locks)}


@app.post("/honeypot", response_model=JudgeResponse)
@app.post("/api/v1/honeypot", response_model=JudgeResponse)
async def honeypot_endpoint(
    request: HoneypotRequest,
    x_api_key: str = Header(default=None, description="API key for authentication"),
):
    start_time = time.time()

    if MODE == "prod" and (not API_KEY or API_KEY == "temp-key"):
        raise HTTPException(status_code=503, detail="Server API key is not configured")
    if API_KEY and not secrets.compare_digest(x_api_key or "", API_KEY):
        raise HTTPException(status_code=401, detail="Invalid API key")

    logger.info(f"REQ session={request.sessionId} | msg='{request.message.text[:60]}'")
    log_request(request.sessionId, request.message.text)

    async with _semaphore:
        async with session_guard(request.sessionId):
            try:
                response = await asyncio.wait_for(
                    run_honeypot_workflow(request), timeout=35.0,
                )
                elapsed = time.time() - start_time
                logger.info(
                    f"OK session={request.sessionId} | state={response.meta.agentState} "
                    f"| turn={response.meta.turn} | time={elapsed:.2f}s"
                )

                return response

            except asyncio.TimeoutError:
                logger.error(f"TIMEOUT session={request.sessionId} after {time.time() - start_time:.2f}s")
                raise HTTPException(status_code=504, detail="Workflow timed out")

            except Exception as e:
                log_error(e, f"session={request.sessionId}")
                raise HTTPException(status_code=503, detail="Workflow unavailable")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log_error(exc, f"Unhandled on {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "detail": "Internal server error",
        },
    )
