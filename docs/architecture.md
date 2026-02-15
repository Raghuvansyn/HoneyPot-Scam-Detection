# Architecture

## System Overview

ScamBait AI is a multi-agent honeypot system built on FastAPI and orchestrated via LangGraph. The system receives incoming scam messages through a REST API, detects whether they are scams, engages the scammer using an AI-powered persona, extracts actionable intelligence, and reports findings to a law enforcement callback endpoint.

---

## High-Level Flow

```
Client (Evaluator / Scammer)
        |
        |  POST /honeypot
        v
+-------------------+
|   FastAPI Server   |
|  (main.py)         |
|  - Auth (x-api-key)|
|  - Semaphore (30)  |
|  - Session Locks   |
|  - 35s Timeout     |
+--------+----------+
         |
         v
+-------------------+
|  LangGraph         |
|  Workflow Engine    |
|  (workflow/graph.py)|
+--------+----------+
         |
         |  1. load_session
         |  2. detection (conditional)
         |  3. persona  OR  not_scam
         |  4. extraction
         |  5. save_session
         |
         v
+-------------------+
|  Response to       |
|  Client            |
+-------------------+
```

---

## Agent Modules

### 1. Detection Agent (`agents/detection.py`)

Cascading pipeline that runs fast checks first and expensive checks only when needed:

| Layer | Method | Speed | When Used |
|-------|--------|-------|-----------|
| 0 | Jailbreak regex guard | <1ms | Always (first check) |
| 1 | Text normalization | <1ms | Always |
| 2 | Digital arrest detection | <5ms | Always |
| 3 | Rule-based keyword scoring | <5ms | Always |
| 4 | ML classifier (TF-IDF + SVM) | <50ms | If rules are inconclusive |
| 5 | LLM fallback (Cerebras/Groq) | 1-3s | If ML is inconclusive |

The pipeline short-circuits at each layer. If rules return a high-confidence result, ML and LLM are never called.

### 2. Persona Agent (`agents/persona.py`)

Generates conversational responses using LLMs (Cerebras primary, Groq fallback). The persona adapts its strategy based on what intelligence has already been extracted:

- **Low intelligence (0 items):** Play confused, act technologically illiterate, force scammer to repeat details.
- **Medium intelligence (1 item):** Targeted probing to extract the next category of information.
- **High intelligence (2+ items):** Verify accuracy of extracted data, then allow conversation to close.

Four distinct personas are available (Meena, Rohan, Ramesh, Mrs. Sharma), assigned deterministically per session.

### 3. Extraction Agent (`agents/extraction.py`)

Regex-based intelligence extraction. Runs on both original text and normalized text (to defeat obfuscation). Extracts:

- Phone numbers (Indian formats)
- UPI IDs (standard and obfuscated)
- Bank account numbers
- Phishing links
- Suspicious keywords

No LLM is used for extraction — this eliminates hallucination risk.

### 4. Hallucination Filter (`agents/hallucination_filter.py`)

Scans LLM persona output before it enters the conversation. Catches and replaces any sensitive data the LLM may have invented (OTPs, phone numbers, bank accounts, URLs).

### 5. Digital Arrest Module (`agents/digital_arrest.py`)

Specialized detector for authority-impersonation scams (India's most prevalent scam type). Detects patterns like:

- Authority keyword mentions (CBI, police, TRAI, court)
- Scam trigger phrases (parcel seized, arrest warrant, money laundering)
- Pressure tactics (stay on call, security deposit, video call hearing)

### 6. Timeline Agent (`agents/timeline.py`)

Analyzes the completed conversation to identify scam phases (urgency, authority, fear, credential request, payment redirection). Generates a summary that is included in the final callback.

---

## Workflow Graph (LangGraph)

```
START
  |
  v
load_session ──────────────────────────────────────+
  |                                                 |
  v                                                 |
[scam already confirmed?]                          |
  |              |                                  |
  YES            NO                                |
  |              |                                  |
  v              v                                  |
persona      detection                             |
  |              |                                  |
  |         [is scam?]                             |
  |          |       |                              |
  |         YES    [trusted?]                      |
  |          |      |       |                       |
  |          v     YES      NO (turn <= 3)         |
  |       persona  |        |                       |
  |          |   not_scam  persona (paranoid probe) |
  |          |     |        |                       |
  v          v     v        v                       |
extraction   extraction  not_scam                  |
  |          |     |        |                       |
  v          v     v        v                       |
save_session ──────────────────────────────────────+
  |
  v
END
```

**Key routing decisions:**

- If scam was already detected in a prior turn, skip detection and go straight to persona.
- If detection says "safe" but it's turn 1-3, engage anyway ("paranoid probe") to catch slow-boil scams.
- If detection returns a trusted sender pattern (real OTP, real bank alert), exit immediately.

---

## Concurrency Model

| Mechanism | Purpose |
|-----------|---------|
| `asyncio.Semaphore(30)` | Limits to 30 concurrent requests; remaining queue |
| Per-session `asyncio.Lock` | Prevents race conditions when same sessionId is sent twice |
| SQLite WAL mode | Allows concurrent reads with single writer |
| Thread-local DB connections | Prevents connection sharing across threads |
| 35-second hard timeout | Prevents hung requests from blocking slots |

---

## Dynamic Termination

Conversations are not terminated at a fixed turn count. Instead, termination is based on intelligence quality:

| Condition | Action |
|-----------|--------|
| 3+ intelligence categories filled | End immediately |
| 2 categories + 6+ messages | End |
| 1 category + 12+ messages | End |
| 0 categories + 12+ messages | End (give up) |
| 20 messages | Hard maximum, end regardless |
| Non-scam detected | End immediately |

---

## External Dependencies

| Dependency | Role |
|------------|------|
| Cerebras API | Primary LLM provider (llama3.1-8b) |
| Groq API | Fallback LLM provider (llama-3.1-8b-instant) |
| GUVI Hackathon endpoint | Receives final callback with extracted intelligence |

---

## Deployment

The application is deployed on Railway. The entry point is `src.main:app` (uvicorn). Environment variables are managed via `.env` locally and platform secrets in production.
