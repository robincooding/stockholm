"""
이동평균선 크로스 전략을 구현한 클래스

지원하는 전략:
- SMA 크로스 (단기 SMA vs 장기 SMA)
- EMA 크로스 (단기 EMA vs 장기 EMA)
- SMA-EMA 크로스 (단기 SMA vs 단기 EMA)
"""

import pandas as pd
import numpy as np
from strategy.base import Strategy

class SMACrossover(Strategy):
    """
    단기/장기 SMA 골든크로스·데드크로스 전략 클래스.
    
    Parameters
    ----------
    short_window : int
        단기 SMA 기간 (기본값: 50일)
    long_window : int
        장기 SMA 기간 (기본값: 200일)
    """
    def __init__(self, short_window: int = 50, long_window: int = 200):
        super().__init__(name=f"SMA({short_window}/{long_window}) Crossover")
        self.short_window = short_window
        self.long_window = long_window
        
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        # 이동평균 계산
        df["sma_short"] = df["close"].rolling(self.short_window).mean()
        df["sma_long"]  = df["close"].rolling(self.long_window).mean()
        df.dropna(subset=["sma_short", "sma_long"], inplace=True)
        
        # 골든크로스: 단기가 장기를 위로 돌파 → 매수(1)
        # 데드크로스: 단기가 장기를 아래로 돌파 → 매도(-1)
        df["signal"] = 0
        df.loc[
            (df["sma_short"].shift(1) < df["sma_long"].shift(1)) &
            (df["sma_short"] > df["sma_long"]),
            "signal"
        ] = 1
        df.loc[
            (df["sma_short"].shift(1) > df["sma_long"].shift(1)) &
            (df["sma_short"] < df["sma_long"]),
            "signal"
        ] = -1

        # 포지션: 매수 신호 후 보유(1), 매도 신호 후 미보유(0)
        df["position"] = df["signal"].replace(-1, 0)
        df["position"] = df["position"].ffill().fillna(0)
        
        return df

class EMACrossover(Strategy):
    """
    단기/장기 EMA 골든크로스·데드크로스 전략 클래스.
    
    Parameters
    ----------
    short_window : int
        단기 EMA 기간 (기본값: 50일)
    long_window : int
        장기 EMA 기간 (기본값: 200일)
    """
    def __init__(self, short_window: int = 50, long_window: int = 200):
        super().__init__(name=f"EMA({short_window}/{long_window}) Crossover")
        self.short_window = short_window
        self.long_window = long_window
        
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        df["ema_short"] = df["close"].ewm(
            span=self.short_window, min_periods=self.short_window, adjust=False
        ).mean()
        df["ema_long"] = df["close"].ewm(
            span=self.long_window, min_periods=self.long_window, adjust=False
        ).mean()
        df.dropna(subset=["ema_short", "ema_long"], inplace=True)

        df["signal"] = 0
        df.loc[
            (df["ema_short"].shift(1) < df["ema_long"].shift(1)) &
            (df["ema_short"] > df["ema_long"]),
            "signal"
        ] = 1
        df.loc[
            (df["ema_short"].shift(1) > df["ema_long"].shift(1)) &
            (df["ema_short"] < df["ema_long"]),
            "signal"
        ] = -1

        df["position"] = df["signal"].replace(-1, 0)
        df["position"] = df["position"].ffill().fillna(0)

        return df
    
class SMAEMACrossover(Strategy):
    """
    단기 EMA가 단기 SMA를 돌파하는 크로스 전략 클래스.
    
    Parameters
    ----------
    window : int
        SMA/EMA 공통 기간 (기본값: 50일)
    """
    def __init__(self, window: int = 50):
        super().__init__(name=f"SMA-EMA({window}) Crossover")
        self.window = window
        
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        df["sma"] = df["close"].rolling(self.window).mean()
        df["ema"] = df["close"].ewm(
            span=self.window, min_periods=self.window, adjust=False
        ).mean()
        df.dropna(subset=["sma", "ema"], inplace=True)

        df["signal"] = 0
        df.loc[
            (df["ema"].shift(1) < df["sma"].shift(1)) &
            (df["ema"] > df["sma"]),
            "signal"
        ] = 1
        df.loc[
            (df["ema"].shift(1) > df["sma"].shift(1)) &
            (df["ema"] < df["sma"]),
            "signal"
        ] = -1

        df["position"] = df["signal"].replace(-1, 0)
        df["position"] = df["position"].ffill().fillna(0)

        return df
    