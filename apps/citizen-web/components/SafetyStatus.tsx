'use client'

// Normal mode safety status display

import { GlassCard } from '@/components/ui/GlassCard'
import type { Incident, TelemetryRecord } from '@/types'
import { getTimeSince } from '@/lib/utils'

interface SafetyStatusProps {
  incidents: Incident[]
  telemetry: TelemetryRecord[]
}

export function SafetyStatus({ incidents, telemetry }: SafetyStatusProps) {
  const activeIncidents = incidents.filter((inc) => inc.state !== 'RESOLVED')

  // Determine status from REAL backend data only
  const hasConfirmedHazards = activeIncidents.some((inc) =>
    inc.hazard_assessments.some(
      (h) => h.state === 'CONFIRMED' || h.state === 'CRITICAL'
    )
  )

  const hasWatchHazards = activeIncidents.some((inc) =>
    inc.hazard_assessments.some((h) => h.state === 'WATCH' || h.state === 'SUSPECTED')
  )

  let statusIcon = '✅'
  let statusText = 'Area Safe'
  let statusColor = 'text-green-400'
  let statusMessage = 'No active hazards in monitored areas'

  if (hasConfirmedHazards) {
    statusIcon = '🚨'
    statusText = 'Hazard Detected'
    statusColor = 'text-red-400'
    statusMessage = `${activeIncidents.length} ${activeIncidents.length === 1 ? 'hazard' : 'hazards'} confirmed in monitored areas`
  } else if (hasWatchHazards) {
    statusIcon = '⚠️'
    statusText = 'Advisory'
    statusColor = 'text-yellow-400'
    statusMessage = `${activeIncidents.length} ${activeIncidents.length === 1 ? 'hazard' : 'hazards'} being monitored`
  } else if (activeIncidents.length > 0) {
    statusMessage = `${activeIncidents.length} ${activeIncidents.length === 1 ? 'incident' : 'incidents'} being monitored`
  }

  return (
    <GlassCard className="text-center py-8">
      <div className="text-6xl mb-4">{statusIcon}</div>
      <h2 className={`text-3xl font-bold mb-2 ${statusColor}`}>{statusText}</h2>
      <p className="text-zinc-300 mb-4">{statusMessage}</p>
      <p className="text-xs text-zinc-500">
        Updated {telemetry[0] ? getTimeSince(telemetry[0].measurement_timestamp) : 'recently'}
      </p>
    </GlassCard>
  )
}
