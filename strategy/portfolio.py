"""
다중 종목 포트폴리오 전략 모듈

기능:
- 동일 비중 포트폴리오
- 리스크 패리티 포트폴리오 (위험 기여도(RC) 동일화)
- 최소 분산 포트폴리오
- 상관관계 분석 (전체 + 최근 롤링)
- 리밸런싱 백테스팅
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from analysis.backtester import Backtester


# === 데이터 수집 헬퍼 ===
def build_price_matrix(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    여러 종목의 종가를 하나의 DataFrame으로 합치는 함수.

    Parameters
    ----------
    data : dict[str, pd.DataFrame]
        {'티커': OHLCV DataFrame} 형태의 딕셔너리

    Returns
    -------
    pd.DataFrame
        index: DatetimeIndex
        columns: 티커명
        공통 날짜만 포함 (inner join)
    """
    prices = {ticker: df["close"] for ticker, df in data.items()}
    return pd.DataFrame(prices).dropna()


# === 상관관계 분석 ===
def analyze_correlation(
    price_matrix: pd.DataFrame,
    rolling_window: int = 252,
) -> dict:
    """
    종목 간 전체 및 최근 롤링 상관관계를 분석하는 함수.

    Parameters
    ----------
    price_matrix : pd.DataFrame
        build_price_matrix() 반환값
    rolling_window : int
        롤링 상관관계 계산 기간 (기본값 252일 = 1년)

    Returns
    -------
    dict
        {
            'correlation'     : 전체 기간 상관계수 행렬,
            'avg_corr'        : 전체 평균 상관계수,
            'recent_avg_corr' : 최근 N일 평균 상관 계수,
            'summary'         : 분산 효과 평가,
        }
    """
    returns = price_matrix.pct_change().dropna()

    # 전체 기간 상관계수
    corr = returns.corr()
    mask = np.ones(corr.shape, dtype=bool)
    np.fill_diagonal(mask, False)
    avg_corr = corr.values[mask].mean()

    # 최근 롤링 상관계수
    recent_returns = returns.iloc[-rolling_window:]
    recent_corr = recent_returns.corr()
    recent_avg_corr = recent_corr.values[mask].mean()

    return {
        "correlation": corr,
        "recent_corr": recent_corr,
        "avg_corr": round(avg_corr, 4),
        "recent_avg_corr": round(recent_avg_corr, 4),
        "summary": (
            "분산 효과 우수"
            if avg_corr < 0.5
            else "분산 효과 보통" if avg_corr < 0.7 else "분산 효과 낮음"
        ),
    }


# === 포트폴리오 비중 계산 ===
def equal_weight(tickers: list[str]) -> dict[str, float]:
    """
    동일 비중 포트폴리오 비중을 반환하는 함수.

    Parameters
    ----------
    tickers : list[str]
        종목 리스트

    Returns
    -------
    dict[str, float]
        {'티커': 비중} (합계 = 1.0)
    """
    weight = 1.0 / len(tickers)
    return {ticker: round(weight, 4) for ticker in tickers}


def risk_parity_weight(
    price_matrix: pd.DataFrame,
    min_weight: float = 0.01,
    max_weight: float = 0.50,
) -> dict[str, float]:
    """
    리스크 패리티 비중을 계산하는 함수.
    각 종목의 리스크 기여도(RC)가 동일하도록 최적화함

    RC(w_i) = w_i x (∂σ/∂w_i) → 모든 종목 동일하게

    Parameters
    ----------
    price_matrix : pd.DataFrame
        build_price_matrix() 반환값
    min_weight : float
        종목별 최소 비중 (기본값: 1%)
    max_weight : float
        종목별 최대 비중 (기본값: 50%)

    Returns
    -------
    dict[str, float]
        {'티커': 비중} (합계 = 1.0)
    """
    returns = price_matrix.pct_change().dropna()
    cov = returns.cov().values
    n = len(price_matrix.columns)

    def risk_contribution(w):
        vol = np.sqrt(w.T @ cov @ w)
        mrc = cov @ w / vol  # Marginal Risk Contribution
        return w * mrc  # Risk Contribution

    def objective(w):
        rc = risk_contribution(w)
        return np.std(rc)  # RC 표준편차 최소화 → 모두 동일하게

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    bounds = [(min_weight, max_weight)] * n
    init_w = np.ones(n) / n

    result = minimize(
        objective,
        init_w,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1000, "ftol": 1e-9},
    )

    weights = result.x if result.success else init_w
    weights = weights / weights.sum()  # re-normalize

    return {
        ticker: round(float(w), 4) for ticker, w in zip(price_matrix.columns, weights)
    }


def min_variance_weight(price_matrix: pd.DataFrame) -> dict[str, float]:
    """
    최소 분산 포트폴리오 비중을 계산하는 함수.
    전체 포트폴리오 변동성을 최소화하는 비중을 반환함

    Parameters
    ----------
    price_matrix : pd.DataFrame
        build_price_matrix() 반환값

    Returns
    -------
    dict[str, float]
        {'티커': 비중} (합계 = 1.0)
    """
    returns = price_matrix.pct_change().dropna()
    cov = returns.cov().values
    n = len(price_matrix.columns)

    # 역공분산(Inverse Covariance) 행렬 기반 최소 분산 해
    try:
        inv_cov = np.linalg.inv(cov)
        ones = np.ones(n)
        weights = inv_cov @ ones / (ones @ inv_cov @ ones)
        weights = np.clip(weights, 0, 1)  # 음수 비중 제거(공매도 방지)
        weights = weights / weights.sum()  # re-normalize
    except np.linalg.LinAlgError:
        # 역행렬 계산 실패 시 동일 비중으로 fallback
        weights = np.ones(n) / n

    return {
        ticker: round(float(w), 4) for ticker, w in zip(price_matrix.columns, weights)
    }


