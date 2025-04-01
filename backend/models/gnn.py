import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, global_mean_pool
from torch_geometric.data import Data
from typing import List, Tuple, Optional

class FraudGNN(nn.Module):
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 64,
        output_dim: int = 1,
        num_layers: int = 3,
        dropout: float = 0.2
    ):
        super(FraudGNN, self).__init__()
        self.num_layers = num_layers
        self.dropout = dropout

        # GCN layers
        self.conv_layers = nn.ModuleList([
            GCNConv(input_dim, hidden_dim, dropout=dropout),
            *[GCNConv(hidden_dim, hidden_dim, dropout=dropout) for _ in range(num_layers - 2)],
            GCNConv(hidden_dim, hidden_dim, dropout=dropout)
        ])

        # Output layers
        self.fc1 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.fc2 = nn.Linear(hidden_dim // 2, output_dim)

    def forward(self, data: Data) -> torch.Tensor:
        x, edge_index = data.x, data.edge_index
        batch = data.batch

        # GCN layers
        for conv in self.conv_layers:
            x = conv(x, edge_index)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)

        # Global pooling
        x = global_mean_pool(x, batch)

        # Fully connected layers
        x = F.relu(self.fc1(x))
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.fc2(x)

        return torch.sigmoid(x)

    def predict(
        self,
        data: Data,
        threshold: float = 0.5
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Make predictions and return probabilities and binary predictions"""
        self.eval()
        with torch.no_grad():
            probabilities = self.forward(data)
            predictions = (probabilities > threshold).float()
        return probabilities, predictions

class FraudDetector:
    def __init__(
        self,
        model: FraudGNN,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.model = model.to(device)
        self.device = device

    def train(
        self,
        train_data: List[Data],
        epochs: int = 100,
        learning_rate: float = 0.001,
        batch_size: int = 32
    ):
        """Train the model"""
        self.model.train()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        criterion = nn.BCELoss()

        for epoch in range(epochs):
            total_loss = 0
            for batch in train_data:
                batch = batch.to(self.device)
                optimizer.zero_grad()

                output = self.model(batch)
                loss = criterion(output, batch.y.unsqueeze(1).float())
                loss.backward()
                optimizer.step()

                total_loss += loss.item()

            avg_loss = total_loss / len(train_data)
            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")

    def evaluate(self, test_data: List[Data]) -> Tuple[float, float]:
        """Evaluate the model and return accuracy and AUC"""
        self.model.eval()
        all_preds = []
        all_labels = []

        with torch.no_grad():
            for batch in test_data:
                batch = batch.to(self.device)
                probabilities, predictions = self.model.predict(batch)
                all_preds.extend(probabilities.cpu().numpy())
                all_labels.extend(batch.y.cpu().numpy())

        # Calculate metrics
        from sklearn.metrics import accuracy_score, roc_auc_score
        accuracy = accuracy_score(all_labels, [1 if p > 0.5 else 0 for p in all_preds])
        auc = roc_auc_score(all_labels, all_preds)

        return accuracy, auc

    def save_model(self, path: str):
        """Save the model to disk"""
        torch.save(self.model.state_dict(), path)

    def load_model(self, path: str):
        """Load the model from disk"""
        self.model.load_state_dict(torch.load(path)) 