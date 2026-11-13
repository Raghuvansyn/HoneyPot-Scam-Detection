# Architecture and tradeoffs

ScamBait is a FastAPI application backed by a six-node LangGraph state machine and SQLite. See [the README](../README.md) for installation, a synthetic example, and offline verification.

## Actual request flow

1. `src/main.py` validates `HoneypotRequest`, checks a configured shared API key, acquires the process semaphore and a lock for the session. Lock entries count queued users and are removed only when no request still uses them.
2. `load_session_node` in `src/workflow/graph.py` loads SQLite JSON state, appends the new incoming message, and advances the combined message count. Client-supplied history is not imported.
3. A previously flagged scam bypasses detection. Otherwise `detect_scam` checks prompt-manipulation patterns, spaced-letter normalization, digital-arrest patterns, rule scores, the lazily trained TF-IDF/LinearSVC model, then the LLM when inconclusive. Provider JSON verdicts and score ranges are validated. Failure is an error, not a safe classification.
4. A scam gets a persona reply. An untrusted, initially safe result can also receive a probing reply while the combined message count is at most three. Other safe messages get a fixed polite response. Trusted templates only bypass the rule stage when no explicit dangerous-action verb is present; message text is not sender authentication.
5. Persona generation sends the last eight messages and a strategy prompt to one configured provider. A generation failure can return scripted text. A limited regex filter removes sensitive-looking output. Extraction then reads only incoming messages labelled `scammer`; generated replies are never evidence.
6. `save_session_node` checks the combined count and extracted categories, optionally performs a callback/dry run, and persists JSON. The API builds a validated response. Workflow exceptions return 503; the 35-second workflow deadline returns 504. Semaphore/lock queue time is outside that deadline.

## Stopping conditions

These thresholds count **incoming messages plus replies**, not user turns:

| Condition | Close when count reaches |
|---|---:|
| Any session |20|
| Not marked scam |10|
| At least 4 contact/payment categories |10|
| At least 3 categories |12|
| At least 2 categories |15|
| At least 1 category |18|

Counts below 8 continue. With zero categories, a scam continues to the hard 20-message limit. Suspicious keywords do not count as contact/payment categories. A successful callback marks `callbackSent`; a dev dry run also returns success. A failed production callback still closes the session. Reusing a closed session can append more messages; there is no immutable closed-session API or retry queue yet.

## Important files

| Path | Responsibility |
|---|---|
| `src/models.py` | Request/response/state shapes and bounded identifiers/input |
| `src/config.py` | Environment and provider configuration |
| `src/main.py` | API, auth, timeout, concurrency controls, error responses |
| `src/workflow/graph.py` | Nodes, conditional routing, persistence and response construction |
| `src/database.py` | WAL SQLite JSON store; thread-local connections keyed by database path |
| `src/agents/detection.py` | Rules, 115 embedded training strings, TF-IDF/SVM, validated LLM fallback |
| `src/agents/persona.py` | Prompt strategy, provider selection, language heuristics, scripted fallback |
| `src/agents/extraction.py` | Regex candidate extraction and text normalization |
| `src/agents/hallucination_filter.py` | Limited sensitive-pattern replacement |
| `src/agents/timeline.py` | Heuristic narrative summary and confidence aggregation |
| `src/utils/callbacks.py` | Actual stopping rules, GUVI callback, local digital-arrest log |
| `tests/offline/test_reliability.py` | No-network regression and full graph checks |

## Decisions and practical limits

The cascade avoids a provider call for obvious rules and confident SVM decisions. It is inspectable and cheap locally, but hand-built rules are brittle and SVM margins are not probabilities. Brand mentions never authenticate a sender. A labelled, independently reviewed evaluation set is needed before optimizing thresholds.

LangGraph makes state and branching visible, at the cost of framework dependencies for a small graph. SQLite makes local replay straightforward. Its synchronous operations can block the event loop; process-local locks do not coordinate multiple workers. A timeout does not guarantee a thread's SQLite operation has stopped. No throughput measurement supports a scalability claim.

Regex extraction is reproducible and avoids model-generated entities, but patterns still misidentify text. Extraction is limited to messages with the expected incoming sender label. It does not verify ownership or validity of an extracted identifier. The output filter can also remove legitimate repeated data and miss unsupported formats.

The historical GUVI endpoint is a hackathon result receiver. It is not a verified police/reporting service. Digital-arrest alert functions only append local log records. Logs and database state have no retention or access-control policy; keep demonstrations synthetic.

Provider fallback currently means client selection at initialization. Runtime inference failures do not switch from Cerebras to Groq. Persona failures can yield scripted text, whereas failed ambiguous detection yields an API error. Explicit provider/fallback metadata, bounded retry policies, callback delivery records, and a broader model evaluation are future work.
