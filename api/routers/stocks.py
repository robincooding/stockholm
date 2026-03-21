"""
종목 검색 및 시세 데이터 관련 API 라우터
"""

from fastapi import APIRouter, HTTPException, Depends
import pandas as pd

from api.schemas import StockRequest, SearchResult
from api.dependencies import get_krx_df
from data.krx_fetcher import get_korean_stock
from data.yahoo_fetcher import get_us_stock
from utils.search import fuzzy_search_company

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/search", response_model=list[SearchResult])
def search_stock(query: str, top_n: int = 5):
    """
    한국 주식 퍼지 종목명 검색.

    Parameters
    ----------
    query : str
        검색할 종목명 (부분 입력 가능)
    top_n : int
        반환할 최대 결과 수 (기본값: 5)
    """
    krx_df = get_krx_df()
    results = fuzzy_search_company(query, krx_df, top_n=top_n)
    if results.empty:
        raise HTTPException(
            status_code=404, detail=f"'{query}'에 대한 검색 결과가 없습니다."
        )
    return results.to_dict(orient="records")


@router.post("/ohlcv")
def get_ohlcv(req: StockRequest):
    """
    종목 OHLCV 데이터를 반환합니다.

    Parameters
    ----------
    req.ticker : str
        종목명(한국) 또는 티커(해외)
    req.market : str
        'kr' 또는 'us'
    req.years : int
        가져올 기간 (년)
    """
    try:
        if req.market == "kr":
            krx_df = get_krx_df()
            df = get_korean_stock(req.ticker, krx_df)
        else:
            df = get_us_stock(req.ticker, years=req.years)

        df = df.reset_index()
        df["date"] = df["date"].astype(str)

        return {
            "ticker": req.ticker,
            "market": req.market,
            "count": len(df),
            "data": df.to_dict(orient="records"),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/regime")
def get_market_regime(req: StockRequest):
    """
    종목의 현재 시장 국면을 반환합니다.
    """
    try:
        if req.market == "kr":
            krx_df = get_krx_df()
            df = get_korean_stock(req.ticker, krx_df)
        else:
            df = get_us_stock(req.ticker, years=req.years)

        from analysis.market_regime import detect_market_regime, get_regime_summary

        df = detect_market_regime(df)
        df.dropna(inplace=True)
        summary = get_regime_summary(df)

        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
