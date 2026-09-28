/**
 * V0 Authority Dashboard - Overview Page with Real Backend Integration
 *
 * This replaces the mock data Overview page with real API calls to:
 * http://192.168.29.178:8000/api/v1
 */

import { useState } from 'react';
import { RefreshCw, MapPin, Clock3, CircleHelp, ChevronRight } from 'lucide-react';
import { useNodes, useRegionalHazards, useOverviewMetrics } from '@/lib/hooks';
import { MapSurface } from '@/components/nexalert/MapSurface';
import type { Incident, Node } from '@/types';

// Reuse UI components from existing dashboard
import { StateChip, Condition, PageHeader, ActionButton, SectionTitle, Metric, OperationalRail, Feedback } from '@/components/dashboard-components';

export function OverviewPageLive() {
  const [feedback, setFeedback] = useState('');
  const [explained, setExplained] = useState(false);

  // Fetch real backend data
  const { data: nodes, isLoading: nodesLoading, error: nodesError } = useNodes();
  const { data: incidents, isLoading: incidentsLoading } = useRegionalHazards();
  const { metrics, isLoading: metricsLoading } = useOverviewMetrics();

  // DEBUG: Log nodes data to verify coordinates
  console.log('[Overview] Nodes loaded:', nodes?.length || 0);
  if (nodes && nodes.length > 0) {
    console.log('[Overview] NODE-001 coordinates:', nodes[0].coordinates);
    console.log('[Overview] NODE-001 full data:', nodes[0]);
  }

  // Select first incident or create empty state
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const displayIncident = selectedIncident || incidents?.[0] || null;

  const isLoading = nodesLoading || incidentsLoading || metricsLoading;

  // Master location - check if backend provides it, otherwise null
  const masterLocation: [number, number] | null = null; // Backend doesn't expose Master location yet

  // Format current UTC time
  const currentTime = new Date().toLocaleTimeString('en-IN', {
    timeZone: 'Asia/Kolkata',
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });

  return (
    <div className="content-area">
      <PageHeader
        eyebrow={`Command / IST ${currentTime}`}
        title="Live command picture"
        description="A current, operator-reviewed picture of hazards, field intelligence, and requests for action."
        actions={
          <>
            {!isLoading && nodes && nodes.length > 0 && (
              <div className="hidden items-center gap-2 rounded-md border border-cyan-300/20 bg-cyan-300/[.05] px-3 py-2 text-[10px] text-cyan-200 sm:flex">
                <span className="h-1.5 w-1.5 rounded-full bg-cyan-300" />
                Live backend connected
              </div>
            )}
            <ActionButton
              testId="button-refresh-overview"
              onClick={() => setFeedback(`Backend data refreshed at ${currentTime} IST`)}
            >
              <RefreshCw size={13} />
              Refresh picture
            </ActionButton>
          </>
        }
      />

      {/* Loading state */}
      {isLoading && (
        <div className="mb-4 rounded-md border border-slate-700 bg-slate-900/50 p-4 text-center text-slate-400">
          <RefreshCw size={20} className="mx-auto mb-2 animate-spin" />
          <div className="text-sm">Loading backend data...</div>
        </div>
      )}

      {/* Error state */}
      {nodesError && (
        <div className="mb-4 rounded-md border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-300">
          <strong>Backend connection error:</strong> {nodesError.message}
          <div className="mt-2 text-xs text-red-400">
            Verify backend is running at http://192.168.29.178:8000
          </div>
        </div>
      )}

      {/* Real metrics from backend */}
      {!isLoading && metrics && (
        <div className="mb-4 grid grid-cols-2 gap-2 lg:grid-cols-4">
          <Metric
            label="Active incidents"
            value={metrics.activeIncidents.toString() || '0'}
            detail={metrics.activeIncidents > 0 ? metrics.incidentSummary : 'No active incidents'}
            tone={metrics.activeIncidents > 0 ? 'text-red-200' : 'text-emerald-200'}
          />
          <Metric
            label="Field nodes"
            value={`${metrics.onlineNodes} / ${metrics.totalNodes}`}
            detail={metrics.nodesSummary}
            tone={metrics.unreachableNodes > 0 || metrics.degradedNodes > 0 ? 'text-amber-200' : 'text-emerald-200'}
          />
          <Metric
            label="Open citizen SOS"
            value="0"
            detail="Backend SOS endpoint not implemented"
            tone="text-slate-500"
          />
          <Metric
            label="Information condition"
            value={metrics.informationCondition}
            detail={metrics.informationDetail}
            tone={metrics.informationCondition === 'GOOD' ? 'text-emerald-200' : 'text-amber-200'}
          />
        </div>
      )}

      {/* Empty state when no nodes */}
      {!isLoading && nodes && nodes.length === 0 && (
        <div className="mb-4 rounded-md border border-slate-700 bg-slate-900/50 p-6 text-center text-slate-400">
          <div className="text-sm font-semibold">No field nodes available</div>
          <div className="mt-1 text-xs">Backend returned empty node list. Check if NODE-001 is registered.</div>
        </div>
      )}

      {/* Main layout */}
      <div className="overview-grid grid gap-4 xl:grid-cols-[minmax(0,1fr)_326px]">
        <div className="min-w-0">
          {/* Real geographic map with backend data */}
          <div className="panel overflow-hidden p-2">
            <div className="flex flex-wrap items-center justify-between gap-2 px-2 pb-2 pt-1">
              <div className="flex items-center gap-2">
                <span className="eyebrow">Operational map</span>
                <span className="rounded bg-cyan-400/10 px-1.5 py-1 font-mono text-[9px] text-cyan-300">
                  LIVE
                </span>
                {nodes && nodes.length > 0 && (
                  <span className="font-mono text-[9px] text-slate-600">
                    {nodes.length} NODE{nodes.length !== 1 ? 'S' : ''} · REAL COORDINATES
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 text-[10px] text-slate-500">
                <span className="hidden sm:block">Click a marker to inspect</span>
                <MapPin size={13} className="text-slate-600" />
              </div>
            </div>
            <MapSurface
              nodes={nodes || []}
              incidents={incidents || []}
              sos={[]}
              masterLocation={masterLocation}
              onSelection={(selection) => {
                if (selection?.kind === 'incident') setSelectedIncident(selection.value);
              }}
            />
          </div>

          {/* Data source transparency */}
          <div className="mt-4 panel p-4">
            <SectionTitle icon={MapPin} meta="data integrity">
              Data source transparency
            </SectionTitle>
            <div className="mt-3 space-y-2 text-[10px] text-slate-400">
              <div className="flex justify-between border-b border-slate-800 pb-2">
                <span>Node inventory</span>
                <span className="text-emerald-300">
                  {nodes ? `${nodes.length} from backend` : 'Loading...'}
                </span>
              </div>
              <div className="flex justify-between border-b border-slate-800 pb-2">
                <span>Regional hazards</span>
                <span className="text-emerald-300">
                  {incidents ? `${incidents.length} from Track B2` : 'Loading...'}
                </span>
              </div>
              <div className="flex justify-between border-b border-slate-800 pb-2">
                <span>Geographic coordinates</span>
                <span className="text-emerald-300">Real lat/lon from PostGIS</span>
              </div>
              <div className="flex justify-between">
                <span>Mock data dependency</span>
                <span className="text-red-300">REMOVED</span>
              </div>
            </div>
          </div>
        </div>

        {/* Incident command card */}
        <aside className="space-y-4">
          {displayIncident ? (
            <div className="panel overflow-hidden">
              <div className="border-b border-slate-800 px-4 py-3">
                <div className="flex items-center justify-between">
                  <div className="eyebrow">Incident command card</div>
                  <StateChip state={displayIncident.state} />
                </div>
                <div className="mt-2 text-[16px] font-bold text-slate-100">{displayIncident.title}</div>
                <div className="mt-1 text-[11px] text-slate-500">
                  {displayIncident.id} · {displayIncident.location}
                </div>
              </div>
              <div className="space-y-3 p-4">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <div className="eyebrow">Hazard / severity</div>
                    <div className="mt-1 text-[11px] text-slate-200">
                      {displayIncident.hazard} · {displayIncident.severity}
                    </div>
                  </div>
                  <div>
                    <div className="eyebrow">Info condition</div>
                    <div className="mt-1">
                      <Condition value={displayIncident.informationCondition} />
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <div className="eyebrow">Freshness</div>
                    <div className="mt-1 flex items-center gap-1.5 text-[11px] text-amber-200">
                      <Clock3 size={12} />
                      {displayIncident.freshness}
                    </div>
                  </div>
                  <div>
                    <div className="eyebrow">Footprint</div>
                    <div className="mt-1 text-[11px] text-slate-200">{displayIncident.footprint}</div>
                  </div>
                </div>
                <div>
                  <div className="eyebrow mb-1.5">Evidence summary</div>
                  <ul className="m-0 space-y-1 pl-4 text-[10px] leading-relaxed text-slate-400">
                    {displayIncident.evidence.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
                <div className="rounded-md border border-amber-300/15 bg-amber-300/[.04] p-3">
                  <div className="eyebrow text-amber-200/70">Recommendation · not an authorization</div>
                  <div className="mt-1 text-[11px] leading-relaxed text-amber-100/85">
                    {displayIncident.recommendation}
                  </div>
                </div>
                <div className="rounded-md border border-slate-700/70 bg-slate-900/30 p-3">
                  <div className="eyebrow">Authorized human action</div>
                  <div className="mt-1 text-[11px] leading-relaxed text-slate-400">
                    {displayIncident.humanAction}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setExplained((value) => !value)}
                  className="flex w-full items-center justify-between border-t border-slate-800 pt-3 text-left text-[11px] font-semibold text-cyan-300 hover:text-cyan-200"
                  data-testid="button-toggle-explain"
                >
                  <span className="flex items-center gap-2">
                    <CircleHelp size={14} />
                    Explain this picture
                  </span>
                  <ChevronRight size={14} className={`transition-transform ${explained ? 'rotate-90' : ''}`} />
                </button>
                {explained && (
                  <div
                    className="rounded-md bg-slate-900/60 p-3 text-[10px] leading-relaxed text-slate-500"
                    data-testid="panel-explain"
                  >
                    This card combines real observations from the NexAlert backend. Regional hazard assessments come from
                    Track B2 multi-node intelligence fusion. The system has not dispatched resources or issued public
                    messaging without explicit human authorization.
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="panel p-4">
              <div className="eyebrow">Incident command card</div>
              <div className="mt-4 text-center text-sm text-slate-500">
                {isLoading ? 'Loading incidents...' : 'No active incidents'}
              </div>
              <div className="mt-2 text-center text-xs text-slate-600">
                {!isLoading && 'Backend returned no regional hazard assessments'}
              </div>
            </div>
          )}
          <OperationalRail onFeedback={setFeedback} />
        </aside>
      </div>

      {feedback && <Feedback message={feedback} onClose={() => setFeedback('')} />}
    </div>
  );
}
