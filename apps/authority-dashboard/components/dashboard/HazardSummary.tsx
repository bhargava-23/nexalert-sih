'use client'

// HazardSummary - Current hazards summary

import { GlassPanel } from '@/components/ui/GlassPanel'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { SectionHeader } from '@/components/ui/SectionHeader'
import { EmptyState } from '@/components/ui/EmptyState'
import { formatTimestamp, getTimeSince, getSeverityColor } from '@/lib/utils'
import type { HazardAssessment } from '@/types'

interface HazardSummaryProps {
  hazards: HazardAssessment[]
}

export function HazardSummary({ hazards }: HazardSummaryProps) {
  const activeHazards = hazards.filter(h =>
    h.state && !['NORMAL', 'RESOLVED'].includes(h.state)
  )

  return (
    <div>
      <SectionHeader
        title="Current Hazards"
        subtitle={activeHazards.length > 0 ? `${activeHazards.length} active` : 'All clear'}
      />
      {activeHazards.length === 0 ? (
        <EmptyState
          title="No Active Hazards"
          description="All monitored areas are reporting normal conditions"
          icon="✓"
        />
      ) : (
        <div className="space-y-3">
          {activeHazards.map((hazard) => (
            <GlassPanel key={hazard.assessment_id} className="relative">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-sm font-semibold text-zinc-300 uppercase">
                      {hazard.hazard_type}
                    </span>
                    {hazard.state && (
                      <StatusBadge
                        status={hazard.state}
                        variant="hazard"
                        size="sm"
                      />
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                    {hazard.evidence != null && (
                      <div className="flex justify-between">
                        <span className="text-zinc-500">Evidence:</span>
                        <span className={getSeverityColor(hazard.evidence)}>
                          {(hazard.evidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    )}
                    {hazard.confidence != null && (
                      <div className="flex justify-between">
                        <span className="text-zinc-500">Confidence:</span>
                        <span className={getSeverityColor(hazard.confidence)}>
                          {(hazard.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    )}
                    {hazard.severity != null && (
                      <div className="flex justify-between">
                        <span className="text-zinc-500">Severity:</span>
                        <span className={getSeverityColor(hazard.severity)}>
                          {(hazard.severity * 100).toFixed(0)}%
                        </span>
                      </div>
                    )}
                    {hazard.risk != null && (
                      <div className="flex justify-between">
                        <span className="text-zinc-500">Risk:</span>
                        <span className={getSeverityColor(hazard.risk)}>
                          {(hazard.risk * 100).toFixed(0)}%
                        </span>
                      </div>
                    )}
                  </div>

                  {hazard.created_at && (
                    <div className="mt-2 text-xs text-zinc-500">
                      Detected: {getTimeSince(hazard.created_at)}
                    </div>
                  )}
                </div>
              </div>
            </GlassPanel>
          ))}
        </div>
      )}
    </div>
  )
}