# === Portfolio Backtesting with Rebalancing ===
def backtest_portfolio(
    data: dict[str, pd.DataFrame],
    weights: dict[str, float],
    initial_capital: float = 10_000_000,
    rebalance_freq: str = "quarterly",
) -> dict:
    """
    포트폴리오 백테스팅을 실행하는 함수. (리밸런싱 지원)

    Parameters
    ----------
    data : dict[str, pd.DataFrame]
        {'티커': OHLCV DataFrame} 딕셔너리
    weights : dict[str, float]
        {'티커': 목표 비중} 딕셔너리
    initial_capital : float
        초기 투자금 (기본값: 10,000,000)
    rebalance_freq : str
        리밸런싱 주기: 'daily' / 'monthly' / 'quarterly' / 'annual' / 'none'

    Returns
    -------
    dict
        {
            'total_return'    : 총 수익률 (%),
            'annual_return'   : 연간 수익률 (%),
            'volatility'      : 연간 변동성 (%),
            'sharpe_ratio'    : 샤프 지수,
            'mdd'             : 최대 낙폭 (%),
            'final_value'     : 최종 자산,
            'ticker_returns'  : 종목별 수익률,
            'portfolio_value' : 포트폴리오 가치 시계열,
        }
    """
    price_matrix = build_price_matrix(data)
    tickers = list(price_matrix.columns)
    weight_array = np.array([weights.get(t, 0) for t in price_matrix.columns])

    # 리밸런싱 날짜 설정
    freq_map = {
        "daily": "D",
        "monthly": "ME",
        "quarterly": "QE",
        "annual": "YE",
    }

    if rebalance_freq == "none":
        rebalance_dates = set()
    else:
        freq = freq_map.get(rebalance_freq, "QE")
        rebalance_dates = set(price_matrix.resample(freq).last().index)

    # 포트폴리오 시뮬레이션
    portfolio_values = []
    current_weights = weight_array.copy()
    portfolio_value = initial_capital

    prev_prices = price_matrix.iloc[0].values

    for date, row in price_matrix.iterrows():
        current_prices = row.values

        # 일별 수익률 반영
        daily_returns = current_prices / prev_prices - 1
        current_weights = current_weights * (1 + daily_returns)
        current_weights = current_weights / current_weights.sum()  # 정규화

        portfolio_value *= 1 + np.sum(current_weights * daily_returns)
        portfolio_values.append(portfolio_value)

        # 리밸런싱
        if date in rebalance_dates:
            current_weights = weight_array.copy()

        prev_prices = current_prices

    portfolio_series = pd.Series(portfolio_values, index=price_matrix.index)
    cumulative = portfolio_series / initial_capital

    # 성과 지표
    daily_rets = portfolio_series.pct_change().dropna()
    total_return = (cumulative.iloc[-1] - 1) * 100
    years = len(price_matrix) / 252
    annual_return = ((1 + total_return / 100) ** (1 / years) - 1) * 100
    volatility = daily_rets.std() * np.sqrt(252) * 100
    sharpe = (
        daily_rets.mean() / daily_rets.std() * np.sqrt(252)
        if daily_rets.std() != 0
        else 0
    )

    rolling_max = cumulative.cummax()
    mdd = ((cumulative - rolling_max) / rolling_max).min() * 100

    ticker_returns = {
        ticker: round(
            (price_matrix[ticker].iloc[-1] / price_matrix[ticker].iloc[0] - 1) * 100, 2
        )
        for ticker in tickers
    }

    return {
        "total_return": round(total_return, 2),
        "annual_return": round(annual_return, 2),
        "volatility": round(volatility, 2),
        "sharpe_ratio": round(sharpe, 2),
        "mdd": round(mdd, 2),
        "final_value": round(portfolio_series.iloc[-1], 0),
        "ticker_returns": ticker_returns,
        "portfolio_value": portfolio_series,
        "rebalance_freq": rebalance_freq,
    }


# === Portfolio Report ===
def portfolio_report(
    result: dict,
    weights: dict[str, float],
    strategy_name: str = "포트폴리오",
    initial_capital: float = 10_000_000,
) -> None:
    """포트폴리오 백테스팅 결과를 출력합니다."""
    print("=" * 50)
    print(f"  {strategy_name} 리포트  [{result['rebalance_freq']} 리밸런싱]")
    print("=" * 50)
    print(f"  초기 투자금    : {initial_capital:>15,.0f} 원")
    print(f"  최종 자산      : {result['final_value']:>15,.0f} 원")
    print("-" * 50)
    print(f"  총 수익률      : {result['total_return']:>14.2f} %")
    print(f"  연간 수익률    : {result['annual_return']:>14.2f} %")
    print(f"  연간 변동성    : {result['volatility']:>14.2f} %")
    print(f"  샤프 지수      : {result['sharpe_ratio']:>14.2f}")
    print(f"  최대 낙폭(MDD) : {result['mdd']:>14.2f} %")
    print("-" * 50)
    print("  종목별 비중 & 수익률:")
    for ticker, weight in weights.items():
        ret = result["ticker_returns"].get(ticker, 0)
        print(f"    {ticker:<8} 비중: {weight*100:>5.1f}%  수익률: {ret:>8.2f}%")
    print("=" * 50)
