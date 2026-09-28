/**
 * Multi-Hazard Page - Real Backend Integration
 * Uses real backend incidents and hazard assessments, no mock data
 */

import { useState } from 'react';
import { Layers, RefreshCw, Search } from 'lucide-react';
import { useIncidents, useRegionalHazards } from '@/lib/hooks';
import { PageHeader, ActionButton, SectionTitle, StateChip, Condition } from '@/components/dashboard-components';

export function MultiHazardPageLive() {
  const [filter, setFilter] = useState('');

  const { data: regionalHazards, isLoading: hazardsLoading, error: hazardsError } = useRegionalHazards();
  const { data: incidents, isLoading: incidentsLoading, error: incidentsError } = useIncidents();

  const isLoading = hazardsLoading || incidentsLoading;
  const error = hazardsError || incidentsError;

  // Filter by search query
  const filteredHazards =
    regionalHazards?.filter((hazard) =>
      `${hazard.hazard_type} ${hazard.operational_state}`.toLowerCase().includes(filter.toLowerCase())
    ) || [];

  // Group hazards by type
  const hazardsByType = filteredHazards.reduce((acc, hazard) => {
    const type = hazard.hazard_type;
    if (!acc[type]) acc[type] = [];
    acc[type].push(hazard);
    return acc;
  }, {} as Record<string, typeof filteredHazards>);

  return (
    <div className="content-area">
      <PageHeader
        eyebrow="Regional intelligence / correlation"
        title="Multi-hazard view"
        description="Track independent hazard assessments without collapsing distinct risks into a single score."
        actions={
          <ActionButton testId="button-refresh-hazards">
            <RefreshCw size={13} />
            Refresh hazards
          </ActionButton>
        }
      />

      {/* Loading state */}
      {isLoading && (
        <div className="mb-4 rounded-md border border-slate-700 bg-slate-900/50 p-4 text-center text-slate-400">
          <RefreshCw size={20} className="mx-auto mb-2 animate-spin" />
          <div className="text-sm">Loading multi-hazard data from backend...</div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="mb-4 rounded-md border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-300">
          <strong>Backend error:</strong> {error.message}
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && filteredHazards.length === 0 && (
        <div className="mb-4 rounded-md border border-slate-700 bg-slate-900/50 p-6 text-center text-slate-400">
          <div className="text-sm font-semibold">No hazard assessments available</div>
          <div className="mt-1 text-xs">Backend returned no regional hazard data</div>
        </div>
      )}

      {/* Main content */}
      {!isLoading && !error && filteredHazards.length > 0 && (
        <div className="space-y-4">
          {/* Metrics */}
          <div className="grid gap-2 sm:grid-cols-4">
            <div className="panel-flat p-3">
              <div className="eyebrow">Total hazards</div>
              <div className="mt-2 text-[21px] font-bold text-slate-100">{filteredHazards.length}</div>
              <div className="mt-1 text-[10px] text-slate-500">
                {Object.keys(hazardsByType).length} distinct hazard types
              </div>
            </div>
            <div className="panel-flat p-3">
              <div className="eyebrow">Active incidents</div>
              <div className="mt-2 text-[21px] font-bold text-red-200">{incidents?.length || 0}</div>
              <div className="mt-1 text-[10px] text-slate-500">From incident correlation</div>
            </div>
            <div className="panel-flat p-3">
              <div className="eyebrow">Hazard types</div>
              <div className="mt-2 text-[21px] font-bold text-amber-200">{Object.keys(hazardsByType).length}</div>
              <div className="mt-1 text-[10px] text-slate-500">Independent assessments</div>
            </div>
            <div className="panel-flat p-3">
              <div className="eyebrow">Data source</div>
              <div className="mt-2 text-[21px] font-bold text-cyan-200">BACKEND</div>
              <div className="mt-1 text-[10px] text-slate-500">Live regional hazards</div>
            </div>
          </div>

          {/* Hazard list */}
          <div className="panel overflow-hidden">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 p-3">
              <SectionTitle icon={Layers} meta={`${filteredHazards.length} assessments`}>
                Multi-hazard register
              </SectionTitle>
              <label className="flex items-center gap-2 rounded-md border border-slate-800 bg-slate-900/60 px-2 py-1.5 text-slate-500">
                <Search size={13} />
                <input
                  value={filter}
                  onChange={(event) => setFilter(event.target.value)}
                  aria-label="Filter hazards"
                  data-testid="input-filter-hazards"
                  placeholder="Filter by hazard or state"
                  className="w-40 bg-transparent text-[10px] text-slate-200 outline-none"
                />
              </label>
            </div>

            <div className="divide-y divide-slate-800/70">
              {filteredHazards.map((hazard) => (
                <div
                  key={hazard.assessment_id}
                  className="flex w-full flex-wrap items-center gap-3 p-3"
                  data-testid={`row-hazard-${hazard.assessment_id}`}
                >
                  <div className="min-w-[180px] flex-1">
                    <div className="text-[12px] font-semibold text-slate-200">{hazard.hazard_type.toUpperCase()}</div>
                    <div className="mt-1 text-[10px] text-slate-500">
                      Assessment ID: {hazard.assessment_id}
                    </div>
                  </div>
                  <StateChip state={hazard.operational_state} />
                  <Condition value={hazard.information_condition} />
                  <div className="hidden text-right sm:block">
                    <div className="text-[10px] text-slate-500">Evidence</div>
                    <div className="font-mono text-[11px] text-amber-200">
                      {hazard.evidence !== null ? hazard.evidence.toFixed(2) : '—'}
                    </div>
                  </div>
                  <div className="hidden text-right sm:block">
                    <div className="text-[10px] text-slate-500">Confidence</div>
                    <div className="font-mono text-[11px] text-amber-200">
                      {hazard.confidence !== null ? hazard.confidence.toFixed(2) : '—'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Hazard independence notice */}
          <div className="panel p-4">
            <div className="rounded-md border border-cyan-300/15 bg-cyan-300/[.04] p-3 text-[11px] leading-relaxed text-cyan-100/80">
              <strong>Multi-hazard independence:</strong> Each hazard type maintains its own evidence, confidence,
              severity, and risk assessment. The system does NOT collapse fire, flood, seismic, and other hazards into a
              single composite score. Operators review each hazard independently.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
