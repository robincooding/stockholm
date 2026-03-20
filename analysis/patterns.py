"""
지지선/저항선 및 추세선을 탐지하는 모듈

- 지지선/저항선: HDBSCAN 클러스터링 기반 자동 탐지
- 추세선: argelextrema로 극값(고점/저점) 탐지
"""

import numpy as np
import pandas as pd
from scipy.signal import argrelextrema
from sklearn.preprocessing import RobustScaler
import hdbscan

# === support/resistance line ===
def find_support_resistance(
    df: pd.DataFrame,
    min_cluster_size: int = 20,
    lookback_months: int = 7,
) -> dict:
    """
    HDBSCAN 클러스터링으로 지지선과 저항선을 탐지하는 함수.
    
    Parameters
    ----------
    df : pd.DataFrame
        OHLCV DataFrame (index: DatetimeIndex, columns에 'close' 필요)
    min_cluster_size : int
        하나의 횡보장을 구성하는 최소 기간 (기본값: 20일 ≈ 1개월)
    lookback_months : int
        분석할 최근 기간 (기본값: 7개월)

    Returns
    -------
    dict
        {
            'support':    [지지선 가격, ...],
            'resistance': [저항선 가격, ...],
            'df':         분석에 사용된 DataFrame (cluster 컬럼 포함)
        }
    """
    # 최근 N개월 데이터만 사용
    from dateutil.relativedelta import relativedelta
    start = df.index[-1] - relativedelta(months=lookback_months)
    df_recent = df.loc[df.index > start].copy()
    
    # 데이터 정규화
    scaler = RobustScaler()
    close_values = df_recent["close"].to_numpy().reshape(-1, 1)
    scaled = scaler.fit_transform(close_values)
    
    # HDBSCAN 클러스터링
    clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size)
    df_recent["cluster"] = clusterer.fit_predict(scaled)

    support    = []
    resistance = []
    
    for cluster_id in df_recent["cluster"].unique():
        if cluster_id == -1:  # 노이즈 포인트 제외
            continue
        cluster_data = df_recent[df_recent["cluster"] == cluster_id]["close"]
        support.append(round(float(cluster_data.min()), 2))
        resistance.append(round(float(cluster_data.max()), 2))

    return {
        "support":    sorted(set(support)),
        "resistance": sorted(set(resistance)),
        "df":         df_recent,
    }

# === Trendline ===
def find_trendlines(
    df: pd.DataFrame,
    order: int = 10,
) -> dict:
    """
    argrelextrema로 고점/저점을 탐지해서 추세선 데이터를 반환하는 함수.
    
    Parameters
    ----------
    df : pd.DataFrame
        OHLCV DataFrame (columns에 'high', 'low', 'close' 필요)
    order : int
        전후 N일 기준으로 극값 탐지 (기본값: 10일)

    Returns
    -------
    dict
        {
            'highs': {'dates': [...], 'prices': [...]},  # 고점들
            'lows':  {'dates': [...], 'prices': [...]},  # 저점들
        }
    """
    # 고점 탐지 (전후 order일 기준 최고점)
    high_idx = argrelextrema(df["high"].values, np.greater_equal, order=order)[0]
    # 저점 탐지 (전후 order일 기준 최저점)
    low_idx = argrelextrema(df["low"].values, np.less_equal, order=order)[0]
    
    return {
        "highs": {
            "dates":  df.index[high_idx].tolist(),
            "prices": df["close"].iloc[high_idx].tolist(),
        },
        "lows": {
            "dates":  df.index[low_idx].tolist(),
            "prices": df["close"].iloc[low_idx].tolist(),
        },
    }

# === Pivot Points ===
def find_pivots(
    df: pd.DataFrame,
    window: int = 10,
) -> dict:
    """
    슬라이딩 윈도우 방식으로 피벗 고점/저점을 탐지하는 함수.
    기존 SupportLine.py / ResistanceLine.py 로직을 통합
    
    Parameters
    ----------
    df : pd.DataFrame
        OHLCV DataFrame (columns에 'high', 'low' 필요)
    window : int
        피벗 탐지 윈도우 크기 (기본값: 10)

    Returns
    -------
    dict
        {
            'support_pivots':    [{'price': float, 'date': Timestamp}, ...],
            'resistance_pivots': [{'price': float, 'date': Timestamp}, ...],
        }
    """
    support_pivots = []
    resistance_pivots = []
    
    # 저점 피벗 (SupportLine)
    low_range = [df["low"].max()] * window
    date_range = [None] * window
    counter = 0
    last_pivot = 0
    
    for i, date in enumerate(df.index):
        current_min = min(low_range)
        value = round(float(df["low"][date]), 2)
        
        low_range = low_range[1:] + [value]
        date_range = date_range[1:] + [date]
        
        if current_min == min(low_range):
            counter += 1
        else:
            counter = 0
            
        if counter == window // 2:
            last_pivot = current_min
            pivot_date = date_range[low_range.index(last_pivot)]
            if pivot_date:
                support_pivots.append({
                    "price": last_pivot,
                    "date": pivot_date,
                })
                
    # 고점 피벗 (ResistanceLine)
    high_range = [0.0] * window
    date_range = [None] * window
    counter    = 0
    last_pivot = 0

    for i, date in enumerate(df.index):
        current_max = max(high_range)
        value = round(float(df["high"][date]), 2)

        high_range = high_range[1:] + [value]
        date_range = date_range[1:] + [date]

        if current_max == max(high_range):
            counter += 1
        else:
            counter = 0

        if counter == window // 2:
            last_pivot = current_max
            pivot_date = date_range[high_range.index(last_pivot)]
            if pivot_date:
                resistance_pivots.append({
                    "price": last_pivot,
                    "date":  pivot_date,
                })
                
    return {
        "support_pivots":    support_pivots,
        "resistance_pivots": resistance_pivots,
    }