"""
백테스팅 관련 API 라우터.
"""

from fastapi import APIRouter, HTTPException
from api.schemas import BacktestRequest, BacktestResult
from api.dependencies import get_krx_df
from data.krx_fetcher import get_korean_stock
from data.yahoo_fetcher import get_us_stock
from strategy.ma_crossover import SMACrossover, EMACrossover, SMAEMACrossover
from strategy.combined import RSIMACDStrategy, BollingerRSIStrategy
from analysis.backtester import Backtester
from analysis.risk import apply_stop_loss_take_profit, apply_trailing_stop

router = APIRouter(prefix="/backtest", tags=["backtest"])

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


@router.post("/run", response_model=BacktestResult)
def run_backtest(req: BacktestRequest):
    """
    백테스팅을 실행하고 결과를 반환합니다.
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
        df_signals = strategy.generate_signals(df)

        # 리스크 관리 적용
        if req.use_trailing_stop:
            df_signals = apply_trailing_stop(
                df_signals,
                trail_pct=req.trail_pct,
            )
        else:
            df_signals = apply_stop_loss_take_profit(
                df_signals,
                stop_loss=req.stop_loss,
                take_profit=req.take_profit,
            )

        bt = Backtester(initial_capital=req.initial_capital)
        bt.run(df_signals)
        result = bt.report()

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/compare")
def compare_strategies(req: BacktestRequest):
    """
    모든 전략을 동시에 백테스팅해서 비교 결과를 반환합니다.
    """
    try:
        df = _fetch_df(req.ticker, req.market, req.years)
        results = []

        for name, strategy_fn in STRATEGY_MAP.items():
            strategy = strategy_fn(req)
            df_signals = strategy.generate_signals(df.copy())
            df_signals = apply_stop_loss_take_profit(
                df_signals,
                stop_loss=req.stop_loss,
                take_profit=req.take_profit,
            )
            bt = Backtester(initial_capital=req.initial_capital)
            bt.run(df_signals)
            r = bt.report()
            r["strategy"] = strategy.name
            results.append(r)

        return {
            "ticker": req.ticker,
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
