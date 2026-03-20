"""
분석 결과를 시각화하는 통합 모듈

OS별 한글 폰트를 자동 감지하여 설정
"""

import platform
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D

# === 한글 폰트 자동 설정 ===
def _set_korean_font():
    """OS별 한글 폰트를 자동으로 설정하는 함수."""
    system = platform.system()
    if system == "Darwin":
        plt.rcParams["font.family"] = "AppleGothic"
    elif system == "Windows":
        plt.rcParams["font.family"] = "Malgun Gothic"
    else:
        plt.rcParams["font.family"] = "NanumGothic"
    plt.rcParams["axes.unicode_minus"] = False

_set_korean_font()

# === 가격 + 이동평균 + 매매 신호 ===
def plot_price_signals(
    df: pd.DataFrame,
    ticker: str = "",
    ma_cols: list[str] = None,
) -> None:
    """
    종가, 이동평균선, 매수/매도 신호를 시각화하는 함수.

    Parameters
    ----------
    df : pd.DataFrame
        generate_signals()가 적용된 DataFrame
    ticker : str
        차트 제목에 표시할 종목명
    ma_cols : list[str]
        표시할 이동평균선 컬럼명 리스트 (예: ['SMA_50', 'SMA_200'])
    """
    fig, ax = plt.subplots(figsize=(16, 7))

    # 종가
    ax.plot(df.index, df["close"], label="종가", color="#2C3E50", linewidth=1.2)

    # 이동평균선
    colors = ["#E74C3C", "#3498DB", "#2ECC71", "#F39C12"]
    if ma_cols:
        for i, col in enumerate(ma_cols):
            if col in df.columns:
                ax.plot(df.index, df[col], label=col,
                        color=colors[i % len(colors)], linewidth=1.0, alpha=0.8)

    # 매수/매도 신호
    if "signal" in df.columns:
        buy  = df[df["signal"] == 1]
        sell = df[df["signal"] == -1]
        ax.scatter(buy.index,  buy["close"],  marker="^", color="#27AE60",
                   s=120, zorder=5, label="매수")
        ax.scatter(sell.index, sell["close"], marker="v", color="#E74C3C",
                   s=120, zorder=5, label="매도")

    ax.set_title(f"{ticker} 가격 & 매매 신호", fontsize=15, fontweight="bold")
    ax.set_ylabel("가격")
    ax.legend(loc="upper left", fontsize=10)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()
    
# === SupportLine / ResistanceLine ===
def plot_support_resistance(
    df: pd.DataFrame,
    sr: dict,
    ticker: str = "",
) -> None:
    """
    종가와 지지선/저항선을 시각화하는 함수.

    Parameters
    ----------
    df : pd.DataFrame
        OHLCV DataFrame
    sr : dict
        find_support_resistance() 반환값
    ticker : str
        차트 제목에 표시할 종목명
    """
    fig, ax = plt.subplots(figsize=(16, 7))

    df_recent = sr["df"]
    ax.plot(df_recent.index, df_recent["close"],
            color="#2C3E50", linewidth=1.2, label="종가")

    for price in sr["support"]:
        ax.axhline(price, color="#3498DB", linestyle="--",
                   linewidth=1.5, alpha=0.8, label=f"지지선 {price:,.0f}")

    for price in sr["resistance"]:
        ax.axhline(price, color="#E74C3C", linestyle="--",
                   linewidth=1.5, alpha=0.8, label=f"저항선 {price:,.0f}")

    ax.set_title(f"{ticker} 지지선 & 저항선", fontsize=15, fontweight="bold")
    ax.set_ylabel("가격")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()
    
# === TrendLine ===
def plot_trendlines(
    df: pd.DataFrame,
    trendlines: dict,
    ticker: str = "",
) -> None:
    """
    종가와 추세선(고점/저점 연결)을 시각화하는 함수.

    Parameters
    ----------
    df : pd.DataFrame
        OHLCV DataFrame
    trendlines : dict
        find_trendlines() 반환값
    ticker : str
        차트 제목에 표시할 종목명
    """
    fig, ax = plt.subplots(figsize=(16, 7))

    ax.plot(df.index, df["close"],
            color="#2C3E50", linewidth=1.2, label="종가", alpha=0.7)

    # 고점 연결
    highs = trendlines["highs"]
    if highs["dates"]:
        ax.plot(highs["dates"], highs["prices"],
                color="#E74C3C", linewidth=1.5,
                marker="^", markersize=6, label="고점 추세선")

    # 저점 연결
    lows = trendlines["lows"]
    if lows["dates"]:
        ax.plot(lows["dates"], lows["prices"],
                color="#3498DB", linewidth=1.5,
                marker="v", markersize=6, label="저점 추세선")

    ax.set_title(f"{ticker} 추세선", fontsize=15, fontweight="bold")
    ax.set_ylabel("가격")
    ax.legend(loc="upper left", fontsize=10)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()
    
