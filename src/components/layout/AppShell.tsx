// ============================================================
// EXAMFLOW – Application Shell Layout
// ============================================================

import { useState, useCallback } from 'react';
import { Outlet, useLocation, Link, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  ClipboardList,
  Users,
  FileText,
  Calculator,
  Shield,
  BarChart3,
  Award,
  ListOrdered,
  RotateCcw,
  Bot,
  Settings,
  Menu,
  X,
  Bell,
  ChevronRight,
  LogOut,
  Palette,
  User,
  PanelLeftClose,
  PanelLeft,
} from 'lucide-react';
import { useTheme, THEMES } from '../../contexts/ThemeContext';
import FloatingAssistant from '../chat/FloatingAssistant';

// ── Navigation Items ─────────────────────────────────────────

const NAV_ITEMS = [
  { path: '/app', icon: LayoutDashboard, label: 'Dashboard', end: true },
  { path: '/app/examinations', icon: ClipboardList, label: 'Examinations' },
  { path: '/app/candidates', icon: Users, label: 'Candidates' },
  { path: '/app/responses', icon: FileText, label: 'Response Management' },
  { path: '/app/evaluation', icon: Calculator, label: 'Evaluation Engine' },
  { path: '/app/proctoring', icon: Shield, label: 'Proctoring' },
  { path: '/app/normalisation', icon: BarChart3, label: 'Normalisation' },
  { path: '/app/results', icon: Award, label: 'Results & Scorecards' },
  { path: '/app/merit-list', icon: ListOrdered, label: 'Merit List' },
  { path: '/app/re-evaluation', icon: RotateCcw, label: 'Re-evaluation' },
  { path: '/app/ai', icon: Bot, label: 'EXAMFLOW AI' },
  { path: '/app/settings', icon: Settings, label: 'Settings' },
];

// ── Breadcrumb mapping ───────────────────────────────────────

const BREADCRUMB_MAP: Record<string, string> = {
  app: 'Dashboard',
  examinations: 'Examinations',
  candidates: 'Candidates',
  responses: 'Response Management',
  evaluation: 'Evaluation Engine',
  proctoring: 'Proctoring',
  normalisation: 'Normalisation',
  results: 'Results & Scorecards',
  'merit-list': 'Merit List',
  're-evaluation': 'Re-evaluation',
  ai: 'EXAMFLOW AI',
  settings: 'Settings',
};

