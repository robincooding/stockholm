"""
전략 신호를 기반으로 백테스팅을 수행하고 수익률 리포트를 생성하는 모듈
"""

import numpy as np
import pandas as pd


class Backtester:
    """
    전략 백테스터 클래스.

    Parameters
    ----------
    initial_capital : float
        초기 투자금 (기본값: 10,000,000원)
    commission : float
        거래 수수료 (기본값: 0.0015 = 0.15%)
    """

    def __init__(
        self,
        initial_capital: float = 10_000_000,
        commission: float = 0.0015,
    ):
        self.initial_capital = initial_capital
        self.commission      = commission
        self.results         = None

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        백테스팅을 실행하는 메서드.

        Parameters
        ----------
        df : pd.DataFrame
            generate_signals()가 적용된 DataFrame
            (signal, position 컬럼 필요)

        Returns
        -------
        pd.DataFrame
            백테스팅 결과 DataFrame
        """
        df = df.copy()

        # 일별 로그 수익률
        df["returns"] = np.log(df["close"] / df["close"].shift(1))

        # 전략 수익률 = 전날 포지션 × 오늘 수익률 (룩어헤드 바이어스 방지)
        df["strategy_returns"] = df["position"].shift(1) * df["returns"]

        # 거래 발생 시 수수료 차감
        df["trade"] = df["signal"].diff().abs()
        df["strategy_returns"] -= df["trade"] * self.commission

        # 누적 수익률
        df["creturns"]          = df["returns"].cumsum().apply(np.exp)
        df["strategy_creturns"] = df["strategy_returns"].cumsum().apply(np.exp)

        # 자산 가치
        df["portfolio_value"] = self.initial_capital * df["strategy_creturns"]

        self.results = df
        return df

    def report(self) -> dict:
        """
        백테스팅 결과 리포트를 반환하는 메서드.

        Returns
        -------
        dict
            {
                'total_return'    : 전략 총 수익률 (%),
                'market_return'   : 시장 총 수익률 (%),
                'annual_return'   : 연간 수익률 (%),
                'mdd'             : 최대 낙폭 (%),
                'win_rate'        : 승률 (%),
                'total_trades'    : 총 거래 횟수,
                'final_value'     : 최종 자산 (원),
                'sharpe_ratio'    : 샤프 지수,
            }
        """
        if self.results is None:
            raise ValueError("run()을 먼저 실행해주세요.")

        df = self.results.dropna()

        # 총 수익률
        total_return  = (df["strategy_creturns"].iloc[-1] - 1) * 100
        market_return = (df["creturns"].iloc[-1] - 1) * 100

        # 연간 수익률
        years = len(df) / 252
        annual_return = ((1 + total_return / 100) ** (1 / years) - 1) * 100

        # MDD
        rolling_max = df["strategy_creturns"].cummax()
        drawdown    = (df["strategy_creturns"] - rolling_max) / rolling_max
        mdd         = drawdown.min() * 100

        # 거래 횟수 및 승률
        trades      = df[df["signal"] != 0]
        total_trades = len(trades)

        winning_trades = 0
        signals = df[df["signal"] != 0]
        for i in range(len(signals) - 1):
            entry = signals.iloc[i]
            exit_ = signals.iloc[i + 1]
            if entry["signal"] == 1:  # 매수 후
                pnl = exit_["close"] - entry["close"]
                if pnl > 0:
                    winning_trades += 1

        win_rate = (winning_trades / max(total_trades // 2, 1)) * 100

        # 샤프 지수 (연간화)
        sharpe = (
            df["strategy_returns"].mean() /
            df["strategy_returns"].std() *
            np.sqrt(252)
        ) if df["strategy_returns"].std() != 0 else 0

        return {
            "total_return":  round(total_return, 2),
            "market_return": round(market_return, 2),
            "annual_return": round(annual_return, 2),
            "mdd":           round(mdd, 2),
            "win_rate":      round(win_rate, 2),
            "total_trades":  total_trades,
            "final_value":   round(df["portfolio_value"].iloc[-1], 0),
            "sharpe_ratio":  round(sharpe, 2),
        }

    def print_report(self) -> None:
        """백테스팅 결과를 보기 좋게 출력하는 메서드"""
        r = self.report()
        print("=" * 40)
        print(f"  백테스팅 결과 리포트")
        print("=" * 40)
        print(f"  초기 투자금    : {self.initial_capital:>15,.0f} 원")
        print(f"  최종 자산      : {r['final_value']:>15,.0f} 원")
        print("-" * 40)
        print(f"  전략 총 수익률 : {r['total_return']:>14.2f} %")
        print(f"  시장 총 수익률 : {r['market_return']:>14.2f} %")
        print(f"  연간 수익률    : {r['annual_return']:>14.2f} %")
        print(f"  최대 낙폭(MDD) : {r['mdd']:>14.2f} %")
        print(f"  승률           : {r['win_rate']:>14.2f} %")
        print(f"  총 거래 횟수   : {r['total_trades']:>14} 회")
        print(f"  샤프 지수      : {r['sharpe_ratio']:>14.2f}")
        print("=" * 40)