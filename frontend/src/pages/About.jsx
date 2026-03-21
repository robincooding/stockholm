const PHASES = [
  { phase: "Phase 1", title: "데이터 수집",        desc: "KRX/네이버 금융/Yahoo Finance 연동, 퍼지 종목명 검색",      done: true },
  { phase: "Phase 2", title: "기술적 지표",         desc: "SMA, EMA, RSI, MACD, 볼린저밴드, 지지/저항선, 추세선",     done: true },
  { phase: "Phase 3", title: "전략 & 백테스팅",     desc: "SMA/EMA 크로스 전략, 수익률/MDD/샤프 지수 리포트",         done: true },
  { phase: "Phase 4", title: "시각화",              desc: "통합 대시보드, RSI/MACD 차트, 백테스팅 수익률 비교",        done: true },
  { phase: "Phase 5", title: "고급 분석",           desc: "지표 조합 전략, 시장 국면 감지, 리스크 관리, 포트폴리오",   done: true },
  { phase: "Phase 6", title: "웹 애플리케이션",     desc: "FastAPI 백엔드 + React 프론트엔드",                         done: true },
];

const STACK = [
  { category: "백엔드",     items: ["Python 3.13", "FastAPI", "pandas", "scikit-learn", "hdbscan", "scipy"] },
  { category: "프론트엔드", items: ["React", "Vite", "Tailwind CSS v4", "Plotly.js", "React Router"] },
  { category: "데이터",     items: ["네이버 금융", "Yahoo Finance", "KRX"] },
  { category: "분석",       items: ["HDBSCAN 클러스터링", "Kelly 공식", "리스크 패리티", "최소 분산"] },
];

export default function About() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-12">

      {/* 헤더 */}
      <div className="text-center mb-16">
        <div className="text-5xl mb-4">📈</div>
        <h1 className="text-4xl font-bold text-white mb-3">Stockholm</h1>
        <p className="text-accent text-lg mb-4">주식 기술적 분석 & 백테스팅 시스템</p>
        <p className="text-neutral leading-relaxed max-w-2xl mx-auto">
          2022년에 작성된 주식 분석 스크립트를 모듈화된 라이브러리로 리팩토링하고,
          FastAPI + React 기반 웹 애플리케이션으로 발전시킨 포트폴리오 프로젝트입니다.
        </p>
      </div>

      {/* 개발 배경 */}
      <section className="mb-16">
        <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
          <span className="text-accent">01</span> 개발 배경
        </h2>
        <div className="bg-cardbg border border-border rounded-xl p-6 text-neutral leading-relaxed space-y-3">
          <p>
            2022년 금융 데이터 분석에 관심을 가지게 되면서 Python으로 주식 기술적 분석
            스크립트를 작성했습니다. 당시에는 시간과 지식의 부족으로 4개의 독립된
            스크립트에 코드가 흩어져 있었고, 백테스팅과 같은 핵심 기능이 미완성인
            상태였습니다.
          </p>
          <p>
            이후 Python과 소프트웨어 설계에 대한 이해가 깊어지면서 기존 코드를
            역할별 패키지로 재구성하고, 미완성 기능을 완성하는 리팩토링 작업을
            진행했습니다. 최종적으로 FastAPI + React 기반 웹 애플리케이션으로
            발전시켜 누구나 쉽게 사용할 수 있는 형태로 완성했습니다.
          </p>
        </div>
      </section>

      {/* 개발 과정 */}
      <section className="mb-16">
        <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
          <span className="text-accent">02</span> 개발 과정
        </h2>
        <div className="space-y-3">
          {PHASES.map((p) => (
            <div
              key={p.phase}
              className="flex items-start gap-4 bg-cardbg border border-border rounded-xl p-4"
            >
              <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                p.done ? 'bg-bull' : 'bg-border'
              }`}>
                {p.done && <span className="text-white text-xs">✓</span>}
              </div>
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-accent text-xs font-medium">{p.phase}</span>
                  <span className="text-white text-sm font-semibold">{p.title}</span>
                </div>
                <p className="text-neutral text-sm">{p.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 기술 스택 */}
      <section className="mb-16">
        <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
          <span className="text-accent">03</span> 기술 스택
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {STACK.map((s) => (
            <div key={s.category} className="bg-cardbg border border-border rounded-xl p-5">
              <h3 className="text-accent text-sm font-medium mb-3">{s.category}</h3>
              <div className="flex flex-wrap gap-2">
                {s.items.map((item) => (
                  <span
                    key={item}
                    className="bg-darkbg border border-border rounded-full px-3 py-1 text-neutral text-xs"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* GitHub 링크 */}
      <div className="text-center">
        <a
          href="https://github.com/robincooding/stockholm"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 bg-cardbg border border-border hover:border-accent text-neutral hover:text-white px-6 py-3 rounded-lg text-sm font-medium transition-colors"
        >
          <span>⭐</span> GitHub에서 보기
        </a>
      </div>

    </div>
  );
}