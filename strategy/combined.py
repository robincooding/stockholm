"""
여러 지표를 조합한 복합 신호 전략 구현 모듈.

전략 목록:
- RSIMACDStrategy   : RSI + MACD + SMA 조합
- BollingerRSI      : 볼린저밴드 + RSI 조합
"""

import pandas as pd
import numpy as np
from strategy.base import Strategy
from analysis.indicators import add_sma, add_rsi, add_macd, add_bollinger


class RSIMACDStrategy(Strategy):
    """
    RSI + MACD + SMA 조합 전략 클래스.

    매수 조건 (3가지 동시 충족):
      1. RSI < rsi_oversold  (과매도)
      2. MACD > MACD_signal  (상승 모멘텀)
      3. 종가 > SMA_window   (중기 상승 추세)

    매도 조건 (하나라도 충족):
      1. RSI > rsi_overbought (과매수)
      2. MACD < MACD_signal   (하락 모멘텀)

    Parameters
    ----------
    rsi_window : int
        RSI 계산 기간 (기본값: 14)
    rsi_oversold : float
        RSI 과매도 기준 (기본값: 35)
    rsi_overbought : float
        RSI 과매수 기준 (기본값: 70)
    sma_window : int
        추세 필터용 SMA 기간 (기본값: 50)
    """

    def __init__(
        self,
        rsi_window: int = 14,
        rsi_oversold: float = 35,
        rsi_overbought: float = 70,
        sma_window: int = 50,
    ):
        super().__init__(name=f"RSI+MACD+SMA({sma_window})")
        self.rsi_window = rsi_window
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.sma_window = sma_window

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_rsi(df, window=self.rsi_window)
        df = add_macd(df)
        df = add_sma(df, windows=[self.sma_window])
        df.dropna(inplace=True)

        rsi_col = f"RSI_{self.rsi_window}"
        sma_col = f"SMA_{self.sma_window}"

        df["signal"] = 0

        # MACD 크로스 방향 감지
        macd_cross_up = (df["MACD"].shift(1) < df["MACD_signal"].shift(1)) & (
            df["MACD"] > df["MACD_signal"]
        )

        macd_cross_down = (df["MACD"].shift(1) > df["MACD_signal"].shift(1)) & (
            df["MACD"] < df["MACD_signal"]
        )

        # 매수: MACD 상승 크로스 + RSI 50이하
        buy_cond = macd_cross_up & (df[rsi_col] < 50)

        # 매도: RSI 과매수 OR MACD 하락 크로스
        sell_cond = (df[rsi_col] > self.rsi_overbought) | macd_cross_down

        df.loc[buy_cond, "signal"] = 1
        df.loc[sell_cond, "signal"] = -1

        # 포지션 없을 때 매도 신호 무시
        position = 0
        for idx in df.index:
            sig = df.loc[idx, "signal"]
            if sig == 1:
                position = 1
            elif sig == -1 and position == 0:
                df.loc[idx, "signal"] = 0
            elif sig == -1 and position == 1:
                position = 0

        df["position"] = df["signal"].replace(-1, 0)
        df["position"] = df["position"].ffill().fillna(0)

        return df


class BollingerRSIStrategy(Strategy):
    """
    볼린저밴드 + RSI 조합 전략 클래스.

    매수 조건 (2가지 동시 충족):
      1. 종가 < BB 하단 (밴드 하단 터치)
      2. RSI < rsi_oversold (과매도 확인)

    매도 조건 (2가지 동시 충족):
      1. 종가 > BB 상단 (밴드 상단 터치)
      2. RSI > rsi_overbought (과매수 확인)

    Parameters
    ----------
    bb_window : int
        볼린저밴드 기간 (기본값: 20)
    bb_std : float
        볼린저밴드 표준편차 배수 (기본값: 2.0)
    rsi_window : int
        RSI 기간 (기본값: 14)
    rsi_oversold : float
        RSI 과매도 기준 (기본값: 40)
    rsi_overbought : float
        RSI 과매수 기준 (기본값: 60)
    """

    def __init__(
        self,
        bb_window: int = 20,
        bb_std: float = 2.0,
        rsi_window: int = 14,
        rsi_oversold: float = 40,
        rsi_overbought: float = 60,
    ):
        super().__init__(name=f"Bollinger+RSI({bb_window}/{rsi_window})")
        self.bb_window = bb_window
        self.bb_std = bb_std
        self.rsi_window = rsi_window
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_bollinger(df, window=self.bb_window, num_std=self.bb_std)
        df = add_rsi(df, window=self.rsi_window)
        df = add_sma(df, windows=[200])  # 장기 추세 필터
        df.dropna(inplace=True)

        rsi_col = f"RSI_{self.rsi_window}"

        df["signal"] = 0

        # 매수: BB 하단 터치 + RSI 과매도 + 장기 상승 추세 (SMA 200 위)
        buy_cond = (
            (df["close"] < df["BB_lower"])
            & (df[rsi_col] < self.rsi_oversold)
            & (df["close"] > df["SMA_200"])  # 하락 추세에서는 매수 안 함
        )

        # 매도: BB 상단 터치 + RSI 과매수
        sell_cond = (df["close"] > df["BB_upper"]) & (df[rsi_col] > self.rsi_overbought)

        df.loc[buy_cond, "signal"] = 1
        df.loc[sell_cond, "signal"] = -1

        # 연속 신호 제거
        df["signal"] = df["signal"].where(df["signal"] != df["signal"].shift(1), 0)

        df["position"] = df["signal"].replace(-1, 0)
        df["position"] = df["position"].ffill().fillna(0)

        return df
