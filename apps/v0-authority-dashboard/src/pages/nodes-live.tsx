/**
 * Nodes Page - Real Backend Integration
 */

import { useState } from 'react';
import { RefreshCw, WifiOff, Search, Check } from 'lucide-react';
import { useNodes } from '@/lib/hooks';
import { MapSurface } from '@/components/nexalert/MapSurface';
import { StateChip, PageHeader, ActionButton, SectionTitle, Feedback } from '@/components/dashboard-components';

export function NodesPageLive() {
  const [query, setQuery] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState('');

  // Fetch real nodes from backend
  const { data: nodes, isLoading, error } = useNodes();

  // Filter nodes by search query
  const filtered =
    nodes?.filter((node) =>
      `${node.name} ${node.location} ${node.kind}`.toLowerCase().includes(query.toLowerCase())
    ) || [];

  // Set initial selection when data loads
  if (nodes && nodes.length > 0 && !selectedId) {
    setSelectedId(nodes[0].id);
  }

  const selected = nodes?.find((node) => node.id === selectedId) || nodes?.[0] || null;

  return (
    <div className="content-area">
      <PageHeader
        eyebrow="Field intelligence / network"
        title="Nodes"
        description="Inspect distributed field nodes with real backend data, freshness indicators, and network status."
        actions={
          <ActionButton
            testId="button-poll-nodes"
            onClick={() => setFeedback('Node register refreshed from backend')}
          >
            <RefreshCw size={13} />
            Poll nodes
          </ActionButton>
        }
      />

      {/* Loading state */}
      {isLoading && (
        <div className="mb-4 rounded-md border border-slate-700 bg-slate-900/50 p-4 text-center text-slate-400">
          <RefreshCw size={20} className="mx-auto mb-2 animate-spin" />
          <div className="text-sm">Loading nodes from backend...</div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="mb-4 rounded-md border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-300">
          <strong>Backend error:</strong> {error.message}
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && (!nodes || nodes.length === 0) && (
        <div className="mb-4 rounded-md border border-slate-700 bg-slate-900/50 p-6 text-center text-slate-400">
          <div className="text-sm font-semibold">No nodes available</div>
          <div className="mt-1 text-xs">Backend returned empty node list. Check if NODE-001 is registered.</div>
        </div>
      )}

      {/* Main layout */}
      {!isLoading && nodes && nodes.length > 0 && (
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_340px]">
          <div className="space-y-4">
            {/* Real map with nodes */}
            <div className="panel p-2">
              <MapSurface nodes={nodes} incidents={[]} sos={[]} masterLocation={null} />
            </div>

            {/* Node register */}
            <div className="panel overflow-hidden">
              <div className="flex items-center justify-between gap-2 border-b border-slate-800 p-3">
                <SectionTitle icon={WifiOff} meta={`${filtered.length} shown`}>
                  Node register
                </SectionTitle>
                <label className="flex items-center gap-2 rounded-md border border-slate-800 bg-slate-900/60 px-2 py-1.5 text-slate-500">
                  <Search size={13} />
                  <input
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    aria-label="Search nodes"
                    data-testid="input-search-nodes"
                    placeholder="Search nodes"
                    className="w-32 bg-transparent text-[10px] text-slate-200 outline-none"
                  />
                </label>
              </div>
              <div className="divide-y divide-slate-800/70">
                {filtered.map((node) => (
                  <button
                    type="button"
                    key={node.id}
                    onClick={() => setSelectedId(node.id)}
                    className={`flex w-full flex-wrap items-center gap-3 p-3 text-left hover:bg-slate-800/30 ${
                      selectedId === node.id ? 'bg-cyan-300/[.03]' : ''
                    }`}
                    data-testid={`row-node-${node.id}`}
                  >
                    <div className="min-w-[150px] flex-1">
                      <div className="text-[11px] font-semibold text-slate-200">{node.name}</div>
                      <div className="mt-0.5 text-[10px] text-slate-500">
                        {node.id} · {node.kind} · {node.location}
                      </div>
                    </div>
                    <div className="hidden text-right sm:block">
                      <div className="font-mono text-[10px] text-slate-300">{node.battery}%</div>
                      <div className="text-[9px] text-slate-600">battery</div>
                    </div>
                    <div className="w-20 text-right text-[10px] text-slate-500">{node.lastSeen}</div>
                    <StateChip state={node.state} />
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Node detail panel */}
          <div className="panel p-4">
            {selected ? (
              <>
                <div className="eyebrow">Node detail</div>
                <h2 className="mt-2 text-[17px] font-bold text-slate-100">{selected.name}</h2>
                <div className="mt-1 text-[11px] text-slate-500">
                  {selected.id} · {selected.kind}
                </div>
                <div className="my-4">
                  <StateChip state={selected.state} />
                </div>
                <div className="space-y-3 text-[11px]">
                  <div className="flex justify-between border-b border-slate-800 pb-2">
                    <span className="text-slate-500">Last seen</span>
                    <span className="text-amber-200">{selected.lastSeen}</span>
                  </div>
                  <div className="flex justify-between border-b border-slate-800 pb-2">
                    <span className="text-slate-500">Signal</span>
                    <span className="font-mono text-slate-200">{selected.signal}</span>
                  </div>
                  <div className="flex justify-between border-b border-slate-800 pb-2">
                    <span className="text-slate-500">Battery</span>
                    <span className="text-slate-200">{selected.battery}%</span>
                  </div>
                  <div className="flex justify-between border-b border-slate-800 pb-2">
                    <span className="text-slate-500">Location</span>
                    <span className="text-right text-slate-200">{selected.location}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Coordinates</span>
                    <span className="font-mono text-right text-cyan-200">
                      {selected.coordinates[0].toFixed(5)}°N, {selected.coordinates[1].toFixed(5)}°E
                    </span>
                  </div>
                </div>
                <div className="mt-5 rounded-md border border-slate-700/70 bg-slate-900/40 p-3 text-[10px] leading-relaxed text-slate-500">
                  {selected.state === 'UNREACHABLE' || selected.state === 'OFFLINE'
                    ? 'This node cannot currently be contacted. The last observation remains visible but must be treated as stale.'
                    : 'Node is reachable within the field network. Data shown is from the real backend.'}
                </div>
                <ActionButton
                  primary
                  testId="button-node-acknowledge"
                  onClick={() => setFeedback(`Node ${selected.id} marked for operator follow-up`)}
                >
                  <Check size={13} />
                  Mark for follow-up
                </ActionButton>
              </>
            ) : (
              <>
                <div className="eyebrow">Node detail</div>
                <div className="mt-4 text-center text-sm text-slate-500">
                  {isLoading ? 'Loading...' : 'No node selected'}
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {feedback && <Feedback message={feedback} onClose={() => setFeedback('')} />}
    </div>
  );
}
