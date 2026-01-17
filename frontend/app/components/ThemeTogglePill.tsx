'use client';

import { useState, useEffect } from 'react';
import { Sun, Moon } from 'lucide-react';

export default function ThemeTogglePill() {
  const [isDark, setIsDark] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
      setIsDark(true);
      document.documentElement.classList.add('dark');
    } else {
      setIsDark(false);
      document.documentElement.classList.remove('dark');
    }
  }, []);

  const toggleTheme = () => {
    const newIsDark = !isDark;
    setIsDark(newIsDark);
    document.documentElement.classList.toggle('dark', newIsDark);
    localStorage.setItem('theme', newIsDark ? 'dark' : 'light');
  };

  if (!mounted) {
    return <div className="w-16 h-8 rounded-full bg-neutral-200 dark:bg-neutral-800" />;
  }

  return (
    <button
      onClick={toggleTheme}
      aria-label="Toggle theme"
      aria-pressed={isDark}
      className={`
        relative w-16 h-8 rounded-full border
        focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]
        ${isDark 
          ? 'bg-neutral-900 border-neutral-700' 
          : 'bg-neutral-100 border-neutral-300'
        }
      `}
    >
      {/* Sun icon - left side */}
      <span className={`absolute left-1.5 top-1/2 -translate-y-1/2 ${isDark ? 'text-neutral-600' : 'text-amber-500'}`}>
        <Sun className="w-4 h-4" strokeWidth={2} />
      </span>

      {/* Moon icon - right side */}
      <span className={`absolute right-1.5 top-1/2 -translate-y-1/2 ${isDark ? 'text-neutral-300' : 'text-neutral-400'}`}>
        <Moon className="w-4 h-4" strokeWidth={2} />
      </span>

      {/* Sliding knob */}
      <span 
        className={`
          absolute top-0.5 w-7 h-7 rounded-full transition-transform duration-200 ease-out
          flex items-center justify-center
          ${isDark 
            ? 'translate-x-[32px] bg-neutral-700' 
            : 'translate-x-0.5 bg-white shadow-sm'
          }
        `}
      >
        {isDark ? (
          <Moon className="w-3.5 h-3.5 text-neutral-300" strokeWidth={2} />
        ) : (
          <Sun className="w-3.5 h-3.5 text-amber-500" strokeWidth={2} />
        )}
      </span>
    </button>
  );
}

