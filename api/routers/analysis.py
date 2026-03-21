"""
기술적 지표 및 패턴 분석 관련 API 라우터
"""

from fastapi import APIRouter, HTTPException
from api.schemas import AnalysisRequest
from api.dependencies import get_krx_df
from data.krx_fetcher import get_korean_stock
from data.yahoo_fetcher import get_us_stock
from analysis.indicators import (
    add_sma,
    add_ema,
    add_rsi,
    add_macd,
    add_bollinger,
    add_returns,
)
from analysis.patterns import find_support_resistance, find_trendlines

router = APIRouter(prefix="/analysis", tags=["analysis"])


def _fetch_df(ticker: str, market: str, years: int):
    """데이터 fetch 공통 헬퍼."""
    if market == "kr":
        krx_df = get_krx_df()
        return get_korean_stock(ticker, krx_df)
    return get_us_stock(ticker, years=years)


@router.post("/indicators")
def get_indicators(req: AnalysisRequest):
    """
    요청한 지표를 계산해서 반환합니다.

    req.indicators 리스트에 포함된 지표만 계산합니다.
    가능한 값: 'sma', 'ema', 'rsi', 'macd', 'bollinger', 'returns'
    """
    try:
        df = _fetch_df(req.ticker, req.market, req.years)

        if "sma" in req.indicators:
            df = add_sma(df)
        if "ema" in req.indicators:
            df = add_ema(df)
        if "rsi" in req.indicators:
            df = add_rsi(df)
        if "macd" in req.indicators:
            df = add_macd(df)
        if "bollinger" in req.indicators:
            df = add_bollinger(df)
        if "returns" in req.indicators:
            df = add_returns(df)

        df = df.dropna().reset_index()
        df["date"] = df["date"].astype(str)

        return {
            "ticker": req.ticker,
            "indicators": req.indicators,
            "count": len(df),
            "data": df.to_dict(orient="records"),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/patterns")
def get_patterns(req: AnalysisRequest):
    """
    지지선/저항선 및 추세선을 반환합니다.
    """
    try:
        df = _fetch_df(req.ticker, req.market, req.years)

        # 지지선 / 저항선
        sr = find_support_resistance(df)
        # 추세선
        tl = find_trendlines(df)

        # 날짜 직렬화
        highs_dates = [str(d) for d in tl["highs"]["dates"]]
        lows_dates = [str(d) for d in tl["lows"]["dates"]]

        return {
            "ticker": req.ticker,
            "support": sr["support"],
            "resistance": sr["resistance"],
            "trendlines": {
                "highs": {
                    "dates": highs_dates,
                    "prices": tl["highs"]["prices"],
                },
                "lows": {
                    "dates": lows_dates,
                    "prices": tl["lows"]["prices"],
                },
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
