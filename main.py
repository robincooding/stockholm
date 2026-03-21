"""
Stockholm - 주식 기술적 분석 CLI 진입점

사용법:
    python main.py
"""

from data.krx_fetcher import fetch_krx_list, get_korean_stock
from data.yahoo_fetcher import get_us_stock
from analysis.indicators import add_all_indicators
from analysis.patterns import find_support_resistance, find_trendlines
from strategy.ma_crossover import SMACrossover, EMACrossover, SMAEMACrossover
from analysis.backtester import Backtester
from visualization.plotter import (
    plot_dashboard,
    plot_support_resistance,
    plot_trendlines,
)
from utils.search import pick_company


# === 메뉴 출력 ===
def print_banner():
    print(
        """
          ╔══════════════════════════════════════╗
          ║         📈  Stockholm v1.0           ║
          ║   기술적 분석 & 백테스팅 시스템      ║
          ╚══════════════════════════════════════╝
          """
    )


def print_menu():
    print(
        """
─────────────────────────────────────
  [1] 한국 주식 분석 (네이버 금융)
  [2] 해외 주식 분석 (Yahoo Finance)
  [0] 종료
─────────────────────────────────────"""
    )


def print_strategy_menu():
    print(
        """
─────────────────────────────────────
  전략 선택
  [1] SMA 크로스 (50/200)
  [2] EMA 크로스 (50/200)
  [3] SMA-EMA 크로스 (50)
─────────────────────────────────────"""
    )


def print_analysis_menu():
    print(
        """
─────────────────────────────────────
  분석 메뉴
  [1] 종합 대시보드
  [2] 지지선 / 저항선
  [3] 추세선
  [4] 백테스팅 리포트
  [5] 전략 비교 (SMA vs EMA vs SMA-EMA)
  [0] 처음으로
─────────────────────────────────────"""
    )


# === 전략 선택 ===
def select_strategy() -> object:
    print_strategy_menu()
    choice = input("전략 선택: ").strip()
    if choice == "1":
        return SMACrossover(50, 200)
    elif choice == "2":
        return EMACrossover(50, 200)
    elif choice == "3":
        return SMAEMACrossover(50)
    else:
        print("기본값 SMA(50/200)으로 설정합니다.")
        return SMACrossover(50, 200)


# === 분석 실행 ===
def run_analysis(df, ticker: str):
    """데이터가 준비된 후 분석 메뉴를 실행하는 함수"""

    # 지표 추가
    df = add_all_indicators(df)

    # 전략 선택 및 신호 생성
    strategy = select_strategy()
    df_signals = strategy.generate_signals(df)

    # 백테스팅
    bt = Backtester(initial_capital=10_000_000)
    df_result = bt.run(df_signals)

    while True:
        print_analysis_menu()
        choice = input("분석 선택: ").strip()

        if choice == "1":
            ma_cols = [
                c for c in ["SMA_50", "SMA_200", "EMA_50"] if c in df_result.columns
            ]
            plot_dashboard(df_result, ticker=ticker, ma_cols=ma_cols)

        elif choice == "2":
            sr = find_support_resistance(df)
            plot_support_resistance(df, sr, ticker=ticker)

        elif choice == "3":
            tl = find_trendlines(df)
            plot_trendlines(df, tl, ticker=ticker)

        elif choice == "4":
            bt.print_report()

        elif choice == "5":
            print("\n전략 비교 중...")
            strategies = [
                SMACrossover(50, 200),
                EMACrossover(50, 200),
                SMAEMACrossover(50),
            ]
            print(
                f"\n{'전략':<25} {'수익률':>8} {'시장':>8} {'MDD':>8} {'승률':>8} {'거래':>6}"
            )
            print("-" * 70)
            for s in strategies:
                df_s = s.generate_signals(df)
                bt_s = Backtester(initial_capital=10_000_000)
                bt_s.run(df_s)
                r = bt_s.report()
                print(
                    f"{s.name:<25} "
                    f"{r['total_return']:>7.2f}% "
                    f"{r['market_return']:>7.2f}% "
                    f"{r['mdd']:>7.2f}% "
                    f"{r['win_rate']:>7.2f}% "
                    f"{r['total_trades']:>5}회"
                )

        elif choice == "0":
            break

        else:
            print("올바른 번호를 입력해주세요.")


# === 메인 루프 ===
def main():
    print_banner()

    # KRX 목록 미리 로드 (한국 주식 선택 시 사용)
    krx_df = None

    while True:
        print_menu()
        choice = input("선택: ").strip()

        if choice == "1":
            # 한국 주식
            if krx_df is None:
                print("\nKRX 종목 목록 로딩 중...")
                from data.krx_fetcher import fetch_krx_list

                krx_df = fetch_krx_list()
                print(f"총 {len(krx_df)}개 종목 로드 완료!")

            query = input("\n종목명을 입력하세요 (예: 삼성전): ").strip()
            result = pick_company(query, krx_df)
            if result is None:
                continue

            code, company = result
            print(f"\n{company} ({code}) 데이터 불러오는 중...")
            try:
                df = get_korean_stock(company, krx_df)
                print(f"데이터 로드 완료! ({len(df)}일치)")
                run_analysis(df, ticker=company)
            except Exception as e:
                print(f"오류 발생: {e}")

        elif choice == "2":
            # 해외 주식
            ticker = input("\n티커를 입력하세요 (예: AAPL, TSLA): ").strip().upper()
            years = input("기간을 입력하세요 (년, 기본값 5): ").strip()
            years = int(years) if years.isdigit() else 5

            print(f"\n{ticker} 데이터 불러오는 중...")
            try:
                df = get_us_stock(ticker, years=years)
                print(f"데이터 로드 완료! ({len(df)}일치)")
                run_analysis(df, ticker=ticker)
            except Exception as e:
                print(f"오류 발생: {e}")

        elif choice == "0":
            print("\n종료합니다. 👋")
            break

        else:
            print("올바른 번호를 입력해주세요.")


if __name__ == "__main__":
    main()