# === RSI ===
def plot_rsi(
    df: pd.DataFrame,
    ticker: str = "",
    window: int = 14,
) -> None:
    """
    종가와 RSI를 함께 시각화하는 함수.

    Parameters
    ----------
    df : pd.DataFrame
        add_rsi()가 적용된 DataFrame
    ticker : str
        차트 제목에 표시할 종목명
    window : int
        RSI 기간 (컬럼명 매칭용)
    """
    rsi_col = f"RSI_{window}"
    if rsi_col not in df.columns:
        raise ValueError(f"'{rsi_col}' 컬럼이 없습니다. add_rsi()를 먼저 실행해주세요.")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 9),
                                    gridspec_kw={"height_ratios": [3, 1]})

    # 종가
    ax1.plot(df.index, df["close"], color="#2C3E50", linewidth=1.2)
    ax1.set_title(f"{ticker} 가격 & RSI", fontsize=15, fontweight="bold")
    ax1.set_ylabel("가격")
    ax1.grid(alpha=0.3)

    # RSI
    ax2.plot(df.index, df[rsi_col], color="#8E44AD", linewidth=1.2, label="RSI")
    ax2.axhline(70, color="#E74C3C", linestyle="--", linewidth=1.0, alpha=0.7, label="과매수(70)")
    ax2.axhline(30, color="#3498DB", linestyle="--", linewidth=1.0, alpha=0.7, label="과매도(30)")
    ax2.fill_between(df.index, df[rsi_col], 70,
                     where=(df[rsi_col] >= 70), alpha=0.2, color="#E74C3C")
    ax2.fill_between(df.index, df[rsi_col], 30,
                     where=(df[rsi_col] <= 30), alpha=0.2, color="#3498DB")
    ax2.set_ylim(0, 100)
    ax2.set_ylabel("RSI")
    ax2.legend(loc="upper left", fontsize=9)
    ax2.grid(alpha=0.3)

    plt.tight_layout()
    plt.show()
    
# === MACD ===
def plot_macd(
    df: pd.DataFrame,
    ticker: str = "",
) -> None:
    """
    종가와 MACD를 함께 시각화하는 함수.

    Parameters
    ----------
    df : pd.DataFrame
        add_macd()가 적용된 DataFrame
    ticker : str
        차트 제목에 표시할 종목명
    """
    for col in ["MACD", "MACD_signal", "MACD_hist"]:
        if col not in df.columns:
            raise ValueError(f"'{col}' 컬럼이 없습니다. add_macd()를 먼저 실행해주세요.")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 9),
                                    gridspec_kw={"height_ratios": [3, 1]})

    # 종가
    ax1.plot(df.index, df["close"], color="#2C3E50", linewidth=1.2)
    ax1.set_title(f"{ticker} 가격 & MACD", fontsize=15, fontweight="bold")
    ax1.set_ylabel("가격")
    ax1.grid(alpha=0.3)

    # MACD
    ax2.plot(df.index, df["MACD"],        color="#E74C3C", linewidth=1.2, label="MACD")
    ax2.plot(df.index, df["MACD_signal"], color="#3498DB", linewidth=1.2, label="Signal")
    ax2.bar(df.index, df["MACD_hist"],
            color=["#27AE60" if v >= 0 else "#E74C3C" for v in df["MACD_hist"]],
            alpha=0.5, label="Histogram")
    ax2.axhline(0, color="gray", linewidth=0.8)
    ax2.set_ylabel("MACD")
    ax2.legend(loc="upper left", fontsize=9)
    ax2.grid(alpha=0.3)

    plt.tight_layout()
    plt.show()

# === 백테스팅 수익률 비교 ===
def plot_backtest(
    df: pd.DataFrame,
    strategy_name: str = "전략",
    ticker: str = "",
) -> None:
    """
    전략 수익률 vs 시장 수익률(Buy & Hold)을 비교 시각화하는 함수.

    Parameters
    ----------
    df : pd.DataFrame
        Backtester.run() 반환값
    strategy_name : str
        범례에 표시할 전략 이름
    ticker : str
        차트 제목에 표시할 종목명
    """
    for col in ["creturns", "strategy_creturns"]:
        if col not in df.columns:
            raise ValueError(f"'{col}' 컬럼이 없습니다. Backtester.run()을 먼저 실행해주세요.")

    fig, ax = plt.subplots(figsize=(16, 7))

    ax.plot(df.index, df["creturns"],
            color="#95A5A6", linewidth=1.5,
            linestyle="--", label="Buy & Hold")
    ax.plot(df.index, df["strategy_creturns"],
            color="#E74C3C", linewidth=1.8, label=strategy_name)

    ax.axhline(1.0, color="gray", linewidth=0.8, linestyle=":")
    ax.set_title(f"{ticker} 백테스팅 — {strategy_name} vs Buy & Hold",
                 fontsize=15, fontweight="bold")
    ax.set_ylabel("누적 수익률 배수")
    ax.legend(loc="upper left", fontsize=11)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()
    
