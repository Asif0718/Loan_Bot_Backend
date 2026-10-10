import os
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from bson import ObjectId

# Set environment variables before importing app
os.environ["RETELL_API_KEY"] = "test_key"
os.environ["RETELL_AGENT_ID"] = "test_agent_id"
os.environ["VERIFY_RETELL_WEBHOOKS"] = "false"

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class FakeCursor:
    def __init__(self, documents):
        self.documents = list(documents)

    def sort(self, field, direction):
        self.documents.sort(key=lambda item: item.get(field, 0), reverse=direction < 0)
        return self

    def skip(self, count):
        self.documents = self.documents[count:]
        return self

    def limit(self, count):
        self.documents = self.documents[:count]
        return self

    async def to_list(self, length):
        return [document.copy() for document in self.documents[:length]]


def matches(document, filters):
    for key, expected in filters.items():
        value = document
        for part in key.split("."):
            value = value.get(part) if isinstance(value, dict) else None
        if value != expected:
            return False
    return True


class FakeCollection:
    def __init__(self):
        self.documents = []

    async def insert_one(self, document):
        stored = document.copy() | {"_id": ObjectId()}
        self.documents.append(stored)
        return SimpleNamespace(inserted_id=stored["_id"])

    async def find_one(self, filters):
        return next((item.copy() for item in self.documents if matches(item, filters)), None)

    def find(self, filters=None):
        return FakeCursor(item for item in self.documents if matches(item, filters or {}))

    async def count_documents(self, filters):
        return sum(matches(item, filters) for item in self.documents)

    async def update_one(self, filters, update, upsert=False):
        document = next((item for item in self.documents if matches(item, filters)), None)
        if document is None and upsert:
            document = filters.copy() | {"_id": ObjectId()}
            document.update(update.get("$setOnInsert", {}))
            self.documents.append(document)
        if document is not None:
            document.update(update.get("$set", {}))
        return SimpleNamespace()


@pytest.fixture(autouse=True)
def fake_database(monkeypatch):
    database = {"calls": FakeCollection(), "profiles": FakeCollection()}
    get_database = AsyncMock(return_value=database)
    monkeypatch.setattr("app.routes.calls.get_database", get_database)
    monkeypatch.setattr("app.routes.profiles.get_database", get_database)
    monkeypatch.setattr("app.routes.webhooks.get_database", get_database)
    return database


def create_profile():
    response = client.post(
        "/api/profiles",
        json={"customer_name": "Rahul Sharma", "language_to_speak": "English"},
    )
    assert response.status_code == 201
    return response.json()["id"]


