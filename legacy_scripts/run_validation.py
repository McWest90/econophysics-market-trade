import torch
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from torch.utils.data import DataLoader
from src.storage import load_ticker_data
from src.ml.dataset import MarketDataset
from src.ml.model import PhysicsLSTMPredictor

TICKER = "SELG"
MODEL_PATH = f"data/{TICKER}_pinn_model.pth"

def validate():
    print(f"Проверка модели PINN на {TICKER}...")

    df = load_ticker_data(TICKER)
    
    df_test = df.tail(500).copy()
    
    dataset = MarketDataset(df_test)
    loader = DataLoader(dataset, batch_size=1, shuffle=False) 

    model = PhysicsLSTMPredictor()
    try:
        model.load_state_dict(torch.load(MODEL_PATH))
        model.eval()
        print("Модель успешно загружена.")
    except FileNotFoundError:
        print("Файл модели не найден. Сначала запустите run_training.py")
        return

    predictions = []
    actuals = []
    phys_theoretical = []

    print("Генерируем прогнозы...")
    with torch.no_grad():
        for x, y, vol_future in loader:
            pred = model(x)
            predictions.append(pred.item())
            
            actuals.append(y.item())
            
            phys_val = (vol_future.item() ** 0.44) 
            phys_theoretical.append(phys_val)

    plt.figure(figsize=(12, 6))
    
    plt.plot(actuals, label='Реальная волатильность', color='blue', alpha=0.5)
    plt.plot(predictions, label='Прогноз PINN (AI)', color='red', linewidth=2)
    
    phys_norm = np.array(phys_theoretical)
    phys_norm = (phys_norm - phys_norm.min()) / (phys_norm.max() - phys_norm.min()) * (max(actuals) - min(actuals)) + min(actuals)
    
    plt.plot(phys_norm, label='Чистая физика (Volume Only)', color='green', linestyle='--', alpha=0.7)

    plt.title(f"PINN Validation: {TICKER} (Last 500 candles)")
    plt.xlabel("Time steps")
    plt.ylabel("Normalized Volatility")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()

if __name__ == "__main__":
    validate()