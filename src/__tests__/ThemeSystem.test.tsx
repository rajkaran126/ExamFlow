import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { ThemeProvider, useTheme, THEMES } from '../contexts/ThemeContext';

function ThemeConsumer() {
  const { theme, setTheme, resolvedTheme } = useTheme();
  return (
    <div>
      <span data-testid="current-theme">{theme}</span>
      <span data-testid="resolved-theme">{resolvedTheme}</span>
      <button onClick={() => setTheme('dark')}>Set Dark</button>
      <button onClick={() => setTheme('terminal')}>Set Terminal</button>
      <button onClick={() => setTheme('roohafza')}>Set Roohafza</button>
      <button onClick={() => setTheme('high-contrast')}>Set High Contrast</button>
    </div>
  );
}

describe('Theme System & Persistence', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
  });

  it('renders default light theme initially', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );

    expect(screen.getByTestId('current-theme').textContent).toBe('light');
    expect(screen.getByTestId('resolved-theme').textContent).toBe('light');
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  });

  it('switches themes and persists selection to localStorage', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );

    fireEvent.click(screen.getByText('Set Terminal'));

    expect(screen.getByTestId('current-theme').textContent).toBe('terminal');
    expect(localStorage.getItem('examflow_theme')).toBe('terminal');
    expect(document.documentElement.getAttribute('data-theme')).toBe('terminal');
  });

  it('supports all 14 alternative themes plus light default', () => {
    expect(THEMES).toHaveLength(14);
    const themeIds = THEMES.map((t) => t.id);
    expect(themeIds).toContain('light');
    expect(themeIds).toContain('dark');
    expect(themeIds).toContain('system');
    expect(themeIds).toContain('high-contrast');
    expect(themeIds).toContain('retro');
    expect(themeIds).toContain('minimalist');
    expect(themeIds).toContain('nature');
    expect(themeIds).toContain('solarized-dark');
    expect(themeIds).toContain('nordic-frost');
    expect(themeIds).toContain('midnight-ocean');
    expect(themeIds).toContain('roohafza');
    expect(themeIds).toContain('minecraft');
    expect(themeIds).toContain('terminal');
    expect(themeIds).toContain('krik-party');
  });
});
