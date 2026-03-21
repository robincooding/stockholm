"""
KRX 상장기업 목록 조회 및 네이버 금융에서 시세 데이터를 가져오는 모듈
"""
import warnings

import ast
from datetime import datetime

import pandas as pd
import requests

# === Constants ===
KRX_URL = (
    "http://kind.krx.co.kr/corpgeneral/corpList.do"
    "?method=download&searchType=13"
)
NAVER_URL = "https://api.finance.naver.com/siseJson.naver"
DEFAULT_COUNT = 2500 # 약 10년치 일봉

# === KRX 종목 목록 ===
def fetch_krx_list() -> pd.DataFrame:
    """
    KRX에서 상장기업 목록을 가져와서 DataFrame으로 반환하는 함수.
    
    Returns
    -------
    pd.DataFrame
        columns: ['code', 'company']
        code는 6자리 zero-padded 문자열 (예: '005930')
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        krx = pd.read_html(KRX_URL, header=0, encoding="euc-kr")[0]
    krx = krx[["종목코드", "회사명"]].rename(columns={"종목코드": "code", "회사명": "company"})
    krx["code"] = krx["code"].astype(str).str.zfill(6)
    return krx.reset_index(drop=True)

# === NAVER 금융 시세 ===
def fetch_naver_ohlcv(code: str, count: int = DEFAULT_COUNT) -> pd.DataFrame:
    """
    네이버 금융 API를 통해 일봉 OHLCV 데이터를 가져와서 DataFrame으로 반환하는 함수.
    
    Parameters
    ----------
    code : str
        종목코드 (6자리 문자열, 예: '005930')
    count : int
        가져올 일수 (기본값 2500 ≈ 10년)

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
    params = {
        "symbol": code,
        "requestType": 0,
        "count": count,
        "startTime": datetime.today().strftime("%Y%m%d"),
        "timeframe": "day",
    }
    response = requests.get(NAVER_URL, params=params, timeout=10)
    response.raise_for_status()

    raw = ast.literal_eval(response.text.strip())
    if not raw or len(raw) < 2:
        raise ValueError(f"종목코드 '{code}'에 대한 데이터를 가져올 수 없습니다.")
    
    df = pd.DataFrame(raw[1:], columns=raw[0]) # 첫 행은 헤더

    col_map = {
        "날짜": "date",
        "시가": "open",
        "고가": "high",
        "저가": "low",
        "종가": "close",
        "거래량": "volume",
    }
    
    df = df.rename(columns=col_map)
    df = df[["date", "open", "high", "low", "close", "volume"]].copy()

    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    df = df.apply(pd.to_numeric, errors="coerce").dropna()
    df = df.astype(int)
    df = df.sort_index() # 오름차순 정렬

    return df

# === Utility Functions ===
def get_korean_stock(
    company: str,
    krx_df: pd.DataFrame | None = None,
    count: int = DEFAULT_COUNT
) -> pd.DataFrame:
    """
    회사명으로 KRX 종목코드 조회한 뒤 네이버 시세를 반환하는 함수.
    
    Parameters
    ----------
    company : str
        회사명 (정확히 일치해야 함 — 퍼지 검색은 utils.search 사용)
    krx_df : pd.DataFrame, optional
        미리 불러온 KRX 목록. None이면 새로 fetch.
    count : int
        가져올 일수.
    """
    if krx_df is None:
        krx_df = fetch_krx_list()
        
    matched = krx_df.loc[krx_df["company"] == company, "code"]
    if matched.empty:
        raise ValueError(
            f"'{company}'을(를) KRX 목록에서 찾을 수 없습니다."
            "utils.search.fuzzy_search_company()로 유사 종목을 검색해보세요."
        )
    
    code = matched.values[0]
    return fetch_naver_ohlcv(code, count=count)