class TestHealth:
    def test_health_endpoint(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_health_endpoint_accepts_head(self):
        resp = client.head("/health")
        assert resp.status_code == 200


class TestCallStart:
    def test_start_call_missing_fields(self):
        """POST /api/calls/start should validate required fields."""
        resp = client.post("/api/calls/start", json={})
        assert resp.status_code == 422

    def test_start_call_partial_fields(self):
        """POST /api/calls/start should validate all required fields."""
        resp = client.post(
            "/api/calls/start",
            json={"customer_name": "Rahul Sharma"}
        )
        assert resp.status_code == 422

    def test_start_call_valid(self):
        """POST /api/calls/start should return call_id and access_token."""
        profile_id = create_profile()
        with patch(
            "app.routes.calls.create_web_call",
            return_value={
                "call_id": "call-1",
                "access_token": "token-1",
                "transport": "gateway",
                "ice_servers": [{"urls": "stun:example.com"}],
            },
        ):
            resp = client.post(
                "/api/calls/start",
                json={"profile_id": profile_id, "agent_name": "Ananya"},
            )
        assert resp.status_code == 200
        assert resp.json() == {
            "call_id": "call-1",
            "access_token": "token-1",
            "transport": "gateway",
            "ice_servers": [{"urls": "stun:example.com"}],
        }

    def test_start_call_retell_failure(self):
        """Should handle unexpected Retell errors gracefully."""
        profile_id = create_profile()
        with patch("app.routes.calls.create_web_call", side_effect=RuntimeError("failed")):
            resp = client.post("/api/calls/start", json={"profile_id": profile_id})
        assert resp.status_code == 502
        assert "stack" not in resp.text.lower()

    def test_retell_call_receives_assignment_variables(self):
        """Every prompt variable required by the assignment is supplied."""
        from app.services.retell_service import create_web_call

        response = SimpleNamespace(
            call_id="call-variables",
            access_token="token",
            transport="gateway",
            ice_servers=None,
        )
        with patch(
            "app.services.retell_service.call_resource.create_web_call",
            return_value=response,
        ) as create:
            create_web_call(
                customer_name="Rahul Sharma",
                language_to_speak="English",
                agent_name="Ananya",
                profile_id="profile-1",
            )

        variables = create.call_args.kwargs["retell_llm_dynamic_variables"]
        assert {
            "company_name",
            "customer_name",
            "agent_name",
            "agent_gender",
            "current_date",
            "current_day",
            "current_time",
            "additional_context_from_rag",
            "language_to_speak",
            "conversation_history",
            "customer_utterance",
        } <= variables.keys()


def test_assignment_prompt_contains_critical_rules():
    prompt = (
        __import__("pathlib").Path(__file__).parents[1]
        / "app"
        / "prompts"
        / "lap_agent.txt"
    ).read_text(encoding="utf-8")

    for requirement in (
        "Agricultural property is an immediate disqualification",
        "Cash income is an immediate disqualification",
        "3 through 15 years inclusive",
        "first missing checklist item",
        "loan-transfer specialist",
        "Never call the customer qualified until all seven",
    ):
        assert requirement in prompt


class TestCallHistory:
    def test_get_calls_empty(self):
        """GET /api/calls should return empty list when no calls exist."""
        resp = client.get("/api/calls")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["limit"] == 20

    def test_get_calls_pagination(self):
        """GET /api/calls should support pagination."""
        resp = client.get("/api/calls?page=1&limit=10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["limit"] == 10

    def test_get_calls_outcome_filter(self):
        """GET /api/calls should support outcome filtering."""
        resp = client.get("/api/calls?outcome=qualified")
        assert resp.status_code == 200


class TestGetSingleCall:
    def test_get_nonexistent_call(self):
        """GET /api/calls/{retell_call_id} should return 404 for missing call."""
        resp = client.get("/api/calls/nonexistent-call-id")
        assert resp.status_code == 404

    def test_get_call_structure(self):
        """GET /api/calls/{retell_call_id} should return proper structure."""
        # This will be tested with MongoDB integration


class TestWebhooks:
    def test_call_started_event(self):
        """POST /webhooks/retell should handle call_started."""
        resp = client.post(
            "/webhooks/retell",
            json={"event": "call_started", "call": {"call_id": "test-call-123"}}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["event"] == "call_started"

    def test_call_ended_event(self):
        """POST /webhooks/retell should handle call_ended."""
        resp = client.post(
            "/webhooks/retell",
            json={"event": "call_ended", "call": {"call_id": "test-call-123"}}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["event"] == "call_ended"

    @patch("app.routes.webhooks.process_call_event", new_callable=AsyncMock)
    def test_call_analyzed_event(self, mock_process_call):
        """POST /webhooks/retell should handle call_analyzed."""
        resp = client.post(
            "/webhooks/retell",
            json={"event": "call_analyzed", "call": {"call_id": "test-call-123"}}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["event"] == "call_analyzed"
        mock_process_call.assert_awaited_once_with(
            "call_analyzed", {"call_id": "test-call-123"}
        )

    def test_unknown_event(self):
        """POST /webhooks/retell should acknowledge unknown events."""
        resp = client.post(
            "/webhooks/retell",
            json={"event": "unknown_event", "call": {"call_id": "test-call-123"}}
        )
        assert resp.status_code == 200


class TestIdempotency:
    def test_duplicate_webhook_upsert(self, fake_database):
        """Duplicate webhook should update existing document, not create duplicate."""
        call = {
            "call_id": "test-call-1",
            "agent_id": "test-agent",
            "call_status": "ended",
            "call_type": "web_call",
            "call_analysis": {},
        }
        from app.routes.webhooks import process_call_event

        asyncio.run(process_call_event("call_ended", call))
        asyncio.run(process_call_event("call_analyzed", call))

        assert len(fake_database["calls"].documents) == 1
        assert fake_database["calls"].documents[0]["last_event"] == "call_analyzed"


class TestProfiles:
    def test_create_and_get_profile(self):
        profile_id = create_profile()
        response = client.get(f"/api/profiles/{profile_id}")
        assert response.status_code == 200
        assert response.json()["customer_name"] == "Rahul Sharma"
