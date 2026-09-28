/**
 * Telemetry Page - Real Backend Integration
 */

import { useState } from 'react';
import { RefreshCw, Activity, Search, Gauge } from 'lucide-react';
import { useLatestTelemetry } from '@/lib/hooks';
import { Condition, PageHeader, ActionButton, SectionTitle, Metric } from '@/components/dashboard-components';
import type { TelemetryRecord } from '@/types';

export function TelemetryPageLive() {
  const [selected, setSelected] = useState<TelemetryRecord | null>(null);
  const [filter, setFilter] = useState('');

  // Fetch real telemetry from backend
  const { data: telemetry, isLoading, error } = useLatestTelemetry();

  // Filter telemetry by search query
  const records =
    telemetry?.filter((record) =>
      `${record.source} ${record.signal} ${record.state}`.toLowerCase().includes(filter.toLowerCase())
    ) || [];

  // Set initial selection when data loads
  if (records.length > 0 && !selected) {
    setSelected(records[0]);
  }

  // Calculate quality metrics
  const goodQuality = records.filter((r) => r.quality === 'GOOD').length;
  const degradedQuality = records.filter((r) => r.quality === 'DEGRADED').length;
  const unknownQuality = records.filter((r) => r.quality === 'UNKNOWN').length;

  const stages = [
    'Raw telemetry',
    'Quality',
    'Health',
    'Reliability',
    'Baseline',
    'Anomaly',
    'Evidence',
    'Confidence',
    'Severity',
    'Operational risk',
    'State',
  ];

  return (
    <div className="content-area">
      <PageHeader
        eyebrow="Field intelligence / inspection"
        title="Telemetry & intelligence"
        description="Trace material observations through quality, evidence, and state without hiding missing or stale inputs."
        actions={
          <ActionButton testId="button-refresh-telemetry">
            <RefreshCw size={13} />
            Refresh telemetry
          </ActionButton>
        }
      />

      {/* Loading state */}
      {isLoading && (
        <div className="mb-4 rounded-md border border-slate-700 bg-slate-900/50 p-4 text-center text-slate-400">
          <RefreshCw size={20} className="mx-auto mb-2 animate-spin" />
          <div className="text-sm">Loading telemetry from backend...</div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="mb-4 rounded-md border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-300">
          <strong>Backend error:</strong> {error.message}
        </div>
      )}

      {/* Metrics */}
      {!isLoading && (
        <div className="mb-4 grid gap-2 sm:grid-cols-3">
          <Metric
            label="Records in view"
            value={`${records.length}`}
            detail="Real backend telemetry"
            tone="text-cyan-200"
          />
          <Metric
            label="Good quality"
            value={goodQuality.toString()}
            detail={`${degradedQuality} degraded · ${unknownQuality} unknown`}
            tone={goodQuality > 0 ? 'text-emerald-200' : 'text-slate-400'}
          />
          <Metric label="Data source" value="BACKEND" detail="Live telemetry feed" tone="text-cyan-200" />
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && records.length === 0 && (
        <div className="mb-4 rounded-md border border-slate-700 bg-slate-900/50 p-6 text-center text-slate-400">
          <div className="text-sm font-semibold">No telemetry available</div>
          <div className="mt-1 text-xs">Backend returned no telemetry records</div>
        </div>
      )}

      {/* Main layout */}
      {!isLoading && records.length > 0 && (
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
          <div className="space-y-4">
            {/* Telemetry register */}
            <div className="panel overflow-hidden">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 p-3">
                <SectionTitle icon={Activity} meta={`${records.length} records`}>
                  Telemetry register
                </SectionTitle>
                <label className="flex items-center gap-2 rounded-md border border-slate-800 bg-slate-900/60 px-2 py-1.5 text-slate-500">
                  <Search size={13} />
                  <input
                    value={filter}
                    onChange={(event) => setFilter(event.target.value)}
                    aria-label="Filter telemetry"
                    data-testid="input-filter-telemetry"
                    placeholder="Filter signal or source"
                    className="w-40 bg-transparent text-[10px] text-slate-200 outline-none"
                  />
                </label>
              </div>
              <div className="divide-y divide-slate-800/70">
                {records.map((record) => (
                  <button
                    type="button"
                    key={record.id}
                    onClick={() => setSelected(record)}
                    className={`flex w-full flex-wrap items-center gap-3 p-3 text-left hover:bg-slate-800/30 ${
                      selected?.id === record.id ? 'bg-cyan-300/[.03]' : ''
                    }`}
                    data-testid={`row-telemetry-${record.id}`}
                  >
                    <div className="min-w-[165px] flex-1">
                      <div className="font-mono text-[10px] text-cyan-200">{record.signal}</div>
                      <div className="mt-1 text-[11px] font-semibold text-slate-200">{record.source}</div>
                    </div>
                    <div className="font-mono text-[11px] text-slate-100">{record.observed}</div>
                    <div className="hidden text-right text-[10px] text-slate-500 sm:block">{record.receivedAt}</div>
                    <Condition value={record.quality} />
                  </button>
                ))}
              </div>
            </div>

            {/* Intelligence pipeline stages */}
            <div className="panel p-4">
              <SectionTitle icon={Gauge} meta="read-only pipeline">
                Interpretation stages
              </SectionTitle>
              <div className="flex flex-wrap gap-2">
                {stages.map((stage, index) => (
                  <div
                    key={stage}
                    className={`flex items-center gap-2 rounded-md border px-2.5 py-2 text-[10px] ${
                      index < 7
                        ? 'border-cyan-300/20 bg-cyan-300/[.04] text-cyan-100'
                        : 'border-slate-800 bg-slate-900/30 text-slate-500'
                    }`}
                  >
                    <span className="font-mono text-[9px] text-slate-600">{String(index + 1).padStart(2, '0')}</span>
                    {stage}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Selected record detail */}
          <div className="panel p-4">
            {selected ? (
              <>
                <div className="eyebrow">Selected record</div>
                <h2 className="mt-2 text-[17px] font-bold text-slate-100">{selected.signal}</h2>
                <div className="mt-1 text-[11px] text-slate-500">
                  {selected.source} · {selected.receivedAt}
                </div>
                <div className="my-4 flex items-center justify-between">
                  <span className="font-mono text-[23px] font-bold text-cyan-100">{selected.observed}</span>
                  <Condition value={selected.quality} />
                </div>
                <div className="space-y-3 text-[11px]">
                  <div className="flex justify-between border-b border-slate-800 pb-2">
                    <span className="text-slate-500">Observed state</span>
                    <span className="text-slate-200">{selected.state}</span>
                  </div>
                  <div className="flex justify-between border-b border-slate-800 pb-2">
                    <span className="text-slate-500">Quality</span>
                    <span className="text-amber-200">{selected.quality}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Received</span>
                    <span className="text-amber-200">{selected.receivedAt}</span>
                  </div>
                </div>
                {selected.measurements && Object.keys(selected.measurements).length > 0 && (
                  <div className="mt-4">
                    <div className="eyebrow mb-2">Raw measurements</div>
                    <div className="space-y-1 text-[10px]">
                      {Object.entries(selected.measurements).map(([key, value]) => (
                        <div key={key} className="flex justify-between font-mono">
                          <span className="text-slate-500">{key}</span>
                          <span className="text-cyan-200">{value !== null ? value : 'NULL'}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                <div className="mt-5 rounded-md border border-amber-300/15 bg-amber-300/[.04] p-3 text-[10px] leading-relaxed text-amber-100/75">
                  Raw telemetry from real backend. A degraded or unknown input stays visible and constrains downstream
                  assessment.
                </div>
              </>
            ) : (
              <>
                <div className="eyebrow">Selected record</div>
                <div className="mt-4 text-center text-sm text-slate-500">No record selected</div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
