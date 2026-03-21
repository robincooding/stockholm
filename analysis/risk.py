"""
리스크 관리 모듈

기능:
- 손절선 / 익절선 적용
- 트레일링 스탑
- 포지션 사이징 (Kelly 공식)
- 리스크/리워드 리포트
"""

import numpy as np
import pandas as pd

# === 손절 (Stop Loss) / 익절 (Take Profit) ===
def apply_stop_loss_take_profit(
    df: pd.DataFrame,
    stop_loss: float = 0.05,
    take_profit: float = 0.15,
) -> pd.DataFrame:
    """
    손절선과 익절선을 적용해 signal을 수정하는 함수.
    
    Parameters
    ----------
    df : pd.DataFrame
        generate_signals()가 적용된 DataFrame
    stop_loss : float
        손절 비율 (기본값: 0.05 = 5%)
    take_profit : float
        익절 비율 (기본값: 0.15 = 15%)

    Returns
    -------
    pd.DataFrame
        손절/익절 조건이 반영된 DataFrame
        추가 컬럼:
        - stop_price   : 현재 손절선 가격
        - target_price : 현재 익절선 가격
        - exit_reason  : 'stop_loss' / 'take_profit' / 'signal' / ''
    """
    df = df.copy()
    df["stop_price"]   = np.nan
    df["target_price"] = np.nan
    df["exit_reason"]  = ""
    
    entry_price = None
    position = 0
    
    for idx in df.index:
        current_price = df.loc[idx, "close"]
        signal = df.loc[idx, "signal"]
        
        if position == 0 and signal == 1:
            # 매수 진입
            entry_price = current_price
            position = 1
            df.loc[idx, "stop_price"] = entry_price * (1 - stop_loss)
            df.loc[idx, "target_price"] = entry_price * (1 + take_profit)
            
        elif position == 1 and entry_price is not None:
            stop_price = entry_price * (1 - stop_loss)
            target_price = entry_price * (1 + take_profit)
            
            df.loc[idx, "stop_price"] = stop_price
            df.loc[idx, "target_price"] = target_price
            
            # 손절 조건
            if current_price <= stop_price:
                df.loc[idx, "signal"] = -1
                df.loc[idx, "exit_reason"] = "stop_loss"
                position = 0
                entry_price = None
                
            # 익절 조건
            elif current_price >= target_price:
                df.loc[idx, "signal"] = -1
                df.loc[idx, "exit_reason"] = "take_profit"
                position = 0
                entry_price = None
                
            # 전략 매도 신호
            elif signal == -1:
                df.loc[idx, "exit_reason"] = "signal"
                position = 0
                entry_price = None
                
    df["position"] = df["signal"].replace(-1, 0)
    df["position"] = df["position"].ffill().fillna(0)
    
    return df

# === Trailing Stop ===
def apply_trailing_stop(
    df: pd.DataFrame,
    trail_pct: float = 0.05,
) -> pd.DataFrame:
    """
    트레일링 스탑을 적용하는 함수.
    고점을 따라 손절선이 자동으로 올라가며 수익을 보호함

Parameters
    ----------
    df : pd.DataFrame
        generate_signals()가 적용된 DataFrame
    trail_pct : float
        트레일링 스탑 비율 (기본값: 0.05 = 5%)

    Returns
    -------
    pd.DataFrame
        추가 컬럼:
        - trailing_stop : 현재 트레일링 스탑 가격
        - exit_reason   : 'trailing_stop' / 'signal' / ''
    """
    df = df.copy()
    df["trailing_stop"] = np.nan
    df["exit_reason"]   = ""

    position = 0
    highest = None
    
    for idx in df.index:
        current_price = df.loc[idx, "close"]
        signal = df.loc[idx, "signal"]
        
        if position == 0 and signal == 1:
            position = 1
            highest = current_price
            
        elif position == 1 and highest is not None:
            # 고점 갱신
            if current_price > highest:
                highest = current_price
                
            trail_price = highest * (1 - trail_pct)
            df.loc[idx, "trailing_stop"] = trail_price
            
            # 트레일링 스탑 발동
            if current_price <= trail_price:
                df.loc[idx, "signal"] = -1
                df.loc[idx, "exit_reason"] = "trailing_stop"
                position = 0
                highest  = None
                
            elif signal == -1:
                df.loc[idx, "exit_reason"] = "signal"
                position = 0
                highest  = None
                
    df["position"] = df["signal"].replace(-1, 0)
    df["position"] = df["position"].ffill().fillna(0)
    
    return df

