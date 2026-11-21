// ============================================================
// EXAMFLOW – Reusable UI Components
// ============================================================

import { type ReactNode, type ButtonHTMLAttributes, forwardRef } from 'react';
import { Loader2 } from 'lucide-react';

// ── Button ───────────────────────────────────────────────────

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      isLoading,
      leftIcon,
      rightIcon,
      children,
      className = '',
      disabled,
      ...props
    },
    ref
  ) => {
    const base =
      'inline-flex items-center justify-center font-medium transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ef-focus)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--ef-bg)] disabled:opacity-50 disabled:pointer-events-none';

    const variants: Record<string, string> = {
      primary:
        'bg-[var(--ef-primary)] text-[var(--ef-primary-fg)] hover:bg-[var(--ef-primary-hover)] active:brightness-90',
      secondary:
        'bg-[var(--ef-secondary)] text-[var(--ef-secondary-fg)] hover:bg-[var(--ef-secondary-hover)] active:brightness-90',
      outline:
        'border border-[var(--ef-border)] bg-transparent text-[var(--ef-fg)] hover:bg-[var(--ef-surface-hover)]',
      ghost:
        'bg-transparent text-[var(--ef-fg-secondary)] hover:bg-[var(--ef-surface-hover)] hover:text-[var(--ef-fg)]',
      danger:
        'bg-[var(--ef-error)] text-white hover:brightness-90 active:brightness-80',
    };

    const sizes: Record<string, string> = {
      sm: 'h-8 px-3 text-sm rounded-[var(--ef-radius-sm)] gap-1.5',
      md: 'h-10 px-4 text-sm rounded-[var(--ef-radius)] gap-2',
      lg: 'h-12 px-6 text-base rounded-[var(--ef-radius)] gap-2.5',
    };

    return (
      <button
        ref={ref}
        className={`${base} ${variants[variant]} ${sizes[size]} ${className}`}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          leftIcon
        )}
        {children}
        {rightIcon}
      </button>
    );
  }
);
Button.displayName = 'Button';

// ── Card ─────────────────────────────────────────────────────

interface CardProps {
  children: ReactNode;
  className?: string;
  glass?: boolean;
  onClick?: () => void;
}

export function Card({ children, className = '', glass, onClick }: CardProps) {
  return (
    <div
      className={`${glass ? 'liquid-glass' : 'bg-[var(--ef-surface)] border border-[var(--ef-border-subtle)]'} rounded-[var(--ef-radius-lg)] shadow-[var(--ef-shadow)] ${onClick ? 'cursor-pointer hover:shadow-[var(--ef-shadow-md)] transition-shadow' : ''} ${className}`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => { if (e.key === 'Enter' || e.key === ' ') onClick(); } : undefined}
    >
      {children}
    </div>
  );
}

// ── Badge ────────────────────────────────────────────────────

interface BadgeProps {
  children: ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info';
  className?: string;
}

