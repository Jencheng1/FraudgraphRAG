from confluent_kafka import Producer, Consumer, KafkaError
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer, AvroDeserializer
from confluent_kafka.serialization import StringSerializer, StringDeserializer
import json
from typing import Dict, Any, Optional, Callable
from ..core.config import settings
import avro.schema
import io

class KafkaClient:
    def __init__(self):
        self.producer = None
        self.consumer = None
        self.schema_registry_client = None
        self.transaction_serializer = None
        self.alert_serializer = None
        self.transaction_deserializer = None
        self.alert_deserializer = None

    def init_producer(self):
        """Initialize Kafka producer"""
        if not self.producer:
            conf = {
                'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
                'security.protocol': 'SASL_SSL',
                'sasl.mechanism': 'PLAIN',
                'sasl.username': settings.KAFKA_API_KEY,
                'sasl.password': settings.KAFKA_API_SECRET,
                'client.id': 'fraud_detection_producer'
            }
            self.producer = Producer(conf)
            self._init_serializers()

    def init_consumer(self, group_id: str = 'fraud_detection_group'):
        """Initialize Kafka consumer"""
        if not self.consumer:
            conf = {
                'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
                'security.protocol': 'SASL_SSL',
                'sasl.mechanism': 'PLAIN',
                'sasl.username': settings.KAFKA_API_KEY,
                'sasl.password': settings.KAFKA_API_SECRET,
                'group.id': group_id,
                'auto.offset.reset': 'earliest',
                'enable.auto.commit': True
            }
            self.consumer = Consumer(conf)
            self._init_serializers()

    def _init_serializers(self):
        """Initialize Avro serializers and deserializers"""
        if not self.schema_registry_client:
            schema_registry_conf = {
                'url': settings.KAFKA_SCHEMA_REGISTRY_URL,
                'basic.auth.user.info': f"{settings.KAFKA_SCHEMA_REGISTRY_API_KEY}:{settings.KAFKA_SCHEMA_REGISTRY_API_SECRET}"
            }
            self.schema_registry_client = SchemaRegistryClient(schema_registry_conf)

        # Transaction schema
        transaction_schema = avro.schema.parse('''
        {
            "type": "record",
            "name": "Transaction",
            "namespace": "com.fraud_detection",
            "fields": [
                {"name": "id", "type": "string"},
                {"name": "amount", "type": "double"},
                {"name": "timestamp", "type": "string"},
                {"name": "user_id", "type": "string"},
                {"name": "features", "type": {"type": "array", "items": "double"}},
                {"name": "fraud_probability", "type": "double"},
                {"name": "label", "type": "int"}
            ]
        }
        ''')

        # Alert schema
        alert_schema = avro.schema.parse('''
        {
            "type": "record",
            "name": "Alert",
            "namespace": "com.fraud_detection",
            "fields": [
                {"name": "transaction_id", "type": "string"},
                {"name": "fraud_probability", "type": "double"},
                {"name": "is_fraudulent", "type": "boolean"},
                {"name": "timestamp", "type": "string"},
                {"name": "context", "type": "string"}
            ]
        }
        ''')

        # Initialize serializers
        self.transaction_serializer = AvroSerializer(
            schema_registry_client=self.schema_registry_client,
            schema_str=str(transaction_schema),
            to_dict=lambda x: x
        )

        self.alert_serializer = AvroSerializer(
            schema_registry_client=self.schema_registry_client,
            schema_str=str(alert_schema),
            to_dict=lambda x: x
        )

        # Initialize deserializers
        self.transaction_deserializer = AvroDeserializer(
            schema_registry_client=self.schema_registry_client,
            schema_str=str(transaction_schema)
        )

        self.alert_deserializer = AvroDeserializer(
            schema_registry_client=self.schema_registry_client,
            schema_str=str(alert_schema)
        )

    def produce_transaction(self, transaction: Dict[str, Any]):
        """Produce a transaction message to Kafka"""
        if not self.producer:
            self.init_producer()

        try:
            # Serialize the transaction
            serialized_value = self.transaction_serializer(
                transaction,
                {'schema': 'com.fraud_detection.Transaction'}
            )

            # Produce the message
            self.producer.produce(
                topic=settings.KAFKA_TRANSACTIONS_TOPIC,
                key=str(transaction['id']),
                value=serialized_value
            )
            self.producer.poll(1)
            self.producer.flush()

        except Exception as e:
            print(f"Error producing transaction: {str(e)}")
            raise

    def produce_alert(self, alert: Dict[str, Any]):
        """Produce a fraud alert message to Kafka"""
        if not self.producer:
            self.init_producer()

        try:
            # Serialize the alert
            serialized_value = self.alert_serializer(
                alert,
                {'schema': 'com.fraud_detection.Alert'}
            )

            # Produce the message
            self.producer.produce(
                topic=settings.KAFKA_ALERTS_TOPIC,
                key=str(alert['transaction_id']),
                value=serialized_value
            )
            self.producer.poll(1)
            self.producer.flush()

        except Exception as e:
            print(f"Error producing alert: {str(e)}")
            raise

    def consume_transactions(self, callback: Callable[[Dict[str, Any]], None]):
        """Consume transaction messages from Kafka"""
        if not self.consumer:
            self.init_consumer()

        try:
            self.consumer.subscribe([settings.KAFKA_TRANSACTIONS_TOPIC])

            while True:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        print(f"Consumer error: {msg.error()}")
                        break

                try:
                    # Deserialize the message
                    transaction = self.transaction_deserializer(
                        msg.value(),
                        {'schema': 'com.fraud_detection.Transaction'}
                    )
                    callback(transaction)

                except Exception as e:
                    print(f"Error processing message: {str(e)}")
                    continue

        except Exception as e:
            print(f"Error in consumer: {str(e)}")
            raise

    def consume_alerts(self, callback: Callable[[Dict[str, Any]], None]):
        """Consume alert messages from Kafka"""
        if not self.consumer:
            self.init_consumer()

        try:
            self.consumer.subscribe([settings.KAFKA_ALERTS_TOPIC])

            while True:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        print(f"Consumer error: {msg.error()}")
                        break

                try:
                    # Deserialize the message
                    alert = self.alert_deserializer(
                        msg.value(),
                        {'schema': 'com.fraud_detection.Alert'}
                    )
                    callback(alert)

                except Exception as e:
                    print(f"Error processing message: {str(e)}")
                    continue

        except Exception as e:
            print(f"Error in consumer: {str(e)}")
            raise

    def close(self):
        """Close Kafka connections"""
        if self.producer:
            self.producer.flush()
            self.producer.close()
        if self.consumer:
            self.consumer.close() 