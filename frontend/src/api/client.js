import axios from "axios";

const BASE_URL = "http://localhost:8000";

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Search Stocks

export const searchStock = (query, topN = 5) =>
  client.get("/stocks/search", { params: { query, top_n: topN } });

export const getOHLCV = (ticker, market = "us", years = 3) =>
  client.post("/stocks/ohlcv", { ticker, market, years });

export const getMarketRegime = (ticker, market = "us", years = 3) =>
  client.post("/stocks/regime", { ticker, market, years });

// Analysis

export const getIndicators = (
  ticker,
  market = "us",
  years = 3,
  indicators = ["sma", "ema", "rsi", "macd", "bollinger"],
) => client.post("/analysis/indicators", { ticker, market, years, indicators });

export const getPatterns = (ticker, market = "us", years = 3) =>
  client.post("/analysis/patterns", { ticker, market, years });

// Strategy

export const getSignals = (
  ticker,
  market = "us",
  years = 3,
  strategy = "sma",
  shortWindow = 50,
  longWindow = 200,
) =>
  client.post("/strategy/signals", {
    ticker,
    market,
    years,
    strategy,
    short_window: shortWindow,
    long_window: longWindow,
  });

// Backtesting

export const runBacktest = (params) => client.post("/backtest/run", params);

export const compareStrategies = (params) =>
  client.post("/backtest/compare", params);

// Portfolio

export const analyzePortfolio = (tickers, years = 3, weightMethod = "equal") =>
  client.post("/portfolio/analyze", {
    tickers,
    years,
    weight_method: weightMethod,
  });

export const backtestPortfolio = (params) =>
  client.post("/portfolio/backtest", params);
