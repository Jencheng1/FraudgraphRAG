import pytest
import torch
import numpy as np
from backend.models.gnn import GNNModel
from backend.models.graphrag import GraphRAG

@pytest.fixture
def sample_graph_data():
    # Create sample graph data for testing
    num_nodes = 10
    num_features = 6
    num_edges = 15
    
    # Generate random node features
    node_features = torch.randn(num_nodes, num_features)
    
    # Generate random edge indices
    edge_index = torch.randint(0, num_nodes, (2, num_edges))
    
    # Generate random labels
    labels = torch.randint(0, 2, (num_nodes,))
    
    return node_features, edge_index, labels

def test_gnn_model_initialization():
    """Test GNN model initialization"""
    model = GNNModel(input_dim=6, hidden_dim=64, output_dim=1)
    assert model is not None
    assert isinstance(model, GNNModel)

def test_gnn_model_forward(sample_graph_data):
    """Test GNN model forward pass"""
    node_features, edge_index, _ = sample_graph_data
    model = GNNModel(input_dim=6, hidden_dim=64, output_dim=1)
    
    output = model(node_features, edge_index)
    assert output.shape == (node_features.shape[0], 1)

def test_graphrag_initialization():
    """Test GraphRAG initialization"""
    graphrag = GraphRAG()
    assert graphrag is not None
    assert isinstance(graphrag, GraphRAG)

def test_graphrag_build_graph(sample_graph_data):
    """Test GraphRAG graph building"""
    graphrag = GraphRAG()
    node_features, edge_index, labels = sample_graph_data
    
    graph = graphrag.build_graph(node_features, edge_index, labels)
    assert graph is not None
    assert graph.num_nodes == node_features.shape[0]
    assert graph.num_edges == edge_index.shape[1]

def test_graphrag_retrieve_context():
    """Test GraphRAG context retrieval"""
    graphrag = GraphRAG()
    query = "test query"
    
    context = graphrag.retrieve_context(query)
    assert context is not None
    assert isinstance(context, str)

def test_graphrag_generate_response():
    """Test GraphRAG response generation"""
    graphrag = GraphRAG()
    query = "test query"
    context = "test context"
    
    response = graphrag.generate_response(query, context)
    assert response is not None
    assert isinstance(response, str) 