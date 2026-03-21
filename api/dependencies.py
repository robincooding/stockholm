"""
FastAPI 공통 의존성 모듈
KRX 종목 목록을 앱 시작 시 한번만 로드해서 캐싱
"""

import pandas as pd
from functools import lru_cache
from data.krx_fetcher import fetch_krx_list


@lru_cache(maxsize=1)
def get_krx_df() -> pd.DataFrame:
    """
    KRX 종목 목록을 캐싱해서 반환합니다.
    앱 실행 중 최초 1회만 fetch하고 이후에는 캐시를 사용합니다.
    """
    return fetch_krx_list()
