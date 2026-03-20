"""
모든 전략이 상속받는 추상 기본 클래스

새로운 전략을 만들 때는 이 클래스를 상속받아서 generate_signals() 메서드를 구현하면 됨.
"""

from abc import ABC, abstractmethod
import pandas as pd

class Strategy(ABC):
    """
    전략 추상 기본 클래스(Abstract Base Class).
    
    Parameters
    ----------
    name : str
        전략 이름 (리포트에 표시됨)
    """
    def __init__(self, name: str):
        self.name = name
        
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        매수/매도 신호를 생성하는 메서드.
        
        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame

        Returns
        -------
        pd.DataFrame
            아래 컬럼이 추가된 DataFrame:
            - signal : 1 (매수), -1 (매도), 0 (중립)
            - position : 현재 포지션 (1: 보유, 0: 미보유)
        """
        pass
    
    def __repr__(self):
        return f"Strategy(name='{self.name}')"
        