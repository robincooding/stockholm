"""
Yahoo Finance에서 해외(및 한국) 주식 OHLCV 데이터를 가져오는 모듈
"""

import datetime

import pandas as pd
import yfinance as yf

# === Constants ===
DEFAULT_PERIOD_YEARS = 10

# === 핵심 fetch 함수 ===
def fetch_yahoo_ohlcv(
    ticker: str,
    start: datetime.date | str | None = None,
    end: datetime.date | str | None = None,
    years: int = DEFAULT_PERIOD_YEARS,
) -> pd.DataFrame:
    """
    Yahoo Finance에서 일봉 OHLCV 데이터를 가져와서 DataFrame으로 반환하는 함수.
    
    Parameters
    ----------
    ticker : str
        야후 파이낸스 티커 (예: 'AAPL', '005930.KS')
    start : date | str | None
        시작일. None이면 end 기준 years년 전.
    end : date | str | None
        종료일. None이면 오늘.
    years : int
        start가 None일 때 사용할 기간 (연 단위).

    Returns
    -------
    pd.DataFrame
        index : DatetimeIndex (날짜, 오름차순)
        columns : ['open', 'high', 'low', 'close', 'volume']

    Raises
    ------
    ValueError
        데이터를 가져오지 못했을 때.
    """
    if end is None:
        end = datetime.date.today()
    if isinstance(end, str):
        end = datetime.date.fromisoformat(end)
        
    if start is None:
        start = datetime.date(end.year - years, end.month, end.today)
    if isinstance(start, str):
        start = datetime.date.fromisoformat(start)
        
    raw = pd.DataFrame = yf.download(
        ticker,
        start=start,
        end=end,
        auto_adjust=True, # 수정주가 사용
        progress=False,
    )
    
    if raw.empty:
        raise ValueError(
            f"티커 '{ticker}'에 대한 데이터를 가져올 수 없습니다."
            "티커 심볼을 확인해주세요."
        )
    
    # yfinance 0.2+는 MultiIndex 컬럼을 반환하는 경우가 있어서 평탄화
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
        
    df = raw[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.columns = ["open", "high", "low", "close", "volume"]
    df.index.name = "date"
    df = df.sort_index()
    
    return df


# === Utility Functions ===
def get_us_stock(ticker: str, years: int = DEFAULT_PERIOD_YEARS) -> pd.DataFrame:
    """ 미국 주식 시세를 반환하는 함수. 티커 그대로 사용. (예: 'AAPL')"""
    return fetch_yahoo_ohlcv(ticker.upper(), years=years)

def get_korean_stock_yahoo(
    ticker: str,
    years: int = DEFAULT_PERIOD_YEARS
) -> pd.DataFrame:
    """
    Yahoo Finance로 한국 주식 시세를 반환하는 함수.
    티커에 '.KS'(코스피) 또는 '.KQ'(코스닥) 접미사 자동으로 붙임.
    
    Parameters
    ----------
    ticker : str
        종목코드 6자리 숫자 문자열 (예: '005930')
    """
    for suffix in (".KS", ".KQ"):
        try:
            return fetch_yahoo_ohlcv(ticker + suffix, years=years)
        except ValueError:
            continue
    raise ValueError(
        f"'{ticker}'을(를) Yahoo Finance에서 찾을 수 없습니다."
        "코스피(.KS) / 코스닥(.KQ) 모두 실패했습니다."
    )