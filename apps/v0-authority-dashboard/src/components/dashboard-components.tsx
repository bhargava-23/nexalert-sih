/**
 * Shared UI components for V0 Authority Dashboard
 * Extracted from dashboard-pages.tsx for reuse
 */

import { type ComponentProps, type ReactNode } from 'react';
import { type LucideIcon } from 'lucide-react';
import type { State } from '@/types';

const stateClass: Record<State, string> = {
  NORMAL: 'state-normal',
  WATCH: 'state-watch',
  SUSPECTED: 'state-suspected',
  CONFIRMED: 'state-confirmed',
  CRITICAL: 'state-critical',
  RESOLVED: 'state-resolved',
};

export function StateChip({ state }: { state: State | string }) {
  const label = state.replaceAll('_', ' ');
  const className =
    stateClass[state as State] ||
    (state === 'GOOD' || state === 'OPERATIONAL' || state === 'ONLINE'
      ? 'state-normal'
      : state === 'DEGRADED' || state === 'REVIEW' || state === 'IN PROGRESS'
        ? 'state-watch'
        : state === 'UNAVAILABLE' || state === 'UNREACHABLE' || state === 'BLOCKED'
          ? 'state-critical'
          : 'state-resolved');
  return (
    <span className={`state-chip ${className}`}>
      <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-current" />
      {label}
    </span>
  );
}

export function Condition({ value }: { value: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 font-mono text-[10px] ${
        value === 'GOOD'
          ? 'condition-good'
          : value === 'DEGRADED'
            ? 'condition-degraded'
            : 'condition-unknown'
      }`}
    >
      <span className="h-1.5 w-1.5 rounded-sm border border-current" />
      {value}
    </span>
  );
}

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-4 flex flex-wrap items-start justify-between gap-4">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1 className="mt-1 text-[23px] font-bold leading-tight tracking-tight text-slate-100">{title}</h1>
        <p className="mt-2 max-w-2xl text-[13px] leading-relaxed text-slate-400">{description}</p>
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

export function ActionButton({
  children,
  primary,
  testId,
  onClick,
}: {
  children: ReactNode;
  primary?: boolean;
  testId?: string;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      className={primary ? 'button-primary' : 'button-compact'}
      data-testid={testId}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

export function SectionTitle({
  icon: Icon,
  meta,
  children,
}: {
  icon: LucideIcon;
  meta?: string;
  children: ReactNode;
}) {
  return (
    <div className="flex items-center gap-2">
      <Icon size={15} className="text-cyan-300" />
      <span className="font-semibold text-slate-200">{children}</span>
      {meta && <span className="ml-auto font-mono text-[9px] text-slate-600">{meta}</span>}
    </div>
  );
}

export function Metric({
  label,
  value,
  detail,
  tone,
}: {
  label: string;
  value: string;
  detail: string;
  tone?: string;
}) {
  return (
    <div className="panel-flat p-3">
      <div className="eyebrow">{label}</div>
      <div className={`mt-2 text-[23px] font-bold ${tone || 'text-slate-100'}`}>{value}</div>
      <div className="mt-1 text-[10px] text-slate-500">{detail}</div>
    </div>
  );
}

export function OperationalRail({ onFeedback }: { onFeedback: (message: string) => void }) {
  // Placeholder - real implementation would fetch from backend
  return (
    <div className="panel p-3">
      <div className="mb-2 flex items-center justify-between">
        <div className="eyebrow">Operational rail</div>
        <span className="font-mono text-[9px] text-slate-600">LIVE</span>
      </div>
      <div className="space-y-1">
        <div className="rounded-md bg-slate-900/60 p-3 text-[10px] text-slate-500">
          Real-time alerts will appear here from backend
        </div>
      </div>
    </div>
  );
}

export function Feedback({ message, onClose }: { message: string; onClose: () => void }) {
  return (
    <div className="fixed bottom-4 right-4 z-50 rounded-md border border-cyan-300/20 bg-cyan-300/10 px-4 py-3 text-sm text-cyan-100 shadow-lg">
      <div className="flex items-center gap-3">
        <span>{message}</span>
        <button
          type="button"
          onClick={onClose}
          className="text-cyan-300 hover:text-cyan-100"
          aria-label="Dismiss"
        >
          ×
        </button>
      </div>
    </div>
  );
}