export function Badge({ children, variant = 'default', className = '' }: BadgeProps) {
  const variants: Record<string, string> = {
    default:
      'bg-[var(--ef-bg-tertiary)] text-[var(--ef-fg-secondary)]',
    success:
      'bg-[var(--ef-success-bg)] text-[var(--ef-success)]',
    warning:
      'bg-[var(--ef-warning-bg)] text-[var(--ef-warning)]',
    error:
      'bg-[var(--ef-error-bg)] text-[var(--ef-error)]',
    info:
      'bg-[var(--ef-info-bg)] text-[var(--ef-info)]',
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 text-xs font-medium rounded-full ${variants[variant]} ${className}`}
    >
      {children}
    </span>
  );
}

// ── Input ────────────────────────────────────────────────────

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, id, className = '', ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="text-sm font-medium text-[var(--ef-fg)]"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={`h-10 w-full rounded-[var(--ef-radius)] border px-3 text-sm bg-[var(--ef-bg)] text-[var(--ef-fg)] placeholder:text-[var(--ef-fg-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--ef-focus)] focus:ring-offset-1 focus:ring-offset-[var(--ef-bg)] transition-colors ${
            error
              ? 'border-[var(--ef-error)]'
              : 'border-[var(--ef-border)]'
          } ${className}`}
          aria-invalid={!!error}
          aria-describedby={error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined}
          {...props}
        />
        {error && (
          <p id={`${inputId}-error`} className="text-xs text-[var(--ef-error)]" role="alert">
            {error}
          </p>
        )}
        {hint && !error && (
          <p id={`${inputId}-hint`} className="text-xs text-[var(--ef-fg-muted)]">
            {hint}
          </p>
        )}
      </div>
    );
  }
);
Input.displayName = 'Input';

// ── Select ───────────────────────────────────────────────────

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options: { value: string; label: string }[];
  placeholder?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, options, placeholder, id, className = '', ...props }, ref) => {
    const selectId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label
            htmlFor={selectId}
            className="text-sm font-medium text-[var(--ef-fg)]"
          >
            {label}
          </label>
        )}
        <select
          ref={ref}
          id={selectId}
          className={`h-10 w-full rounded-[var(--ef-radius)] border px-3 text-sm bg-[var(--ef-bg)] text-[var(--ef-fg)] focus:outline-none focus:ring-2 focus:ring-[var(--ef-focus)] focus:ring-offset-1 focus:ring-offset-[var(--ef-bg)] transition-colors ${
            error
              ? 'border-[var(--ef-error)]'
              : 'border-[var(--ef-border)]'
          } ${className}`}
          aria-invalid={!!error}
          {...props}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        {error && (
          <p className="text-xs text-[var(--ef-error)]" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }
);
Select.displayName = 'Select';

// ── Table ────────────────────────────────────────────────────

interface Column<T> {
  key: string;
  header: string;
  render?: (item: T) => ReactNode;
  className?: string;
}

interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyField: keyof T;
  onRowClick?: (item: T) => void;
  emptyMessage?: string;
  isLoading?: boolean;
}

export function Table<T extends Record<string, unknown>>({
  columns,
  data,
  keyField,
  onRowClick,
  emptyMessage = 'No data available',
  isLoading,
}: TableProps<T>) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-[var(--ef-primary)]" />
        <span className="ml-2 text-[var(--ef-fg-muted)]">Loading…</span>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-[var(--ef-radius-lg)] border border-[var(--ef-border-subtle)]">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-[var(--ef-bg-secondary)] border-b border-[var(--ef-border)]">
            {columns.map((col) => (
              <th
                key={col.key}
                className={`px-4 py-3 text-left font-semibold text-[var(--ef-fg-secondary)] ${col.className || ''}`}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-4 py-12 text-center text-[var(--ef-fg-muted)]"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((item) => (
              <tr
                key={String(item[keyField])}
                className={`border-b border-[var(--ef-border-subtle)] bg-[var(--ef-surface)] hover:bg-[var(--ef-surface-hover)] transition-colors ${
                  onRowClick ? 'cursor-pointer' : ''
                }`}
                onClick={() => onRowClick?.(item)}
                tabIndex={onRowClick ? 0 : undefined}
                onKeyDown={onRowClick ? (e) => { if (e.key === 'Enter') onRowClick(item); } : undefined}
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={`px-4 py-3 text-[var(--ef-fg)] ${col.className || ''}`}
                  >
                    {col.render
                      ? col.render(item)
                      : String(item[col.key] ?? '')}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

// ── Dialog / Modal ───────────────────────────────────────────

interface DialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
}

export function Dialog({ open, onClose, title, children, footer }: DialogProps) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="dialog-title"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />
      {/* Panel */}
      <div className="relative z-10 w-full max-w-lg mx-4 liquid-glass p-6">
        <h2
          id="dialog-title"
          className="text-lg font-semibold text-[var(--ef-fg)] mb-4"
        >
          {title}
        </h2>
        <div className="text-[var(--ef-fg-secondary)]">{children}</div>
        {footer && (
          <div className="mt-6 flex justify-end gap-3">{footer}</div>
        )}
      </div>
    </div>
  );
}

// ── Empty State ──────────────────────────────────────────────

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      {icon && (
        <div className="mb-4 text-[var(--ef-fg-muted)]">{icon}</div>
      )}
      <h3 className="text-lg font-semibold text-[var(--ef-fg)]">{title}</h3>
      {description && (
        <p className="mt-1 text-sm text-[var(--ef-fg-muted)] max-w-sm">
          {description}
        </p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

// ── Status Indicator ─────────────────────────────────────────

interface StatusIndicatorProps {
  status: 'success' | 'warning' | 'error' | 'info' | 'neutral';
  label: string;
  showDot?: boolean;
}

export function StatusIndicator({
  status,
  label,
  showDot = true,
}: StatusIndicatorProps) {
  const colors: Record<string, string> = {
    success: 'text-[var(--ef-success)]',
    warning: 'text-[var(--ef-warning)]',
    error: 'text-[var(--ef-error)]',
    info: 'text-[var(--ef-info)]',
    neutral: 'text-[var(--ef-fg-muted)]',
  };

  const dotColors: Record<string, string> = {
    success: 'bg-[var(--ef-success)]',
    warning: 'bg-[var(--ef-warning)]',
    error: 'bg-[var(--ef-error)]',
    info: 'bg-[var(--ef-info)]',
    neutral: 'bg-[var(--ef-fg-muted)]',
  };

  return (
    <span className={`inline-flex items-center gap-1.5 text-sm font-medium ${colors[status]}`}>
      {showDot && (
        <span
          className={`h-2 w-2 rounded-full ${dotColors[status]}`}
          aria-hidden="true"
        />
      )}
      {label}
    </span>
  );
}

// ── Pagination ───────────────────────────────────────────────

interface PaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ page, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null;

  return (
    <nav
      className="flex items-center justify-center gap-1 mt-4"
      aria-label="Pagination"
    >
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        className="px-3 py-1.5 text-sm rounded-[var(--ef-radius)] border border-[var(--ef-border)] text-[var(--ef-fg-secondary)] hover:bg-[var(--ef-surface-hover)] disabled:opacity-50 disabled:pointer-events-none"
        aria-label="Previous page"
      >
        Previous
      </button>
      {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
        let pageNum: number;
        if (totalPages <= 7) {
          pageNum = i + 1;
        } else if (page <= 4) {
          pageNum = i + 1;
        } else if (page >= totalPages - 3) {
          pageNum = totalPages - 6 + i;
        } else {
          pageNum = page - 3 + i;
        }
        return (
          <button
            key={pageNum}
            onClick={() => onPageChange(pageNum)}
            className={`px-3 py-1.5 text-sm rounded-[var(--ef-radius)] ${
              pageNum === page
                ? 'bg-[var(--ef-primary)] text-[var(--ef-primary-fg)]'
                : 'border border-[var(--ef-border)] text-[var(--ef-fg-secondary)] hover:bg-[var(--ef-surface-hover)]'
            }`}
            aria-current={pageNum === page ? 'page' : undefined}
          >
            {pageNum}
          </button>
        );
      })}
      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
        className="px-3 py-1.5 text-sm rounded-[var(--ef-radius)] border border-[var(--ef-border)] text-[var(--ef-fg-secondary)] hover:bg-[var(--ef-surface-hover)] disabled:opacity-50 disabled:pointer-events-none"
        aria-label="Next page"
      >
        Next
      </button>
    </nav>
  );
}

// ── Tabs ─────────────────────────────────────────────────────

interface TabItem {
  id: string;
  label: string;
  icon?: ReactNode;
}

interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onTabChange: (id: string) => void;
  className?: string;
}

export function Tabs({ tabs, activeTab, onTabChange, className = '' }: TabsProps) {
  return (
    <div
      className={`flex gap-1 border-b border-[var(--ef-border)] ${className}`}
      role="tablist"
    >
      {tabs.map((tab) => (
        <button
          key={tab.id}
          role="tab"
          aria-selected={tab.id === activeTab}
          className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
            tab.id === activeTab
              ? 'border-[var(--ef-primary)] text-[var(--ef-primary)]'
              : 'border-transparent text-[var(--ef-fg-muted)] hover:text-[var(--ef-fg-secondary)] hover:border-[var(--ef-border)]'
          }`}
          onClick={() => onTabChange(tab.id)}
        >
          {tab.icon}
          {tab.label}
        </button>
      ))}
    </div>
  );
}

// ── Skeleton ─────────────────────────────────────────────────

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className = '' }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse rounded-[var(--ef-radius)] bg-[var(--ef-bg-tertiary)] ${className}`}
      aria-hidden="true"
    />
  );
}

// ── DemoDataBanner ───────────────────────────────────────────

export function DemoDataBanner() {
  return (
    <div
      className="mb-4 px-4 py-2 rounded-[var(--ef-radius)] bg-[var(--ef-warning-bg)] border border-[var(--ef-warning)] text-[var(--ef-warning)] text-sm font-medium flex items-center gap-2"
      role="status"
    >
      <span className="font-bold uppercase tracking-wider text-xs px-2 py-0.5 rounded bg-[var(--ef-warning)] text-white">
        DEMO DATA
      </span>
      The data displayed is for demonstration purposes only and does not reflect live examination data.
    </div>
  );
}
