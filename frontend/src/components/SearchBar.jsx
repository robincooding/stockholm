import { useState } from 'react';
import { searchStock } from '../api/client';

export default function SearchBar({ onSelect, market = 'us' }) {
  const [query,   setQuery]   = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    if (market === 'us') {
      // 해외 주식은 티커 직접 입력
      onSelect(query.toUpperCase());
      setResults([]);
      return;
    }
    setLoading(true);
    try {
      const res = await searchStock(query);
      setResults(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSearch();
  };

  return (
    <div className="relative w-full">
      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={market === 'kr' ? '종목명 검색 (예: 삼성전)' : '티커 입력 (예: AAPL)'}
          className="flex-1 bg-cardbg border border-border rounded-lg px-4 py-2 text-white placeholder-neutral text-sm focus:outline-none focus:border-accent"
        />
        <button
          onClick={handleSearch}
          disabled={loading}
          className="bg-accent hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
        >
          {loading ? '검색 중...' : '검색'}
        </button>
      </div>

      {/* 검색 결과 드롭다운 */}
      {results.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-cardbg border border-border rounded-lg overflow-hidden z-10 shadow-xl">
          {results.map((r) => (
            <button
              key={r.code}
              onClick={() => {
                onSelect(r.company);
                setQuery(r.company);
                setResults([]);
              }}
              className="w-full flex items-center justify-between px-4 py-3 hover:bg-border text-left transition-colors"
            >
              <span className="text-white text-sm">{r.company}</span>
              <span className="text-neutral text-xs">{r.code}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}