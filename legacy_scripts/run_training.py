import torch
from torch.utils.data import DataLoader
from src.storage import load_ticker_data
from src.ml.dataset import MarketDataset
from src.ml.model import PhysicsLSTMPredictor
from src.ml.loss import pinn_loss_function

TICKER = "SELG"
EPOCHS = 100

def train():
    print(f"🧠 Обучение PINN модели на {TICKER}...")
    
    df = load_ticker_data(TICKER)
    if df.empty:
        print("Нет данных. Запустите run_collection.py")
        return
        
    dataset = MarketDataset(df)
    loader = DataLoader(dataset, batch_size=32, shuffle=True)
    
    model = PhysicsLSTMPredictor()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    
    model.train()
    
    for epoch in range(EPOCHS):
        total_loss = 0
        
        for batch_x, batch_y, batch_vol in loader:
            optimizer.zero_grad()
            
            pred = model(batch_x)
            
            loss, data_l, phys_l = pinn_loss_function(pred, batch_y, batch_vol)
            
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
        print(f"Epoch {epoch+1}/{EPOCHS} | Loss: {total_loss / len(loader):.6f}")
    
    torch.save(model.state_dict(), f"data/{TICKER}_pinn_model.pth")
    print("Модель сохранена!")

if __name__ == "__main__":
    train()