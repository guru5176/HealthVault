import { useEffect, useState } from 'react';
import './ThemeToggle.css';

export default function ThemeToggle() {
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.remove('light');
    } else {
      document.documentElement.classList.add('light');
    }
  }, [isDark]);

  return (
    <div className="theme-toggle-container" onClick={() => setIsDark(!isDark)}>
      <div className={`theme-track ${isDark ? 'dark' : 'light'}`}>
        <div className="theme-clouds">☁️</div>
        <div className="theme-stars">✨</div>
        <div className={`theme-thumb ${isDark ? 'dark' : 'light'}`}>
          {isDark ? (
             <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#F5F5F5" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"></path></svg>
          ) : (
             <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#FFD700" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="4"></circle><path d="M12 2v2"></path><path d="M12 20v2"></path><path d="m4.93 4.93 1.41 1.41"></path><path d="m17.66 17.66 1.41 1.41"></path><path d="M2 12h2"></path><path d="M20 12h2"></path><path d="m6.34 17.66-1.41 1.41"></path><path d="m19.07 4.93-1.41 1.41"></path></svg>
          )}
        </div>
      </div>
    </div>
  );
}
