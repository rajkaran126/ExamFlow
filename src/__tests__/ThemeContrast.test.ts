import { describe, it, expect } from 'vitest';

// WCAG relative luminance formula
function getLuminance(r: number, g: number, b: number): number {
  const [rs, gs, bs] = [r, g, b].map((c) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

function getContrastRatio(hex1: string, hex2: string): number {
  const parseHex = (h: string) => {
    const clean = h.replace('#', '').trim();
    if (clean.length === 3) {
      return [
        parseInt(clean[0] + clean[0], 16),
        parseInt(clean[1] + clean[1], 16),
        parseInt(clean[2] + clean[2], 16),
      ];
    }
    return [
      parseInt(clean.substring(0, 2), 16),
      parseInt(clean.substring(2, 4), 16),
      parseInt(clean.substring(4, 6), 16),
    ];
  };

  const [r1, g1, b1] = parseHex(hex1);
  const [r2, g2, b2] = parseHex(hex2);

  const l1 = getLuminance(r1, g1, b1);
  const l2 = getLuminance(r2, g2, b2);

  const brightest = Math.max(l1, l2);
  const darkest = Math.min(l1, l2);

  return (brightest + 0.05) / (darkest + 0.05);
}

describe('Theme Contrast & WCAG AA Verification', () => {
  const themePairs = [
    { name: 'Light', bg: '#ffffff', fg: '#1a1a2e', primary: '#4263eb', primaryFg: '#ffffff' },
    { name: 'Dark', bg: '#0f0f1a', fg: '#e9ecef', primary: '#748ffc', primaryFg: '#0f0f1a' },
    { name: 'High Contrast', bg: '#000000', fg: '#ffffff', primary: '#5599ff', primaryFg: '#000000' },
    { name: 'Retro', bg: '#fdf6e3', fg: '#3b3024', primary: '#b35900', primaryFg: '#fdf6e3' },
    { name: 'Minimalist', bg: '#fafafa', fg: '#212121', primary: '#212121', primaryFg: '#ffffff' },
    { name: 'Nature', bg: '#f5f0e8', fg: '#2d3a2d', primary: '#4a7c59', primaryFg: '#f5f0e8' },
    { name: 'Solarized Dark', bg: '#002b36', fg: '#fdf6e3', primary: '#268bd2', primaryFg: '#fdf6e3' },
    { name: 'Nordic Frost', bg: '#eceff4', fg: '#2e3440', primary: '#5e81ac', primaryFg: '#eceff4' },
    { name: 'Midnight Ocean', bg: '#0a1628', fg: '#e0e8f0', primary: '#0ea5e9', primaryFg: '#0a1628' },
    { name: 'Roohafza', bg: '#fff5f5', fg: '#4a1520', primary: '#c41e3a', primaryFg: '#fff5f5' },
    { name: 'Minecraft', bg: '#c6a96c', fg: '#3b2d1a', primary: '#5a8f3c', primaryFg: '#ffffff' },
    { name: 'Terminal', bg: '#0c0c0c', fg: '#00ff00', primary: '#00ff00', primaryFg: '#0c0c0c' },
    { name: 'Krik Party', bg: '#1a0a2e', fg: '#f0e6ff', primary: '#e040fb', primaryFg: '#1a0a2e' },
  ];

  themePairs.forEach(({ name, bg, fg, primary, primaryFg }) => {
    it(`theme ${name} satisfies WCAG AA contrast ratio (>= 4.5:1 for body, >= 3.0:1 for primary button)`, () => {
      const textContrast = getContrastRatio(bg, fg);
      const buttonContrast = getContrastRatio(primary, primaryFg);

      // Body text >= 4.5:1
      expect(textContrast).toBeGreaterThanOrEqual(4.5);
      // Interactive primary indicator >= 3.0:1
      expect(buttonContrast).toBeGreaterThanOrEqual(3.0);
    });
  });
});
