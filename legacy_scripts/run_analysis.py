import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.storage import load_ticker_data
from src.physics import calculate_square_root_law

TICKERS = ["SBER", "FLOT", "SELG"]

def main():
    print("Запуск физического анализатора (SQL Edition)...")
    
    for ticker in TICKERS:
        print(f"Загрузка {ticker} из БД...", end=" ")
        df = load_ticker_data(ticker)
        
        if df.empty:
            print("Пусто (сначала запустите run_collection.py)")
            continue
            
        print(f"OK ({len(df)} свечей)")
        
        res = calculate_square_root_law(df)
        
        if not res:
            print(f"{ticker}: Недостаточно данных для построения модели.")
            continue
            
        alpha = res['alpha']
        r2 = res['r2']
        status = "CONFIRMED" if (0.4 <= alpha <= 0.6 and r2 > 0.9) else "⚠️ ANOMALY"
        
        print(f"   Результат:")
        print(f"   Alpha (Наклон): {alpha:.4f}")
        print(f"   R^2 (Точность): {r2:.4f}")
        print(f"   Вердикт: {status}\n")
        
        plot_results(ticker, res, status)

def plot_results(ticker, res, status):
    plt.figure(figsize=(10, 6))
    
    plt.scatter(res['raw_data']['log_Q'], res['raw_data']['log_I'], 
                alpha=0.05, color='#CCCCCC', label='Шум (Raw)')
    
    plt.scatter(res['binned_data']['log_Q'], res['binned_data']['log_I'], 
                color='red', s=30, label='Усреднение (Bins)')
    
    sm = res['smart_money']
    plt.scatter(sm['log_Q'], sm['log_I'], color='lime', s=80, edgecolors='black', label='Smart Money')
    
    slope, intercept = res['params']
    x_vals = np.linspace(sm['log_Q'].min(), sm['log_Q'].max(), 100)
    y_vals = slope * x_vals + intercept
    plt.plot(x_vals, y_vals, color='blue', linewidth=3, label=f'Model (k={slope:.2f})')
    
    plt.title(f"Market Impact Law: {ticker}\nStatus: {status} (R2={res['r2']:.2f})")
    plt.xlabel("Log(Volume) [Энергия]")
    plt.ylabel("Log(Volatility) [Амплитуда]")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.show()

if __name__ == "__main__":
    main()