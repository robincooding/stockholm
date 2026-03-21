"""
포트폴리오 관련 API 라우터
"""

from fastapi import APIRouter, HTTPException
from api.schemas import PortfolioRequest, PortfolioResult
from data.yahoo_fetcher import get_us_stock
from strategy.portfolio import (
    build_price_matrix,
    analyze_correlation,
    equal_weight,
    risk_parity_weight,
    min_variance_weight,
    backtest_portfolio,
)

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

WEIGHT_MAP = {
    "equal": equal_weight,
    "risk_parity": risk_parity_weight,
    "min_variance": min_variance_weight,
}


@router.post("/analyze")
def analyze_portfolio(req: PortfolioRequest):
    """
    포트폴리오 상관관계 분석 및 비중을 반환합니다.
    """
    try:
        data = {t: get_us_stock(t, years=req.years) for t in req.tickers}
        price_matrix = build_price_matrix(data)
        corr_result = analyze_correlation(price_matrix)

        # 비중 계산
        weight_fn = WEIGHT_MAP.get(req.weight_method)
        if not weight_fn:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 비중 방식입니다. 가능한 값: {list(WEIGHT_MAP.keys())}",
            )

        if req.weight_method == "equal":
            weights = weight_fn(req.tickers)
        else:
            weights = weight_fn(price_matrix)

        return {
            "tickers": req.tickers,
            "weights": weights,
            "avg_corr": corr_result["avg_corr"],
            "recent_avg_corr": corr_result["recent_avg_corr"],
            "summary": corr_result["summary"],
            "correlation": corr_result["correlation"].round(2).to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/backtest", response_model=PortfolioResult)
def run_portfolio_backtest(req: PortfolioRequest):
    """
    포트폴리오 백테스팅을 실행합니다.
    """
    try:
        data = {t: get_us_stock(t, years=req.years) for t in req.tickers}
        price_matrix = build_price_matrix(data)

        weight_fn = WEIGHT_MAP.get(req.weight_method)
        if not weight_fn:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 비중 방식입니다. 가능한 값: {list(WEIGHT_MAP.keys())}",
            )

        if req.weight_method == "equal":
            weights = weight_fn(req.tickers)
        else:
            weights = weight_fn(price_matrix)

        result = backtest_portfolio(
            data,
            weights,
            initial_capital=req.initial_capital,
            rebalance_freq=req.rebalance_freq,
        )

        return {
            **result,
            "weights": weights,
            "rebalance_freq": req.rebalance_freq,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
