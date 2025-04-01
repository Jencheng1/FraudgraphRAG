import random
from datetime import datetime, timedelta
from typing import List, Dict
import uuid
from ..core.database import get_supabase, get_neo4j

def generate_sample_users(num_users: int = 100) -> List[Dict]:
    """Generate sample user data"""
    users = []
    for _ in range(num_users):
        user = {
            "id": str(uuid.uuid4()),
            "name": f"User_{random.randint(1, 1000)}",
            "email": f"user_{random.randint(1, 1000)}@example.com",
            "created_at": datetime.now().isoformat(),
            "risk_score": random.uniform(0, 1)
        }
        users.append(user)
    return users

def generate_sample_transactions(
    users: List[Dict],
    num_transactions: int = 1000
) -> List[Dict]:
    """Generate sample transaction data"""
    transactions = []
    for _ in range(num_transactions):
        user = random.choice(users)
        amount = random.uniform(10, 10000)
        timestamp = datetime.now() - timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 24)
        )
        
        # Generate features for the transaction
        features = [
            amount,
            random.uniform(0, 1),  # time_of_day
            random.uniform(0, 1),  # day_of_week
            random.uniform(0, 1),  # amount_deviation
            random.uniform(0, 1),  # location_deviation
            user["risk_score"]
        ]
        
        transaction = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "amount": amount,
            "timestamp": timestamp.isoformat(),
            "features": features,
            "fraud_probability": random.uniform(0, 1),
            "label": random.choice([0, 1])  # 1 for fraudulent transactions
        }
        transactions.append(transaction)
    return transactions

def init_supabase():
    """Initialize Supabase with sample data"""
    supabase = get_supabase()
    
    # Create users
    users = generate_sample_users()
    for user in users:
        supabase.table("users").insert(user).execute()
    
    # Create transactions
    transactions = generate_sample_transactions(users)
    for transaction in transactions:
        supabase.table("transactions").insert(transaction).execute()

def init_neo4j():
    """Initialize Neo4j with sample data"""
    neo4j = get_neo4j()
    
    # Create constraints
    constraints = [
        "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) ON (u.id) IS UNIQUE",
        "CREATE CONSTRAINT transaction_id IF NOT EXISTS FOR (t:Transaction) ON (t.id) IS UNIQUE"
    ]
    
    for constraint in constraints:
        neo4j.session().run(constraint)
    
    # Create sample data
    users = generate_sample_users(50)  # Fewer users for Neo4j
    transactions = generate_sample_transactions(users, 200)  # Fewer transactions for Neo4j
    
    # Create users
    for user in users:
        query = """
        CREATE (u:User $user_data)
        """
        neo4j.session().run(query, user_data=user)
    
    # Create transactions and relationships
    for transaction in transactions:
        # Create transaction node
        query = """
        CREATE (t:Transaction $transaction_data)
        WITH t
        MATCH (u:User {id: $user_id})
        CREATE (t)-[:BELONGS_TO]->(u)
        """
        neo4j.session().run(
            query,
            transaction_data={
                "id": transaction["id"],
                "amount": transaction["amount"],
                "timestamp": transaction["timestamp"],
                "fraud_probability": transaction["fraud_probability"],
                "label": transaction["label"]
            },
            user_id=transaction["user_id"]
        )
    
    # Create some transaction relationships
    for i in range(len(transactions)):
        for j in range(i + 1, min(i + 3, len(transactions))):
            if random.random() < 0.3:  # 30% chance of connection
                query = """
                MATCH (t1:Transaction {id: $id1})
                MATCH (t2:Transaction {id: $id2})
                CREATE (t1)-[r:CONNECTED_TO]->(t2)
                SET r.timestamp = $timestamp
                """
                neo4j.session().run(
                    query,
                    id1=transactions[i]["id"],
                    id2=transactions[j]["id"],
                    timestamp=datetime.now().isoformat()
                )

def main():
    """Initialize both databases with sample data"""
    print("Initializing Supabase...")
    init_supabase()
    
    print("Initializing Neo4j...")
    init_neo4j()
    
    print("Sample data initialization completed!")

if __name__ == "__main__":
    main() 