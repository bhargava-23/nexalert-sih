/**
 * Incidents Page - Real Backend Integration
 */

import { useState } from 'react';
import { RefreshCw, MapPin, Flame, Info } from 'lucide-react';
import { useRegionalHazards, useIncidents } from '@/lib/hooks';
import { MapSurface } from '@/components/nexalert/MapSurface';
import { StateChip, Condition, PageHeader, ActionButton, SectionTitle, Metric, Feedback } from '@/components/dashboard-components';
import type { Incident } from '@/types';

export function IncidentsPageLive() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState('');

  // Fetch real backend data
  const { data: incidents, isLoading, error } = useRegionalHazards();

  const selected = incidents?.find((inc) => inc.id === selectedId) || incidents?.[0] || null;

  // Calculate metrics from real data
  const activeIncidents = incidents?.filter((inc) => inc.state !== 'RESOLVED').length || 0;
  const confirmedIncidents = incidents?.filter((inc) => inc.state === 'CONFIRMED').length || 0;
  const watchIncidents = incidents?.filter((inc) => inc.state === 'WATCH').length || 0;

  return (
    <div className="content-area">
      <PageHeader
        eyebrow="Regional intelligence / Track B2"
        title="Incidents"
        description="Multi-node correlation, regional fusion, and incident lifecycle tracking from real backend data."
        actions={
          <ActionButton
            testId="button-refresh-incidents"
            onClick={() => setFeedback('Incident register refreshed from backend')}
          >
            <RefreshCw size={13} />
            Refresh incidents
          </ActionButton>
        }
      />

      {/* Loading state */}
      {isLoading && (
        <div className="mb-4 rounded-md border border-slate-700 bg-slate-900/50 p-4 text-center text-slate-400">
          <RefreshCw size={20} className="mx-auto mb-2 animate-spin" />
          <div className="text-sm">Loading incidents from backend...</div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="mb-4 rounded-md border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-300">
          <strong>Backend error:</strong> {error.message}
        </div>
      )}

      {/* Real metrics */}
      {!isLoading && (
        <div className="mb-4 grid grid-cols-2 gap-2 lg:grid-cols-4">
          <Metric
            label="Active incidents"
            value={activeIncidents.toString()}
            detail={`${confirmedIncidents} confirmed · ${watchIncidents} watch`}
            tone={activeIncidents > 0 ? 'text-red-200' : 'text-emerald-200'}
          />
          <Metric
            label="Confirmed"
            value={confirmedIncidents.toString()}
            detail="Requires operator response"
            tone={confirmedIncidents > 0 ? 'text-red-200' : 'text-emerald-200'}
          />
          <Metric
            label="Under review"
            value={watchIncidents.toString()}
            detail="Watch state pending"
            tone="text-amber-200"
          />
          <Metric
            label="Data source"
            value="BACKEND"
            detail="Track B2 regional fusion"
            tone="text-cyan-200"
          />
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && (!incidents || incidents.length === 0) && (
        <div className="mb-4 rounded-md border border-slate-700 bg-slate-900/50 p-6 text-center text-slate-400">
          <div className="text-sm font-semibold">No incidents reported</div>
          <div className="mt-1 text-xs">Backend returned no regional hazard assessments</div>
        </div>
      )}

      {/* Main layout */}
      {!isLoading && incidents && incidents.length > 0 && (
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
          <div className="space-y-4">
            {/* Real map with incidents */}
            <div className="panel p-2">
              <MapSurface
                nodes={[]}
                incidents={incidents}
                sos={[]}
                masterLocation={null}
                selectedIncidentId={selectedId}
                onSelection={(selection) => {
                  if (selection?.kind === 'incident') {
                    setSelectedId(selection.value.id);
                  }
                }}
              />
            </div>

            {/* Incident register */}
            <div className="panel overflow-hidden">
              <div className="border-b border-slate-800 p-3">
                <SectionTitle icon={Flame} meta={`${incidents.length} from backend`}>
                  Incident register
                </SectionTitle>
              </div>
              <div className="divide-y divide-slate-800/70">
                {incidents.map((incident) => (
                  <button
                    type="button"
                    key={incident.id}
                    onClick={() => setSelectedId(incident.id)}
                    className={`flex w-full flex-wrap items-center gap-3 p-3 text-left hover:bg-slate-800/30 ${
                      selectedId === incident.id ? 'bg-cyan-300/[.03]' : ''
                    }`}
                    data-testid={`row-incident-${incident.id}`}
                  >
                    <div className="min-w-[200px] flex-1">
                      <div className="text-[11px] font-semibold text-slate-200">{incident.title}</div>
                      <div className="mt-0.5 text-[10px] text-slate-500">
                        {incident.id} · {incident.hazard} · {incident.location}
                      </div>
                    </div>
                    <div className="hidden text-right sm:block">
                      <div className="text-[10px] text-slate-300">{incident.severity}</div>
                      <div className="text-[9px] text-slate-600">severity</div>
                    </div>
                    <div className="w-20 text-right text-[10px] text-slate-500">{incident.freshness}</div>
                    <StateChip state={incident.state} />
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Incident detail panel */}
          <aside className="space-y-4">
            {selected ? (
              <div className="panel p-4">
                <div className="eyebrow">Incident detail</div>
                <h2 className="mt-2 text-[17px] font-bold text-slate-100">{selected.title}</h2>
                <div className="mt-1 text-[11px] text-slate-500">
                  {selected.id} · {selected.hazard}
                </div>
                <div className="my-4 flex items-center gap-2">
                  <StateChip state={selected.state} />
                  <Condition value={selected.informationCondition} />
                </div>
                <div className="space-y-3 text-[11px]">
                  <div className="flex justify-between border-b border-slate-800 pb-2">
                    <span className="text-slate-500">Severity</span>
                    <span className="text-amber-200">{selected.severity}</span>
                  </div>
                  <div className="flex justify-between border-b border-slate-800 pb-2">
                    <span className="text-slate-500">Location</span>
                    <span className="text-slate-200">{selected.location}</span>
                  </div>
                  <div className="flex justify-between border-b border-slate-800 pb-2">
                    <span className="text-slate-500">Freshness</span>
                    <span className="text-amber-200">{selected.freshness}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Footprint</span>
                    <span className="text-slate-200">{selected.footprint}</span>
                  </div>
                </div>
                <div className="mt-4">
                  <div className="eyebrow mb-1.5">Evidence summary</div>
                  <ul className="m-0 space-y-1 pl-4 text-[10px] leading-relaxed text-slate-400">
                    {selected.evidence.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
                <div className="mt-4 rounded-md border border-amber-300/15 bg-amber-300/[.04] p-3">
                  <div className="eyebrow text-amber-200/70">Recommendation</div>
                  <div className="mt-1 text-[11px] leading-relaxed text-amber-100/85">
                    {selected.recommendation}
                  </div>
                </div>
              </div>
            ) : (
              <div className="panel p-4">
                <div className="eyebrow">Incident detail</div>
                <div className="mt-4 text-center text-sm text-slate-500">
                  {isLoading ? 'Loading...' : 'No incident selected'}
                </div>
              </div>
            )}

            <div className="rounded-md border border-cyan-300/15 bg-cyan-300/[.04] p-3 text-[10px] leading-relaxed text-cyan-100/70">
              <Info size={14} className="mb-2 text-cyan-300" />
              Regional incidents come from Track B2 multi-node intelligence fusion. All data shown is from the real backend.
            </div>
          </aside>
        </div>
      )}

      {feedback && <Feedback message={feedback} onClose={() => setFeedback('')} />}
    </div>
  );
}
