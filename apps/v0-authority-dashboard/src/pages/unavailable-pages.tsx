/**
 * Placeholder pages for backend endpoints not yet implemented
 * Shows truthful "unavailable" states instead of fabricating data
 */

import { Info, Siren, Bell, FileCheck, Activity } from 'lucide-react';
import { PageHeader } from '@/components/dashboard-components';

export function CitizenSOSPageUnavailable() {
  return (
    <div className="content-area">
      <PageHeader
        eyebrow="Citizen safety / emergency requests"
        title="Citizen SOS"
        description="Direct requests from the public for emergency assistance."
      />
      <div className="panel p-8">
        <div className="mx-auto max-w-md text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full border border-slate-700 bg-slate-900/60">
            <Siren size={32} className="text-slate-500" />
          </div>
          <h3 className="mb-2 text-lg font-semibold text-slate-200">SOS Endpoint Not Implemented</h3>
          <p className="mb-4 text-sm leading-relaxed text-slate-400">
            The backend does not currently expose a <code className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-xs text-cyan-300">/api/v1/sos</code> endpoint.
            This page will display real citizen emergency requests when the backend implements SOS tracking.
          </p>
          <div className="rounded-md border border-amber-300/20 bg-amber-300/5 p-3 text-left text-xs leading-relaxed text-amber-100/80">
            <Info size={14} className="mb-1 inline text-amber-300" /> <strong>No mock data shown.</strong> When backend SOS
            functionality is available, this page will connect to real emergency requests without fabricating placeholder data.
          </div>
        </div>
      </div>
    </div>
  );
}

export function AlertsPageUnavailable() {
  return (
    <div className="content-area">
      <PageHeader
        eyebrow="Public messaging / authorization"
        title="Alert Management"
        description="Draft, review, authorize, and track public alerts and warnings."
      />
      <div className="panel p-8">
        <div className="mx-auto max-w-md text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full border border-slate-700 bg-slate-900/60">
            <Bell size={32} className="text-slate-500" />
          </div>
          <h3 className="mb-2 text-lg font-semibold text-slate-200">Alerts Endpoint Verification Needed</h3>
          <p className="mb-4 text-sm leading-relaxed text-slate-400">
            The backend may have <code className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-xs text-cyan-300">/api/v1/alerts/*</code> routes,
            but integration has not been verified. This page will display real alert lifecycle tracking when the endpoint is confirmed operational.
          </p>
          <div className="rounded-md border border-amber-300/20 bg-amber-300/5 p-3 text-left text-xs leading-relaxed text-amber-100/80">
            <Info size={14} className="mb-1 inline text-amber-300" /> <strong>No fabricated alerts.</strong> Alert management
            requires explicit human authorization and will never show mock or synthetic alert data.
          </div>
        </div>
      </div>
    </div>
  );
}

export function ResponsePageUnavailable() {
  return (
    <div className="content-area">
      <PageHeader
        eyebrow="Coordination / human action"
        title="Response & Actions"
        description="Track recommendations, authorization, and execution of response actions."
      />
      <div className="panel p-8">
        <div className="mx-auto max-w-md text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full border border-slate-700 bg-slate-900/60">
            <FileCheck size={32} className="text-slate-500" />
          </div>
          <h3 className="mb-2 text-lg font-semibold text-slate-200">Response Actions Endpoint Not Found</h3>
          <p className="mb-4 text-sm leading-relaxed text-slate-400">
            No <code className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-xs text-cyan-300">/api/v1/actions</code> or
            response coordination endpoint was found in the backend routes. This page will display real response action tracking
            when the backend implements action management.
          </p>
          <div className="rounded-md border border-amber-300/20 bg-amber-300/5 p-3 text-left text-xs leading-relaxed text-amber-100/80">
            <Info size={14} className="mb-1 inline text-amber-300" /> <strong>Action tracking unavailable.</strong> Response
            actions represent human decisions and authorizations. No synthetic actions will be displayed.
          </div>
        </div>
      </div>
    </div>
  );
}

export function AuditPageUnavailable() {
  return (
    <div className="content-area">
      <PageHeader
        eyebrow="Governance / immutable record"
        title="Audit Trail"
        description="Retained record of operator and system activity."
      />
      <div className="panel p-8">
        <div className="mx-auto max-w-md text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full border border-slate-700 bg-slate-900/60">
            <Activity size={32} className="text-slate-500" />
          </div>
          <h3 className="mb-2 text-lg font-semibold text-slate-200">Audit Endpoint Not Implemented</h3>
          <p className="mb-4 text-sm leading-relaxed text-slate-400">
            No <code className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-xs text-cyan-300">/api/v1/audit</code> endpoint
            was found in the backend routes. This page will display real audit logs when the backend implements audit trail
            persistence.
          </p>
          <div className="rounded-md border border-amber-300/20 bg-amber-300/5 p-3 text-left text-xs leading-relaxed text-amber-100/80">
            <Info size={14} className="mb-1 inline text-amber-300" /> <strong>No mock audit records.</strong> Audit trails are
            immutable records of actual system activity. Synthetic entries would undermine governance integrity.
          </div>
        </div>
      </div>
    </div>
  );
}

export function SystemPageLive() {
  return (
    <div className="content-area">
      <PageHeader
        eyebrow="System / resilience"
        title="System Status"
        description="Backend health and system service availability."
      />
      <div className="panel p-8">
        <div className="mx-auto max-w-md text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full border border-slate-700 bg-slate-900/60">
            <Activity size={32} className="text-slate-500" />
          </div>
          <h3 className="mb-2 text-lg font-semibold text-slate-200">Detailed Service Status Unavailable</h3>
          <p className="mb-4 text-sm leading-relaxed text-slate-400">
            The backend provides basic health monitoring at{' '}
            <code className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-xs text-cyan-300">/health</code>, but
            detailed per-service status tracking is not yet implemented. When available, this page will show individual
            service health, uptime, and diagnostics.
          </p>
          <div className="rounded-md border border-cyan-300/20 bg-cyan-300/5 p-3 text-left text-xs leading-relaxed text-cyan-100/80">
            <Info size={14} className="mb-1 inline text-cyan-300" /> <strong>Basic health available.</strong> The backend
            /health endpoint returns overall system status. Granular service monitoring requires backend implementation.
          </div>
        </div>
      </div>
    </div>
  );
}
