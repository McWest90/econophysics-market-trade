from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd

from .loader import download_data
from .storage import load_ticker_data, init_db
from .physics import calculate_square_root_law
from .physics import calculate_deviations

from .ml_handler import ai_service

app = FastAPI(title="QuantCore Brain", version="1.0")

@app.on_event("startup")
def on_startup():
    init_db()

class AnalysisResponse(BaseModel):
    ticker: str
    alpha: float
    r2: float
    status: str

class TickerRequest(BaseModel):
    ticker: str
    days: int = 60


@app.get("/")
def health_check():
    return {"status": "active", "service": "Python Brain"}

@app.post("/collect", summary="Запустить сбор данных")
def trigger_collection(req: TickerRequest, background_tasks: BackgroundTasks):
    """
    Асинхронно запускает скачивание данных, чтобы не блокировать сервер.
    """
    background_tasks.add_task(download_data, req.ticker, req.days)
    return {"message": f"Сбор данных для {req.ticker} запущен в фоне."}

@app.get("/analyze/{ticker}", response_model=AnalysisResponse)
def get_physics_analysis(ticker: str):
    """
    Проверяет закон квадратного корня для тикера.
    """
    df = load_ticker_data(ticker)
    
    if df.empty:
        raise HTTPException(status_code=404, detail="Данные не найдены. Сначала вызовите /collect")

    res = calculate_square_root_law(df)
    
    if not res:
        raise HTTPException(status_code=400, detail="Недостаточно данных для анализа")

    status = "CONFIRMED" if res['r2'] > 0.9 else "ANOMALY"
    
    return {
        "ticker": ticker,
        "alpha": res['alpha'],
        "r2": res['r2'],
        "status": status
    }

@app.get("/predict/{ticker}")
def get_ai_prediction(ticker: str):
    """
    Возвращает прогноз волатильности от PINN (Нейросети).
    """
    df = load_ticker_data(ticker)
    
    if df.empty:
        raise HTTPException(status_code=404, detail="Нет исторических данных")

    ai_vol = ai_service.predict(ticker, df)
    
    if ai_vol is None:
        raise HTTPException(status_code=400, detail="Модель не найдена или мало данных")
    
    phys_res = calculate_square_root_law(df)
    current_z_score = 0.0
    
    if phys_res:
        pass 

    return {
        "ticker": ticker,
        "ai_volatility_prediction": ai_vol,
        "recommendation": "WATCH" if ai_vol > 0.1 else "SLEEP"
    }

@app.get("/indicators/{ticker}")
def get_zscore_history(ticker: str):
    """
    Возвращает историю Z-Score для графика.
    """
    df = load_ticker_data(ticker)
    if df.empty:
        raise HTTPException(status_code=404, detail="Нет данных")
    
    df_slice = df.tail(500).copy()

    model = calculate_square_root_law(df_slice)
    if not model:
        raise HTTPException(status_code=400, detail="Мало данных для физики")
        
    df_dev = calculate_deviations(df_slice, model)
    
    result = []
    for _, row in df_dev.iterrows():
        result.append({
            "time": row['time'],
            "z_score": row['z_score'] if not pd.isna(row['z_score']) else 0.0
        })
        
    return result