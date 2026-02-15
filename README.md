# ScamBait AI

**An AI-powered honeypot system that detects scams, engages scammers in realistic conversation, and extracts actionable intelligence for law enforcement.**

Built for the **GUVI Hackathon 2026**.

| | |
|---|---|
| **Deployed URL** | `https://scambait-ai-production.up.railway.app/api/v1/honeypot` |
| **API Key** | `GUVI-Hackathon-2026-ScamBait-xK9mP2vL7qR3wT8` |
| **GitHub** | [github.com/diyaavirmani/HoneyPot-Scam-Detection](https://github.com/diyaavirmani/HoneyPot-Scam-Detection) |

---

## Description

Traditional scam detection systems simply block suspicious messages. ScamBait AI takes a fundamentally different approach: it **engages** the scammer using a convincing AI persona, prolonging the conversation to extract phone numbers, UPI IDs, bank accounts, and phishing links. This intelligence is then automatically relayed to law enforcement endpoints.

**Core strategy:**

```
Scam Detected  -->  Engage Scammer  -->  Extract Intelligence  -->  Report to LEA
```

The system uses a multi-agent architecture orchestrated via LangGraph, with a cascading detection pipeline (Rules -> ML -> LLM fallback) and context-aware persona generation that adapts its conversation strategy based on what intelligence has already been extracted.

---

## Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| **Framework** | FastAPI (async) | High-performance API with concurrency controls |
| **Orchestration** | LangGraph | Multi-agent workflow with conditional routing |
| **LLM Integration** | LangChain + Cerebras / Groq | Persona generation and fallback scam detection |
| **ML Model** | scikit-learn (TF-IDF + LinearSVC) | Fast pattern-based scam classification |
| **Database** | SQLite (WAL mode) | Session persistence with concurrent access |
| **Language** | Python 3.11+ | Full ML/NLP ecosystem support |

**LLM Models used:**
- Primary: Cerebras `llama3.1-8b`
- Fallback: Groq `llama-3.1-8b-instant`

---

## Setup Instructions

### Prerequisites

- Python 3.11+
- A Groq API key ([free tier available](https://console.groq.com))
- A Cerebras API key (optional, Groq is used as fallback)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/diyaavirmani/HoneyPot-Scam-Detection.git
cd HoneyPot-Scam-Detection

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# Edit .env and add your API keys

# 4. Start the server
python run.py
```

The server starts at `http://localhost:8002`. Interactive API docs are available at `http://localhost:8002/docs`.

---

## API Endpoint

| Field | Value |
|---|---|
| **Deployed URL** | `https://scambait-ai-production.up.railway.app/api/v1/honeypot` |
| **Alternate URL** | `https://scambait-ai-production.up.railway.app/honeypot` |
| **Method** | `POST` |
| **Authentication** | `x-api-key` header |
| **Content-Type** | `application/json` |

### Request Format

```json
{
  "sessionId": "test-session-001",
  "message": {
    "sender": "scammer",
    "text": "URGENT! Your bank account has been blocked. Send OTP to 9876543210.",
    "timestamp": "2026-02-16T10:00:00Z"
  },
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

### Response Format

```json
{
  "status": "success",
  "reply": "Oh no! What happened? Let me get my pen...",
  "meta": {
    "agentState": "engaging",
    "sessionStatus": "active",
    "persona": "confused_customer",
    "turn": 2,
    "agentNotes": "Detection: SCAM (confidence: 0.95)"
  }
}
```

### cURL Example

```bash
curl -X POST "https://scambait-ai-production.up.railway.app/api/v1/honeypot" \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "sessionId": "demo-001",
    "message": {
      "sender": "scammer",
      "text": "Your KYC is pending. Update now or account will be frozen.",
      "timestamp": "2026-02-16T10:00:00Z"
    }
  }'
```

---

## Approach

### How We Detect Scams

The detection engine uses a **cascading pipeline** — fast checks run first, expensive checks only when needed:

1. **Jailbreak Guard** — Instant block for prompt injection attempts
2. **Text Normalization** — Defeats obfuscation like `U R G E N T` or word-to-digit tricks
3. **Digital Arrest Module** — Specialized detector for India's most prevalent scam type (authority impersonation, arrest threats)
4. **Rule-Based Scoring** — Keyword matching with whitelist for legitimate senders (OTPs, Amazon, banks)
5. **ML Classifier** — TF-IDF + LinearSVC trained on 100 labeled samples (50 scam, 50 legitimate)
6. **LLM Fallback** — "Vibe check" for ambiguous messages (pig butchering, multi-language scams) using Cerebras/Groq

### How We Extract Intelligence

All extraction is **regex-based** (no LLM hallucination risk):

- **Phone numbers** — Indian formats: `+91-XXXXXXXXXX`, 10-digit, spaced digits
- **UPI IDs** — Standard (`user@paytm`) and obfuscated (`user at paytm dot com`)
- **Bank accounts** — 9-18 digit account numbers
- **Phishing links** — URLs including shortened links (`bit.ly`, `tinyurl`)
- **Suspicious keywords** — urgency markers, financial terms, threat language

### How We Maintain Engagement

The persona agent uses a **context-aware strategy** that adapts based on extracted intelligence:

| Intelligence State | Strategy | Goal |
|---|---|---|
| **0 items extracted** | Play dumb, act confused | Force scammer to repeat details |
| **1 item extracted** | Targeted probing | Extract the next category |
| **2+ items extracted** | Verify and confirm | Validate accuracy, then close |

Four distinct personas (Meena, Rohan, Ramesh, Mrs. Sharma) are assigned per session, each with unique personality traits and engagement styles. All responses pass through an **anti-hallucination filter** that catches any sensitive data the LLM might invent.

---

## Architecture

```
                          +-------------------+
                          |   FastAPI Server   |
                          | (Concurrency Mgr)  |
                          +---------+---------+
                                    |
                          +---------v---------+
                          |   LangGraph        |
                          |   Workflow Engine   |
                          +---------+---------+
                                    |
              +---------------------+---------------------+
              |                     |                     |
    +---------v-------+   +---------v-------+   +---------v-------+
    | Detection Agent |   |  Persona Agent  |   | Extraction Agent|
    | (Rules+ML+LLM)  |   | (LLM + Context) |   |  (Regex-based)  |
    +-----------------+   +-----------------+   +-----------------+
              |                     |                     |
              +---------------------+---------------------+
                                    |
                          +---------v---------+
                          |  Session Manager   |
                          |  (SQLite + WAL)    |
                          +-------------------+
                                    |
                          +---------v---------+
                          |  GUVI Callback     |
                          |  (Final Report)    |
                          +-------------------+
```

**Workflow graph:** `START` -> `load_session` -> `detection` -> `persona` -> `extraction` -> `save_session` -> `END`

Conditional routing after detection decides whether to engage (scam detected) or politely exit (legitimate message). A "paranoid engagement" mode keeps conversations going for at least 3 turns even for initially-safe messages, catching slow-boil scams that start with casual greetings.

---

## Project Structure

```
HoneyPot-Scam-Detection/
|
+-- README.md                         # Setup and usage instructions
+-- requirements.txt                  # Python dependencies
+-- .env.example                      # Environment variables template
+-- run.py                            # Local server startup script
+-- render.yaml                       # Render.com deployment config
+-- LICENSE                           # MIT License
|
+-- src/                              # Source code
|   +-- main.py                       # Main API implementation (FastAPI)
|   +-- config.py                     # Environment variable management
|   +-- models.py                     # Pydantic request/response schemas
|   +-- database.py                   # SQLite session manager (WAL mode)
|   |
|   +-- agents/                       # Honeypot agent modules
|   |   +-- detection.py              # Cascading scam detection (Rules -> ML -> LLM)
|   |   +-- persona.py                # Context-aware persona generation
|   |   +-- extraction.py             # Intelligence extraction (regex-based)
|   |   +-- hallucination_filter.py   # Anti-hallucination safety layer
|   |   +-- timeline.py               # Conversation summarization
|   |   +-- digital_arrest.py         # Digital arrest scam specialization
|   |
|   +-- workflow/                     # LangGraph orchestration
|   |   +-- graph.py                  # Workflow graph definition & execution
|   |
|   +-- utils/                        # Utilities
|       +-- logger.py                 # Structured logging (console + file)
|       +-- callbacks.py              # GUVI callback & dynamic termination
|
+-- tests/                            # Test suite
|   +-- test_detection.py             # Detection accuracy tests
|   +-- test_strict_language.py       # Language consistency tests
|   +-- stress_limit_finder.py        # Concurrency stress testing
|   +-- test_scam.json                # Scam message samples
|   +-- test_legit.json               # Legitimate message samples
|
+-- evaluation/                       # Evaluation toolkit
|   +-- README.md                     # Evaluation documentation
|   +-- dataset/reddit_scams.json     # Reddit-sourced scam dataset
|   +-- scripts/run_evaluation.py     # Batch evaluation runner
|   +-- scripts/expand_prompts.py     # Prompt variation generator
|
+-- docs/                             # Additional documentation
    +-- architecture.md               # System architecture & design
```

---

## Testing

### Run Detection Accuracy Tests

```bash
python tests/test_detection.py
```

### Run Language Consistency Tests

```bash
python tests/test_strict_language.py
```

### Interactive API Testing

Start the server and open the Swagger UI:

```
http://localhost:8002/docs
```

---

## Key Features

- **Hybrid Detection** — Rules + ML + LLM fallback in a cascading pipeline
- **Context-Aware Persona** — LLM-generated responses that adapt based on extracted intelligence
- **Real-Time Extraction** — Regex-based extraction of phone numbers, UPI IDs, bank accounts, and phishing links
- **Digital Arrest Prevention** — Specialized module for authority-impersonation scams
- **Anti-Hallucination Filter** — Catches fabricated sensitive data before it enters the conversation
- **Dynamic Termination** — Ends conversations based on intelligence quality, not arbitrary turn limits
- **Concurrency Safe** — Semaphore + session locks handle 50+ simultaneous sessions
- **Graceful Degradation** — Always returns a valid response, never a 500 error

---

## Team

Team Kaizen
---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
