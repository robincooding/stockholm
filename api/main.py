"""
Stockholm FastAPI 백엔드 entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import stocks, analysis, strategy, backtest, portfolio

app = FastAPI(
    title="Stockholm API",
    description="한국/해외 주식 기술적 분석 & 백테스팅 API",
    version="1.0.0",
)

# === CORS 설정 ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],  # React 개발 서버
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Router 등록 ===
app.include_router(stocks.router)
app.include_router(analysis.router)
app.include_router(strategy.router)
app.include_router(backtest.router)
app.include_router(portfolio.router)


@app.get("/")
def root():
    return {
        "name": "Stockholm API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