# === 종합 대시보드 ===
def plot_dashboard(
    df: pd.DataFrame,
    ticker: str = "",
    ma_cols: list[str] = None,
) -> None:
    """
    가격/이동평균, RSI, MACD, 백테스팅 수익률을 한 화면에 표시하는 함수.

    Parameters
    ----------
    df : pd.DataFrame
        모든 지표와 백테스팅 결과가 포함된 DataFrame
    ticker : str
        차트 제목에 표시할 종목명
    ma_cols : list[str]
        표시할 이동평균선 컬럼명 리스트
    """
    fig = plt.figure(figsize=(18, 14))
    gs  = gridspec.GridSpec(4, 1, height_ratios=[3, 1, 1, 1], hspace=0.4)

    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    ax3 = fig.add_subplot(gs[2], sharex=ax1)
    ax4 = fig.add_subplot(gs[3], sharex=ax1)

    # 1. 가격 + 이동평균 + 신호
    ax1.plot(df.index, df["close"], color="#2C3E50", linewidth=1.2, label="종가")
    colors = ["#E74C3C", "#3498DB", "#2ECC71", "#F39C12"]
    if ma_cols:
        for i, col in enumerate(ma_cols):
            if col in df.columns:
                ax1.plot(df.index, df[col], color=colors[i % len(colors)],
                         linewidth=1.0, alpha=0.8, label=col)
    if "signal" in df.columns:
        buy  = df[df["signal"] == 1]
        sell = df[df["signal"] == -1]
        ax1.scatter(buy.index,  buy["close"],  marker="^",
                    color="#27AE60", s=100, zorder=5, label="매수")
        ax1.scatter(sell.index, sell["close"], marker="v",
                    color="#E74C3C", s=100, zorder=5, label="매도")
    ax1.set_title(f"{ticker} 종합 대시보드", fontsize=15, fontweight="bold")
    ax1.set_ylabel("가격")
    ax1.legend(loc="upper left", fontsize=9)
    ax1.grid(alpha=0.3)

    # 2. RSI
    if "RSI_14" in df.columns:
        ax2.plot(df.index, df["RSI_14"], color="#8E44AD", linewidth=1.0)
        ax2.axhline(70, color="#E74C3C", linestyle="--", linewidth=0.8, alpha=0.7)
        ax2.axhline(30, color="#3498DB", linestyle="--", linewidth=0.8, alpha=0.7)
        ax2.fill_between(df.index, df["RSI_14"], 70,
                         where=(df["RSI_14"] >= 70), alpha=0.2, color="#E74C3C")
        ax2.fill_between(df.index, df["RSI_14"], 30,
                         where=(df["RSI_14"] <= 30), alpha=0.2, color="#3498DB")
        ax2.set_ylim(0, 100)
        ax2.set_ylabel("RSI")
        ax2.grid(alpha=0.3)

    # 3. MACD
    if all(c in df.columns for c in ["MACD", "MACD_signal", "MACD_hist"]):
        ax3.plot(df.index, df["MACD"],        color="#E74C3C", linewidth=1.0, label="MACD")
        ax3.plot(df.index, df["MACD_signal"], color="#3498DB", linewidth=1.0, label="Signal")
        ax3.bar(df.index, df["MACD_hist"],
                color=["#27AE60" if v >= 0 else "#E74C3C" for v in df["MACD_hist"]],
                alpha=0.5)
        ax3.axhline(0, color="gray", linewidth=0.6)
        ax3.set_ylabel("MACD")
        ax3.legend(loc="upper left", fontsize=8)
        ax3.grid(alpha=0.3)

    # 4. 백테스팅 수익률
    if "strategy_creturns" in df.columns:
        ax4.plot(df.index, df["creturns"],
                 color="#95A5A6", linewidth=1.2, linestyle="--", label="Buy & Hold")
        ax4.plot(df.index, df["strategy_creturns"],
                 color="#E74C3C", linewidth=1.5, label="전략")
        ax4.axhline(1.0, color="gray", linewidth=0.6, linestyle=":")
        ax4.set_ylabel("누적 수익률")
        ax4.legend(loc="upper left", fontsize=8)
        ax4.grid(alpha=0.3)

    fig.align_ylabels([ax1, ax2, ax3, ax4])
    plt.subplots_adjust(hspace=0.4)
    plt.show()