import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
import json

client = TestClient(app)

@pytest.fixture
def sample_transaction():
    return {
        "id": "test_transaction_1",
        "user_id": "test_user_1",
        "amount": 1000.0,
        "timestamp": "2024-04-01T12:00:00",
        "features": [1000.0, 0.5, 0.3, 0.1, 0.2, 0.4],
        "fraud_probability": 0.8,
        "label": 1
    }

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_detect_fraud(sample_transaction):
    """Test fraud detection endpoint"""
    response = client.post("/detect-fraud", json=sample_transaction)
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert "is_fraudulent" in data
    assert "explanation" in data

def test_get_alerts():
    """Test get alerts endpoint"""
    response = client.get("/alerts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_user_profile():
    """Test get user profile endpoint"""
    user_id = "test_user_1"
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "risk_score" in data
    assert "transaction_history" in data

def test_get_transaction_history():
    """Test get transaction history endpoint"""
    user_id = "test_user_1"
    response = client.get(f"/users/{user_id}/transactions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_update_alert_status():
    """Test update alert status endpoint"""
    alert_id = "test_alert_1"
    status = "resolved"
    response = client.put(f"/alerts/{alert_id}/status", json={"status": status})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == status 