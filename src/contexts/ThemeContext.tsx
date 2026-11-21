// ============================================================
// EXAMFLOW – Theme Context
// ============================================================

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from 'react';

export const THEMES = [
  { id: 'light', label: 'Light' },
  { id: 'dark', label: 'Dark' },
  { id: 'system', label: 'System' },
  { id: 'high-contrast', label: 'High Contrast' },
  { id: 'retro', label: 'Retro / Vintage' },
  { id: 'minimalist', label: 'Minimalist' },
  { id: 'nature', label: 'Nature / Earthy' },
  { id: 'solarized-dark', label: 'Solarized Dark' },
  { id: 'nordic-frost', label: 'Nordic Frost' },
  { id: 'midnight-ocean', label: 'Midnight Ocean' },
  { id: 'roohafza', label: 'Roohafza' },
  { id: 'minecraft', label: 'Minecraft' },
  { id: 'terminal', label: 'Terminal' },
  { id: 'krik-party', label: 'Krik Party' },
] as const;

export type ThemeId = (typeof THEMES)[number]['id'];

interface ThemeContextValue {
  theme: ThemeId;
  resolvedTheme: Exclude<ThemeId, 'system'>;
  setTheme: (theme: ThemeId) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

const STORAGE_KEY = 'examflow_theme';

function getSystemTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches
    ? 'dark'
    : 'light';
}

function resolveTheme(theme: ThemeId): Exclude<ThemeId, 'system'> {
  if (theme === 'system') return getSystemTheme();
  return theme;
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<ThemeId>(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as ThemeId | null;
    if (stored && THEMES.some((t) => t.id === stored)) return stored;
    return 'light';
  });

  const [resolvedTheme, setResolvedTheme] = useState<Exclude<ThemeId, 'system'>>(
    () => resolveTheme(theme)
  );

  const setTheme = useCallback((newTheme: ThemeId) => {
    setThemeState(newTheme);
    localStorage.setItem(STORAGE_KEY, newTheme);
  }, []);

  // Apply theme attribute
  useEffect(() => {
    const resolved = resolveTheme(theme);
    setResolvedTheme(resolved);
    document.documentElement.setAttribute('data-theme', resolved);
  }, [theme]);

  // Listen for OS theme change when using system theme
  useEffect(() => {
    if (theme !== 'system') return;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => {
      const resolved = resolveTheme('system');
      setResolvedTheme(resolved);
      document.documentElement.setAttribute('data-theme', resolved);
    };
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within a ThemeProvider');
  return ctx;
}
