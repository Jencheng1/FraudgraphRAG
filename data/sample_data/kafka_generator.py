import random
import time
from datetime import datetime, timedelta
import uuid
from typing import List, Dict
import threading
from ...backend.utils.kafka_client import KafkaClient
from ...backend.core.config import settings

class TransactionGenerator:
    def __init__(self, kafka_client: KafkaClient):
        self.kafka_client = kafka_client
        self.running = False
        self.thread = None

    def generate_transaction(self) -> Dict:
        """Generate a single transaction"""
        amount = random.uniform(10, 10000)
        timestamp = datetime.now().isoformat()
        user_id = str(uuid.uuid4())
        
        # Generate features for the transaction
        features = [
            amount,
            random.uniform(0, 1),  # time_of_day
            random.uniform(0, 1),  # day_of_week
            random.uniform(0, 1),  # amount_deviation
            random.uniform(0, 1),  # location_deviation
            random.uniform(0, 1)   # user_risk_score
        ]
        
        transaction = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "amount": amount,
            "timestamp": timestamp,
            "features": features,
            "fraud_probability": random.uniform(0, 1),
            "label": random.choice([0, 1])  # 1 for fraudulent transactions
        }
        
        return transaction

    def generate_and_send(self):
        """Generate and send transactions to Kafka"""
        while self.running:
            try:
                # Generate a transaction
                transaction = self.generate_transaction()
                
                # Send to Kafka
                self.kafka_client.produce_transaction(transaction)
                
                print(f"Sent transaction: {transaction['id']}")
                
                # Random delay between transactions (0.1 to 2 seconds)
                time.sleep(random.uniform(0.1, 2))
                
            except Exception as e:
                print(f"Error generating transaction: {str(e)}")
                time.sleep(1)  # Wait before retrying

    def start(self):
        """Start the transaction generator"""
        self.running = True
        self.thread = threading.Thread(target=self.generate_and_send)
        self.thread.start()
        print("Transaction generator started")

    def stop(self):
        """Stop the transaction generator"""
        self.running = False
        if self.thread:
            self.thread.join()
        print("Transaction generator stopped")

def main():
    # Initialize Kafka client
    kafka_client = KafkaClient()
    
    try:
        # Create and start transaction generator
        generator = TransactionGenerator(kafka_client)
        generator.start()
        
        # Keep the script running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping transaction generator...")
        generator.stop()
    finally:
        kafka_client.close()

if __name__ == "__main__":
    main() 