import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import SearchBar from '../components/SearchBar';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import StatCard from '../components/StatCard';
import RegimeBadge from '../components/RegimeBadge';
import PlotChart from '../components/PlotChart';
import {
  getIndicators, getPatterns, getSignals,
  runBacktest, getMarketRegime,
} from '../api/client';

const STRATEGIES = [
  { value: 'sma',           label: 'SMA 크로스' },
  { value: 'ema',           label: 'EMA 크로스' },
  { value: 'smaema',        label: 'SMA-EMA 크로스' },
  { value: 'rsimacd',       label: 'RSI+MACD 조합' },
  { value: 'bollinger_rsi', label: 'Bollinger+RSI 조합' },
];

export default function Analysis() {
  const [searchParams] = useSearchParams();
  const [market,    setMarket]    = useState(searchParams.get('market') || 'us');
  const [ticker,    setTicker]    = useState(searchParams.get('ticker') || '');
  const [years,     setYears]     = useState(3);
  const [strategy,  setStrategy]  = useState('sma');
  const [tab,       setTab]       = useState('chart');

  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState(null);
  const [data,     setData]     = useState(null);
  const [patterns, setPatterns] = useState(null);
  const [signals,  setSignals]  = useState(null);
  const [backtest, setBacktest] = useState(null);
  const [regime,   setRegime]   = useState(null);

  const handleAnalyze = useCallback(async () => {
    if (!ticker) return;
    setLoading(true);
    setError(null);

    try {
      const [indRes, patRes, sigRes, btRes, regRes] = await Promise.all([
        getIndicators(ticker, market, years),
        getPatterns(ticker, market, years),
        getSignals(ticker, market, years, strategy),
        runBacktest({ ticker, market, years, strategy, initial_capital: 10000000, stop_loss: 0.05, take_profit: 0.15 }),
        getMarketRegime(ticker, market, years),
      ]);

      setData(indRes.data);
      setPatterns(patRes.data);
      setSignals(sigRes.data);
      setBacktest(btRes.data);
      setRegime(regRes.data);
    } catch (e) {
      setError(e.response?.data?.detail || '데이터를 불러오는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  }, [ticker, market, years, strategy]);

  useEffect(() => {
    if (ticker) handleAnalyze();
  }, [ticker, handleAnalyze]);

  // 차트 데이터
  const chartData = () => {
    if (!data?.data) return [];
    const df = data.data;
    const dates = df.map(d => d.date);

    const traces = [
      {
        x: dates, y: df.map(d => d.close),
        type: 'scatter', name: '종가',
        line: { color: '#ECF0F1', width: 1.5 },
      },
      {
        x: dates, y: df.map(d => d.SMA_50),
        type: 'scatter', name: 'SMA 50',
        line: { color: '#E74C3C', width: 1, dash: 'dot' },
      },
      {
        x: dates, y: df.map(d => d.SMA_200),
        type: 'scatter', name: 'SMA 200',
        line: { color: '#3498DB', width: 1, dash: 'dot' },
      },
    ];

    // 매수/매도 신호
    if (signals?.signals) {
      const buys  = signals.signals.filter(s => s.signal === 1);
      const sells = signals.signals.filter(s => s.signal === -1);
      traces.push({
        x: buys.map(s => s.date), y: buys.map(s => s.close),
        type: 'scatter', mode: 'markers', name: '매수',
        marker: { color: '#27AE60', size: 10, symbol: 'triangle-up' },
      });
      traces.push({
        x: sells.map(s => s.date), y: sells.map(s => s.close),
        type: 'scatter', mode: 'markers', name: '매도',
        marker: { color: '#E74C3C', size: 10, symbol: 'triangle-down' },
      });
    }

    // 지지선 / 저항선
    if (patterns) {
      patterns.support?.forEach(price => {
        traces.push({
          x: [dates[0], dates[dates.length - 1]],
          y: [price, price],
          type: 'scatter', name: `지지 ${price}`,
          line: { color: '#3498DB', width: 1, dash: 'dash' },
          showlegend: false,
        });
      });
      patterns.resistance?.forEach(price => {
        traces.push({
          x: [dates[0], dates[dates.length - 1]],
          y: [price, price],
          type: 'scatter', name: `저항 ${price}`,
          line: { color: '#E74C3C', width: 1, dash: 'dash' },
          showlegend: false,
        });
      });
    }

    return traces;
  };

  const rsiData = () => {
    if (!data?.data) return [];
    const df = data.data;
    return [{
      x: df.map(d => d.date),
      y: df.map(d => d.RSI_14),
      type: 'scatter', name: 'RSI',
      line: { color: '#8E44AD', width: 1.5 },
    }];
  };

  const macdData = () => {
    if (!data?.data) return [];
    const df = data.data;
    return [
      {
        x: df.map(d => d.date), y: df.map(d => d.MACD),
        type: 'scatter', name: 'MACD',
        line: { color: '#E74C3C', width: 1.5 },
      },
      {
        x: df.map(d => d.date), y: df.map(d => d.MACD_signal),
        type: 'scatter', name: 'Signal',
        line: { color: '#3498DB', width: 1.5 },
      },
      {
        x: df.map(d => d.date), y: df.map(d => d.MACD_hist),
        type: 'bar', name: 'Histogram',
        marker: { color: df.map(d => d.MACD_hist >= 0 ? '#27AE60' : '#E74C3C') },
      },
    ];
  };

  const plotLayout = (title, yTitle = '가격') => ({
    title:       { text: title, font: { color: '#ECF0F1', size: 14 } },
    paper_bgcolor: '#1A2535',
    plot_bgcolor:  '#1A2535',
    font:        { color: '#ECF0F1' },
    xaxis:       { gridcolor: '#2C3E50', color: '#ECF0F1' },
    yaxis:       { gridcolor: '#2C3E50', color: '#ECF0F1', title: yTitle },
    legend:      { bgcolor: 'transparent', font: { color: '#ECF0F1' } },
    margin:      { t: 40, r: 20, b: 40, l: 60 },
  });

  const plotConfig = { responsive: true, displayModeBar: false };

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <h1 className="text-2xl font-bold text-white mb-6">종목 분석</h1>

      {/* 검색 영역 */}
      <div className="bg-cardbg border border-border rounded-xl p-6 mb-6">
        <div className="flex flex-wrap gap-4 mb-4">

          {/* 마켓 선택 */}
          <div className="flex gap-2">
            {['us', 'kr'].map(m => (
              <button
                key={m}
                onClick={() => setMarket(m)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                  market === m
                    ? 'bg-accent border-accent text-white'
                    : 'border-border text-neutral hover:text-white'
                }`}
              >
                {m === 'us' ? '🇺🇸 해외' : '🇰🇷 한국'}
              </button>
            ))}
          </div>

          {/* 기간 선택 */}
          <select
            value={years}
            onChange={e => setYears(Number(e.target.value))}
            className="bg-cardbg border border-border rounded-lg px-3 py-1.5 text-white text-xs focus:outline-none focus:border-accent"
          >
            {[1, 2, 3, 5, 10].map(y => (
              <option key={y} value={y}>{y}년</option>
            ))}
          </select>

          {/* 전략 선택 */}
          <select
            value={strategy}
            onChange={e => setStrategy(e.target.value)}
            className="bg-cardbg border border-border rounded-lg px-3 py-1.5 text-white text-xs focus:outline-none focus:border-accent"
          >
            {STRATEGIES.map(s => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>

        <div className="flex gap-3">
          <div className="flex-1">
            <SearchBar
              onSelect={t => setTicker(t)}
              market={market}
            />
          </div>
          <button
            onClick={handleAnalyze}
            disabled={!ticker || loading}
            className="bg-accent hover:bg-blue-600 text-white px-6 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            분석
          </button>
        </div>
      </div>

      {/* 로딩 / 에러 */}
      {loading && <LoadingSpinner message="분석 중..." />}
      {error   && <ErrorMessage message={error} />}

      {/* 결과 */}
      {!loading && backtest && (
        <>
          {/* 시장 국면 + 백테스팅 요약 */}
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-lg font-semibold text-white">{ticker}</h2>
            {regime && <RegimeBadge regime={regime.current_regime} />}
            {regime && (
              <span className="text-neutral text-xs">
                추천: {regime.recommended}
              </span>
            )}
          </div>

          {/* 성과 카드 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <StatCard
              label="전략 수익률"
              value={`${backtest.total_return.toFixed(2)}`}
              unit="%"
              color={backtest.total_return >= 0 ? 'text-bull' : 'text-bear'}
            />
            <StatCard
              label="시장 수익률"
              value={`${backtest.market_return.toFixed(2)}`}
              unit="%"
              color="text-accent"
            />
            <StatCard
              label="MDD"
              value={`${backtest.mdd.toFixed(2)}`}
              unit="%"
              color="text-bear"
            />
            <StatCard
              label="샤프 지수"
              value={backtest.sharpe_ratio.toFixed(2)}
              color={backtest.sharpe_ratio >= 1 ? 'text-bull' : 'text-neutral'}
            />
            <StatCard
              label="승률"
              value={`${backtest.win_rate.toFixed(1)}`}
              unit="%"
              color="text-white"
            />
            <StatCard
              label="총 거래"
              value={backtest.total_trades}
              unit="회"
              color="text-white"
            />
            <StatCard
              label="연간 수익률"
              value={`${backtest.annual_return.toFixed(2)}`}
              unit="%"
              color={backtest.annual_return >= 0 ? 'text-bull' : 'text-bear'}
            />
            <StatCard
              label="최종 자산"
              value={(backtest.final_value / 10000).toFixed(0)}
              unit="만원"
              color="text-white"
            />
          </div>

          {/* 탭 */}
          <div className="flex gap-2 mb-4">
            {[
              { key: 'chart', label: '가격 차트' },
              { key: 'rsi',   label: 'RSI' },
              { key: 'macd',  label: 'MACD' },
            ].map(t => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  tab === t.key
                    ? 'bg-accent text-white'
                    : 'bg-cardbg border border-border text-neutral hover:text-white'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* 차트 */}
          <div className="bg-cardbg border border-border rounded-xl p-4">
            {tab === 'chart' && (
              <PlotChart
                data={chartData()}
                layout={plotLayout(`${ticker} 가격 & 신호`)}
                config={plotConfig}
                style={{ width: '100%', height: '450px' }}
              />
            )}
            {tab === 'rsi' && (
              <>
                <PlotChart
                  data={rsiData()}
                  layout={{
                    ...plotLayout(`${ticker} RSI`, 'RSI'),
                    shapes: [
                      { type: 'line', x0: 0, x1: 1, xref: 'paper', y0: 70, y1: 70,
                        line: { color: '#E74C3C', width: 1, dash: 'dash' } },
                      { type: 'line', x0: 0, x1: 1, xref: 'paper', y0: 30, y1: 30,
                        line: { color: '#3498DB', width: 1, dash: 'dash' } },
                    ],
                    yaxis: { range: [0, 100], gridcolor: '#2C3E50', color: '#ECF0F1' },
                  }}
                  config={plotConfig}
                  style={{ width: '100%', height: '300px' }}
                />
              </>
            )}
            {tab === 'macd' && (
              <PlotChart
                data={macdData()}
                layout={plotLayout(`${ticker} MACD`, 'MACD')}
                config={plotConfig}
                style={{ width: '100%', height: '300px' }}
              />
            )}
          </div>
        </>
      )}
    </div>
  );
}