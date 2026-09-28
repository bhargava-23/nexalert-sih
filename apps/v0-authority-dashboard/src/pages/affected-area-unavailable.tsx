/**
 * Affected Area Page - Unavailable State
 * No affected-area/exposure endpoint found in backend
 */

import { Info, AreaChart } from 'lucide-react';
import { PageHeader } from '@/components/dashboard-components';

export function AffectedAreaPageUnavailable() {
  return (
    <div className="content-area">
      <PageHeader
        eyebrow="Impact / footprint"
        title="Affected Area"
        description="Understand exposed places, services, and people without collapsing distinct hazards into one score."
      />
      <div className="panel p-8">
        <div className="mx-auto max-w-md text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full border border-slate-700 bg-slate-900/60">
            <AreaChart size={32} className="text-slate-500" />
          </div>
          <h3 className="mb-2 text-lg font-semibold text-slate-200">Affected Area Endpoint Not Implemented</h3>
          <p className="mb-4 text-sm leading-relaxed text-slate-400">
            The backend does not currently expose an affected-area or exposure assessment endpoint. This page will display
            impact footprints, population exposure, and infrastructure analysis when the backend implements spatial exposure
            calculations.
          </p>
          <div className="rounded-md border border-amber-300/20 bg-amber-300/5 p-3 text-left text-xs leading-relaxed text-amber-100/80">
            <Info size={14} className="mb-1 inline text-amber-300" /> <strong>No fabricated impact data.</strong> Affected
            area analysis requires real geospatial intersection with infrastructure, population, and hazard footprints.
            Showing fake exposure counts or percentages would misrepresent actual risk.
          </div>
        </div>
      </div>
    </div>
  );
}
