import time
import csv
import torch
from datetime import datetime
from decimal import Decimal

from t_tech.invest import Client, OrderDirection, OrderType
from t_tech.invest.sandbox.client import SandboxClient 
from t_tech.invest.utils import quotation_to_decimal, decimal_to_quotation

from ..config import TOKEN, BASE_DIR, DATA_DIR
from ..storage import load_ticker_data
from ..loader import download_data
from ..ml.model import PhysicsLSTMPredictor
from ..ml.dataset import MarketDataset
from ..physics import calculate_square_root_law, calculate_deviations

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
TRADES_LOG_FILE = LOG_DIR / "sandbox_trades.csv"

if not TRADES_LOG_FILE.exists():
    with open(TRADES_LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["time", "ticker", "action", "price", "quantity", "reason", "balance_after"])

class SandboxBot:
    def __init__(self, ticker="SELG"):
        self.ticker = ticker
        
        self.model_path = DATA_DIR / f"{ticker}_pinn_model.pth"
        self.model = PhysicsLSTMPredictor()
        try:
            self.model.load_state_dict(torch.load(self.model_path))
            self.model.eval()
            print(f"AI Модель загружена: {ticker}")
        except:
            print(f"ОШИБКА: Нет модели для {ticker}. Сначала обучите сеть!")
            self.model = None

    def log_trade(self, action, price, qty, reason, balance):
        with open(TRADES_LOG_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now(), self.ticker, action, price, qty, reason, balance])

    def get_signal(self):
        if not self.model: return None
        
        # 1. Качаем данные
        download_data(self.ticker, days_back=3)
        df = load_ticker_data(self.ticker)
        if len(df) < 100: return None
        
        phys_model = calculate_square_root_law(df)
        if not phys_model: return None
        df_phys = calculate_deviations(df, phys_model)
        last_candle = df_phys.iloc[-1]
        
        df_for_ai = df.tail(80).copy() 
        ds = MarketDataset(df_for_ai)
        if len(ds) < 1: return None
        
        x, _, _ = ds[0]
        with torch.no_grad():
            ai_vol = self.model(x.unsqueeze(0)).item()
            
        return {
            'z_score': last_candle['z_score'],
            'ai_vol': ai_vol,
            'price': last_candle['close'],
            'time': last_candle['time']
        }

    def run(self):
        print(f"\nЗапуск Песочницы для {self.ticker}...")
        
        with SandboxClient(TOKEN) as client:
            accounts = client.users.get_accounts().accounts
            account_id = None
            
            for acc in accounts:
                if acc.status == 1:
                    account_id = acc.id
                    break
            
            if not account_id:
                print("Открываем новый счет...")
                resp = client.sandbox.open_sandbox_account()
                account_id = resp.account_id
                client.sandbox.sandbox_pay_in(
                    account_id=account_id,
                    amount=decimal_to_quotation(Decimal(100000))
                )
            
            try:
                instruments = client.instruments.find_instrument(query=self.ticker).instruments
                uid = next(i.uid for i in instruments if i.class_code == 'TQBR')
            except StopIteration:
                print("Тикер не найден")
                return

            print("Начинаем наблюдение...")
            
            has_position = False
            entry_price = 0
            
            try:
                while True:
                    state = self.get_signal()
                    if not state:
                        time.sleep(10)
                        continue
                        
                    portfolio = client.sandbox.get_sandbox_portfolio(account_id=account_id)
                    money_val = portfolio.total_amount_currencies
                    rub_balance = quotation_to_decimal(money_val)

                    z = state['z_score']
                    ai = state['ai_vol']
                    price = state['price']
                    
                    status_msg = f"⏱ {state['time'].strftime('%H:%M')} | Price: {price} | Z: {z:.2f} | AI: {ai:.3f}"
                    
                    signal_buy = (z < -2.0) and (ai > 0.10)
                    
                    if signal_buy and not has_position:
                        print(f"\n🔥 СИГНАЛ BUY! {status_msg}")
                        client.orders.post_order(
                            instrument_id=uid, quantity=1,
                            direction=OrderDirection.ORDER_DIRECTION_BUY,
                            account_id=account_id,
                            order_type=OrderType.ORDER_TYPE_MARKET
                        )
                        self.log_trade("BUY", price, 1, f"Z={z:.2f}", rub_balance)
                        has_position = True
                        entry_price = price
                        print("Ордер отправлен.")

                    elif has_position:
                        profit_pct = (price - entry_price) / entry_price * 100
                        print(f"PnL: {profit_pct:.2f}% | {status_msg}", end="\r")
                        
                        if profit_pct > 0.3 or z > 0:
                            print(f"\nПРОДАЖА! PnL: {profit_pct:.2f}%")
                            client.orders.post_order(
                                instrument_id=uid, quantity=1,
                                direction=OrderDirection.ORDER_DIRECTION_SELL,
                                account_id=account_id,
                                order_type=OrderType.ORDER_TYPE_MARKET
                            )
                            self.log_trade("SELL", price, 1, f"PnL={profit_pct:.2f}%", rub_balance)
                            has_position = False
                    
                    else:
                        print(f"{status_msg} ...", end="\r")
                    
                    time.sleep(60)

            except KeyboardInterrupt:
                print("\nСтоп.")