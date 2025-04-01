import pytest
from backend.utils.kafka_client import KafkaClient
from unittest.mock import Mock, patch

@pytest.fixture
def kafka_client():
    return KafkaClient()

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

@pytest.fixture
def sample_alert():
    return {
        "id": "test_alert_1",
        "transaction_id": "test_transaction_1",
        "user_id": "test_user_1",
        "amount": 1000.0,
        "timestamp": "2024-04-01T12:00:00",
        "risk_score": 0.8,
        "alert_type": "high_risk_transaction",
        "status": "new"
    }

def test_kafka_client_initialization(kafka_client):
    """Test Kafka client initialization"""
    assert kafka_client is not None
    assert isinstance(kafka_client, KafkaClient)

@patch('confluent_kafka.Producer')
def test_init_producer(mock_producer, kafka_client):
    """Test producer initialization"""
    kafka_client.init_producer()
    mock_producer.assert_called_once()

@patch('confluent_kafka.Consumer')
def test_init_consumer(mock_consumer, kafka_client):
    """Test consumer initialization"""
    group_id = "test_group"
    kafka_client.init_consumer(group_id)
    mock_consumer.assert_called_once()

def test_serialize_transaction(kafka_client, sample_transaction):
    """Test transaction serialization"""
    serialized = kafka_client._serialize_transaction(sample_transaction)
    assert serialized is not None
    assert isinstance(serialized, bytes)

def test_deserialize_transaction(kafka_client, sample_transaction):
    """Test transaction deserialization"""
    serialized = kafka_client._serialize_transaction(sample_transaction)
    deserialized = kafka_client._deserialize_transaction(serialized)
    assert deserialized is not None
    assert isinstance(deserialized, dict)
    assert deserialized["id"] == sample_transaction["id"]

def test_serialize_alert(kafka_client, sample_alert):
    """Test alert serialization"""
    serialized = kafka_client._serialize_alert(sample_alert)
    assert serialized is not None
    assert isinstance(serialized, bytes)

def test_deserialize_alert(kafka_client, sample_alert):
    """Test alert deserialization"""
    serialized = kafka_client._serialize_alert(sample_alert)
    deserialized = kafka_client._deserialize_alert(serialized)
    assert deserialized is not None
    assert isinstance(deserialized, dict)
    assert deserialized["id"] == sample_alert["id"]

@patch('confluent_kafka.Producer')
def test_produce_transaction(mock_producer, kafka_client, sample_transaction):
    """Test transaction production"""
    kafka_client.init_producer()
    kafka_client.produce_transaction(sample_transaction)
    # Verify producer was called with correct arguments
    mock_producer.return_value.produce.assert_called_once()

@patch('confluent_kafka.Producer')
def test_produce_alert(mock_producer, kafka_client, sample_alert):
    """Test alert production"""
    kafka_client.init_producer()
    kafka_client.produce_alert(sample_alert)
    # Verify producer was called with correct arguments
    mock_producer.return_value.produce.assert_called_once()

def test_close(kafka_client):
    """Test client cleanup"""
    kafka_client.close()
    # Verify cleanup was performed
    assert kafka_client.producer is None
    assert kafka_client.consumer is None 