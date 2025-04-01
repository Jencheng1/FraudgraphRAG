import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import networkx as nx
from datetime import datetime
import json

# Configure the page
st.set_page_config(
    page_title="Fraud Detection Dashboard",
    page_icon="🔍",
    layout="wide"
)

# Constants
API_BASE_URL = "http://localhost:8000/api/v1"

def fetch_data(endpoint: str, params: dict = None) -> dict:
    """Fetch data from the API"""
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {str(e)}")
        return None

def create_transaction_network(transactions: list) -> go.Figure:
    """Create an interactive network visualization"""
    G = nx.Graph()
    
    # Add nodes and edges
    for transaction in transactions:
        G.add_node(
            transaction["id"],
            amount=transaction["amount"],
            fraud_probability=transaction.get("fraud_probability", 0),
            timestamp=transaction["timestamp"]
        )
        
        if "user_id" in transaction:
            G.add_edge(transaction["id"], transaction["user_id"])
    
    # Create the visualization
    pos = nx.spring_layout(G)
    
    # Create edges
    edge_trace = go.Scatter(
        x=[],
        y=[],
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines'
    )
    
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_trace['x'] += tuple([x0, x1, None])
        edge_trace['y'] += tuple([y0, y1, None])
    
    # Create nodes
    node_trace = go.Scatter(
        x=[],
        y=[],
        mode='markers+text',
        hoverinfo='text',
        text=[],
        marker=dict(
            showscale=True,
            colorscale='YlOrRd',
            size=10,
            colorbar=dict(
                thickness=15,
                title='Fraud Probability',
                xanchor='left',
                titleside='right'
            )
        )
    )
    
    for node in G.nodes():
        x, y = pos[node]
        node_trace['x'] += tuple([x])
        node_trace['y'] += tuple([y])
        node_trace['text'] += tuple([f"ID: {node}<br>Amount: ${G.nodes[node]['amount']}<br>Fraud Prob: {G.nodes[node]['fraud_probability']:.2f}"])
    
    # Create the figure
    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40)
        )
    )
    
    return fig

def main():
    st.title("🔍 Fraud Detection Dashboard")
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Overview", "Transactions", "Alerts", "Model Status"]
    )
    
    if page == "Overview":
        show_overview()
    elif page == "Transactions":
        show_transactions()
    elif page == "Alerts":
        show_alerts()
    elif page == "Model Status":
        show_model_status()

def show_overview():
    st.header("System Overview")
    
    # Fetch system status
    status = fetch_data("health")
    if status:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("System Status", status["status"].capitalize())
        with col2:
            st.metric("Database Connections", 
                     "✅ Connected" if all(status["database_connections"].values()) else "❌ Disconnected")
    
    # Recent transactions
    st.subheader("Recent Transactions")
    transactions = fetch_data("alerts", {"threshold": 0.5})
    if transactions:
        df = pd.DataFrame(transactions)
        st.dataframe(df[["id", "amount", "fraud_probability", "timestamp"]].head(5))
    
    # Network visualization
    st.subheader("Transaction Network")
    if transactions:
        fig = create_transaction_network(transactions)
        st.plotly_chart(fig, use_container_width=True)

def show_transactions():
    st.header("Transaction Analysis")
    
    # Transaction search
    transaction_id = st.text_input("Enter Transaction ID")
    if transaction_id:
        transaction = fetch_data(f"transaction/{transaction_id}")
        if transaction:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Fraud Probability", f"{transaction['fraud_probability']:.2%}")
            with col2:
                st.metric("Status", "Fraudulent" if transaction["is_fraudulent"] else "Legitimate")
            
            st.json(transaction["context"])
    
    # User transactions
    user_id = st.text_input("Enter User ID")
    if user_id:
        transactions = fetch_data(f"user/{user_id}/transactions")
        if transactions:
            df = pd.DataFrame(transactions)
            st.dataframe(df)
            
            # Create network visualization
            fig = create_transaction_network(transactions)
            st.plotly_chart(fig, use_container_width=True)

def show_alerts():
    st.header("Fraud Alerts")
    
    # Alert threshold
    threshold = st.slider("Alert Threshold", 0.0, 1.0, 0.7, 0.1)
    
    # Fetch alerts
    alerts = fetch_data("alerts", {"threshold": threshold})
    if alerts:
        df = pd.DataFrame(alerts)
        
        # Alert statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Alerts", len(alerts))
        with col2:
            st.metric("Average Fraud Probability", f"{df['fraud_probability'].mean():.2%}")
        with col3:
            st.metric("Total Amount at Risk", f"${df['amount'].sum():,.2f}")
        
        # Alert table
        st.dataframe(df)
        
        # Alert timeline
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(df['timestamp']),
            y=df['fraud_probability'],
            mode='markers',
            name='Alerts'
        ))
        fig.update_layout(
            title="Alert Timeline",
            xaxis_title="Time",
            yaxis_title="Fraud Probability"
        )
        st.plotly_chart(fig, use_container_width=True)

def show_model_status():
    st.header("Model Status")
    
    # Fetch model status
    status = fetch_data("model/status")
    if status:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Model Accuracy", f"{status['accuracy']:.2%}")
        with col2:
            st.metric("AUC Score", f"{status['auc']:.2%}")
    
    # Model training
    st.subheader("Model Training")
    epochs = st.number_input("Number of Epochs", min_value=1, max_value=1000, value=100)
    if st.button("Train Model"):
        with st.spinner("Training model..."):
            response = requests.post(f"{API_BASE_URL}/train", params={"epochs": epochs})
            if response.status_code == 200:
                st.success("Model training completed successfully!")
            else:
                st.error(f"Error training model: {response.text}")

if __name__ == "__main__":
    main() 