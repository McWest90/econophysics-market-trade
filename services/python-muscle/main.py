import os
import asyncio
import logging
import time
import traceback
from sqlalchemy import create_engine, text
from t_tech.invest import AsyncClient, CandleInterval, MarketDataRequest, SubscribeCandlesRequest, SubscriptionAction

# Настройка логов
logging.basicConfig(level=logging.INFO, format="%(asctime)s [MUSCLE] %(message)s")
logger = logging.getLogger("Muscle")

# Конфиг
TOKEN = os.getenv("T_BANK_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
WATCHLIST = ["SELG", "SBER", "FLOT", "KMAZ", "VTBR"]

INSERT_QUERY = text("""
    INSERT INTO candles (ticker, time, open, high, low, close, volume, volatility)
    VALUES (:ticker, :time, :open, :high, :low, :close, :volume, :volatility)
    ON CONFLICT (ticker, time) DO NOTHING
""")

def get_db_engine():
    if not DATABASE_URL:
        logger.error("DATABASE_URL не задан!")
        exit(1)
    return create_engine(DATABASE_URL)

async def main():
    if not TOKEN:
        logger.error("T_BANK_TOKEN не задан!")
        return

    engine = get_db_engine()
    
    # --- ВАЖНОЕ ИСПРАВЛЕНИЕ: KEEPALIVE OPTIONS ---
    # Это заставит клиента пинговать сервер, чтобы соединение не рвалось
    grpc_options = [
        ('grpc.keepalive_time_ms', 15000),          # Пинг каждые 15 сек
        ('grpc.keepalive_timeout_ms', 5000),       # Ждем ответа 5 сек
        ('grpc.keepalive_permit_without_calls', 1), # Разрешить пинг, даже если нет данных (рынок закрыт)
        ('grpc.http2.max_pings_without_data', 0),  # Снять ограничение на кол-во пингов
    ]

    async with AsyncClient(TOKEN, options=grpc_options) as client:
        logger.info("🔌 Подключение к T-Bank API...")

        # --- ЭТАП А: Получаем UID инструментов ---
        uid_map = {} 
        uids_to_subscribe = []

        for ticker in WATCHLIST:
            try:
                resp = await client.instruments.find_instrument(query=ticker)
                for item in resp.instruments:
                    if item.class_code == 'TQBR':
                        uid_map[item.uid] = ticker
                        uids_to_subscribe.append(item.uid)
                        logger.info(f"✅ Найден {ticker}: {item.uid}")
                        break
            except Exception as e:
                logger.error(f"❌ Не найден {ticker}: {e}")

        if not uids_to_subscribe:
            logger.error("Не на что подписываться. Выход.")
            return

        # --- ЭТАП Б: Подготовка запроса ---
        async def request_iterator():
            yield MarketDataRequest(
                subscribe_candles_request=SubscribeCandlesRequest(
                    subscription_action=SubscriptionAction.SUBSCRIPTION_ACTION_SUBSCRIBE,
                    instruments=[
                        {"instrument_id": uid, "interval": CandleInterval.CANDLE_INTERVAL_1_MIN}
                        for uid in uids_to_subscribe
                    ],
                    waiting_close=False
                )
            )
            # Вечный цикл, чтобы генератор не закрылся
            while True:
                await asyncio.sleep(60)

        logger.info("📡 Подписываемся на поток свечей...")

        market_data_stream = client.market_data_stream.market_data_stream(request_iterator())

        logger.info("🚀 Muscle запущен! Слушаем рынок...")

        try:
            async for marketdata in market_data_stream:
                if marketdata.candle:
                    c = marketdata.candle
                    uid = c.instrument_uid
                    
                    if uid not in uid_map:
                        continue

                    ticker = uid_map[uid]
                    
                    def cast(q): return q.units + q.nano / 1e9
                    
                    open_p = cast(c.open)
                    high_p = cast(c.high)
                    low_p = cast(c.low)
                    close_p = cast(c.close)
                    volatility = high_p - low_p
                    
                    try:
                        with engine.begin() as conn:
                            conn.execute(INSERT_QUERY, {
                                "ticker": ticker,
                                "time": c.time,
                                "open": open_p,
                                "high": high_p,
                                "low": low_p,
                                "close": close_p,
                                "volume": c.volume,
                                "volatility": volatility
                            })
                        logger.info(f"📥 {ticker} | {c.time.strftime('%H:%M')} | P: {close_p} | Vol: {c.volume}")
                    except Exception as e:
                        logger.error(f"Ошибка БД: {e}")

                if marketdata.ping:
                    logger.debug("Ping received")

        except Exception as e:
             # Логируем, но не паникуем, внешний цикл перезапустит
             logger.warning(f"Разрыв соединения: {e}")

if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            logger.info("🛑 Остановка сервиса...")
            break
        except Exception as e:
            logger.error(f"💥 Критическая ошибка: {e}. Рестарт через 5 сек...")
            time.sleep(5)