from typing import List, Dict, Any, Optional
import torch
from torch_geometric.data import Data
from neo4j import GraphDatabase
from .gnn import FraudGNN
import numpy as np

class GraphRAG:
    def __init__(
        self,
        neo4j_driver: GraphDatabase.driver,
        gnn_model: FraudGNN,
        embedding_dim: int = 64
    ):
        self.neo4j_driver = neo4j_driver
        self.gnn_model = gnn_model
        self.embedding_dim = embedding_dim

    def _create_graph_data(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        labels: Optional[List[int]] = None
    ) -> Data:
        """Create PyTorch Geometric Data object from graph data"""
        # Convert node features to tensor
        node_features = torch.tensor(
            [node['features'] for node in nodes],
            dtype=torch.float
        )

        # Convert edge indices to tensor
        edge_index = torch.tensor(
            [[edge['source'], edge['target']] for edge in edges],
            dtype=torch.long
        ).t().contiguous()

        # Create labels tensor if provided
        y = torch.tensor(labels, dtype=torch.long) if labels else None

        return Data(
            x=node_features,
            edge_index=edge_index,
            y=y
        )

    def _get_subgraph(
        self,
        node_id: str,
        depth: int = 2
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Retrieve subgraph from Neo4j"""
        query = """
        MATCH path = (start:Transaction {id: $node_id})
        -[*1..$depth]-(related)
        WITH path, start, related
        RETURN path, start, related
        """
        
        with self.neo4j_driver.session() as session:
            result = session.run(query, node_id=node_id, depth=depth)
            
            nodes = []
            edges = []
            seen_nodes = set()
            seen_edges = set()
            
            for record in result:
                path = record["path"]
                for node in path.nodes:
                    if node.id not in seen_nodes:
                        nodes.append({
                            "id": node.id,
                            "features": self._extract_node_features(node)
                        })
                        seen_nodes.add(node.id)
                
                for rel in path.relationships:
                    edge_key = (rel.start_node.id, rel.end_node.id)
                    if edge_key not in seen_edges:
                        edges.append({
                            "source": rel.start_node.id,
                            "target": rel.end_node.id,
                            "type": rel.type
                        })
                        seen_edges.add(edge_key)
            
            return nodes, edges

    def _extract_node_features(self, node) -> List[float]:
        """Extract features from Neo4j node"""
        # This is a placeholder - implement feature extraction based on your data model
        features = []
        for key in node.keys():
            if isinstance(node[key], (int, float)):
                features.append(float(node[key]))
        return features

    def retrieve_context(
        self,
        transaction_id: str,
        depth: int = 2
    ) -> Data:
        """Retrieve relevant graph context for a transaction"""
        nodes, edges = self._get_subgraph(transaction_id, depth)
        return self._create_graph_data(nodes, edges)

    def predict_fraud(
        self,
        transaction_id: str,
        threshold: float = 0.5
    ) -> Dict[str, Any]:
        """Predict fraud probability for a transaction"""
        # Retrieve graph context
        graph_data = self.retrieve_context(transaction_id)
        
        # Get prediction from GNN model
        probabilities, predictions = self.gnn_model.predict(graph_data, threshold)
        
        # Get relevant context from Neo4j
        context = self._get_explanation_context(transaction_id)
        
        return {
            "transaction_id": transaction_id,
            "fraud_probability": float(probabilities[0]),
            "is_fraudulent": bool(predictions[0]),
            "context": context
        }

    def _get_explanation_context(
        self,
        transaction_id: str
    ) -> Dict[str, Any]:
        """Get explanation context for the prediction"""
        query = """
        MATCH (t:Transaction {id: $transaction_id})
        OPTIONAL MATCH (t)-[:BELONGS_TO]->(u:User)
        OPTIONAL MATCH (t)-[:CONNECTED_TO]->(r:Transaction)
        RETURN t, u, collect(r) as related_transactions
        """
        
        with self.neo4j_driver.session() as session:
            result = session.run(query, transaction_id=transaction_id)
            record = result.single()
            
            if not record:
                return {}
            
            transaction = record["t"]
            user = record["u"]
            related_transactions = record["related_transactions"]
            
            return {
                "transaction": dict(transaction),
                "user": dict(user) if user else None,
                "related_transactions": [
                    dict(t) for t in related_transactions
                ]
            }

    def update_graph(
        self,
        transaction_data: Dict[str, Any],
        relationships: List[Dict[str, Any]]
    ):
        """Update the graph with new transaction data"""
        # Create transaction node
        create_query = """
        CREATE (t:Transaction $transaction_data)
        WITH t
        UNWIND $relationships as rel
        MATCH (related {id: rel.related_id})
        CREATE (t)-[r:CONNECTED_TO]->(related)
        SET r += rel.properties
        """
        
        with self.neo4j_driver.session() as session:
            session.run(
                create_query,
                transaction_data=transaction_data,
                relationships=relationships
            ) 