import { useState } from 'react';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import StatCard from '../components/StatCard';
import PlotChart from '../components/PlotChart';
import { analyzePortfolio, backtestPortfolio } from '../api/client';

const WEIGHT_METHODS = [
  { value: 'equal',        label: '동일 비중' },
  { value: 'risk_parity',  label: '리스크 패리티' },
  { value: 'min_variance', label: '최소 분산' },
];

const REBALANCE_FREQS = [
  { value: 'none',      label: '없음' },
  { value: 'monthly',   label: '월별' },
  { value: 'quarterly', label: '분기' },
  { value: 'annual',    label: '연간' },
];

export default function Portfolio() {
  const [tickerInput,    setTickerInput]    = useState('AAPL,MSFT,GOOGL,NVDA,GLD');
  const [years,          setYears]          = useState(3);
  const [weightMethod,   setWeightMethod]   = useState('equal');
  const [rebalanceFreq,  setRebalanceFreq]  = useState('quarterly');
  const [loading,        setLoading]        = useState(false);
  const [error,          setError]          = useState(null);
  const [analysis,       setAnalysis]       = useState(null);
  const [backtest,       setBacktest]       = useState(null);

  const handleAnalyze = async () => {
    const tickers = tickerInput.split(',').map(t => t.trim().toUpperCase()).filter(Boolean);
    if (tickers.length < 2) {
      setError('최소 2개 이상의 종목을 입력해주세요.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const [anaRes, btRes] = await Promise.all([
        analyzePortfolio(tickers, years, weightMethod),
        backtestPortfolio({
          tickers,
          years,
          weight_method:   weightMethod,
          rebalance_freq:  rebalanceFreq,
          initial_capital: 10000000,
        }),
      ]);
      setAnalysis(anaRes.data);
      setBacktest(btRes.data);
    } catch (e) {
      setError(e.response?.data?.detail || '오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const weightChartData = () => {
    if (!analysis) return [];
    const tickers = Object.keys(analysis.weights);
    return [{
      type:   'pie',
      labels: tickers,
      values: tickers.map(t => analysis.weights[t]),
      hole:   0.4,
      marker: {
        colors: ['#2E86C1', '#27AE60', '#E74C3C', '#F39C12', '#8E44AD',
                 '#1ABC9C', '#E67E22', '#95A5A6'],
      },
      textinfo:     'label+percent',
      textfont:     { color: '#ECF0F1' },
      hovertemplate: '%{label}: %{percent}<extra></extra>',
    }];
  };

  const corrHeatmap = () => {
    if (!analysis?.correlation) return [];
    const tickers = Object.keys(analysis.correlation);
    const z = tickers.map(t1 =>
      tickers.map(t2 => analysis.correlation[t1]?.[t2] ?? 0)
    );
    return [{
      type:        'heatmap',
      x:           tickers,
      y:           tickers,
      z,
      colorscale:  'RdBu',
      reversescale: true,
      zmin: -1, zmax: 1,
      text:        z.map(row => row.map(v => v.toFixed(2))),
      texttemplate: '%{text}',
      textfont:    { color: '#ECF0F1', size: 11 },
    }];
  };

  const plotLayout = (title) => ({
    title:         { text: title, font: { color: '#ECF0F1', size: 14 } },
    paper_bgcolor: '#1A2535',
    plot_bgcolor:  '#1A2535',
    font:          { color: '#ECF0F1' },
    margin:        { t: 40, r: 20, b: 40, l: 60 },
  });

  const plotConfig = { responsive: true, displayModeBar: false };

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <h1 className="text-2xl font-bold text-white mb-6">포트폴리오 분석</h1>

      {/* 설정 영역 */}
      <div className="bg-cardbg border border-border rounded-xl p-6 mb-6">
        <div className="mb-4">
          <label className="text-neutral text-xs mb-1 block">
            종목 입력 (쉼표로 구분)
          </label>
          <input
            type="text"
            value={tickerInput}
            onChange={e => setTickerInput(e.target.value)}
            placeholder="AAPL, MSFT, GOOGL, NVDA, GLD"
            className="w-full bg-darkbg border border-border rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:border-accent"
          />
        </div>

        <div className="flex flex-wrap gap-4 mb-4">
          <div>
            <label className="text-neutral text-xs mb-1 block">기간</label>
            <select
              value={years}
              onChange={e => setYears(Number(e.target.value))}
              className="bg-darkbg border border-border rounded-lg px-3 py-1.5 text-white text-xs focus:outline-none focus:border-accent"
            >
              {[1, 2, 3, 5].map(y => (
                <option key={y} value={y}>{y}년</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-neutral text-xs mb-1 block">비중 방식</label>
            <select
              value={weightMethod}
              onChange={e => setWeightMethod(e.target.value)}
              className="bg-darkbg border border-border rounded-lg px-3 py-1.5 text-white text-xs focus:outline-none focus:border-accent"
            >
              {WEIGHT_METHODS.map(m => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-neutral text-xs mb-1 block">리밸런싱</label>
            <select
              value={rebalanceFreq}
              onChange={e => setRebalanceFreq(e.target.value)}
              className="bg-darkbg border border-border rounded-lg px-3 py-1.5 text-white text-xs focus:outline-none focus:border-accent"
            >
              {REBALANCE_FREQS.map(f => (
                <option key={f.value} value={f.value}>{f.label}</option>
              ))}
            </select>
          </div>
        </div>

        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="bg-accent hover:bg-blue-600 text-white px-6 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
        >
          {loading ? '분석 중...' : '포트폴리오 분석'}
        </button>
      </div>

      {loading && <LoadingSpinner message="포트폴리오 분석 중..." />}
      {error   && <ErrorMessage message={error} />}

      {!loading && backtest && analysis && (
        <>
          {/* 성과 카드 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <StatCard
              label="총 수익률"
              value={`${backtest.total_return.toFixed(2)}`}
              unit="%"
              color={backtest.total_return >= 0 ? 'text-bull' : 'text-bear'}
            />
            <StatCard
              label="연간 수익률"
              value={`${backtest.annual_return.toFixed(2)}`}
              unit="%"
              color={backtest.annual_return >= 0 ? 'text-bull' : 'text-bear'}
            />
            <StatCard
              label="연간 변동성"
              value={`${backtest.volatility.toFixed(2)}`}
              unit="%"
              color="text-neutral"
            />
            <StatCard
              label="샤프 지수"
              value={backtest.sharpe_ratio.toFixed(2)}
              color={backtest.sharpe_ratio >= 1 ? 'text-bull' : 'text-neutral'}
            />
            <StatCard
              label="MDD"
              value={`${backtest.mdd.toFixed(2)}`}
              unit="%"
              color="text-bear"
            />
            <StatCard
              label="최종 자산"
              value={(backtest.final_value / 10000).toFixed(0)}
              unit="만원"
              color="text-white"
            />
            <StatCard
              label="평균 상관계수"
              value={analysis.avg_corr.toFixed(3)}
              color="text-accent"
            />
            <StatCard
              label="분산 평가"
              value={analysis.summary}
              color="text-white"
            />
          </div>

          {/* 차트 영역 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            {/* 비중 파이 차트 */}
            <div className="bg-cardbg border border-border rounded-xl p-4">
              <PlotChart
                data={weightChartData()}
                layout={{
                  ...plotLayout('포트폴리오 비중'),
                  showlegend: false,
                }}
                config={plotConfig}
                style={{ width: '100%', height: '300px' }}
              />
            </div>

            {/* 상관관계 히트맵 */}
            <div className="bg-cardbg border border-border rounded-xl p-4">
              <PlotChart
                data={corrHeatmap()}
                layout={{
                  ...plotLayout('종목 간 상관관계'),
                  xaxis: { color: '#ECF0F1' },
                  yaxis: { color: '#ECF0F1' },
                }}
                config={plotConfig}
                style={{ width: '100%', height: '300px' }}
              />
            </div>
          </div>

          {/* 종목별 수익률 테이블 */}
          <div className="bg-cardbg border border-border rounded-xl p-6">
            <h3 className="text-white font-semibold mb-4">종목별 비중 & 수익률</h3>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-neutral border-b border-border">
                  <th className="text-left py-2">종목</th>
                  <th className="text-right py-2">비중</th>
                  <th className="text-right py-2">수익률</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(analysis.weights).map(([ticker, weight]) => {
                  const ret = backtest.ticker_returns?.[ticker] ?? 0;
                  return (
                    <tr key={ticker} className="border-b border-border/50">
                      <td className="py-2 text-white font-medium">{ticker}</td>
                      <td className="py-2 text-right text-neutral">
                        {(weight * 100).toFixed(1)}%
                      </td>
                      <td className={`py-2 text-right font-medium ${
                        ret >= 0 ? 'text-bull' : 'text-bear'
                      }`}>
                        {ret.toFixed(2)}%
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}