/**
 * V0 Authority Dashboard - Citizen SOS Page with Real Backend Integration
 *
 * Displays real SOS requests from citizens via backend /api/v1/sos endpoints
 */

import { useState } from 'react';
import { RefreshCw, MapPin, Clock, HeartPulse, Check, AlertTriangle } from 'lucide-react';
import { PageHeader, ActionButton, SectionTitle, StateChip, Feedback } from '@/components/dashboard-components';

interface SOSRequest {
  sos_id: string;
  status: string;
  location_lat?: number;
  location_lon?: number;
  message?: string;
  device_info?: string;
  created_at: string;
  updated_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
}

// Fetch SOS requests from backend
async function fetchSOSRequests(): Promise<SOSRequest[]> {
  const BACKEND_URL = 'https://raspberrypi.tail39c545.ts.net';
  const response = await fetch(`${BACKEND_URL}/api/v1/sos`);
  if (!response.ok) {
    throw new Error(`Failed to fetch SOS requests: ${response.status}`);
  }
  return response.json();
}

// Update SOS status
async function updateSOSStatus(sosId: string, status: string): Promise<void> {
  const BACKEND_URL = 'https://raspberrypi.tail39c545.ts.net';
  const response = await fetch(`${BACKEND_URL}/api/v1/sos/${sosId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status })
  });
  if (!response.ok) {
    throw new Error(`Failed to update SOS status: ${response.status}`);
  }
}

export function CitizenSOSPageLive() {
  const [sosRequests, setSOSRequests] = useState<SOSRequest[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState('');
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  // Load SOS requests
  const loadSOS = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchSOSRequests();
      setSOSRequests(data);
      console.log('[Citizen SOS] Loaded SOS requests:', data.length);
    } catch (err: any) {
      console.error('[Citizen SOS] Failed to load:', err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Acknowledge SOS
  const acknowledgeSOS = async (sosId: string) => {
    setUpdatingId(sosId);
    try {
      await updateSOSStatus(sosId, 'ACKNOWLEDGED');
      setFeedback(`SOS ${sosId.substring(0, 8)} acknowledged`);
      await loadSOS();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setUpdatingId(null);
    }
  };

  // Resolve SOS
  const resolveSOS = async (sosId: string) => {
    setUpdatingId(sosId);
    try {
      await updateSOSStatus(sosId, 'RESOLVED');
      setFeedback(`SOS ${sosId.substring(0, 8)} resolved`);
      await loadSOS();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setUpdatingId(null);
    }
  };

  // Format timestamp
  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  // Load on mount
  useState(() => {
    loadSOS();
  });

  const currentTime = new Date().toLocaleTimeString('en-IN', {
    timeZone: 'Asia/Kolkata',
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });

  // Filter SOS by status
  const openSOS = sosRequests.filter(s => s.status === 'PENDING');
  const acknowledgedSOS = sosRequests.filter(s => s.status === 'ACKNOWLEDGED');
  const resolvedSOS = sosRequests.filter(s => s.status === 'RESOLVED');

  return (
    <div className="content-area">
      <PageHeader
        eyebrow={`Citizen safety / IST ${currentTime}`}
        title="Citizen SOS"
        description="Direct emergency requests from citizens. Real-time backend integration with geolocation tracking."
        actions={
          <>
            {!isLoading && sosRequests.length > 0 && (
              <div className="hidden items-center gap-2 rounded-md border border-cyan-300/20 bg-cyan-300/[.05] px-3 py-2 text-[10px] text-cyan-200 sm:flex">
                <span className="h-1.5 w-1.5 rounded-full bg-cyan-300" />
                {openSOS.length} open SOS
              </div>
            )}
            <ActionButton
              testId="button-refresh-sos"
              onClick={() => {
                loadSOS();
                setFeedback(`SOS requests refreshed at ${currentTime} IST`);
              }}
            >
              <RefreshCw size={13} />
              Refresh
            </ActionButton>
          </>
        }
      />

      {/* Loading state */}
      {isLoading && (
        <div className="mb-4 rounded-md border border-slate-700 bg-slate-900/50 p-4 text-center text-slate-400">
          <RefreshCw size={20} className="mx-auto mb-2 animate-spin" />
          <div className="text-sm">Loading SOS requests from backend...</div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="mb-4 rounded-md border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-300">
          <strong>Backend error:</strong> {error}
        </div>
      )}

      {/* Metrics */}
      {!isLoading && (
        <div className="mb-4 grid grid-cols-2 gap-2 lg:grid-cols-4">
          <div className="panel-flat p-3">
            <div className="eyebrow">OPEN</div>
            <div className="mt-2 text-[21px] font-bold text-red-200">{openSOS.length}</div>
            <div className="mt-1 text-[10px] text-slate-500">Pending acknowledgment</div>
          </div>
          <div className="panel-flat p-3">
            <div className="eyebrow">ACKNOWLEDGED</div>
            <div className="mt-2 text-[21px] font-bold text-amber-200">{acknowledgedSOS.length}</div>
            <div className="mt-1 text-[10px] text-slate-500">Response in progress</div>
          </div>
          <div className="panel-flat p-3">
            <div className="eyebrow">RESOLVED</div>
            <div className="mt-2 text-[21px] font-bold text-emerald-200">{resolvedSOS.length}</div>
            <div className="mt-1 text-[10px] text-slate-500">Completed</div>
          </div>
          <div className="panel-flat p-3">
            <div className="eyebrow">TOTAL</div>
            <div className="mt-2 text-[21px] font-bold text-slate-100">{sosRequests.length}</div>
            <div className="mt-1 text-[10px] text-slate-500">All-time requests</div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && sosRequests.length === 0 && (
        <div className="mb-4 rounded-md border border-slate-700 bg-slate-900/50 p-6 text-center text-slate-400">
          <HeartPulse size={32} className="mx-auto mb-2 text-slate-600" />
          <div className="text-sm font-semibold">No SOS requests</div>
          <div className="mt-1 text-xs">Backend returned empty SOS list. Send a test SOS from Citizen UI.</div>
        </div>
      )}

      {/* SOS Requests List */}
      {!isLoading && sosRequests.length > 0 && (
        <div className="space-y-4">
          {/* Open SOS */}
          {openSOS.length > 0 && (
            <div className="panel overflow-hidden">
              <div className="border-b border-slate-800 px-4 py-3">
                <SectionTitle icon={AlertTriangle}>
                  Open SOS Requests
                </SectionTitle>
              </div>
              <div className="divide-y divide-slate-800">
                {openSOS.map((sos) => (
                  <div key={sos.sos_id} className="p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-sm font-semibold text-slate-200">
                            {sos.sos_id.substring(0, 8)}
                          </span>
                          <StateChip state={sos.status} />
                        </div>
                        <div className="mt-2 space-y-1 text-xs text-slate-400">
                          <div className="flex items-center gap-2">
                            <Clock size={12} />
                            <span>Created: {formatTime(sos.created_at)}</span>
                          </div>
                          {sos.location_lat && sos.location_lon && (
                            <div className="flex items-center gap-2">
                              <MapPin size={12} />
                              <span>Location: {sos.location_lat.toFixed(5)}, {sos.location_lon.toFixed(5)}</span>
                            </div>
                          )}
                          {!sos.location_lat && !sos.location_lon && (
                            <div className="flex items-center gap-2 text-amber-400">
                              <MapPin size={12} />
                              <span>No location available</span>
                            </div>
                          )}
                        </div>
                        {sos.message && (
                          <div className="mt-2 text-sm text-slate-300">{sos.message}</div>
                        )}
                      </div>
                      <div className="flex flex-col gap-2">
                        <button
                          type="button"
                          onClick={() => acknowledgeSOS(sos.sos_id)}
                          disabled={updatingId === sos.sos_id}
                          className="button-compact button-primary"
                          data-testid={`button-acknowledge-${sos.sos_id.substring(0, 8)}`}
                        >
                          {updatingId === sos.sos_id ? 'Updating...' : 'Acknowledge'}
                        </button>
                        <button
                          type="button"
                          onClick={() => resolveSOS(sos.sos_id)}
                          disabled={updatingId === sos.sos_id}
                          className="button-compact"
                          data-testid={`button-resolve-${sos.sos_id.substring(0, 8)}`}
                        >
                          {updatingId === sos.sos_id ? 'Updating...' : 'Resolve'}
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Acknowledged SOS */}
          {acknowledgedSOS.length > 0 && (
            <div className="panel overflow-hidden">
              <div className="border-b border-slate-800 px-4 py-3">
                <SectionTitle icon={Clock}>
                  Acknowledged SOS
                </SectionTitle>
              </div>
              <div className="divide-y divide-slate-800">
                {acknowledgedSOS.map((sos) => (
                  <div key={sos.sos_id} className="p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-sm font-semibold text-slate-200">
                            {sos.sos_id.substring(0, 8)}
                          </span>
                          <StateChip state={sos.status} />
                        </div>
                        <div className="mt-2 space-y-1 text-xs text-slate-400">
                          <div>Created: {formatTime(sos.created_at)}</div>
                          {sos.acknowledged_at && (
                            <div>Acknowledged: {formatTime(sos.acknowledged_at)}</div>
                          )}
                          {sos.location_lat && sos.location_lon && (
                            <div>Location: {sos.location_lat.toFixed(5)}, {sos.location_lon.toFixed(5)}</div>
                          )}
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => resolveSOS(sos.sos_id)}
                        disabled={updatingId === sos.sos_id}
                        className="button-compact"
                        data-testid={`button-resolve-${sos.sos_id.substring(0, 8)}`}
                      >
                        {updatingId === sos.sos_id ? 'Updating...' : 'Resolve'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Resolved SOS */}
          {resolvedSOS.length > 0 && (
            <div className="panel overflow-hidden">
              <div className="border-b border-slate-800 px-4 py-3">
                <SectionTitle icon={Check}>
                  Resolved SOS
                </SectionTitle>
              </div>
              <div className="divide-y divide-slate-800">
                {resolvedSOS.slice(0, 10).map((sos) => (
                  <div key={sos.sos_id} className="p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-sm font-semibold text-slate-400">
                            {sos.sos_id.substring(0, 8)}
                          </span>
                          <StateChip state={sos.status} />
                        </div>
                        <div className="mt-2 space-y-1 text-xs text-slate-500">
                          <div>Created: {formatTime(sos.created_at)}</div>
                          {sos.resolved_at && (
                            <div>Resolved: {formatTime(sos.resolved_at)}</div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Feedback toast */}
      {feedback && <Feedback message={feedback} onClose={() => setFeedback('')} />}
    </div>
  );
}
