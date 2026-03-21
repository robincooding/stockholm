# 📈 Stockholm

> 당신의 투자 판단을 데이터로 — 한국/해외 주식 기술적 분석 & 백테스팅 시스템

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![pandas](https://img.shields.io/badge/pandas-2.2-150458?logo=pandas)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 📌 프로젝트 소개

Stockholm은 2022년에 작성된 주식 기술적 분석 스크립트를 **모듈화된 라이브러리 구조로 리팩토링**한 프로젝트입니다.

흩어져 있던 4개의 독립 스크립트(`SMA_EMA_Strategy_Automation.py`, `Trendline_Automation.py`, `SupportLine.py`, `ResistanceLine.py`)를 역할별 패키지로 재구성하고, 미완성이었던 백테스팅과 추가 지표를 완성했습니다.

**한국 주식(네이버 금융)** 과 **해외 주식(Yahoo Finance)** 을 모두 지원하며, CLI와 Jupyter Notebook 두 가지 환경에서 사용할 수 있습니다.

---

## ✨ 주요 기능

### 데이터 수집

- KRX 상장기업 목록 자동 조회
- 네이버 금융 OHLCV 데이터 수집 (한국 주식, 약 10년치)
- Yahoo Finance OHLCV 데이터 수집 (해외 주식)
- **퍼지(Fuzzy) 종목명 검색** — 정확한 이름 몰라도 검색 가능

### 기술적 지표

| 지표       | 설명                              |
| ---------- | --------------------------------- |
| SMA        | 단순 이동평균 (20, 50, 200일)     |
| EMA        | 지수 이동평균 (12, 26, 50, 200일) |
| RSI        | 상대강도지수 — 과매수/과매도 판단 |
| MACD       | 이동평균 수렴/발산 — 모멘텀 측정  |
| 볼린저밴드 | 변동성 기반 밴드 — 돌파/수축 신호 |
| 로그수익률 | 일별/누적 수익률                  |

### 패턴 분석

- **HDBSCAN 클러스터링** 기반 지지선/저항선 자동 탐지
- **argrelextrema** 기반 추세선 (고점/저점 연결)
- 슬라이딩 윈도우 피벗 포인트 탐지

### 전략 & 백테스팅

- SMA / EMA / SMA-EMA 크로스 전략
- 수익률, 연간수익률, MDD, 승률, 샤프지수 리포트
- 전략 비교 (여러 전략 동시 비교)
- Buy & Hold 대비 성과 비교

### 시각화

- 종가 + 이동평균 + 매수/매도 신호
- 지지선/저항선 차트
- 추세선 차트
- RSI / MACD 차트
- 백테스팅 수익률 비교 차트
- **종합 대시보드** (4개 차트 한 화면)

---

## 🗂️ 프로젝트 구조

```
stockholm/
├── data/
│   ├── krx_fetcher.py       # KRX 종목 목록 + 네이버 금융 시세
│   └── yahoo_fetcher.py     # Yahoo Finance 시세
├── analysis/
│   ├── indicators.py        # 기술적 지표 계산
│   ├── patterns.py          # 지지/저항선, 추세선
│   └── backtester.py        # 백테스팅 & 수익률 리포트
├── strategy/
│   ├── base.py              # 전략 추상 클래스
│   └── ma_crossover.py      # SMA/EMA 크로스 전략
├── visualization/
│   └── plotter.py           # 통합 시각화
├── utils/
│   └── search.py            # 퍼지 종목명 검색
├── main.py                  # CLI 진입점
├── notebook.ipynb           # Jupyter 대화형 분석
└── requirements.txt
```

---

## 🚀 시작하기

### 요구사항

- Python 3.11 이상
- macOS / Windows / Linux

### 설치

```bash
git clone https://github.com/robincooding/stockholm.git
cd stockholm
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### CLI 실행

```bash
python main.py
```

```
╔══════════════════════════════════════╗
║         📈  Stockholm v1.0          ║
║   기술적 분석 & 백테스팅 시스템      ║
╚══════════════════════════════════════╝

  [1] 한국 주식 분석 (네이버 금융)
  [2] 해외 주식 분석 (Yahoo Finance)
  [0] 종료
```

### Jupyter Notebook 실행

```bash
jupyter notebook
```

---

## 📊 사용 예시

### 한국 주식 분석

```python
from data.krx_fetcher import fetch_krx_list, get_korean_stock
from utils.search import fuzzy_search_company

# 퍼지 검색
krx = fetch_krx_list()
results = fuzzy_search_company("삼성전", krx)

# 데이터 수집
df = get_korean_stock("삼성전자", krx)
```

### 해외 주식 분석

```python
from data.yahoo_fetcher import get_us_stock
from analysis.indicators import add_all_indicators

df = get_us_stock("AAPL", years=3)
df = add_all_indicators(df)
```

### 백테스팅

```python
from strategy.ma_crossover import SMACrossover
from analysis.backtester import Backtester

strategy = SMACrossover(short_window=20, long_window=60)
df_signals = strategy.generate_signals(df)

bt = Backtester(initial_capital=10_000_000)
bt.run(df_signals)
bt.print_report()
```

```
========================================
  백테스팅 결과 리포트
========================================
  초기 투자금    :      10,000,000 원
  최종 자산      :      12,350,000 원
----------------------------------------
  전략 총 수익률 :           23.50 %
  시장 총 수익률 :           39.60 %
  연간 수익률    :            7.30 %
  최대 낙폭(MDD) :           -8.20 %
  승률           :           62.50 %
  총 거래 횟수   :              16 회
  샤프 지수      :            0.87
========================================
```

### 시각화

```python
from visualization.plotter import plot_dashboard

plot_dashboard(df_result, ticker="AAPL", ma_cols=["SMA_20", "SMA_60"])
```

---

## 📦 패키지 목록

| 패키지       | 버전   | 용도              |
| ------------ | ------ | ----------------- |
| pandas       | ≥ 2.2  | 데이터프레임 처리 |
| numpy        | ≥ 1.25 | 수치 계산         |
| requests     | ≥ 2.31 | HTTP 요청         |
| yfinance     | ≥ 0.2  | Yahoo Finance     |
| scikit-learn | ≥ 1.6  | 데이터 스케일링   |
| hdbscan      | ≥ 0.8  | 클러스터링        |
| scipy        | ≥ 1.11 | 신호 처리         |
| matplotlib   | ≥ 3.7  | 시각화            |
| rapidfuzz    | ≥ 3.0  | 퍼지 검색         |
| jupyter      | ≥ 1.0  | Notebook          |

---

## 🗺️ 로드맵

- [x] Phase 1 — 데이터 수집 + 퍼지 검색
- [x] Phase 2 — 기술적 지표 + 패턴 분석
- [x] Phase 3 — 전략 + 백테스팅
- [x] Phase 4 — 시각화 + CLI + Notebook
- [ ] Phase 5 — 지표 조합 전략 + 리스크 관리 + 포트폴리오
- [ ] Phase 6 — FastAPI + React 웹 애플리케이션

---

## 📄 라이선스

MIT License
