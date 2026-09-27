import { createContext, useContext, useEffect, useState } from 'react';

const STORAGE_KEY = 'retainhq-theme';
// Set by the pre-paint script in index.html for first-time logged-out visitors
// on "/" (landing-theme A/B). Read-only here.
const VARIANT_KEY = 'retainhq-landing-variant';

const ThemeContext = createContext({
  theme: 'light',
  toggleTheme: () => {},
  setTheme: () => {},
});

function getInitialTheme() {
  if (typeof window === 'undefined') return 'light';
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'light' || stored === 'dark') return stored;
    const variant = localStorage.getItem(VARIANT_KEY);
    if (variant === 'light' || variant === 'dark') return variant;
  } catch {
    /* localStorage unavailable (private mode) */
  }
  // Warm white is the default for everyone — never the OS/system preference.
  return 'light';
}

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(getInitialTheme);

  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle('dark', theme === 'dark');
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      /* ignore persistence failures */
    }
  }, [theme]);

  const value = {
    theme,
    setTheme: setThemeState,
    toggleTheme: () => setThemeState((t) => (t === 'dark' ? 'light' : 'dark')),
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  return useContext(ThemeContext);
}
