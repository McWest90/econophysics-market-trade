import time
import torch
import logging
from decimal import Decimal
from t_tech.invest import OrderDirection, OrderType, SandboxClient, Client

from src.config import TOKEN, logger
from src.storage import load_ticker_data
from src.loader import download_data
from src.ml.model import PhysicsLSTMPredictor
from src.ml.dataset import MarketDataset
from src.physics import calculate_square_root_law, calculate_deviations

SANDBOX_MODE = True
TICKER = "SELG"
LOT_SIZE = 10

MODEL_PATH = f"data/{TICKER}_pinn_model.pth" 

class PhysicsBot:
    def __init__(self):
        self.client_cls = SandboxClient if SANDBOX_MODE else Client
        
        self.model = PhysicsLSTMPredictor()
        try:
            self.model.load_state_dict(torch.load(MODEL_PATH))
            self.model.eval()
            logger.info(f"Модель для {TICKER} успешно загружена.")
        except FileNotFoundError:
            logger.error("Модель не найдена! Сначала запустите run_training.py")
            exit()

    def get_signal(self):
        """Анализирует рынок и ищет аномалии"""
        download_data(TICKER, days_back=3)
        
        df = load_ticker_data(TICKER)
        if len(df) < 100: return None
        
        phys_model = calculate_square_root_law(df)
        if not phys_model: return None
        
        df_phys = calculate_deviations(df, phys_model)
        last_candle = df_phys.iloc[-1]
        
        ds = MarketDataset(df.tail(80))
        if len(ds) < 1: return None
        
        x_tensor, _, _ = ds[0] 
        with torch.no_grad():
            ai_volatility = self.model(x_tensor.unsqueeze(0)).item()
            
        return {
            'time': last_candle['time'],
            'price': last_candle['close'],
            'z_score': last_candle['z_score'],
            'ai_vol': ai_volatility
        }

    def trade_loop(self):
        logger.info(f"Запуск бота на {TICKER}. Режим: {'SANDBOX' if SANDBOX_MODE else 'REAL'}")
        
        with self.client_cls(TOKEN) as client:
            if SANDBOX_MODE:
                try:
                    accounts = client.users.get_accounts().accounts
                    for acc in accounts:
                        client.sandbox.sandbox_close_account(account_id=acc.id)
                except: pass
                
                resp = client.sandbox.sandbox_open_account()
                account_id = resp.account_id
                client.sandbox.sandbox_pay_in(
                    account_id=account_id,
                    amount={"currency": "rub", "units": 100000, "nano": 0}
                )
                logger.info("Песочница: Зачислено 100,000 руб.")
            else:
                account_id = client.users.get_accounts().accounts[0].id

            instruments = client.instruments.find_instrument(query=TICKER).instruments
            uid = next(i.uid for i in instruments if i.class_code == 'TQBR')

            logger.info("Начинаем наблюдение...")
            
            while True:
                try:
                    state = self.get_signal()
                    if not state:
                        time.sleep(10)
                        continue

                    
                    is_anomaly = state['z_score'] < -2.0
                    is_ai_alert = state['ai_vol'] > 0.10
                    
                    log_msg = f"{state['time']} | Z: {state['z_score']:.2f} | AI: {state['ai_vol']:.3f}"
                    
                    if is_anomaly and is_ai_alert:
                        logger.info(f"{log_msg} -> ПОКУПКА!")
                        
                        client.orders.post_order(
                            instrument_id=uid,
                            quantity=1,
                            direction=OrderDirection.ORDER_DIRECTION_BUY,
                            account_id=account_id,
                            order_type=OrderType.ORDER_TYPE_MARKET
                        )
                        
                        logger.info("Позиция открыта. Ждем 10 минут...")
                        time.sleep(600)
                        
                        client.orders.post_order(
                            instrument_id=uid,
                            quantity=1,
                            direction=OrderDirection.ORDER_DIRECTION_SELL,
                            account_id=account_id,
                            order_type=OrderType.ORDER_TYPE_MARKET
                        )
                        logger.info("Позиция закрыта.")
                        
                    else:
                        print(f"{log_msg} ...", end="\r")
                    
                    time.sleep(60)

                except KeyboardInterrupt:
                    logger.info("Стоп.")
                    break
                except Exception as e:
                    logger.error(f"Ошибка: {e}")
                    time.sleep(5)

if __name__ == "__main__":
    bot = PhysicsBot()
    bot.trade_loop()