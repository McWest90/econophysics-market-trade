import torch
import torch.nn as nn

class PhysicsLSTMPredictor(nn.Module):
    def __init__(self, input_dim=3, hidden_dim=64, num_layers=2):
        super().__init__()
        
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        
        self.fc = nn.Linear(hidden_dim, 1)
        
    def forward(self, x):
        
        lstm_out, _ = self.lstm(x)
        
        last_step = lstm_out[:, -1, :]
        
        prediction = self.fc(last_step)
        return prediction.squeeze()