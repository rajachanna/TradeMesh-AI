from decimal import Decimal
from fastapi.testclient import TestClient
import pytest
import trademesh.api as module


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("TM_API_KEY", "long-test-api-key-123456789")
    monkeypatch.setenv("TM_WEBHOOK_SECRET", "long-test-hook-secret-12345")
    monkeypatch.setattr(module, "DATABASE", tmp_path / "paper.sqlite")
    return TestClient(module.app)


def signal(**changes):
    data = {
        "secret": "long-test-hook-secret-12345", "id": "trade-001",
        "symbol": "BTCUSDT", "side": "buy", "quantity": "0.01", "price": "65000"
    }
    data.update(changes)
    return data


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["mode"] == "PAPER_ONLY"


def test_authentication(client):
    assert client.get("/portfolio").status_code == 401
    assert client.get("/portfolio", headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.get("/portfolio", headers={"X-API-Key": "long-test-api-key-123456789"}).status_code == 200


def test_buy_deduplication_and_sell(client):
    response = client.post("/webhook", json=signal())
    assert response.status_code == 200
    assert response.json()["status"] == "paper_filled"
    assert client.post("/webhook", json=signal()).json()["status"] == "duplicate"
    response = client.post("/webhook", json=signal(id="trade-002", side="sell", price="66000"))
    assert response.status_code == 200
    portfolio = client.get("/portfolio", headers={"X-API-Key": "long-test-api-key-123456789"}).json()
    assert Decimal(portfolio["cash_usd"]) == Decimal("10010")
    assert portfolio["positions"] == []
    assert len(portfolio["orders"]) == 2


@pytest.mark.parametrize("change,code", [
    ({"secret": "wrong"}, 401),
    ({"symbol": "XAUUSD"}, 422),
    ({"quantity": "1"}, 422),
    ({"price": "-3"}, 422),
    ({"side": "hold"}, 422),
])
def test_invalid_alerts_rejected(client, change, code):
    response = client.post("/webhook", json=signal(**change))
    assert response.status_code == code


def test_prevent_naked_short(client):
    response = client.post("/webhook", json=signal(side="sell"))
    assert response.status_code == 422
    assert client.get("/portfolio", headers={"X-API-Key": "long-test-api-key-123456789"}).json()["orders"] == []


def test_cash_and_exposure_limit(client):
    first = client.post("/webhook", json=signal(quantity="0.03", price="65000"))
    assert first.status_code == 200
    over_limit = client.post("/webhook", json=signal(id="trade-002", quantity="0.02", price="65000"))
    assert over_limit.status_code == 422
    portfolio = client.get("/portfolio", headers={"X-API-Key": "long-test-api-key-123456789"}).json()
    assert len(portfolio["orders"]) == 1