export default function AppShell() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [themeDropdownOpen, setThemeDropdownOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { theme, setTheme } = useTheme();

  const toggleSidebar = useCallback(() => {
    setSidebarCollapsed((prev) => !prev);
  }, []);

  const isActive = (path: string, end?: boolean) => {
    if (end) return location.pathname === path;
    return location.pathname.startsWith(path);
  };

  // Build breadcrumbs
  const pathSegments = location.pathname.split('/').filter(Boolean);
  const breadcrumbs = pathSegments.map((segment, index) => ({
    label: BREADCRUMB_MAP[segment] || segment,
    path: '/' + pathSegments.slice(0, index + 1).join('/'),
  }));

  const currentPage = breadcrumbs[breadcrumbs.length - 1]?.label || 'Dashboard';

  return (
    <div className="flex h-screen bg-[var(--ef-bg)] overflow-hidden">
      {/* ── Sidebar ──────────────────────────────────────── */}
      <aside
        className={`hidden lg:flex flex-col bg-[var(--ef-sidebar-bg)] text-[var(--ef-sidebar-fg)] transition-all duration-300 ${
          sidebarCollapsed ? 'w-16' : 'w-64'
        }`}
      >
        {/* Logo */}
        <div className={`flex items-center h-16 px-4 border-b border-white/10 ${sidebarCollapsed ? 'justify-center' : 'gap-3'}`}>
          <div className="h-8 w-8 rounded-lg bg-[var(--ef-primary)] flex items-center justify-center text-[var(--ef-primary-fg)] font-bold text-sm flex-shrink-0">
            EF
          </div>
          {!sidebarCollapsed && (
            <span className="font-display text-xl tracking-tight">EXAMFLOW</span>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-4 px-2" aria-label="Main navigation">
          <ul className="space-y-1">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path, item.end);
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                      active
                        ? 'bg-[var(--ef-sidebar-active)] text-white'
                        : 'text-[var(--ef-sidebar-fg)] opacity-75 hover:opacity-100 hover:bg-[var(--ef-sidebar-hover)]'
                    } ${sidebarCollapsed ? 'justify-center' : ''}`}
                    title={sidebarCollapsed ? item.label : undefined}
                    aria-current={active ? 'page' : undefined}
                  >
                    <Icon className="h-5 w-5 flex-shrink-0" />
                    {!sidebarCollapsed && <span>{item.label}</span>}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Collapse toggle */}
        <div className="p-2 border-t border-white/10">
          <button
            onClick={toggleSidebar}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm opacity-75 hover:opacity-100 hover:bg-[var(--ef-sidebar-hover)] transition-colors"
            aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {sidebarCollapsed ? (
              <PanelLeft className="h-5 w-5" />
            ) : (
              <>
                <PanelLeftClose className="h-5 w-5" />
                <span>Collapse</span>
              </>
            )}
          </button>
        </div>
      </aside>

      {/* ── Mobile Overlay ───────────────────────────────── */}
      {mobileMenuOpen && (
        <div className="lg:hidden fixed inset-0 z-40">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setMobileMenuOpen(false)}
          />
          <aside className="relative z-50 w-72 h-full bg-[var(--ef-sidebar-bg)] text-[var(--ef-sidebar-fg)] flex flex-col">
            <div className="flex items-center justify-between h-16 px-4 border-b border-white/10">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-lg bg-[var(--ef-primary)] flex items-center justify-center text-[var(--ef-primary-fg)] font-bold text-sm">
                  EF
                </div>
                <span className="font-display text-xl tracking-tight">EXAMFLOW</span>
              </div>
              <button
                onClick={() => setMobileMenuOpen(false)}
                className="p-1 rounded hover:bg-[var(--ef-sidebar-hover)]"
                aria-label="Close menu"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <nav className="flex-1 overflow-y-auto py-4 px-2">
              <ul className="space-y-1">
                {NAV_ITEMS.map((item) => {
                  const Icon = item.icon;
                  const active = isActive(item.path, item.end);
                  return (
                    <li key={item.path}>
                      <Link
                        to={item.path}
                        onClick={() => setMobileMenuOpen(false)}
                        className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                          active
                            ? 'bg-[var(--ef-sidebar-active)] text-white'
                            : 'opacity-75 hover:opacity-100 hover:bg-[var(--ef-sidebar-hover)]'
                        }`}
                        aria-current={active ? 'page' : undefined}
                      >
                        <Icon className="h-5 w-5" />
                        <span>{item.label}</span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </nav>
          </aside>
        </div>
      )}

      {/* ── Main Content ─────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="h-16 flex items-center justify-between px-4 lg:px-6 border-b border-[var(--ef-border-subtle)] bg-[var(--ef-surface)]">
          <div className="flex items-center gap-3">
            <button
              className="lg:hidden p-2 rounded-lg hover:bg-[var(--ef-surface-hover)]"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Open menu"
            >
              <Menu className="h-5 w-5 text-[var(--ef-fg)]" />
            </button>

            {/* Breadcrumbs */}
            <nav aria-label="Breadcrumb" className="hidden sm:block">
              <ol className="flex items-center gap-1 text-sm">
                {breadcrumbs.map((crumb, i) => (
                  <li key={crumb.path} className="flex items-center gap-1">
                    {i > 0 && (
                      <ChevronRight className="h-3.5 w-3.5 text-[var(--ef-fg-muted)]" />
                    )}
                    {i === breadcrumbs.length - 1 ? (
                      <span className="font-medium text-[var(--ef-fg)]">
                        {crumb.label}
                      </span>
                    ) : (
                      <Link
                        to={crumb.path}
                        className="text-[var(--ef-fg-muted)] hover:text-[var(--ef-fg)]"
                      >
                        {crumb.label}
                      </Link>
                    )}
                  </li>
                ))}
              </ol>
            </nav>

            {/* Mobile title */}
            <h1 className="sm:hidden font-semibold text-[var(--ef-fg)]">
              {currentPage}
            </h1>
          </div>

          {/* Right actions */}
          <div className="flex items-center gap-2">
            {/* Theme Selector */}
            <div className="relative">
              <button
                className="p-2 rounded-lg hover:bg-[var(--ef-surface-hover)] text-[var(--ef-fg-secondary)]"
                onClick={() => {
                  setThemeDropdownOpen(!themeDropdownOpen);
                  setNotificationsOpen(false);
                }}
                aria-label="Change theme"
                aria-expanded={themeDropdownOpen}
              >
                <Palette className="h-5 w-5" />
              </button>
              {themeDropdownOpen && (
                <div className="absolute right-0 top-full mt-2 w-56 py-2 bg-[var(--ef-surface)] border border-[var(--ef-border)] rounded-[var(--ef-radius-lg)] shadow-[var(--ef-shadow-lg)] z-50 max-h-80 overflow-y-auto">
                  {THEMES.map((t) => (
                    <button
                      key={t.id}
                      className={`w-full text-left px-4 py-2 text-sm hover:bg-[var(--ef-surface-hover)] transition-colors ${
                        theme === t.id
                          ? 'text-[var(--ef-primary)] font-medium'
                          : 'text-[var(--ef-fg)]'
                      }`}
                      onClick={() => {
                        setTheme(t.id);
                        setThemeDropdownOpen(false);
                      }}
                    >
                      {t.label}
                      {theme === t.id && ' ✓'}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Notifications */}
            <div className="relative">
              <button
                className="p-2 rounded-lg hover:bg-[var(--ef-surface-hover)] text-[var(--ef-fg-secondary)] relative"
                onClick={() => {
                  setNotificationsOpen(!notificationsOpen);
                  setThemeDropdownOpen(false);
                }}
                aria-label="Notifications"
                aria-expanded={notificationsOpen}
              >
                <Bell className="h-5 w-5" />
                <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-[var(--ef-error)]" aria-hidden="true" />
              </button>
              {notificationsOpen && (
                <div className="absolute right-0 top-full mt-2 w-80 bg-[var(--ef-surface)] border border-[var(--ef-border)] rounded-[var(--ef-radius-lg)] shadow-[var(--ef-shadow-lg)] z-50">
                  <div className="p-4 border-b border-[var(--ef-border-subtle)]">
                    <h3 className="font-semibold text-sm text-[var(--ef-fg)]">
                      Notifications
                    </h3>
                  </div>
                  <div className="p-4 text-sm text-[var(--ef-fg-muted)] text-center">
                    No new notifications
                  </div>
                </div>
              )}
            </div>

            {/* User Menu */}
            <button
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-[var(--ef-surface-hover)] transition-colors"
              onClick={() => navigate('/app/settings')}
              aria-label="User profile"
            >
              <div className="h-8 w-8 rounded-full bg-[var(--ef-primary)] flex items-center justify-center">
                <User className="h-4 w-4 text-[var(--ef-primary-fg)]" />
              </div>
              <span className="hidden md:block text-sm font-medium text-[var(--ef-fg)]">
                Admin
              </span>
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <Outlet />
        </main>

        {/* Global Floating AI Assistant */}
        <FloatingAssistant />
      </div>
    </div>
  );
}
