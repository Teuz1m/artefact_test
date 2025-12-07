import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


class TestAPI:
    def test_health_endpoint(self):
        response = client.get("/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data

    def test_query_endpoint_structure(self, mock_agent):
        response = client.post(
            "/v1/query",
            json={"query": "Qual a capital do Brasil?"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "response" in data
        assert isinstance(data["success"], bool)
        assert isinstance(data["response"], str)
        assert data["response"] == "Brasília é a capital do Brasil."

    def test_query_empty_request(self):
        response = client.post(
            "/v1/query",
            json={}
        )
        assert response.status_code == 422

    def test_query_invalid_json(self):
        response = client.post(
            "/v1/query",
            data="invalid json"
        )
        assert response.status_code == 422

    def test_query_empty_string(self):
        response = client.post(
            "/v1/query",
            json={"query": ""}
        )
        assert response.status_code == 200
