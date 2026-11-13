"""Exercise the real API/graph/store with an explicitly mocked persona provider."""
import asyncio
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Set before importing application configuration.
os.environ["MODE"] = "dev"
os.environ["API_KEY"] = "offline-demo-only"

import httpx
from src.database import SessionManager
from src.main import app
from src.workflow import graph


async def run():
    with tempfile.TemporaryDirectory() as directory:
        store = SessionManager(str(Path(directory) / "demo.db"))
        persona = AsyncMock(return_value="MOCK FIXTURE: Please repeat the payment instructions.")
        with patch.object(graph, "SessionManager", return_value=store), \
             patch.object(graph, "generate_persona_response", persona), \
             patch("src.agents.detection.get_llm", side_effect=AssertionError("Unexpected provider call")):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://offline") as client:
                for turn in range(10):
                    response = await client.post("/api/v1/honeypot", headers={"x-api-key": "offline-demo-only"}, json={
                        "sessionId": "offline-demo",
                        "message": {"sender": "scammer", "text": "URGENT! Send money to demo@paytm immediately.",
                                    "timestamp": "2026-01-01T00:00:00Z"},
                    })
                    response.raise_for_status()
                    result = response.json()
                    if result["meta"]["sessionStatus"] == "closed":
                        break
        assert result["meta"]["sessionStatus"] == "closed"
        assert result["scamDetected"] is True
        assert store.get_session("offline-demo")["totalMessages"] == 18
        print(json.dumps({"mode": "offline provider fixture; callback dry run", "requests": turn + 1,
                          "response": result}, indent=2))


if __name__ == "__main__":
    asyncio.run(run())
