from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from pydantic import BaseModel
from ..core.database import get_neo4j, get_supabase
from ..models.gnn import FraudGNN, FraudDetector
from ..models.graphrag import GraphRAG
from ..core.config import settings

router = APIRouter()

# Initialize models
gnn_model = FraudGNN(input_dim=64)  # Adjust input_dim based on your feature space
fraud_detector = FraudDetector(gnn_model)
graphrag = GraphRAG(get_neo4j(), gnn_model)

class Transaction(BaseModel):
    id: str
    amount: float
    timestamp: str
    user_id: str
    features: List[float]

class TransactionResponse(BaseModel):
    transaction_id: str
    fraud_probability: float
    is_fraudulent: bool
    context: Dict[str, Any]

@router.post("/predict", response_model=TransactionResponse)
async def predict_fraud(transaction: Transaction):
    """Predict fraud probability for a transaction"""
    try:
        # Update graph with new transaction
        transaction_data = transaction.dict()
        relationships = [
            {
                "related_id": transaction.user_id,
                "properties": {"type": "BELONGS_TO"}
            }
        ]
        graphrag.update_graph(transaction_data, relationships)
        
        # Get prediction
        result = graphrag.predict_fraud(transaction.id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transaction/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: str):
    """Get fraud prediction for an existing transaction"""
    try:
        result = graphrag.predict_fraud(transaction_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}/transactions")
async def get_user_transactions(user_id: str):
    """Get all transactions for a user"""
    query = """
    MATCH (t:Transaction)-[:BELONGS_TO]->(u:User {id: $user_id})
    RETURN t
    ORDER BY t.timestamp DESC
    """
    
    try:
        with get_neo4j().session() as session:
            result = session.run(query, user_id=user_id)
            transactions = [dict(record["t"]) for record in result]
            return transactions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_fraud_alerts(threshold: float = 0.7):
    """Get high-risk transactions"""
    query = """
    MATCH (t:Transaction)
    WHERE t.fraud_probability >= $threshold
    RETURN t
    ORDER BY t.fraud_probability DESC
    """
    
    try:
        with get_neo4j().session() as session:
            result = session.run(query, threshold=threshold)
            alerts = [dict(record["t"]) for record in result]
            return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train")
async def train_model(epochs: int = 100):
    """Train the GNN model"""
    try:
        # Get training data from Neo4j
        query = """
        MATCH (t:Transaction)
        WHERE t.label IS NOT NULL
        RETURN t
        """
        
        with get_neo4j().session() as session:
            result = session.run(query)
            training_data = []
            
            for record in result:
                transaction = record["t"]
                # Create graph data for each transaction
                graph_data = graphrag.retrieve_context(transaction["id"])
                graph_data.y = torch.tensor([transaction["label"]], dtype=torch.long)
                training_data.append(graph_data)
        
        # Train the model
        fraud_detector.train(training_data, epochs=epochs)
        
        return {"message": "Model training completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model/status")
async def get_model_status():
    """Get model status and metrics"""
    try:
        # Get test data
        query = """
        MATCH (t:Transaction)
        WHERE t.label IS NOT NULL
        RETURN t
        LIMIT 100
        """
        
        with get_neo4j().session() as session:
            result = session.run(query)
            test_data = []
            
            for record in result:
                transaction = record["t"]
                graph_data = graphrag.retrieve_context(transaction["id"])
                graph_data.y = torch.tensor([transaction["label"]], dtype=torch.long)
                test_data.append(graph_data)
        
        # Evaluate model
        accuracy, auc = fraud_detector.evaluate(test_data)
        
        return {
            "accuracy": accuracy,
            "auc": auc,
            "model_path": settings.MODEL_PATH
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 