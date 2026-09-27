import { createContext, useContext, useEffect, useState } from 'react';
import { onLandingThemeVariant } from './analytics';

const STORAGE_KEY = 'retainhq-theme';

const ThemeContext = createContext({
  theme: 'light',
  toggleTheme: () => {},
  setTheme: () => {},
});

function hasStoredTheme() {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'light' || localStorage.getItem(STORAGE_KEY) === 'dark';
  } catch {
    return false;
  }
}

function getInitialTheme() {
  if (typeof window === 'undefined') return 'light';
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'light' || stored === 'dark') return stored;
  } catch {
    /* localStorage unavailable (private mode) */
  }
  // Warm white is the default for everyone — never the OS/system preference.
  // Dark is opt-in, either via the toggle or (for a first-time visitor with no
  // stored preference) the landing-page theme experiment below.
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

  // First-time, no-preference visitors only: let the PostHog "landing-theme"
  // experiment pick light/dark. Anyone who already has a stored preference
  // (including a returning visitor who was previously bucketed) is untouched —
  // this never fights the user's own toggle.
  useEffect(() => {
    if (hasStoredTheme()) return;
    onLandingThemeVariant((variant) => setThemeState(variant));
  }, []);

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
