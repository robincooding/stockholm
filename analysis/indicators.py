"""
주식 DataFrame에 기술적 지표 컬럼을 추가하는 모듈

모든 함수는 DataFrame을 받아 지표 컬럼이 추가된 DataFrame을 반환
원본 DataFrame은 수정X (copy 사용).
"""

import numpy as np
import pandas as pd


# === SMA ===
def add_sma(df: pd.DataFrame, windows: list[int] = [20, 50, 200]) -> pd.DataFrame:
    """
    단순 이동평균(SMA)를 추가하는 함수.

    Parameters
    ----------
    df : pd.DataFrame
        OHLCV DataFrame (columns에 'close' 필요)
    windows : list[int]
        계산할 기간 리스트 (기본값: 20, 50, 200일)

    Returns
    -------
    pd.DataFrame
        SMA_{window} 컬럼이 추가된 DataFrame
        예: SMA_20, SMA_50, SMA_200
    """
    df = df.copy()
    for window in windows:
        df[f"SMA_{window}"] = df["close"].rolling(window=window).mean()
    return df


# === EMA ===
def add_ema(df: pd.DataFrame, windows: list[int] = [12, 26, 50, 200]) -> pd.DataFrame:
    """
    지수 이동평균(EMA)을 추가하는 함수.

    Parameters
    ----------
    df : pd.DataFrame
        OHLCV DataFrame (columns에 'close' 필요)
    windows : list[int]
        계산할 기간 리스트 (기본값: 12, 26, 50, 200일)

    Returns
    -------
    pd.DataFrame
        EMA_{window} 컬럼이 추가된 DataFrame
        예: EMA_12, EMA_26, EMA_50, EMA_200
    """
    df = df.copy()
    for window in windows:
        df[f"EMA_{window}"] = (
            df["close"].ewm(span=window, min_periods=window, adjust=False).mean()
        )
    return df


# === RSI ===
def add_rsi(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    """
    상대강도지수(RSI)를 추가하는 함수.

    Parameters
    ----------
    df : pd.DataFrame
        OHLCV DataFrame (columns에 'close' 필요)
    window : int
        RSI 계산 기간 (기본값: 14일)

    Returns
    -------
    pd.DataFrame
        RSI_{window} 컬럼이 추가된 DataFrame
        값 범위: 0 ~ 100
        70 이상 과매수, 30 이하 과매도
    """
    df = df.copy()
    delta = df["close"].diff()

    gain = delta.clip(lower=0)  # 상승분만
    loss = -delta.clip(upper=0)  # 하락분만 (양수로)

    avg_gain = gain.ewm(com=window - 1, min_periods=window).mean()
    avg_loss = loss.ewm(com=window - 1, min_periods=window).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    df[f"RSI_{window}"] = 100 - (100 / (1 + rs))
    return df


# === MACD ===
def add_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """
    MACD 지표를 추가하는 함수.

    Parameters
    ----------
    df : pd.DataFrame
        OHLCV DataFrame (columns에 'close' 필요)
    fast : int
        단기 EMA 기간 (기본값: 12)
    slow : int
        장기 EMA 기간 (기본값: 26)
    signal : int
        Signal 기간 (기본값: 9)

    Returns
    -------
    pd.DataFrame
        추가되는 컬럼:
        - MACD        : 단기 EMA - 장기 EMA
        - MACD_signal : MACD의 EMA (signal 기간)
        - MACD_hist   : MACD - Signal (히스토그램)
    """
    df = df.copy()
    ema_fast = df["close"].ewm(span=fast, min_periods=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, min_periods=slow, adjust=False).mean()

    df["MACD"] = ema_fast - ema_slow
    df["MACD_signal"] = (
        df["MACD"].ewm(span=signal, min_periods=signal, adjust=False).mean()
    )
    df["MACD_hist"] = df["MACD"] - df["MACD_signal"]
    return df


# === Bollinger Band ===
def add_bollinger(
    df: pd.DataFrame,
    window: int = 20,
    num_std: float = 2.0,
) -> pd.DataFrame:
    """
    볼린저밴드를 추가하는 함수.

    Parameters
    ----------
    df : pd.DataFrame
        OHLCV DataFrame (columns에 'close' 필요)
    window : int
        이동평균 기간 (기본값: 20일)
    num_std : float
        표준편차 배수 (기본값: 2.0)

    Returns
    -------
    pd.DataFrame
        추가되는 컬럼:
        - BB_mid   : 중간 밴드 (SMA)
        - BB_upper : 상단 밴드
        - BB_lower : 하단 밴드
        - BB_width : 밴드 폭 (상단 - 하단) / 중간
    """
    df = df.copy()
    mid = df["close"].rolling(window=window).mean()
    std = df["close"].rolling(window=window).std()

    df["BB_mid"] = mid
    df["BB_upper"] = mid + num_std * std
    df["BB_lower"] = mid - num_std * std
    df["BB_width"] = (df["BB_upper"] - df["BB_lower"]) / df["BB_mid"]
    return df


# === 로그 수익률 ===
def add_returns(df: pd.DataFrame) -> pd.DataFrame:
    """
    로그 수익률 및 누적 수익률을 추가하는 함수.

    Returns
    -------
    pd.DataFrame
        추가되는 컬럼:
        - returns  : 일별 로그 수익률
        - creturns : 누적 로그 수익률
    """
    df = df.copy()
    df["returns"] = np.log(df["close"] / df["close"].shift(1))
    df["creturns"] = df["returns"].cumsum().apply(np.exp)
    return df


# === 모든 지표 추가 ===
def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    모든 지표를 한번에 추가하는 함수.

    Parameters
    ----------
    df : pd.DataFrame
        OHLCV DataFrame

    Returns
    -------
    pd.DataFrame
        모든 지표 컬럼이 추가된 DataFrame
    """
    df = add_sma(df)
    df = add_ema(df)
    df = add_rsi(df)
    df = add_macd(df)
    df = add_bollinger(df)
    df = add_returns(df)
    return df
