"""
시장 국면(상승/하락/횡보) 감지 및 선행 지표 계산 모듈

선행 지표:
- ADX       : 추세 강도
- OBV       : 거래량 기반 매집/분산
- Stochastic: 단기 과매수/과매도
"""

import pandas as pd
import numpy as np


# === ADX (평균 방향 지수) ===
def add_adx(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    """
    ADX (Average Directional Index) 추세 강도 지표를 추가하는 함수.

    ADX > 25 : 강한 추세
    ADX < 20 : 추세 없음 (횡보)

    Parameters
    ----------
    df : pd.DataFrame
        OHLCV DataFrame
    window : int
        ADX 계산 기간 (기본값: 14)

    Returns
    -------
    pd.DataFrame
        추가되는 컬럼:
        - ADX    : 추세 강도 (0~100)
        - DI_pos : 양방향 지표
        - DI_neg : 음방향 지표
    """
    df = df.copy()

    high = df["high"]
    low = df["low"]
    close = df["close"]

    # True Range
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Directional Movement
    dm_pos = high - high.shift(1)
    dm_neg = low.shift(1) - low

    dm_pos = dm_pos.where((dm_pos > dm_neg) & (dm_pos > 0), 0)
    dm_neg = dm_neg.where((dm_neg > dm_pos) & (dm_neg > 0), 0)

    # Smoothed
    atr = tr.ewm(span=window, adjust=False).mean()
    di_pos = 100 * dm_pos.ewm(span=window, adjust=False).mean() / atr
    di_neg = 100 * dm_neg.ewm(span=window, adjust=False).mean() / atr

    dx = 100 * (di_pos - di_neg).abs() / (di_pos + di_neg).replace(0, np.nan)
    df["ADX"] = dx.ewm(span=window, adjust=False).mean()
    df["DI_pos"] = di_pos
    df["DI_neg"] = di_neg

    return df


# === OBV(거래량 균형 지표) ===
def add_obv(df: pd.DataFrame) -> pd.DataFrame:
    """
    OBV (On-Balance Volume) 거래량 기반 매집/분산 지표를 추가하는 함수.

    OBV 상승 + 가격 상승 → 강한 상승 추세 확인
    OBV 상승 + 가격 횡보 → 매집 중 (선행 신호)
    OBV 하락 + 가격 횡보 → 분산 중 (하락 선행 신호)

    Returns
    -------
    pd.DataFrame
        추가되는 컬럼:
        - OBV       : 누적 거래량
        - OBV_slope : OBV 기울기 (추세 방향)
    """
    df = df.copy()

    direction = np.sign(df["close"].diff()).fillna(0)
    df["OBV"] = (direction * df["volume"]).cumsum()

    # MA 대비 상대 변화율로 안정화
    obv_ma = df["OBV"].rolling(20).mean()
    df["OBV_slope"] = (df["OBV"] - obv_ma.shift(10)) / obv_ma.shift(10).abs().replace(
        0, np.nan
    )

    return df


# === Stochastic Oscillator ===
def add_stochastic(
    df: pd.DataFrame,
    k_window: int = 14,
    d_window: int = 3,
) -> pd.DataFrame:
    """
    Stochastic Oscillator를 추가하는 함수.

    RSI보다 빠르게 반응하는 단기 과매수/과매도 지표

    %K > 80 : 과매수
    %K < 20 : 과매도
    %K가 %D를 위로 크로스 → 매수 신호

    Parameters
    ----------
    df : pd.DataFrame
        OHLCV DataFrame
    k_window : int
        %K 기간 (기본값: 14)
    d_window : int
        %D 기간 (기본값: 3)

    Returns
    -------
    pd.DataFrame
        추가되는 컬럼:
        - STOCH_K : Fast Stochastic
        - STOCH_D : Slow Stochastic (신호선)
    """
    df = df.copy()

    lowest_low = df["low"].rolling(k_window).min()
    highest_high = df["high"].rolling(k_window).max()

    df["STOCH_K"] = 100 * (
        (df["close"] - lowest_low) / (highest_high - lowest_low).replace(0, np.nan)
    )
    df["STOCH_D"] = df["STOCH_K"].rolling(d_window).mean()

    return df


# === 시장 국면 감지 ===
def detect_market_regime(
    df: pd.DataFrame,
    short_window: int = 50,
    long_window: int = 200,
    slope_window: int = 20,
) -> pd.DataFrame:
    """
    SMA 기울기 기반으로 시장 국면을 감지하는 함수.

    Parameters
    ----------
    df : pd.DataFrame
        OHLCV DataFrame
    short_window : int
        단기 SMA 기간 (기본값: 50)
    long_window : int
        장기 SMA 기간 (기본값: 200)
    slope_window : int
        기울기 계산 기간 (기본값: 20)

    Returns
    -------
    pd.DataFrame
        추가되는 컬럼:
        - regime       : 'bull' / 'bear' / 'range'
        - regime_score : -1 (하락) ~ 1 (상승) 연속값
    """
    df = df.copy()

    sma_short = df["close"].rolling(short_window).mean()
    sma_long = df["close"].rolling(long_window).mean()

    # 기울기: (현재값 - N일 전 값) / N일 전 값
    slope_short = (sma_short - sma_short.shift(slope_window)) / sma_short.shift(
        slope_window
    )
    slope_long = (sma_long - sma_long.shift(slope_window)) / sma_long.shift(
        slope_window
    )
    trend_score = (slope_short + slope_long) / 2

    # Normalize ADX (-1 ~ 1)
    # non-linear normalization with tanh
    df = add_adx(df)
    adx_direction = np.sign(df["DI_pos"] - df["DI_neg"])
    adx_norm = adx_direction * np.tanh(df["ADX"] / 25)
    adx_norm = adx_norm.clip(-1, 1)

    # Normalize OBV (-1 ~ 1)
    df = add_obv(df)
    obv_norm = df["OBV_slope"].clip(-1, 1)

    # Normalize Stochastic (-1 ~ 1)
    df = add_stochastic(df)
    stoch_norm = (df["STOCH_K"] - 50) / 50
    stoch_norm = stoch_norm.clip(-1, 1)

    # 종합 regime scores
    df["regime_score"] = (
        0.4 * trend_score + 0.2 * adx_norm + 0.2 * obv_norm + 0.2 * stoch_norm
    )

    # regime type
    conditions = [
        (sma_short > sma_long)
        & (slope_short > 0)
        & (slope_long > 0)
        & (df["regime_score"] > 0.3),  # 상승장 (bull market)
        (sma_short < sma_long)
        & (slope_short < 0)
        & (slope_long < 0)
        & (df["regime_score"] < -0.3),  # 하락장 (bear market)
        (df["regime_score"] > 0.1),  # 약한 상승장 (weak bull market)
        (df["regime_score"] < -0.1),  # 약한 하락장 (weak bear market)
    ]
    choices = ["bull", "bear", "weak_bull", "weak_bear"]
    df["regime"] = np.select(conditions, choices, default="range")

    return df


# === market regime 적응형 전략 선택 ===
def get_regime_summary(df: pd.DataFrame) -> dict:
    """
    최근 시장 국면을 요약하는 함수

    Returns
    -------
    dict
        {
            'current_regime'  : 현재 국면 ('bull'/'bear'/'range'),
            'regime_score'    : 국면 점수 (-1 ~ 1),
            'adx'             : ADX 값 (추세 강도),
            'obv_slope'       : OBV 기울기,
            'stoch_k'         : 현재 Stochastic %K,
            'recommended'     : 추천 전략,
        }
    """
    latest = df.iloc[-1]

    regime = latest.get("regime", "range")
    adx = latest.get("ADX", 0)

    # 추천 전략 결정
    if regime == "bull" and adx > 25:
        recommended = "SMA/EMA 크로스 전략 (강한 상승 추세)"
    elif regime in ("bull", "weak_bull"):
        recommended = "RSI+MACD 조합 전략 (약한 상승 추세)"
    elif regime == "bear" and adx > 25:
        recommended = "현금 보유 권장 (강한 하락 추세)"
    elif regime in ("bear", "weak_bear"):
        recommended = "Bollinger+RSI 전략(약한 하락 - 반등 대기)"
    else:
        recommended = "Bollinger+RSI 전략 (횡보장)"

    return {
        "current_regime": regime,
        "regime_score": round(float(latest.get("regime_score", 0)), 4),
        "adx": round(float(adx), 2),
        "obv_slope": round(float(latest.get("OBV_slope", 0)), 4),
        "stoch_k": round(float(latest.get("STOCH_K", 0)), 2),
        "recommended": recommended,
    }
