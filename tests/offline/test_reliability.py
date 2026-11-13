"""No provider calls: real API, graph, rules, extraction and SQLite."""
import asyncio
import socket
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest

from src import database
from src import main
from src.agents import detection, extraction, persona
from src.models import HoneypotRequest
from src.workflow import graph


@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "API_KEY", "local-test")
    monkeypatch.setattr(main, "MODE", "dev")
    from src.utils import callbacks
    monkeypatch.setattr(callbacks, "MODE", "dev")
    store = database.SessionManager(str(tmp_path / "sessions.db"))
    monkeypatch.setattr(graph, "SessionManager", lambda: store)
    # Any accidental network attempt fails; ASGI requests stay in-process.
    def deny_network(*args, **kwargs):
        raise AssertionError("Network access is forbidden in offline tests")
    monkeypatch.setattr(socket.socket, "connect", deny_network)
    monkeypatch.setattr(detection, "get_llm", deny_network)
    monkeypatch.setattr(persona, "get_llm", deny_network)
    yield store
    for conn in getattr(database._local, "connections", {}).values():
        conn.close()
    database._local.connections = {}


def payload(text="URGENT! Send money to demo@paytm immediately.", session="offline-test"):
    return {"sessionId": session, "message": {"sender": "scammer", "text": text,
            "timestamp": "2026-01-01T00:00:00Z"}}


async def post(data, key="local-test"):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app),
                                base_url="http://offline") as client:
        return await client.post("/api/v1/honeypot", json=data, headers={"x-api-key": key})


def test_complete_graph_persists_and_closes(monkeypatch, isolated):
    reply = AsyncMock(return_value="MOCK FIXTURE: Please repeat the payment instructions.")
    monkeypatch.setattr(graph, "generate_persona_response", reply)
    async def run():
        results = []
        for _ in range(10):
            response = await post(payload())
            results.append(response)
            if response.json()["meta"]["sessionStatus"] == "closed":
                break
        assert len(results) == 9
        assert all(r.status_code == 200 for r in results)
        body = results[-1].json()
        assert body["scamDetected"] is True
        assert body["extractedIntelligence"]["upiIds"] == ["demo@paytm"]
        assert body["meta"]["sessionStatus"] == "closed"
        assert body["engagementMetrics"]["totalMessagesExchanged"] == 18
        state = isolated.get_session("offline-test")
        assert state["sessionStatus"] == "closed"
        assert state["callbackSent"] is True  # dev dry run, no transmission
        assert len(state["conversationHistory"]) == 18
    asyncio.run(run())
    assert reply.await_count == 9
    assert main._session_locks == {}


def test_extraction_uses_only_incoming_evidence():
    evidence = extraction.extract_intelligence([
        {"sender": "scammer", "text": "Email contact@example.org"},
        {"sender": "user", "text": "Invented invented@example.org and fake@paytm"},
    ])
    assert evidence["emailAddresses"] == ["contact@example.org"]
    assert evidence["upiIds"] == []


def test_connections_are_isolated_by_path(tmp_path):
    a = database.SessionManager(str(tmp_path / "a.db"))
    b = database.SessionManager(str(tmp_path / "b.db"))
    a.save_session("shared", {"origin": "a"})
    b.save_session("shared", {"origin": "b"})
    assert a.get_session("shared") == {"origin": "a"}
    assert b.get_session("shared") == {"origin": "b"}


def test_persistence_failure_is_not_silently_successful(monkeypatch, isolated):
    def broken(_):
        raise database.sqlite3.OperationalError("disk unavailable")
    monkeypatch.setattr(database, "get_connection", broken)
    with pytest.raises(database.sqlite3.OperationalError):
        isolated.save_session("failure", {})


