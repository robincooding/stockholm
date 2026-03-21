"""
전략 신호 생성 관련 API 라우터
"""

from fastapi import APIRouter, HTTPException
from api.schemas import StrategyRequest
from api.dependencies import get_krx_df
from data.krx_fetcher import get_korean_stock
from data.yahoo_fetcher import get_us_stock
from strategy.ma_crossover import SMACrossover, EMACrossover, SMAEMACrossover
from strategy.combined import RSIMACDStrategy, BollingerRSIStrategy

router = APIRouter(prefix="/strategy", tags=["strategy"])

STRATEGY_MAP = {
    "sma": lambda req: SMACrossover(req.short_window, req.long_window),
    "ema": lambda req: EMACrossover(req.short_window, req.long_window),
    "smaema": lambda req: SMAEMACrossover(req.short_window),
    "rsimacd": lambda req: RSIMACDStrategy(),
    "bollinger_rsi": lambda req: BollingerRSIStrategy(),
}


def _fetch_df(ticker: str, market: str, years: int):
    if market == "kr":
        krx_df = get_krx_df()
        return get_korean_stock(ticker, krx_df)
    return get_us_stock(ticker, years=years)


@router.post("/signals")
def get_signals(req: StrategyRequest):
    """
    전략 신호(매수/매도)를 생성해서 반환합니다.
    """
    try:
        df = _fetch_df(req.ticker, req.market, req.years)

        strategy_fn = STRATEGY_MAP.get(req.strategy)
        if not strategy_fn:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 전략입니다. 가능한 값: {list(STRATEGY_MAP.keys())}",
            )

        strategy = strategy_fn(req)
        df = strategy.generate_signals(df)
        df = df.dropna().reset_index()
        df["date"] = df["date"].astype(str)

        # 신호 발생 날짜만 따로 추출
        signals = df[df["signal"] != 0][["date", "close", "signal"]].to_dict(
            orient="records"
        )

        return {
            "ticker": req.ticker,
            "strategy": strategy.name,
            "total_signals": len(signals),
            "signals": signals,
            "data": df.to_dict(orient="records"),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
