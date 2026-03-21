import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import Home from './pages/Home';
import Analysis from './pages/Analysis';
import Portfolio from './pages/Portfolio';
import About from './pages/About';

function Navbar() {
  const linkClass = ({ isActive }) =>
    `px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? 'bg-accent text-white'
        : 'text-gray-400 hover:text-white hover:bg-border'
    }`;

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-cardbg border-b border-border">
      <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-2xl">📈</span>
          <span className="text-white font-bold text-lg">Stockholm</span>
          <span className="text-neutral text-xs ml-1">v1.0</span>
        </div>
        <div className="flex gap-2">
          <NavLink to="/"          className={linkClass}>홈</NavLink>
          <NavLink to="/analysis"  className={linkClass}>분석</NavLink>
          <NavLink to="/portfolio" className={linkClass}>포트폴리오</NavLink>
          <NavLink to="/about"     className={linkClass}>소개</NavLink>
        </div>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-darkbg">
        <Navbar />
        <main className="pt-16">
          <Routes>
            <Route path="/"          element={<Home />} />
            <Route path="/analysis"  element={<Analysis />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/about"     element={<About />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}