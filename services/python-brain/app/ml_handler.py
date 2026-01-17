import torch
import numpy as np
from pathlib import Path
from .ml.model import PhysicsLSTMPredictor
from .ml.dataset import MarketDataset
from .config import logger

class AIModelService:
    def __init__(self):
        self.models = {}
        self.base_path = Path("/app/models")

    def load_model(self, ticker: str):
        """Загружает веса модели в память, если еще не загружены"""
        if ticker in self.models:
            return True

        model_path = self.base_path / f"{ticker}_pinn_model.pth"
        
        if not model_path.exists():
            logger.warning(f"Файл модели {model_path} не найден.")
            return False

        try:
            model = PhysicsLSTMPredictor()
            model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
            model.eval()
            
            self.models[ticker] = model
            logger.info(f"Модель для {ticker} загружена в память.")
            return True
        except Exception as e:
            logger.error(f"Ошибка загрузки модели {ticker}: {e}")
            return False

    def predict(self, ticker: str, df):
        """
        Берет DataFrame, готовит данные и делает прогноз
        """
        if ticker not in self.models:
            loaded = self.load_model(ticker)
            if not loaded:
                return None

        if len(df) < 80:
            return None
            
        df_tail = df.tail(80).copy()
        
        ds = MarketDataset(df_tail)
        
        if len(ds) < 1:
            return None
            
        x_tensor, _, _ = ds[0]
        
        model = self.models[ticker]
        with torch.no_grad():
            prediction = model(x_tensor.unsqueeze(0)).item()
            
        return prediction

ai_service = AIModelService()