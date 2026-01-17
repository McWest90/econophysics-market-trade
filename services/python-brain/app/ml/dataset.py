import torch
import pandas as pd
import numpy as np
from torch.utils.data import Dataset
from sklearn.preprocessing import MinMaxScaler

class MarketDataset(Dataset):
    def __init__(self, df, lookback=60, forecast=10):
        """
        lookback: сколько минут смотрим назад (история)
        forecast: на сколько минут вперед предсказываем
        """
        self.lookback = lookback
        self.forecast = forecast

        df = df.copy() 
        

        df['log_ret'] = np.log(df['close'] / df['close'].shift(1)).fillna(0)
        df['log_vol'] = np.log(df['volume'] + 1).fillna(0)
        df['volatility'] = df['high'] - df['low']
        
        self.scaler_price = MinMaxScaler()
        self.scaler_vol = MinMaxScaler()
        
        data_price = self.scaler_price.fit_transform(df[['log_ret', 'volatility']].values)
        data_vol = self.scaler_vol.fit_transform(df[['log_vol']].values)
        
        self.data = np.hstack([data_price, data_vol])
        
        self.raw_volumes = df['volume'].values

    def __len__(self):
        return len(self.data) - self.lookback - self.forecast

    def __getitem__(self, idx):
        x = self.data[idx : idx + self.lookback]
        

        y_target = self.data[idx + self.lookback : idx + self.lookback + self.forecast, 1].mean()
        
        vol_future = self.raw_volumes[idx + self.lookback : idx + self.lookback + self.forecast].mean()
        
        return torch.tensor(x, dtype=torch.float32), \
               torch.tensor(y_target, dtype=torch.float32), \
               torch.tensor(vol_future, dtype=torch.float32)