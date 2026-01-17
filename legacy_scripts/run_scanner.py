import pandas as pd
import numpy as np
from src.storage import load_ticker_data
from src.physics import calculate_square_root_law, calculate_deviations

TICKERS = ["FLOT", "SBER", "SELG"] 

def main():
    print("Запуск Backtest-сканера (Анализ эффективности сигналов)...\n")
    
    for ticker in TICKERS:
        df = load_ticker_data(ticker)
        if df.empty: continue
            
        model = calculate_square_root_law(df)
        if not model: continue
            
        df_dev = calculate_deviations(df, model)
        
        look_forward_candles = 10
        df_dev['future_close'] = df_dev['close'].shift(-look_forward_candles)
        
        df_dev['profit_10min'] = (df_dev['future_close'] - df_dev['close']) / df_dev['close'] * 100
        
        whales = df_dev[df_dev['z_score'] < -2.5].copy()
        
        if whales.empty:
            print(f"--- {ticker}: Аномалий не найдено ---")
            continue
            
        print(f"--- {ticker}: Найдено {len(whales)} ситуаций 'Скрытый игрок' ---")
        
        significant_moves = whales[whales['profit_10min'].abs() > 0.1]
        
        print(f"Всего сигналов: {len(whales)}")
        print(f"Значимых движений (>0.1% за 10 мин): {len(significant_moves)}")
        print(f"Средняя доходность (по модулю): {whales['profit_10min'].abs().mean():.4f}%")
        
        top_moves = whales.reindex(whales['profit_10min'].abs().sort_values(ascending=False).index).head(5)
        
        print("\nТоп-5 движений после аномалии:")
        print(top_moves[['time', 'close', 'volume', 'z_score', 'profit_10min']])
        print("-" * 60 + "\n")

if __name__ == "__main__":
    main()