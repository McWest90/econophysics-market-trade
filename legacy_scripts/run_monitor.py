import time
import pandas as pd
from datetime import datetime
from src.storage import load_ticker_data, get_last_candle_time
from src.physics import calculate_square_root_law, calculate_deviations
from src.loader import download_data

WATCHLIST = ["FLOT", "SELG","SBER"]

def monitor_market():
    print(f"Запуск монитора эконофизики...")
    print(f"Отслеживаем активы: {WATCHLIST}")
    print("Нажмите Ctrl+C для остановки.\n")

    try:
        while True:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Обновление данных...", end=" ")
            
            for ticker in WATCHLIST:
                download_data(ticker, days_back=1)
            
            print("Готово.")

            for ticker in WATCHLIST:
                df = load_ticker_data(ticker)
                if len(df) < 100: continue
                
                model = calculate_square_root_law(df)
                if not model: continue
                
                df_dev = calculate_deviations(df, model)
                
                last_candle = df_dev.iloc[-1]
                z_score = last_candle['z_score']
                

                if z_score < -2.5:
                    print(f"\nАНОМАЛИЯ: {ticker}")
                    print(f"   Время:  {last_candle['time']}")
                    print(f"   Z-Score: {z_score:.2f} (Сжатие пружины!)")
                    print(f"   Объем:   {last_candle['volume']}")
                    print(f"   Цена:    {last_candle['close']}")
                    print("   Возможен резкий импульс в ближайшие 10 минут!\n")
            
            time.sleep(60)

    except KeyboardInterrupt:
        print("\nМониторинг остановлен.")

if __name__ == "__main__":
    monitor_market()