# === Kelly Position Sizing ===
def kelly_position_size(
    win_rate: float,
    avg_win: float,
    avg_loss: float,
    fraction: float = 0.5,
) -> dict:
    """
    Kelly 공식으로 최적 포지션 크기를 계산하는 함수.
    
    Parameters
    ----------
    win_rate : float
        승률 (0~1)
    avg_win : float
        평균 수익률 (0~1)
    avg_loss : float
        평균 손실률 (0~1, 양수로 입력)
    fraction : float
        Kelly 분수 (기본값: 0.5 = 하프 켈리)

    Returns
    -------
    dict
        {
            'kelly_full'  : 풀 켈리 비율,
            'kelly_half'  : 하프 켈리 비율 (권장),
            'invest_pct'  : 실제 투자 비율 (%),
            'rr_ratio'    : 리스크/리워드 비율,
        }
    """
    if avg_loss == 0:
        return {"kelly_full": 0, "kelly_half": 0, "invest_pct": 0, "rr_ratio": 0}
    
    rr_ratio = avg_win / avg_loss
    loss_rate = 1 - win_rate
    kelly_full = (win_rate * rr_ratio - loss_rate) / rr_ratio
    kelly_full = max(kelly_full, 0) # 음수면 0 (투자 안 함)
    kelly_half = kelly_full * fraction
    
    return {
        "kelly_full":  round(kelly_full, 4),
        "kelly_half":  round(kelly_half, 4),
        "invest_pct":  round(kelly_half * 100, 2),
        "rr_ratio":    round(rr_ratio, 2),
    }
    
# === Risk Report ===
def risk_report(
    df: pd.DataFrame,
    initial_capital: float = 10_000_000,
    stop_loss: float = 0.05,
    take_profit: float = 0.15,
) -> None:
    """손절, 익절 결과 report를 출력하는 함수."""
    if "exit_reason" not in df.columns:
        print("apply_stop_loss_take_profit() 또는 apply_trailing_stop()을 먼저 실행해주세요.")
        return

    exits = df[df["exit_reason"] != ""]

    stop_loss_cnt   = len(exits[exits["exit_reason"] == "stop_loss"])
    take_profit_cnt = len(exits[exits["exit_reason"] == "take_profit"])
    signal_cnt      = len(exits[exits["exit_reason"] == "signal"])
    trailing_cnt    = len(exits[exits["exit_reason"] == "trailing_stop"])
    total           = len(exits)

    print("=" * 45)
    print("  리스크 관리 리포트")
    print("=" * 45)
    print(f"  총 청산 횟수     : {total:>10} 회")
    print(f"  손절 청산        : {stop_loss_cnt:>10} 회  ({stop_loss_cnt/max(total,1)*100:.1f}%)")
    print(f"  익절 청산        : {take_profit_cnt:>10} 회  ({take_profit_cnt/max(total,1)*100:.1f}%)")
    print(f"  트레일링 스탑    : {trailing_cnt:>10} 회  ({trailing_cnt/max(total,1)*100:.1f}%)")
    print(f"  전략 신호 청산   : {signal_cnt:>10} 회  ({signal_cnt/max(total,1)*100:.1f}%)")
    print("-" * 45)
    print(f"  손절선           : {stop_loss*100:>9.1f} %")
    print(f"  익절선           : {take_profit*100:>9.1f} %")
    print(f"  R/R 비율         : {take_profit/stop_loss:>9.1f} x")
    print("=" * 45)