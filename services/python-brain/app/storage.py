from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, BigInteger
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import exists
import pandas as pd

from src.config import DATA_DIR, logger

DB_PATH = DATA_DIR / "market_data.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Candle(Base):
    __tablename__ = "candles"

    ticker = Column(String, primary_key=True, index=True)
    time = Column(DateTime, primary_key=True, index=True)
    
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(BigInteger)
    
    volatility = Column(Float) 


def init_db():
    Base.metadata.create_all(bind=engine)
    logger.info(f"База данных подключена: {DB_PATH}")


def get_last_candle_time(ticker: str):
    session = SessionLocal()
    try:
        last_candle = session.query(Candle).filter(Candle.ticker == ticker).order_by(Candle.time.desc()).first()
        if last_candle:
            return last_candle.time
        return None
    finally:
        session.close()


def save_candles_to_db(candles_data: list):
    session = SessionLocal()
    try:
        objects = []
        for c in candles_data:
            candle = Candle(
                ticker=c['ticker'],
                time=c['time'],
                open=c['open'],
                high=c['high'],
                low=c['low'],
                close=c['close'],
                volume=c['volume'],
                volatility=c['high'] - c['low']
            )
            objects.append(candle)
        
        for obj in objects:
            session.merge(obj)
            
        session.commit()
        logger.info(f"Сохранено {len(objects)} свечей в БД")
    except Exception as e:
        logger.error(f"Ошибка записи в БД: {e}")
        session.rollback()
    finally:
        session.close()

def load_ticker_data(ticker: str) -> pd.DataFrame:
    """
    Загружает историю по тикеру из БД прямо в DataFrame.
    """
    query = f"SELECT * FROM candles WHERE ticker = '{ticker}' ORDER BY time ASC"
    
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
        
    if not df.empty:
        df['time'] = pd.to_datetime(df['time'])
        if df['time'].dt.tz is None:
            df['time'] = df['time'].dt.tz_localize('UTC')
        
    return df