import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import SearchBar from '../components/SearchBar';

const FEATURES = [
  {
    icon: "📊",
    title: "기술적 지표",
    desc: "SMA, EMA, RSI, MACD, 볼린저밴드 등 핵심 지표를 한눈에"
  },
  {
    icon: "🎯",
    title: "전략 백테스팅",
    desc: "다양한 전략의 과거 수익률, MDD, 샤프지수를 시뮬레이션"
  },
  {
    icon: "🛡️",
    title: "리스크 관리",
    desc: "손절/익절, 트레일링 스탑, Kelly 포지션 사이징"
  },
  {
    icon: "🌐",
    title: "시장 국면 감지",
    desc: "ADX, OBV, Stochastic 기반 상승/하락/횡보장 자동 분류"
  },
  {
    icon: "💼",
    title: "포트폴리오 분석",
    desc: "리스크 패리티, 최소분산, 상관관계 기반 최적 비중 산출"
  },
  {
    icon: "🔍",
    title: "퍼지 종목 검색",
    desc: "정확한 이름 몰라도 유사도 기반으로 한국 종목 검색"
  },
];

const STATS = [
  { value: "2,700+", label: "KRX 상장 종목" },
  { value: "10년",   label: "데이터 조회 기간" },
  { value: "5가지",  label: "분석 전략" },
  { value: "3가지",  label: "포트폴리오 최적화" },
];

export default function Home() {
  const [market, setMarket] = useState('us');
  const navigate = useNavigate();

  const handleSelect = (ticker) => {
    navigate(`/analysis?ticker=${ticker}&market=${market}`);
  };

  return (
    <div className="min-h-screen bg-darkbg">

      {/* 히어로 섹션 */}
      <section className="max-w-7xl mx-auto px-6 py-24 text-center">
        <div className="inline-flex items-center gap-2 bg-accent/10 border border-accent/30 rounded-full px-4 py-1 text-accent text-xs mb-6">
          📈 한국 / 해외 주식 기술적 분석 시스템
        </div>
        <h1 className="text-5xl font-bold text-white mb-4 leading-tight">
          데이터로 읽는<br />
          <span className="text-accent">당신의 투자</span>
        </h1>
        <p className="text-neutral text-lg mb-12 max-w-xl mx-auto">
          Stockholm은 주식 기술적 분석과 백테스팅을 위한
          오픈소스 분석 도구입니다.
        </p>

        {/* 검색 영역 */}
        <div className="max-w-xl mx-auto">
          {/* 마켓 선택 */}
          <div className="flex gap-2 mb-3 justify-center">
            {['us', 'kr'].map((m) => (
              <button
                key={m}
                onClick={() => setMarket(m)}
                className={`px-4 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                  market === m
                    ? 'bg-accent border-accent text-white'
                    : 'border-border text-neutral hover:text-white'
                }`}
              >
                {m === 'us' ? '🇺🇸 해외 주식' : '🇰🇷 한국 주식'}
              </button>
            ))}
          </div>
          <SearchBar onSelect={handleSelect} market={market} />
          <p className="text-neutral text-xs mt-2">
            {market === 'us'
              ? 'AAPL, TSLA, NVDA 등 티커를 입력하세요'
              : '삼성전자, 카카오 등 종목명을 입력하세요'}
          </p>
        </div>
      </section>

      {/* 통계 */}
      <section className="border-y border-border bg-cardbg/50">
        <div className="max-w-7xl mx-auto px-6 py-8 grid grid-cols-2 md:grid-cols-4 gap-6">
          {STATS.map((s) => (
            <div key={s.label} className="text-center">
              <div className="text-3xl font-bold text-accent">{s.value}</div>
              <div className="text-neutral text-sm mt-1">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* 기능 소개 */}
      <section className="max-w-7xl mx-auto px-6 py-20">
        <h2 className="text-2xl font-bold text-white text-center mb-12">
          주요 기능
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="bg-cardbg border border-border rounded-xl p-6 hover:border-accent/50 transition-colors"
            >
              <div className="text-3xl mb-3">{f.icon}</div>
              <h3 className="text-white font-semibold mb-2">{f.title}</h3>
              <p className="text-neutral text-sm leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-7xl mx-auto px-6 py-12 text-center">
        <div className="bg-cardbg border border-border rounded-2xl p-12">
          <h2 className="text-2xl font-bold text-white mb-4">
            지금 바로 분석을 시작해보세요
          </h2>
          <p className="text-neutral mb-8">
            종목을 검색하고 기술적 지표와 백테스팅 결과를 확인하세요.
          </p>
          <div className="flex gap-4 justify-center">
            <button
              onClick={() => navigate('/analysis')}
              className="bg-accent hover:bg-blue-600 text-white px-6 py-3 rounded-lg font-medium transition-colors"
            >
              분석 시작하기
            </button>
            <button
              onClick={() => navigate('/about')}
              className="border border-border hover:border-accent text-neutral hover:text-white px-6 py-3 rounded-lg font-medium transition-colors"
            >
              프로젝트 소개
            </button>
          </div>
        </div>
      </section>

    </div>
  );
}