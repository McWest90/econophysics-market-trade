import time
import logging
from datetime import timedelta, timezone
from t_tech.invest import Client, CandleInterval
from t_tech.invest.utils import now, quotation_to_decimal
from t_tech.invest.exceptions import RequestError

from .config import TOKEN, logger
from .storage import save_candles_to_db, get_last_candle_time, init_db

init_db()

def get_instrument_uid(client, ticker, class_code='TQBR'):
    """Находит UID инструмента по тикеру."""
    try:
        instruments = client.instruments.find_instrument(query=ticker).instruments
        for item in instruments:
            if item.ticker == ticker and item.class_code == class_code:
                logger.info(f"Инструмент найден: {item.name} (UID: {item.uid})")
                return item.uid
        logger.error(f"Инструмент {ticker} не найден в режиме {class_code}")
        return None
    except Exception as e:
        logger.error(f"Ошибка поиска инструмента: {e}")
        return None

def download_data(ticker, days_back=60, class_code='TQBR'):
    """
    Скачивает свечи с механизмом повторных попыток (Retry) и сохраняет в БД.
    """
    if not TOKEN:
        logger.error("Нет токена. Прерывание.")
        return
    
    last_time = get_last_candle_time(ticker)
    current_time = now()
    
    if last_time:
        if last_time.tzinfo is None:
            last_time = last_time.replace(tzinfo=timezone.utc)
            
        start_time = last_time + timedelta(minutes=1)
        logger.info(f"{ticker}: Найдена история (последняя: {last_time}). Докачиваем с {start_time}")
    else:
        start_time = current_time - timedelta(days=days_back)
        logger.info(f"{ticker}: История пуста. Качаем с нуля за {days_back} дней")

    if (current_time - start_time).total_seconds() < 60:
        logger.info(f"zzz {ticker}: Данные актуальны.")
        return

    max_retries = 3
    attempt = 0
    
    while attempt < max_retries:
        try:
            with Client(TOKEN) as client:
                uid = get_instrument_uid(client, ticker, class_code)
                if not uid:
                    return 

                new_candles = []
                for candle in client.get_all_candles(
                    instrument_id=uid,
                    from_=start_time,
                    interval=CandleInterval.CANDLE_INTERVAL_1_MIN,
                ):
                    new_candles.append({
                        'ticker': ticker, 
                        'time': candle.time,
                        'open': float(quotation_to_decimal(candle.open)),
                        'close': float(quotation_to_decimal(candle.close)),
                        'high': float(quotation_to_decimal(candle.high)),
                        'low': float(quotation_to_decimal(candle.low)),
                        'volume': candle.volume
                    })

            if not new_candles:
                logger.info(f"Нет новых данных для {ticker}")
                return

            save_candles_to_db(new_candles)
            return 

        except RequestError as e:
            logger.warning(f"Ошибка сети: {e}. Ретрай через 5 сек...")
            time.sleep(5)
            attempt += 1
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            return

    logger.error(f"Не удалось скачать {ticker} после {max_retries} попыток.")