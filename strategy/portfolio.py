"""
다중 종목 포트폴리오 전략 모듈

기능:
- 동일 비중 포트폴리오
- 리스크 패리티 포트폴리오
- 상관관계 분석
- 포트폴리오 백테스팅 리포트
"""

import numpy as np
import pandas as pd
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
    prices = {}
    for ticker, df in data.items():
        prices[ticker] = df["close"]

    price_matrix = pd.DataFrame(prices).dropna()
    return price_matrix


# === 상관관계 분석 ===
def analyze_correlation(price_matrix: pd.DataFrame) -> dict:
    """
    종목 간 상관관계를 분석하는 함수.

    Parameters
    ----------
    price_matrix : pd.DataFrame
        build_price_matrix() 반환값

    Returns
    -------
    dict
        {
            'correlation' : 상관계수 행렬,
            'summary'     : 평균 상관계수 요약,
        }
    """
    returns = price_matrix.pct_change().dropna()
    corr = returns.corr()

    # 대각선 제외 평균 상관계수
    mask = np.ones(corr.shape, dtype=bool)
    np.fill_diagonal(mask, False)
    avg_corr = corr.values[mask].mean()

    return {
        "correlation": corr,
        "avg_corr": round(avg_corr, 4),
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


def risk_parity_weight(price_matrix: pd.DataFrame) -> dict[str, float]:
    """
    리스크 패리티 비중을 계산하는 함수.
    변동성이 낮은 종목에 더 높은 비중을 부여함

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
    vol = returns.std()  # 종목별 변동성
    inv_vol = 1.0 / vol  # 변동성 역수
    weights = inv_vol / inv_vol.sum()  # 정규화

    return {ticker: round(float(w), 4) for ticker, w in weights.items()}


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


# === Portfolio Backtesting ===
def backtest_portfolio(
    data: dict[str, pd.DataFrame],
    weights: dict[str, float],
    initial_capital: float = 10_000_000,
) -> dict:
    """
    포트폴리오 백테스팅을 실행하는 함수.

    Parameters
    ----------
    data : dict[str, pd.DataFrame]
        {'티커': OHLCV DataFrame} 딕셔너리
    weights : dict[str, float]
        {'티커': 비중} 딕셔너리
    initial_capital : float
        초기 투자금 (기본값: 10,000,000)

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
    returns = price_matrix.pct_change().dropna()

    # 포트폴리오 일별 수익률
    weight_array = np.array([weights.get(t, 0) for t in price_matrix.columns])
    portfolio_returns = returns.values @ weight_array
    portfolio_returns = pd.Series(portfolio_returns, index=returns.index)

    # 누적 수익률 및 자산 가치
    cumulative = (1 + portfolio_returns).cumprod()
    portfolio_value = initial_capital * cumulative

    # 성과 지표
    total_return = (cumulative.iloc[-1] - 1) * 100
    years = len(returns) / 252
    annual_return = ((1 + total_return / 100) ** (1 / years) - 1) * 100
    volatility = portfolio_returns.std() * np.sqrt(252) * 100

    sharpe = (
        (portfolio_returns.mean() / portfolio_returns.std() * np.sqrt(252))
        if portfolio_returns.std() != 0
        else 0
    )

    # MDD
    rolling_max = cumulative.cummax()
    drawdown = (cumulative - rolling_max) / rolling_max
    mdd = drawdown.min() * 100

    # 종목별 수익률
    ticker_returns = {
        ticker: round(
            (price_matrix[ticker].iloc[-1] / price_matrix[ticker].iloc[0] - 1) * 100, 2
        )
        for ticker in price_matrix.columns
    }

    return {
        "total_return": round(total_return, 2),
        "annual_return": round(annual_return, 2),
        "volatility": round(volatility, 2),
        "sharpe_ratio": round(sharpe, 2),
        "mdd": round(mdd, 2),
        "final_value": round(portfolio_value.iloc[-1], 0),
        "ticker_returns": ticker_returns,
        "portfolio_value": portfolio_value,
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
    print(f"  {strategy_name} 리포트")
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
