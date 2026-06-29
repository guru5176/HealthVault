"""API integration tests for Health Wallet."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Health check endpoint tests."""

    def test_health_check(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "components" in data

    def test_health_metrics(self):
        resp = client.get("/api/health/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_requests" in data
        assert "latency" in data

    def test_health_models(self):
        resp = client.get("/api/health/models")
        assert resp.status_code == 200
        data = resp.json()
        assert "current_model" in data


class TestVaultEndpoints:
    """Health Wallet API tests."""

    def test_list_records(self):
        resp = client.get("/api/vault/records")
        assert resp.status_code == 200
        data = resp.json()
        assert "records" in data
        assert "count" in data
        assert data["count"] > 0

    def test_get_record(self):
        # First get list
        records = client.get("/api/vault/records").json()["records"]
        if records:
            record_id = records[0]["id"]
            resp = client.get(f"/api/vault/records/{record_id}")
            assert resp.status_code == 200
            assert "content" in resp.json()

    def test_get_nonexistent_record(self):
        resp = client.get("/api/vault/records/nonexistent_xyz")
        assert resp.status_code == 404

    def test_search_records(self):
        resp = client.get("/api/vault/search?q=medication")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data

    def test_search_short_query(self):
        resp = client.get("/api/vault/search?q=a")
        assert resp.status_code == 400

    def test_create_record(self):
        resp = client.post("/api/vault/records", json={
            "title": "Test Record",
            "content": "This is a test health record.",
            "category": "general",
        })
        assert resp.status_code == 200
        assert resp.json()["record"]["title"] == "Test Record"


class TestCareRouterEndpoints:
    """Care Router API tests."""

    def test_drug_check(self):
        resp = client.post("/api/care/drug-check", json={
            "medications": ["escitalopram", "ibuprofen"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "interactions" in data
        assert len(data["interactions"]) > 0

    def test_drug_check_no_interactions(self):
        resp = client.post("/api/care/drug-check", json={
            "medications": ["loratadine", "vitamin_d"],
        })
        assert resp.status_code == 200
        assert resp.json()["interaction_count"] == 0

    def test_drug_check_insufficient_meds(self):
        resp = client.post("/api/care/drug-check", json={
            "medications": ["aspirin"],
        })
        assert resp.status_code == 400


class TestChatEndpoints:
    """Chat API tests."""

    def test_chat_empty_message(self):
        resp = client.post("/api/chat", json={
            "message": "",
            "stream": False,
        })
        assert resp.status_code == 400

    def test_chat_history(self):
        resp = client.get("/api/chat/history")
        assert resp.status_code == 200
        assert "history" in resp.json()

    def test_chat_clear(self):
        resp = client.post("/api/chat/clear")
        assert resp.status_code == 200


class TestFrontend:
    """Frontend serving tests."""

    def test_serve_root(self):
        resp = client.get("/")
        assert resp.status_code == 200