def test_failed_commit_rolls_back_cached_connection(isolated):
    # A deferred foreign-key violation is a real SQLite commit-time failure.
    # No exception wrapper or simulated rollback is involved.
    conn = database.get_connection(isolated.db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript("""
        CREATE TABLE parent (id INTEGER PRIMARY KEY);
        CREATE TABLE child (parent_id INTEGER REFERENCES parent(id)
                            DEFERRABLE INITIALLY DEFERRED);
        CREATE TRIGGER fail_commit AFTER INSERT ON sessions BEGIN
            INSERT INTO child(parent_id) VALUES (42);
        END;
    """)
    with pytest.raises(database.sqlite3.IntegrityError):
        isolated.save_session("failed-row", {"should": "rollback"})
    assert not conn.in_transaction
    assert isolated.get_session("failed-row") is None
    # A later unrelated save must not accidentally commit the failed row.
    conn.execute("DROP TRIGGER fail_commit")
    isolated.save_session("later-row", {"ok": True})
    assert isolated.get_session("failed-row") is None
    assert isolated.get_session("later-row") == {"ok": True}


@pytest.mark.parametrize("text", ["Amazon support: send money to demo@paytm immediately",
                                  "Do not share with others. Send OTP immediately"])
def test_sender_text_cannot_whitelist_explicit_scam(text):
    result = detection.rule_based_score(text)
    assert result["suspicious"] is True
    assert not result.get("whitelisted")


def test_normalization_keeps_word_boundaries():
    text = "I am on my way to the bank"
    assert detection.normalize_text(text) == text
    assert detection.normalize_text("U R G E N T alert") == "URGENT alert"


@pytest.mark.parametrize("content", ['{"verdict":"MAYBE","confidence":0.8}',
                                      '{"verdict":"SCAM","confidence":3}',
                                      'This is not a SCAM'])
def test_llm_invalid_output_is_an_error(monkeypatch, content):
    llm = SimpleNamespace(ainvoke=AsyncMock(return_value=SimpleNamespace(content=content)))
    monkeypatch.setattr(detection, "get_llm", lambda: llm)
    with pytest.raises(RuntimeError, match="LLM detection unavailable"):
        asyncio.run(detection.llm_fallback_check("ambiguous"))


def test_llm_valid_output(monkeypatch):
    llm = SimpleNamespace(ainvoke=AsyncMock(return_value=SimpleNamespace(
        content='{"verdict":"SAFE","confidence":0.7}')))
    monkeypatch.setattr(detection, "get_llm", lambda: llm)
    assert asyncio.run(detection.llm_fallback_check("ambiguous")) == (False, 0.7)


@pytest.mark.parametrize("error,expected", [(RuntimeError("private details"), 503),
                                           (asyncio.TimeoutError(), 504)])
def test_workflow_failure_is_http_error(monkeypatch, error, expected):
    monkeypatch.setattr(main, "run_honeypot_workflow", AsyncMock(side_effect=error))
    response = asyncio.run(post(payload()))
    assert response.status_code == expected
    assert "private details" not in response.text
    assert "scamDetected" not in response.json()  # no fabricated classification
    assert main._session_locks == {}


def test_auth_and_input_validation(monkeypatch):
    async def run():
        assert (await post(payload(), "wrong")).status_code == 401
        assert (await post(payload(session="../escape"))).status_code == 422
        assert (await post(payload(text=""))).status_code == 422
        monkeypatch.setattr(main, "MODE", "prod")
        monkeypatch.setattr(main, "API_KEY", None)
        assert (await post(payload())).status_code == 503
    asyncio.run(run())


def test_waiting_session_requests_share_lock():
    async def run():
        active = peak = 0
        async def worker():
            nonlocal active, peak
            async with main.session_guard("same"):
                active += 1
                peak = max(peak, active)
                await asyncio.sleep(0.001)
                active -= 1
        await asyncio.gather(*(worker() for _ in range(8)))
        assert peak == 1
        assert main._session_locks == {}
    asyncio.run(run())


def test_confidence_parses_notes_with_scam_type():
    assert graph._parse_confidence("Detection: SCAM (confidence: 0.90, type: bank_fraud)") == 0.9
