"""
KRX 상장기업 목록에서 퍼지(fuzzy) 종목명 검색을 지원하는 모듈

검색 우선순위:
  1. 정확히 일치
  2. 입력값으로 시작하는 종목
  3. 입력값을 포함하는 종목
  4. 편집 거리(Levenshtein) 기반 유사도 — rapidfuzz 없으면 difflib 사용
"""

from __future__ import annotations

import pandas as pd

# rapidfuzz가 있으면 사용, 없으면 difflib으로 fallback
try:
    from rapidfuzz import process as rf_process, fuzz
    _USE_RAPIDFUZZ = True
except ImportError:
    from difflib import SequenceMatcher
    _USE_RAPIDFUZZ = False
    
# === 내부 helper 함수 ===
def _similarity(a: str, b: str) -> float:
    """ 두 문자열의 유사도를 계산하는 함수 (0 ~ 100)"""
    if _USE_RAPIDFUZZ:
        return fuzz.ratio(a, b)
    return SequenceMatcher(None, a, b).ratio() * 100

# === 메인 search 함수 ===
def fuzzy_search_company(
    query: str,
    krx_df: pd.DataFrame,
    top_n: int = 5,
    score_cutoff: float = 40.0,
) -> pd.DataFrame:
    """
    KRX 종목에서 query와 유사한 종목을 반환하는 함수.
    
    Parameters
    ----------
    query : str
        검색할 종목명 (부분 입력 가능).
    krx_df : pd.DataFrame
        fetch_krx_list()로 불러온 KRX 목록.
    top_n : int
        반환할 최대 결과 수.
    score_cutoff : float
        이 점수 미만의 결과는 제외 (0~100).

    Returns
    -------
    pd.DataFrame
        columns: ['code', 'company', 'score']
        score 기준 내림차순 정렬.
    """
    query = query.strip()
    companies: pd.Series = krx_df["company"]
    
    # 1. 정확히 일치
    exact = krx_df[companies == query].copy()
    if not exact.empty:
        exact["score"] = 100.0
        return exact[["code", "company", "score"]].head(top_n)
    
    # 2, 3. 시작/포함 우선 풀 구성
    starts_with = krx_df[companies.str.startswith(query)].copy()
    contains = krx_df[companies.str.contains(query, regex=False)].copy()
    priority = pd.concat([starts_with, contains]).drop_duplicates("code")
    
    # priority 항목에 보정 점수 부여
    def priority_score(company):
        # rapidfuzz로 정확한 유사도 계산
        similarity = _similarity(query, company)
        # 검색어와 길이 차이가 적을수록 높은 점수
        length_diff = len(company) - len(query)
        length_bonus = max(0, 10 - length_diff * 2)
        return similarity + length_bonus
        
    priority["score"] = priority["company"].apply(priority_score)
    
    # 4. 편집 거리 기반 유사도
    if _USE_RAPIDFUZZ:
        results = rf_process.extract(
            query,
            companies.tolist(),
            scorer=fuzz.ratio,
            limit=top_n * 3,
            score_cutoff=score_cutoff,
        )
        fuzzy_idx = [
            krx_df.index[companies.tolist().index(r[0])]
            for r in results
        ]
        fuzzy_scores = {
            krx_df.loc[idx, "company"]: r[1]
            for idx, r in zip(fuzzy_idx, results)
        }
        fuzzy_df = krx_df.loc[fuzzy_idx].copy()
        fuzzy_df["score"] = fuzzy_df["company"].map(fuzzy_scores)
    else:
        scores = companies.apply(lambda c: _similarity(query, c))
        mask = scores >= score_cutoff
        fuzzy_df = krx_df[mask].copy()
        fuzzy_df["score"] = scores[mask]
    
    combined = (
        pd.concat([priority, fuzzy_df])
        .drop_duplicates("code")
        .sort_values(["score", "company"], ascending=[False, True])
        .head(top_n)
    )
    
    return combined[["code", "company", "score"]].reset_index(drop=True)

# === 대화형 선택 함수 ===
def pick_company(
    query: str,
    krx_df: pd.DataFrame,
    top_n: int = 5,
) -> tuple[str, str] | None:
    """
    퍼지 검색 후 사용자에게 선택지를 출력하고 선택받아 (code, company) 튜플을 반환하는 함수.
    결과가 없으면 None을 반환.
    CLI 환경에서 사용하는 대화형 헬퍼.
    """
    results = fuzzy_search_company(query, krx_df, top_n=top_n)
    
    if results.empty:
        print(f"'{query}'와(과) 유사한 종목을 찾지 못했습니다.")
        return None
    
    # 정확히 일치하면 바로 반환
    if results.iloc[0]["score"] == 100.0 and len(results) == 1:
        row = results.iloc[0]
        return row["code"], row["company"]

    print(f"\n'{query}' 검색 결과:")
    for i, row in results.iterrows():
        print(f"  [{i + 1}] {row['company']} ({row['code']})  — 유사도 {row['score']:.0f}점")

    while True:
        choice = input("\n번호를 선택하세요 (0: 취소): ").strip()
        if choice == "0":
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(results):
            row = results.iloc[int(choice) - 1]
            return row["code"], row["company"]
        print("올바른 번호를 입력해주세요.")
    