import time
from typing import Dict, Callable
from ...backend.utils.kafka_client import KafkaClient
from ...backend.core.config import settings

class TransactionProcessor:
    def __init__(self, kafka_client: KafkaClient):
        self.kafka_client = kafka_client
        self.running = False
        self.processed_count = 0
        self.fraud_count = 0

    def process_transaction(self, transaction: Dict) -> None:
        """Process a single transaction and generate alerts if necessary"""
        self.processed_count += 1
        
        # Check if transaction is fraudulent
        if transaction.get("fraud_probability", 0) > 0.7 or transaction.get("label", 0) == 1:
            self.fraud_count += 1
            
            # Generate alert
            alert = {
                "id": f"alert_{transaction['id']}",
                "transaction_id": transaction['id'],
                "user_id": transaction['user_id'],
                "amount": transaction['amount'],
                "timestamp": transaction['timestamp'],
                "risk_score": transaction['fraud_probability'],
                "alert_type": "high_risk_transaction",
                "status": "new"
            }
            
            # Send alert to Kafka
            self.kafka_client.produce_alert(alert)
            print(f"Generated alert for transaction {transaction['id']}")

        # Print statistics every 100 transactions
        if self.processed_count % 100 == 0:
            print(f"\nProcessed {self.processed_count} transactions")
            print(f"Fraudulent transactions: {self.fraud_count}")
            print(f"Fraud rate: {(self.fraud_count / self.processed_count) * 100:.2f}%")

    def process_alerts(self, alert: Dict) -> None:
        """Process incoming alerts"""
        print(f"Received alert: {alert['id']}")
        print(f"Transaction ID: {alert['transaction_id']}")
        print(f"Risk Score: {alert['risk_score']}")
        print(f"Status: {alert['status']}")
        print("-" * 50)

    def start_processing(self):
        """Start processing transactions and alerts"""
        self.running = True
        
        # Start transaction consumer
        self.kafka_client.consume_transactions(self.process_transaction)
        
        # Start alert consumer
        self.kafka_client.consume_alerts(self.process_alerts)
        
        print("Transaction processor started")

    def stop_processing(self):
        """Stop processing transactions and alerts"""
        self.running = False
        print("Transaction processor stopped")

def main():
    # Initialize Kafka client
    kafka_client = KafkaClient()
    
    try:
        # Create and start transaction processor
        processor = TransactionProcessor(kafka_client)
        processor.start_processing()
        
        # Keep the script running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping transaction processor...")
        processor.stop_processing()
    finally:
        kafka_client.close()

if __name__ == "__main__":
    main() 