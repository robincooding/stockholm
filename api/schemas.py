"""
FastAPI 요청/응답 Pydantic 모델 정의
"""

from pydantic import BaseModel
from typing import Optional


# === 요청 모델 ===
class StockRequest(BaseModel):
    ticker: str
    years: int = 3
    market: str = "us"


class AnalysisRequest(BaseModel):
    ticker: str
    years: int = 3
    market: str = "us"
    indicators: list[str] = ["sma", "ema", "rsi", "macd", "bollinger"]


class StrategyRequest(BaseModel):
    ticker: str
    years: int = 3
    market: str = "us"
    strategy: str = "sma"  # 'sma' / 'ema' / 'smaema' / 'rsimacd' / 'bollinger_rsi'
    short_window: int = 50
    long_window: int = 200


class BacktestRequest(BaseModel):
    ticker: str
    years: int = 3
    market: str = "us"
    strategy: str = "sma"
    short_window: int = 50
    long_window: int = 200
    initial_capital: float = 10_000_000
    stop_loss: float = 0.05
    take_profit: float = 0.15
    use_trailing_stop: bool = False
    trail_pct: float = 0.05


class PortfolioRequest(BaseModel):
    tickers: list[str]
    years: int = 3
    weight_method: str = "equal"  # 'equal' / 'risk_parity' / 'min_variance'
    rebalance_freq: str = "quarterly"
    initial_capital: float = 10_000_000


# === 응답 모델 ===
class SearchResult(BaseModel):
    code: str
    company: str
    score: float


class RegimeSummary(BaseModel):
    current_regime: str
    regime_score: float
    adx: float
    obv_slope: float
    stoch_k: float
    recommended: str


class BacktestResult(BaseModel):
    total_return: float
    market_return: float
    annual_return: float
    mdd: float
    win_rate: float
    total_trades: int
    final_value: float
    sharpe_ratio: float


class PortfolioResult(BaseModel):
    total_return: float
    annual_return: float
    volatility: float
    sharpe_ratio: float
    mdd: float
    final_value: float
    ticker_returns: dict[str, float]
    weights: dict[str, float]
    rebalance_freq: str
