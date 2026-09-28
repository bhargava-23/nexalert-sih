/**
 * Historical Data Page - Unavailable State
 * No historical data endpoint found in backend
 */

import { Info, History as HistoryIcon } from 'lucide-react';
import { PageHeader } from '@/components/dashboard-components';

export function HistoricalPageUnavailable() {
  return (
    <div className="content-area">
      <PageHeader
        eyebrow="Analytics / retrospective"
        title="Historical Data"
        description="Review past incidents, trends, and long-term patterns."
      />
      <div className="panel p-8">
        <div className="mx-auto max-w-md text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full border border-slate-700 bg-slate-900/60">
            <HistoryIcon size={32} className="text-slate-500" />
          </div>
          <h3 className="mb-2 text-lg font-semibold text-slate-200">Historical Data Endpoint Not Implemented</h3>
          <p className="mb-4 text-sm leading-relaxed text-slate-400">
            The backend does not currently expose a historical data or analytics endpoint. This page will display incident
            trends, sensor history, and long-term patterns when the backend implements historical data queries.
          </p>
          <div className="rounded-md border border-amber-300/20 bg-amber-300/5 p-3 text-left text-xs leading-relaxed text-amber-100/80">
            <Info size={14} className="mb-1 inline text-amber-300" /> <strong>No mock data shown.</strong> Historical
            analysis requires real backend persistence and time-series queries. Fabricating historical trends would
            misrepresent system capability.
          </div>
        </div>
      </div>
    </div>
  );
}
